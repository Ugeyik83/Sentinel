"""
crew/runner.py
CrewAI simülasyon çalıştırıcı.
Hiyerarşik veya Konsensüs — debate katmanı entegre.

FIX (2026-05): Groq + hierarchical modda internal delegation tool çağrıları
(Groq tool calling) 'tool_use_failed' hatasına düşebiliyor.
Bu nedenle provider=groq iken hierarchical istenirse otomatik sequential'a fallback yapar.
"""

import json
import logging
from pathlib import Path

from crewai import Crew, Process
from crew.org_loader import OrgLoader
from crew.tasks import ScenarioTaskBuilder
from crew.conflict_tracker import ConflictTracker
from crew.debate.orchestrator import DebateOrchestrator

from app.utils.llm_client import get_provider

logger = logging.getLogger(__name__)


class SimulationRunner:
    def __init__(self, run_dir: str, org_chart_path: str = "config/org_chart.json"):
        self.run_dir = Path(run_dir)
        self.org_chart_path = org_chart_path

        self.loader = OrgLoader(org_chart_path)
        self.agents = self.loader.build_agents()

        self.task_builder = ScenarioTaskBuilder()
        self.conflict_tracker = ConflictTracker(run_dir)
        self.debate = DebateOrchestrator(run_dir)

    def run(self, scenario: dict) -> dict:
        mode = scenario.get("simulation_mode", "hierarchical")

        # ✅ Groq provider + hierarchical => tool/delegation hatalarına düşebiliyor
        # (delegate_work_to_coworker tool çağrısı sırasında Groq "tool_use_failed" dönebiliyor)
        provider = get_provider()
        if provider == "groq" and mode == "hierarchical":
            logger.warning(
                "Provider=groq iken hierarchical mod tool/delegation hatasına düşebilir. "
                "Otomatik olarak sequential moda geçiliyor."
            )
            mode = "sequential"

        logger.info(f"Simülasyon başlıyor: {scenario.get('name')} | mod: {mode} | provider: {provider}")

        # ── Faz 1: CrewAI simülasyonu ─────────────────────────────────────────
        tasks = self.task_builder.build_tasks(scenario, self.agents)

        process = Process.hierarchical if mode == "hierarchical" else Process.sequential
        manager = self.agents.get("managing_director") if mode == "hierarchical" else None

        # Manager agent agents listesinden çıkarılmalı (hierarchical için)
        agent_list = list(self.agents.values())
        if manager and manager in agent_list:
            agent_list = [a for a in agent_list if a != manager]

        crew = Crew(
            agents=agent_list,
            tasks=tasks,
            process=process,
            manager_agent=manager,
            verbose=True,
        )

        crew_result = crew.kickoff()
        crew_result_str = str(crew_result)

        # Org pozisyonlarını görev çıktılarından çıkar
        org_positions = self._extract_org_positions(tasks)

        # ── Faz 2: Debate katmanı ─────────────────────────────────────────────
        logger.info("Debate katmanı başlıyor...")
        debate_result = self.debate.run(
            scenario=scenario,
            simulation_result=crew_result_str,
            org_positions=org_positions,
        )

        # ── Sonucu birleştir ──────────────────────────────────────────────────
        output = {
            "scenario_id": scenario.get("id"),
            "scenario_name": scenario.get("name"),
            "simulation_mode": mode,
            "provider": provider,
            "result": crew_result_str,
            "debate": debate_result,
            "conflict_log": self.conflict_tracker.get_log(),
            "final_decision": debate_result.get("debate_summary", {}).get("judge_decision", crew_result_str),
        }

        out_path = self.run_dir / "simulation" / "result.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2))

        logger.info(f"Simülasyon + Debate tamamlandı: {scenario.get('name')}")
        return output

    def _extract_org_positions(self, tasks: list) -> dict:
        """Görev çıktılarından org chart pozisyonlarını çıkar."""
        positions = {}
        for task in tasks:
            agent_role = getattr(task.agent, "role", "unknown")
            output = getattr(task, "output", None)
            if output:
                raw = getattr(output, "raw", str(output))
                positions[agent_role] = raw[:500]
        return positions