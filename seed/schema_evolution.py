"""
seed/schema_evolution.py
Yeni belgelerden şema evrim önerileri üretir.
Onay mekanizması ile kontrollü genişleme.
"""

import json
import logging
import yaml
from pathlib import Path
from app.utils.llm_client import chat_json

logger = logging.getLogger(__name__)
EDGE_TYPES_PATH = Path("seed/edge_types.yaml")
OCCURRENCE_THRESHOLD = 3


class SchemaEvolutionEngine:
    def __init__(self):
        self.schema = self._load_schema()
        self.pending = []

    def _load_schema(self) -> dict:
        if EDGE_TYPES_PATH.exists():
            return yaml.safe_load(EDGE_TYPES_PATH.read_text())
        return {}

    def _all_edge_types(self) -> list:
        types = []
        for category_types in self.schema.values():
            types.extend(category_types)
        return types

    def detect_new_patterns(self, extraction: dict) -> list:
        existing_edges = self._all_edge_types()
        suggestions = []

        for rel in extraction.get("relationships", []):
            rel_type = rel.get("relation", "")
            if rel_type and rel_type not in existing_edges:
                existing = next(
                    (s for s in suggestions if s["name"] == rel_type), None
                )
                if existing:
                    existing["occurrence_count"] += 1
                    existing["examples"].append(
                        f"{rel.get('source')} → {rel.get('target')}"
                    )
                else:
                    suggestions.append({
                        "name": rel_type,
                        "occurrence_count": 1,
                        "examples": [f"{rel.get('source')} → {rel.get('target')}"],
                        "auto_promoted": False,
                    })

        # Eşik kontrolü — otomatik kabul
        for s in suggestions:
            if s["occurrence_count"] >= OCCURRENCE_THRESHOLD:
                s["auto_promoted"] = True
                self._add_to_schema(s["name"])
                logger.info(f"Otomatik kabul: {s['name']} (eşik: {OCCURRENCE_THRESHOLD})")

        self.pending = [s for s in suggestions if not s["auto_promoted"]]
        return suggestions

    def approve(self, edge_type: str, category: str = "etki"):
        self._add_to_schema(edge_type, category)
        self.pending = [p for p in self.pending if p["name"] != edge_type]

    def reject(self, edge_type: str):
        self.pending = [p for p in self.pending if p["name"] != edge_type]

    def _add_to_schema(self, edge_type: str, category: str = "etki"):
        if category not in self.schema:
            self.schema[category] = []
        if edge_type not in self.schema[category]:
            self.schema[category].append(edge_type)
            EDGE_TYPES_PATH.write_text(
                yaml.dump(self.schema, allow_unicode=True, default_flow_style=False)
            )
