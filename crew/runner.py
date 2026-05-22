"""
crew/runner.py
CrewAI simülasyon çalıştırıcı.
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
        logger.info(f"Simülasyon: {scenario['name']} | mod: {mode}")

        tasks = self.task_builder.build_tasks(scenario, self.agents)

        if mode == "hierarchical":
            result = self._run_hierarchical(tasks)
        else:
            result = self._run_sequential(tasks)

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

        return output

    def _run_hierarchical(self, tasks):
        """
        Hierarchical modda manager agent agents listesinde OLMAMALI.
        Manager ayrı parametre olarak geçilir.
        """
        manager = self.agents.get("managing_director")

        # Manager'ı agents listesinden çıkar
        worker_agents = [
            agent for agent_id, agent in self.agents.items()
            if agent_id != "managing_director"
        ]

        # Task'ların agent'larını da filtrele — MD task'ı sequential'a bırak
        worker_tasks = [t for t in tasks if t.agent != manager]
        md_tasks = [t for t in tasks if t.agent == manager]

        crew = Crew(
            agents=worker_agents,
            tasks=worker_tasks,
            process=Process.hierarchical,
            manager_agent=manager,
            verbose=True,
        )
        result = crew.kickoff()

        # MD kararını sequential olarak al
        if md_tasks and manager:
            md_crew = Crew(
                agents=[manager],
                tasks=md_tasks,
                process=Process.sequential,
                verbose=True,
            )
            md_result = md_crew.kickoff()
            return f"{result}\n\n=== YÖNETİM KARARI ===\n{md_result}"

        return result

    def _run_sequential(self, tasks):
        """Consensus modu — tüm ajanlar sırayla çalışır."""
        all_agents = list(self.agents.values())
        crew = Crew(
            agents=all_agents,
            tasks=tasks,
            process=Process.sequential,
            verbose=True,
        )
        return crew.kickoff()