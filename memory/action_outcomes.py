"""memory/action_outcomes.py — Aksiyon sonuç takibi."""
import json
import logging
from pathlib import Path
logger = logging.getLogger(__name__)

OUTCOMES_PATH = Path("memory/outcomes/action_outcomes.json")

class ActionOutcomeStore:
    def record(self, action_type: str, success: bool, impact_pct: float):
        data = self._load()
        if action_type not in data:
            data[action_type] = []
        data[action_type].append({"success": success, "impact_pct": impact_pct})
        OUTCOMES_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTCOMES_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def success_rate(self, action_type: str) -> float:
        data = self._load()
        records = data.get(action_type, [])
        if not records:
            return 0.7  # default
        return sum(1 for r in records if r["success"]) / len(records)

    def _load(self) -> dict:
        if OUTCOMES_PATH.exists():
            return json.loads(OUTCOMES_PATH.read_text())
        return {}
