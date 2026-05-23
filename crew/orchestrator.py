"""
crew/debate/orchestrator.py

MAD (Multi-Agent Debate) ana akış kontrolcüsü.

Akış:
1. Protokol seç (impact score'a göre)
2. Ajanları hazırla (org chart + debate rolleri)
3. Opening turu — kör, paralel
4. Adaptive stopping — dur mu devam et mi?
5. Rebuttal turları — şeffaf
6. Judge — final karar + muhalefet şerhi + escalation kararı
7. Trace kaydet

Literatür:
- Opening round kör çalışmalı (anchoring bias önlemi)
- 3 tur yeterli, adaptive stopping token maliyetini %40-60 düşürür
- Critic + Defender + Judge üçlüsü en sade etkili pattern
"""

import asyncio
import logging
import os
import uuid
from datetime import datetime, timezone

import yaml
from openai import OpenAI

from crew.debate.adaptive_stopping import AdaptiveStopping
from crew.debate.memory_link import find_similar_debates, format_memory_context, get_outcome_lessons
from crew.debate.roles import DevilsAdvocate, Judge, RedTeam
from crew.debate.trace_logger import TraceLogger

logger = logging.getLogger(__name__)

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
MODEL = os.environ.get("LLM_MODEL_NAME", "gpt-4o")

# Protokol config yükle
_PROTOCOLS_PATH = os.path.join(os.path.dirname(__file__), "config", "protocols.yaml")
with open(_PROTOCOLS_PATH, encoding="utf-8") as f:
    PROTOCOLS = yaml.safe_load(f)["protocols"]


def select_protocol(scenario: dict) -> tuple[str, dict]:
    """
    Senaryo impact_score ve uncertainty'e göre protokol seç.
    Varsayılan: standard_debate.
    """
    impact = scenario.get("impact_score", 0.5)
    uncertainty = scenario.get("uncertainty", 0.5)

    if impact >= 0.7 or uncertainty >= 0.6:
        return "adversarial_deep", PROTOCOLS["adversarial_deep"]
    elif impact >= 0.4:
        return "standard_debate", PROTOCOLS["standard_debate"]
    else:
        return "fast_consensus", PROTOCOLS["fast_consensus"]


def _build_org_agent_prompt(agent_info: dict, scenario: dict, memory_ctx: str) -> str:
    """Org chart ajanı için sistem prompt."""
    return (
        f"Sen {agent_info['role']} pozisyonundasın. "
        f"Domain: {', '.join(agent_info.get('domain', []))}. "
        f"Karar yetkisi: {agent_info.get('decision_authority', 'functional')}. "
        f"Sadece kendi domain'inden konuş. "
        f"Yanıtın 3-4 cümle, net pozisyon + gerekçe + güven skoru (0-1). "
        f"\n{memory_ctx}"
    )


