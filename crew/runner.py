"""
crew/runner.py
CrewAI simülasyon çalıştırıcı.
Hiyerarşik veya Konsensüs — senaryoya göre seçilir.
"""

import json
import logging
from pathlib import Path
from crewai import Crew, Process
from crew.org_loader import OrgLoader, ScenarioTaskBuilder
from crew.conflict_tracker import ConflictTracker

logger = logging.getLogger(__name__)


class SimulationRunner:
    def __init__(self, run_dir: str,
                 org_chart_path: str = "config/org_chart.json"):
        self.run_dir = Path(run_dir)
        self.org_chart_path = org_chart_path
        self.loader = OrgLoader(org_chart_path)
        self.agents = self.loader.build_agents()
        self.task_builder = ScenarioTaskBuilder()
        self.conflict_tracker = ConflictTracker(run_dir)

    def run(self, scenario: dict) -> dict:
        mode = scenario.get("simulation_mode", "hierarchical")
        logger.info(f"Simülasyon başlıyor: {scenario['name']} | mod: {mode}")

        tasks = self.task_builder.build_tasks(scenario, self.agents)
        process = (
            Process.hierarchical if mode == "hierarchical"
            else Process.sequential
        )

        manager = self.agents.get("managing_director") if mode == "hierarchical" else None

        crew = Crew(
            agents=list(self.agents.values()),
            tasks=tasks,
            process=process,
            manager_agent=manager,
            verbose=True,
        )

        result = crew.kickoff()

        # Sonucu kaydet
        output = {
            "scenario_id": scenario.get("id"),
            "scenario_name": scenario.get("name"),
            "simulation_mode": mode,
            "result": str(result),
            "conflict_log": self.conflict_tracker.get_log(),
        }

        out_path = self.run_dir / "simulation" / "result.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2))

        logger.info(f"Simülasyon tamamlandı: {scenario['name']}")
        return output
