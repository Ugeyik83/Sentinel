"""
memory/decision_parameters.py
Geçmiş dersler → makine-okunabilir karar parametresi.
Few-shot format ile LLM prompt'una girer.
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
PARAMS_PATH = Path("memory/lessons_learned/decision_params.json")


class DecisionParameterStore:
    def __init__(self):
        self.params = self._load()

    def _load(self) -> list:
        if PARAMS_PATH.exists():
            return json.loads(PARAMS_PATH.read_text(encoding="utf-8"))
        return []

    def store(self, lesson: dict):
        lesson["stored_at"] = datetime.now(timezone.utc).isoformat()
        self.params.append(lesson)
        PARAMS_PATH.parent.mkdir(parents=True, exist_ok=True)
        PARAMS_PATH.write_text(
            json.dumps(self.params, ensure_ascii=False, indent=2)
        )

    def retrieve_for_prompt(self, scenario_context: str, top_k: int = 5) -> str:
        if not self.params:
            return ""

        # Basit keyword matching — ChromaDB eklenince semantic olacak
        scored = []
        keywords = scenario_context.lower().split()
        for param in self.params:
            context = param.get("context", "").lower()
            score = sum(1 for kw in keywords if kw in context)
            scored.append((score, param))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = [p for _, p in scored[:top_k] if _[0] > 0]

        if not top:
            return ""

        return "\n\n".join([
            f"GEÇMİŞ DERS #{i+1}:\n"
            f"Durum: {p.get('context', '?')}\n"
            f"Karar: {p.get('decision', {}).get('action', '?')}\n"
            f"Sonuç: {p.get('outcome', {}).get('actual_impact', '?')}\n"
            f"Başarı: {p.get('outcome', {}).get('success_score', 0)}"
            for i, p in enumerate(top)
        ])
