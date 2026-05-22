"""
signals/reliability_tracker.py
Kaynak doğruluk geçmişi + dinamik kalibrasyon.
Her outcome girildiğinde kaynak reliability'si güncellenir.
"""

import json
import logging
import yaml
from pathlib import Path
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
RELIABILITY_PATH = Path("config/source_reliability.yaml")
HISTORY_PATH = Path("uploads/runs/reliability_history.json")


class ReliabilityTracker:
    def __init__(self):
        self.config = self._load_config()
        self.history = self._load_history()

    def _load_config(self) -> dict:
        if RELIABILITY_PATH.exists():
            return yaml.safe_load(RELIABILITY_PATH.read_text())
        return {"sources": {}}

    def _load_history(self) -> dict:
        if HISTORY_PATH.exists():
            return json.loads(HISTORY_PATH.read_text())
        return {}

    def record_outcome(self, source: str, signal_id: str, was_accurate: bool):
        if source not in self.history:
            self.history[source] = []
        self.history[source].append({
            "signal_id": signal_id,
            "accurate": was_accurate,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        })
        self._update_reliability(source)
        self._save_history()

    def _update_reliability(self, source: str):
        records = self.history.get(source, [])
        if len(records) < 5:
            return
        recent = records[-100:]
        accuracy = sum(1 for r in recent if r["accurate"]) / len(recent)

        sources = self.config.get("sources", {})
        if source not in sources:
            sources[source] = {"reliability": 0.50, "tier": 4}

        old = sources[source]["reliability"]
        # Exponential moving average
        sources[source]["reliability"] = round(0.7 * old + 0.3 * accuracy, 3)

        RELIABILITY_PATH.write_text(
            yaml.dump(self.config, allow_unicode=True, default_flow_style=False)
        )
        logger.info(f"Reliability güncellendi: {source} → {sources[source]['reliability']}")

    def _save_history(self):
        HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        HISTORY_PATH.write_text(json.dumps(self.history, ensure_ascii=False, indent=2))

    def get_reliability(self, source: str) -> float:
        return self.config.get("sources", {}).get(source, {}).get("reliability", 0.30)
