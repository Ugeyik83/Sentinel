"""
crew/runner.py — SENTINEL Simülasyon Çalıştırıcı

Konuşma akışı buradan üretilir ve kaydedilir.

Akış:
  1. Debate katmanı (MAD) — ajanlar arası yapılandırılmış tartışma
     Her tur, her ajan yanıtı conversation_log'a eklenir
  2. CrewAI katmanı — hiyerarşik görev simülasyonu
  3. Çıktılar birleştirilir, dosyaya kaydedilir

Konuşma akışı formatı (conversation_log):
  [
    {"turn": 0, "round": 0, "round_type": "opening",
     "agent": "CFO", "role_type": "org_chart",
     "message": "...", "timestamp": "..."},
    {"turn": 1, "round": 0, "round_type": "opening",
     "agent": "Devil's Advocate", ...},
    ...
  ]
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from crewai import Crew, Process

from crew.conflict_tracker import ConflictTracker
from crew.tasks import ScenarioTaskBuilder
from crew.org_loader import OrgLoader

logger = logging.getLogger(__name__)

DEBATE_ENABLED = True   # env'den okunabilir


class SimulationRunner:
    """
    Mevcut runner.py ile geriye dönük uyumlu.
    Debate katmanı + konuşma logu eklendi.
    """

    def __init__(self, run_dir: str,
                 org_chart_path: str = "config/org_chart.json"):
        self.run_dir = Path(run_dir)
        self.loader = OrgLoader(org_chart_path)
        self.agents = self.loader.build_agents()
        self.task_builder = ScenarioTaskBuilder()
        self.conflict_tracker = ConflictTracker(run_dir)

    def run(self, scenario: dict) -> dict:
        """
        Geriye dönük uyumlu — eski injector.py çağrıları çalışmaya devam eder.
        Debate katmanını otomatik aktive eder.
        """
        run_id = f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        return run_full(
            scenario=scenario,
            run_dir=str(self.run_dir),
            org_chart_path="config/org_chart.json",
            run_id=run_id,
        )


def run_full(
    scenario: dict,
    run_dir: str,
    org_chart_path: str = "config/org_chart.json",
    run_id: str = None,
    use_debate: bool = True,
) -> dict:
    """
    Ana simülasyon fonksiyonu.
    Debate + CrewAI + konuşma logu.
    """
    if run_id is None:
        run_id = f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    run_path = Path(run_dir)
    conversation_log = []   # ← Tüm konuşma akışı buraya
    debate_result = None
    crewai_result = None

    loader = OrgLoader(org_chart_path)
    agents = loader.build_agents()
    task_builder = ScenarioTaskBuilder()
    conflict_tracker = ConflictTracker(run_dir)

    # Org chart ajanlarını dict formatına çevir (debate için)
    org_agents_list = _agents_to_list(loader)

    # ── DEBATE KATMANI ────────────────────────────────────────────────────
    if use_debate and DEBATE_ENABLED:
        try:
            from crew.debate.orchestrator import run_debate

            # run_debate'i konuşma logu yakalayacak şekilde sarmalıyoruz
            debate_result = run_debate(
                scenario=scenario,
                org_agents=org_agents_list,
                run_id=run_id,
            )

            # Debate trace'inden konuşma akışını çıkar
            conversation_log = _extract_conversation(debate_result, run_id)

        except Exception as e:
            logger.error(f"Debate hatası: {e}")
            conversation_log.append(_system_msg(f"Debate katmanı başlatılamadı: {e}"))

    # ── CREWAI KATMANI ────────────────────────────────────────────────────
    try:
        # Debate bağlamını senaryo açıklamasına ekle
        enriched_scenario = _enrich_scenario_with_debate(scenario, debate_result)
        tasks = task_builder.build_tasks(enriched_scenario, agents)

        crew = Crew(
            agents=list(agents.values()),
            tasks=tasks,
            process=Process.sequential,
            verbose=False,
        )

        crewai_output = crew.kickoff()
        crewai_result = str(crewai_output)

        # CrewAI görev çıktılarını konuşma loguna ekle
        conversation_log.extend(
            _extract_crewai_conversation(tasks, crewai_result)
        )

    except Exception as e:
        logger.error(f"CrewAI hatası: {e}")
        conversation_log.append(_system_msg(f"CrewAI simülasyonu başlatılamadı: {e}"))

    # ── ÇIKTI ────────────────────────────────────────────────────────────
    output = {
        "run_id": run_id,
        "scenario_id": scenario.get("id", scenario.get("name", "unknown")),
        "scenario_name": scenario.get("name", ""),
        "simulation_mode": scenario.get("simulation_mode", "hierarchical"),
        "started_at": datetime.now(timezone.utc).isoformat(),
        "debate_result": debate_result,
        "crewai_result": crewai_result,
        "conversation_log": conversation_log,       # ← Ana konuşma akışı
        "conflict_log": conflict_tracker.get_log(),
        "final_decision": (
            debate_result.get("decision", "") if debate_result
            else crewai_result or ""
        ),
        "confidence": debate_result.get("confidence", 0.5) if debate_result else 0.5,
        "escalation": debate_result.get("escalation", "OTONOM") if debate_result else "OTONOM",
    }

    # Kaydet
    _save(run_path, output)
    return output


# ── KONUŞMA AKIŞI ÇIKARTICI ───────────────────────────────────────────────

def _extract_conversation(debate_result: dict, run_id: str) -> list[dict]:
    """
    Debate trace dosyasından tur tur konuşma akışını çıkar.
    Trace yoksa debate_result'taki özet bilgiyle yetinir.
    """
    conversation = []
    turn = 0

    # Trace dosyasından oku
    trace_path = Path(debate_result.get("trace_path", ""))
    if trace_path.exists():
        try:
            trace = json.loads(trace_path.read_text(encoding="utf-8"))
            for round_data in trace.get("rounds", []):
                round_num = round_data["round"]
                round_type = round_data["type"]

                for resp in round_data.get("responses", []):
                    conversation.append({
                        "turn": turn,
                        "round": round_num,
                        "round_type": round_type,
                        "agent": resp.get("agent", "?"),
                        "role_type": resp.get("role_type", "org_chart"),
                        "message": resp.get("position", ""),
                        "confidence": resp.get("confidence"),
                        "timestamp": resp.get("timestamp", ""),
                        "source": "debate",
                    })
                    turn += 1

                # Tur sonu konvergans notu
                conv = round_data.get("convergence", {})
                conversation.append({
                    "turn": turn,
                    "round": round_num,
                    "round_type": "convergence_check",
                    "agent": "SYSTEM",
                    "role_type": "system",
                    "message": (
                        f"Konvergans: {conv.get('convergence_score', 0):.2f} | "
                        f"Sebep: {conv.get('reason', '?')} | "
                        f"Devam: {'Hayır' if conv.get('should_stop') else 'Evet'}"
                    ),
                    "timestamp": "",
                    "source": "system",
                })
                turn += 1

            # Judge kararı
            final = trace.get("final_decision", {})
            if final:
                conversation.append({
                    "turn": turn,
                    "round": -1,
                    "round_type": "judge",
                    "agent": "Judge",
                    "role_type": "judge",
                    "message": (
                        f"[KARAR] {final.get('decision', '')}\n"
                        f"[GEREKÇE] {final.get('rationale', '')}\n"
                        f"[MUHALİF] {final.get('dissent', '')}\n"
                        f"[ESCALASYON] {final.get('escalation', 'OTONOM')}"
                    ),
                    "confidence": final.get("confidence"),
                    "timestamp": final.get("decided_at", ""),
                    "source": "judge",
                })
                turn += 1

        except Exception as e:
            logger.warning(f"Trace okunamadı: {e}")
            conversation.append(_system_msg(f"Trace okunamadı: {e}"))

    else:
        # Trace yok — özet bilgiden üret
        conversation.append({
            "turn": 0,
            "round": 0,
            "round_type": "summary",
            "agent": "SYSTEM",
            "role_type": "system",
            "message": (
                f"Debate tamamlandı | Protokol: {debate_result.get('protocol')} | "
                f"Tur: {debate_result.get('rounds_completed')} | "
                f"Konvergans: {debate_result.get('convergence_trajectory', [{}])[-1] if debate_result.get('convergence_trajectory') else 'N/A'}"
            ),
            "source": "system",
        })

    return conversation


def _extract_crewai_conversation(tasks, crewai_output: str) -> list[dict]:
    """
    CrewAI görev çıktılarını konuşma formatına çevir.
    Her görev = bir konuşma turu.
    """
    conversation = []
    # CrewAI'da görev çıktıları doğrudan erişilebilir değil — özet ekle
    conversation.append({
        "turn": 9000,   # Debate'den sonra
        "round": -1,
        "round_type": "crewai_summary",
        "agent": "CrewAI Simülasyon",
        "role_type": "crewai",
        "message": crewai_output[:2000] if crewai_output else "CrewAI çıktısı yok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "crewai",
    })
    return conversation


def _enrich_scenario_with_debate(scenario: dict, debate_result: dict | None) -> dict:
    """Debate sonucunu senaryo açıklamasına ekle — CrewAI bağlam olarak kullanır."""
    if not debate_result:
        return scenario
    enriched = dict(scenario)
    debate_ctx = (
        f"\n\n[DEBATE ÖN ANALİZ — {debate_result.get('protocol', '')} protokolü]\n"
        f"Öneri: {debate_result.get('decision', '')}\n"
        f"Muhalefet: {debate_result.get('dissent', '')}\n"
        f"Güven: {debate_result.get('confidence', 0):.2f}"
    )
    enriched["description"] = enriched.get("description", "") + debate_ctx
    return enriched


# ── YARDIMCI ─────────────────────────────────────────────────────────────────

def _agents_to_list(loader: OrgLoader) -> list[dict]:
    """OrgLoader'daki CrewAI Agent'ları debate için dict listesine çevir."""
    result = []
    hierarchy = loader.chart.get("hierarchy", {})
    _flatten_node(hierarchy, result)
    return result


def _flatten_node(node: dict, result: list):
    result.append({
        "role": node.get("role", ""),
        "id": node.get("id", ""),
        "domain": node.get("domain", []),
        "decision_authority": node.get("decision_authority", "functional"),
        "level": node.get("level", 2),
    })
    for child in node.get("delegates_to", []):
        _flatten_node(child, result)


def _system_msg(text: str) -> dict:
    return {
        "turn": -1,
        "round": -1,
        "round_type": "system",
        "agent": "SYSTEM",
        "role_type": "system",
        "message": text,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "system",
    }


def _save(run_path: Path, output: dict):
    sim_dir = run_path / "simulation"
    sim_dir.mkdir(parents=True, exist_ok=True)
    result_path = sim_dir / "result.json"
    result_path.write_text(
        json.dumps(output, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    # Konuşma akışını ayrı dosyaya da yaz — UI okur
    conv_path = sim_dir / "conversation_log.json"
    conv_path.write_text(
        json.dumps(output["conversation_log"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info(f"Simülasyon kaydedildi: {result_path}")
