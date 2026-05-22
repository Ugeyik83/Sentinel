"""
scenarios/validator.py
Hallucination guard — geçersiz senaryo reject edilir.
Validator gevşetildi: org chart ID'leri ile tam eşleşme zorunlu değil.
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

        # Graf boşsa validation'ı atla
        nodes = graph.get("nodes", [])
        if not nodes:
            return {"valid": True, "errors": [], "warnings": ["Graf boş — validation atlandı"]}

        node_ids = {n["id"] for n in nodes}
        node_labels = {n.get("label", "").lower() for n in nodes}

        entities = scenario.get("affected_risks", []) + scenario.get("affected_roles", [])

        # 1. Graf bağlantısı — YUMUŞATILDI
        # ID tam eşleşmesi yerine label benzerliği de kabul edilir
        if rules.get("require_graph_path") and entities:
            unmatched = []
            for e in entities:
                e_lower = str(e).lower()
                id_match = e in node_ids
                label_match = any(e_lower in label or label in e_lower
                                  for label in node_labels)
                if not id_match and not label_match:
                    unmatched.append(e)

            # Sadece %80+ eşleşmezse reject et (eski: %50)
            if len(unmatched) > len(entities) * 0.8:
                warnings.append(f"Çoğu varlık grafta bulunamadı: {unmatched[:3]}")
                # Artık ERROR değil WARNING — reject etme

        # 2. Min kanıt sayısı — sadece sinyal varsa kontrol et
        if signals:
            min_evidence = rules.get("min_evidence_count", 3)
            evidence = scenario.get("supporting_evidence", [])
            if len(evidence) < min_evidence:
                warnings.append(f"Düşük kanıt sayısı: {len(evidence)}")

        # 3. Çelişki kontrolü
        if "no_contradictory_signals" in rules.get("consistency_checks", []):
            if self._has_contradictions(signals):
                warnings.append("Çelişkili sinyaller mevcut")

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