"""
crew/runner.py — CrewAI simülasyon çalıştırıcı.
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
        self.loader = OrgLoader(org_chart_path)
        self.agents = self.loader.build_agents()
        self.task_builder = ScenarioTaskBuilder()
        self.conflict_tracker = ConflictTracker(run_dir)

    def run(self, scenario: dict) -> dict:
        mode = scenario.get("simulation_mode", "sequential")
        logger.info(f"Simülasyon: {scenario['name']} | mod: {mode}")

        tasks = self.task_builder.build_tasks(scenario, self.agents)

        # Her modda sequential kullan — en stabil
        all_agents = list(self.agents.values())

        crew = Crew(
            agents=all_agents,
            tasks=tasks,
            process=Process.sequential,
            verbose=True,
        )

        result = crew.kickoff()

        output = {
            "scenario_id": scenario.get("id"),
            "scenario_name": scenario.get("name"),
            "simulation_mode": mode,
            "result": str(result),
            "conflict_log": self.conflict_tracker.get_log(),
        }

        out_path = self.run_dir / "simulation" / "result.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(output, ensure_ascii=False, indent=2)
        )

        return output