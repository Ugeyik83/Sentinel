"""
scenarios/generator.py
LLM + memory few-shot + sinyal → otomatik senaryo üretimi.
"""

import json
import logging
import yaml
from pathlib import Path
from datetime import datetime, timezone
from app.utils.llm_client import chat_json
from scenarios.confidence import ConfidenceScorer
from scenarios.validator import ScenarioValidator

logger = logging.getLogger(__name__)

CATALOG_DIR = Path("scenarios/catalog")

SYSTEM = """Sen kurumsal risk senaryosu uzmanısın.
Verilen sinyallerden ve geçmiş derslerden yola çıkarak
şirkete özgü risk senaryoları üret.

Her senaryo için şu JSON formatını kullan:
{
  "id": "sc_YYYYMMDD_NNN",
  "name": "Senaryo adı",
  "description": "Detaylı açıklama",
  "affected_risks": ["risk_id_1", "risk_id_2"],
  "affected_roles": ["role_id_1", "role_id_2"],
  "simulation_mode": "hierarchical|consensus",
  "time_horizon_days": 30,
  "trigger_signals": ["sinyal adları"],
  "supporting_evidence": ["kanıt 1", "kanıt 2"],
  "source_references": ["kaynak 1", "kaynak 2"]
}"""


class ScenarioGenerator:
    def __init__(self, model: str = None):
        self.model = model
        self.scorer = ConfidenceScorer()
        self.validator = ScenarioValidator()

    def generate(self, signals: list, graph: dict,
                 past_lessons: str = "", count: int = 3) -> list:
        signal_summary = self._summarize_signals(signals)
        graph_summary = self._summarize_graph(graph)

        messages = [
            {"role": "system", "content": SYSTEM},
            {
                "role": "user",
                "content": (
                    f"Geçmiş dersler:\n{past_lessons}\n\n"
                    f"Mevcut sinyaller:\n{signal_summary}\n\n"
                    f"Graf bağlamı:\n{graph_summary}\n\n"
                    f"{count} adet senaryo üret. "
                    f"Çıktı: {{\"scenarios\": [...]}}"
                ),
            },
        ]

        result = chat_json(messages, model=self.model, temperature=0.4)
        raw_scenarios = result.get("scenarios", [])

        validated = []
        for scenario in raw_scenarios:
            scenario["id"] = self._gen_id()
            scenario["generated_at"] = datetime.now(timezone.utc).isoformat()

            # Confidence score
            scenario["confidence"] = self.scorer.score(scenario, signals, graph)

            # Validation
            validation = self.validator.validate(scenario, graph, signals)
            if validation["valid"]:
                validated.append(scenario)
            else:
                logger.warning(
                    f"Senaryo reddedildi [{scenario['name']}]: "
                    f"{validation['errors'][0]}"
                )

        # Katalog senaryolarını ekle
        catalog = self._load_catalog_scenarios(signals)
        validated.extend(catalog)

        validated.sort(key=lambda s: s["confidence"].get("confidence", 0), reverse=True)
        logger.info(f"{len(validated)} senaryo üretildi ({len(raw_scenarios)} LLM, {len(catalog)} katalog)")
        return validated

    def _summarize_signals(self, signals: list) -> str:
        top = sorted(signals, key=lambda s: s.get("composite_score", 0), reverse=True)[:10]
        return "\n".join(
            f"- {s.get('title', '?')} (skor: {s.get('composite_score', 0):.2f}, "
            f"kaynak: {s.get('source', '?')})"
            for s in top
        )

    def _summarize_graph(self, graph: dict) -> str:
        meta = graph.get("metadata", {})
        top_nodes = sorted(
            graph.get("nodes", []),
            key=lambda n: n.get("degree", 0),
            reverse=True
        )[:5]
        return (
            f"Domain: {meta.get('domain', '?')}, "
            f"Temalar: {', '.join(meta.get('key_themes', []))}, "
            f"En bağlı varlıklar: {', '.join(n['label'] for n in top_nodes)}"
        )

    def _load_catalog_scenarios(self, signals: list) -> list:
        catalog = []
        for yaml_file in CATALOG_DIR.glob("*.yaml"):
            data = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
            for scenario in data.get("scenarios", []):
                if self._is_triggered(scenario, signals):
                    scenario["source"] = "catalog"
                    scenario["confidence"] = {"confidence": 0.85, "signal_strength": "catalog"}
                    scenario["generated_at"] = datetime.now(timezone.utc).isoformat()
                    catalog.append(scenario)
        return catalog

    def _is_triggered(self, scenario: dict, signals: list) -> bool:
        # Basit trigger kontrolü — geliştirilecek
        trigger = scenario.get("trigger", "")
        signal_metrics = {s.get("metric", ""): s.get("composite_score", 0) for s in signals}
        # Eşik sinyali varsa tetikle
        for metric, score in signal_metrics.items():
            if metric in trigger and score > 0.5:
                return True
        return False

    def _gen_id(self) -> str:
        from datetime import datetime
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        import random
        return f"sc_{ts}_{random.randint(100, 999)}"
