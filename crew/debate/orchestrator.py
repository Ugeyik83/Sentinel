"""
crew/debate/orchestrator.py
Debate loop orkestratörü.
Faz 1: 3 sabit tur, senkron. Adaptive stopping Faz 2'de.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from crew.debate.roles import DevilsAdvocate, RedTeam, Judge
from crew.debate.trace_logger import TraceLogger

logger = logging.getLogger(__name__)

MAX_ROUNDS = 3


class DebateOrchestrator:
    """
    Senaryo + simülasyon sonucu → debate → final karar.

    Akış:
    Tur 0 (Açılış): Tüm org chart ajanları kör paralel analiz
    Tur 1 (İtiraz):  Devil's Advocate + Red Team devreye girer
    Tur 2 (Kapanış): Sentez + Judge kararı
    """

    def __init__(self, run_dir: str):
        self.run_dir = Path(run_dir)
        self.devil = DevilsAdvocate()
        self.red_team = RedTeam()
        self.judge = Judge()
        self.trace = TraceLogger(run_dir)

    def run(self, scenario: dict, simulation_result: str,
            org_positions: dict) -> dict:
        """
        Ana debate döngüsü.

        Args:
            scenario: Senaryo dict
            simulation_result: CrewAI simülasyon çıktısı (string)
            org_positions: {role: analysis_text} — org chart ajanlarının görüşleri

        Returns:
            debate_result dict
        """
        scenario_name = scenario.get("name", "")
        time_horizon = scenario.get("time_horizon_days", 90)
        history = []

        logger.info(f"Debate başlıyor: {scenario_name}")

        # ── TUR 0: Açılış ─────────────────────────────────────────────────────
        context_tur0 = self._build_opening_context(
            scenario_name, time_horizon, simulation_result, org_positions
        )

        devil_opening = self.devil.respond(
            f"Senaryo: {context_tur0}\n\nAçılış itirazın nedir?",
            history
        )
        self.trace.log_turn(0, "Devil's Advocate", "opening", devil_opening)

        red_opening = self.red_team.respond(
            f"Senaryo: {context_tur0}\n\nBaşarısızlık modlarını listele.",
            history
        )
        self.trace.log_turn(0, "Red Team", "opening", red_opening)

        history.append({
            "content": f"Tur 0 açılış:\n{context_tur0}",
            "response": f"Devil's Advocate: {devil_opening}\n\nRed Team: {red_opening}"
        })

        # ── TUR 1: İtiraz ─────────────────────────────────────────────────────
        org_consensus = self._summarize_org_positions(org_positions)

        devil_rebuttal = self.devil.respond(
            (
                f"Org chart konsensüsü: {org_consensus}\n\n"
                f"Devil's Advocate açılışı: {devil_opening}\n\n"
                f"Red Team bulguları: {red_opening}\n\n"
                "Bu bulguları dikkate alarak en güçlü tek itirazını yenile."
            ),
            history
        )
        self.trace.log_turn(1, "Devil's Advocate", "rebuttal", devil_rebuttal)

        red_rebuttal = self.red_team.respond(
            (
                f"Org chart konsensüsü: {org_consensus}\n\n"
                f"Tur 0 başarısızlık modları: {red_opening}\n\n"
                "En kritik başarısızlık moduna odaklanarak derinleştir. "
                "Hala 3 mod yaz ama birincisini daha somutlaştır."
            ),
            history
        )
        self.trace.log_turn(1, "Red Team", "rebuttal", red_rebuttal)

        history.append({
            "content": "Tur 1 itiraz turu",
            "response": (
                f"Devil's Advocate (itiraz): {devil_rebuttal}\n\n"
                f"Red Team (derinleştirme): {red_rebuttal}"
            )
        })

        # ── TUR 2: Kapanış + Judge ─────────────────────────────────────────────
        judge_context = (
            f"Senaryo: {scenario_name} ({time_horizon} gün)\n\n"
            f"Simülasyon bulguları: {simulation_result[:1500]}\n\n"
            f"Org chart pozisyonları:\n{org_consensus}\n\n"
            f"Devil's Advocate son itirazı: {devil_rebuttal}\n\n"
            f"Red Team başarısızlık modları: {red_rebuttal}\n\n"
            "Tüm bu argümanları değerlendirerek final kararını ver."
        )

        judge_decision = self.judge.respond(judge_context, history)
        self.trace.log_turn(2, "Judge", "decision", judge_decision)

        # ── Sonuç ─────────────────────────────────────────────────────────────
        result = {
            "scenario": scenario_name,
            "rounds_completed": MAX_ROUNDS,
            "debate_summary": {
                "devil_advocate_final": devil_rebuttal,
                "red_team_failures": red_rebuttal,
                "judge_decision": judge_decision,
            },
            "trace": self.trace.get_log(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }

        # Kaydet
        out_path = self.run_dir / "simulation" / "debate_result.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2))

        logger.info(f"Debate tamamlandı: {scenario_name}")
        return result

    def _build_opening_context(self, scenario_name, time_horizon,
                                simulation_result, org_positions) -> str:
        org_summary = "\n".join([
            f"  - {role}: {text[:200]}"
            for role, text in list(org_positions.items())[:5]
        ])
        return (
            f"Senaryo: {scenario_name}\n"
            f"Zaman ufku: {time_horizon} gün\n\n"
            f"Simülasyon özeti: {simulation_result[:800]}\n\n"
            f"Org chart pozisyonları:\n{org_summary}"
        )

    def _summarize_org_positions(self, org_positions: dict) -> str:
        if not org_positions:
            return "Org chart pozisyonu yok."
        lines = []
        for role, text in list(org_positions.items())[:6]:
            short = text[:150].replace("\n", " ")
            lines.append(f"  [{role}]: {short}...")
        return "\n".join(lines)
