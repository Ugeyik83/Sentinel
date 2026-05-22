"""
scenarios/injector.py
Senaryo → CrewAI runner'a besle.
"""

import logging
from scenarios.generator import ScenarioGenerator
from crew.runner import SimulationRunner

logger = logging.getLogger(__name__)


class ScenarioInjector:
    def __init__(self, run_dir: str):
        self.run_dir = run_dir
        self.runner = SimulationRunner(run_dir)

    def inject_and_run(self, scenario: dict) -> dict:
        logger.info(f"Senaryo enjekte ediliyor: {scenario['name']}")
        return self.runner.run(scenario)

    def inject_top(self, scenarios: list) -> dict:
        """En yüksek güvenli senaryoyu çalıştır."""
        if not scenarios:
            raise ValueError("Senaryo listesi boş")
        top = sorted(
            scenarios,
            key=lambda s: s.get("confidence", {}).get("confidence", 0),
            reverse=True
        )[0]
        return self.inject_and_run(top)
