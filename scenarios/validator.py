"""
scenarios/validator.py
Hallucination guard — geçersiz senaryo reject edilir.
"""

import logging
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)
VALIDATION_PATH = Path("config/scenario_validation.yaml")


class ScenarioValidator:
    def __init__(self):
        self.rules = self._load_rules()

    def _load_rules(self) -> dict:
        if VALIDATION_PATH.exists():
            return yaml.safe_load(VALIDATION_PATH.read_text())
        return {}

    def validate(self, scenario: dict, graph: dict, signals: list) -> dict:
        rules = self.rules.get("validation_rules", {})
        errors = []
        warnings = []

        node_ids = {n["id"] for n in graph.get("nodes", [])}
        entities = scenario.get("affected_risks", []) + scenario.get("affected_roles", [])

        # 1. Graf bağlantısı
        if rules.get("require_graph_path"):
            unknown = [e for e in entities if e and e not in node_ids]
            if unknown and len(unknown) > len(entities) * 0.5:
                errors.append(f"Varlıkların %50+ grafta yok: {unknown[:3]}")

        # 2. Min kanıt sayısı
        min_evidence = rules.get("min_evidence_count", 3)
        evidence = scenario.get("supporting_evidence", [])
        if len(evidence) < min_evidence:
            errors.append(f"Yetersiz kanıt: {len(evidence)} < {min_evidence}")

        # 3. Typed edge kontrolü
        if rules.get("require_typed_edges"):
            relations = [e.get("relation", "") for e in graph.get("edges", [])]
            if "related_to" in relations or "related" in relations:
                warnings.append("Tiplendirilmemiş edge bulundu")

        # 4. Çelişki kontrolü
        if "no_contradictory_signals" in rules.get("consistency_checks", []):
            if self._has_contradictions(signals):
                warnings.append("Çelişkili sinyaller mevcut")

        # 5. Max entity
        max_entities = rules.get("max_entities_per_scenario", 15)
        if len(entities) > max_entities:
            warnings.append(f"Çok fazla entity: {len(entities)} > {max_entities}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "rejected_reason": errors[0] if errors else None,
        }

    def _has_contradictions(self, signals: list) -> bool:
        metrics = {}
        for s in signals:
            metric = s.get("metric", "")
            value = s.get("value", 0)
            if metric in metrics:
                prev = metrics[metric]
                if prev > 0 and value < 0 or prev < 0 and value > 0:
                    return True
            metrics[metric] = value
        return False