def _call_org_agent(agent_info: dict, scenario: dict, prior_responses: list, round_num: int, memory_ctx: str) -> dict:
    """Org chart ajanını çağır."""
    system = _build_org_agent_prompt(agent_info, scenario, memory_ctx)

    if round_num == 0:
        # Opening: kör — sadece senaryo görür
        user = (
            f"Senaryo: {scenario.get('title', '')}\n"
            f"Detay: {scenario.get('description', '')}\n\n"
            f"Bu senaryoya kendi domain'inden bakarak pozisyonunu açıkla. "
            f"Önerilen aksiyonu ve güven skorunu belirt."
        )
    else:
        # Rebuttal: diğer yanıtları da görür
        prior_text = "\n".join([
            f"- {r['agent']}: {r['position']}"
            for r in prior_responses
            if r.get("agent") != agent_info["role"]
        ])
        user = (
            f"Senaryo: {scenario.get('title', '')}\n\n"
            f"Diğer ajanların Tur {round_num - 1} görüşleri:\n{prior_text}\n\n"
            f"Bu görüşleri değerlendirerek kendi pozisyonunu güncelle veya savun. "
            f"Neden katılıyor ya da katılmıyor musun?"
        )

    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=400,
            temperature=0.7,
        )
        content = resp.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Org agent {agent_info['role']} hatası: {e}")
        content = f"[Yanıt üretilemedi: {e}]"

    return {
        "agent": agent_info["role"],
        "role_type": "org_chart",
        "round": round_num,
        "position": content,
        "confidence": 0.7,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def run_debate(scenario: dict, org_agents: list[dict], run_id: str | None = None) -> dict:
    """
    Ana debate fonksiyonu.

    Args:
        scenario: Senaryo dict (title, description, impact_score, uncertainty, ...)
        org_agents: Org chart'tan seçilen ajan listesi (role, domain, decision_authority)
        run_id: Mevcut simülasyon run ID'si (trace kayıt için)

    Returns:
        debate_result dict — orchestrator, simulate.py'ye bunu verir
    """
    # Debate ID
    debate_id = f"deb_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    # Protokol seç
    protocol_name, protocol_cfg = select_protocol(scenario)
    logger.info(f"Debate {debate_id} başladı | Protokol: {protocol_name} | Senaryo: {scenario.get('title', '')}")

    # Trace logger başlat
    tracer = TraceLogger(
        debate_id=debate_id,
        scenario_id=scenario.get("id", scenario.get("title", "unknown")),
        protocol=protocol_name,
    )

    # Memory context yükle
    similar = find_similar_debates(scenario, top_k=3)
    memory_ctx = format_memory_context(similar)
    lessons = get_outcome_lessons()
    if lessons:
        memory_ctx += f"\n\nGeçmişten öğrenilenler:\n{lessons}"

    # Debate rolleri hazırla
    devil = DevilsAdvocate() if protocol_cfg["agents"]["devil_advocate"] else None
    red_team = RedTeam() if protocol_cfg["agents"]["red_team"] else None
    judge = Judge()

    # Adaptive stopping hazırla
    stopper = AdaptiveStopping(
        threshold=protocol_cfg["convergence"]["threshold"],
        max_rounds=protocol_cfg["rounds"]["max"],
        min_rounds=protocol_cfg["rounds"]["min"],
    )

    # Org chart ajanlarını protokole göre sınırla
    agent_count = min(
        protocol_cfg["agents"]["org_chart_count"],
        len(org_agents)
    )
    active_org_agents = org_agents[:agent_count]

    all_responses: list[dict] = []
    round_num = 0

    # --- TUR DÖNGÜSÜ ---
    while True:
        round_type = "opening" if round_num == 0 else "rebuttal"
        round_responses: list[dict] = []

        # 1. Org chart ajanları
        for agent_info in active_org_agents:
            resp = _call_org_agent(
                agent_info=agent_info,
                scenario=scenario,
                prior_responses=all_responses,
                round_num=round_num,
                memory_ctx=memory_ctx,
            )
            round_responses.append(resp)

        # 2. Devil's Advocate
        if devil:
            da_resp = devil.respond(scenario, round_responses, round_num)
            round_responses.append(da_resp)

        # 3. Red Team (sadece adversarial_deep ve round > 0)
        if red_team and round_num > 0:
            rt_resp = red_team.respond(scenario, round_responses, round_num)
            round_responses.append(rt_resp)

        all_responses.extend(round_responses)

        # 4. Adaptive stopping kontrolü
        stop_state = stopper.update(round_responses)
        tracer.log_round(round_num, round_type, round_responses, stop_state)

        if stop_state["should_stop"]:
            logger.info(
                f"Debate durdu | Tur: {round_num} | "
                f"Sebep: {stop_state['reason']} | "
                f"Konvergans: {stop_state['convergence_score']:.2f}"
            )
            break

        round_num += 1

    # --- JUDGE ---
    decision = judge.adjudicate(scenario, all_responses)
    tracer.log_decision(decision)

    # Escalation kontrolü
    protocol_human_threshold = protocol_cfg["escalation"]["human_threshold"]
    if decision.get("confidence", 1.0) < (1 - protocol_human_threshold):
        decision["escalation"] = "YK_GEREKLI"
        logger.info(f"Debate {debate_id} → YK'ya escalate edildi (güven düşük)")

    # Metadata
    tracer.log_metadata(
        protocol=protocol_name,
        rounds_completed=round_num + 1,
        agents_used=[a["role"] for a in active_org_agents],
        devil_advocate_active=devil is not None,
        red_team_active=red_team is not None,
        similar_debates_found=len(similar),
        model=MODEL,
    )

    # Kaydet
    saved_path = tracer.save(run_id=run_id)

    result = {
        "debate_id": debate_id,
        "protocol": protocol_name,
        "rounds_completed": round_num + 1,
        "convergence_trajectory": tracer.convergence_trajectory,
        "decision": decision.get("decision", ""),
        "rationale": decision.get("rationale", ""),
        "dissent": decision.get("dissent", ""),
        "confidence": decision.get("confidence", 0.5),
        "escalation": decision.get("escalation", "OTONOM"),
        "agents_participated": [r["agent"] for r in all_responses if r["round"] == 0],
        "trace_path": str(saved_path),
        "memory_context_used": len(similar) > 0,
        "similar_debates": similar,
    }

    logger.info(
        f"Debate {debate_id} tamamlandı | "
        f"Karar: {result['decision'][:60]}... | "
        f"Güven: {result['confidence']:.2f} | "
        f"Escalation: {result['escalation']}"
    )
    return result
