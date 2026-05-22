"""
memory/tracker.py
Tahmin kayıt + outcome girişi + accuracy hesabı.
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
OUTCOMES_DIR = Path("memory/outcomes")


class OutcomeTracker:
    def record_prediction(self, run_id: str, prediction: dict):
        path = OUTCOMES_DIR / f"{run_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "run_id": run_id,
            "prediction": prediction,
            "predicted_at": datetime.now(timezone.utc).isoformat(),
            "actual": None,
            "accuracy": None,
        }
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        logger.info(f"Tahmin kaydedildi: {run_id}")

    def update_actual(self, run_id: str, actual_outcome: dict) -> float:
        path = OUTCOMES_DIR / f"{run_id}.json"
        if not path.exists():
            logger.error(f"Run bulunamadı: {run_id}")
            return 0.0

        data = json.loads(path.read_text())
        data["actual"] = actual_outcome
        data["actual_recorded_at"] = datetime.now(timezone.utc).isoformat()
        data["accuracy"] = self._calculate_accuracy(
            data["prediction"], actual_outcome
        )
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        logger.info(f"Outcome güncellendi: {run_id} (accuracy: {data['accuracy']})")
        return data["accuracy"]

    def _calculate_accuracy(self, prediction: dict, actual: dict) -> float:
        pred_level = prediction.get("risk_level", "medium")
        actual_level = actual.get("risk_level", "medium")
        levels = ["low", "medium", "high", "critical"]
        try:
            diff = abs(levels.index(pred_level) - levels.index(actual_level))
            return round(1.0 - diff * 0.33, 2)
        except ValueError:
            return 0.5

    def list_runs(self) -> list:
        return [
            json.loads(f.read_text())
            for f in OUTCOMES_DIR.glob("*.json")
        ]
