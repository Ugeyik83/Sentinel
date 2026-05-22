"""
signals/aggregator.py
Ham sinyal → güvenilirlik ağırlıklı feed.
score = normalized_value × weight × source_reliability × anomaly_factor
"""

import logging
import yaml
from pathlib import Path
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

RELIABILITY_PATH = Path("config/source_reliability.yaml")
THRESHOLDS_PATH = Path("config/thresholds.yaml")


class SignalAggregator:
    def __init__(self):
        self.reliability = self._load_reliability()
        self.thresholds = self._load_thresholds()

    def _load_reliability(self) -> dict:
        if RELIABILITY_PATH.exists():
            return yaml.safe_load(RELIABILITY_PATH.read_text()).get("sources", {})
        return {}

    def _load_thresholds(self) -> dict:
        if THRESHOLDS_PATH.exists():
            return yaml.safe_load(THRESHOLDS_PATH.read_text())
        return {}

    def aggregate(self, raw_signals: list) -> list:
        scored = []
        for signal in raw_signals:
            scored_signal = self._score(signal)
            if scored_signal:
                scored.append(scored_signal)
        scored.sort(key=lambda s: s["composite_score"], reverse=True)
        return scored

    def _score(self, signal: dict) -> dict:
        source = signal.get("source", "random_rss")
        source_cfg = self.reliability.get(source, {"reliability": 0.30, "tier": 4})
        reliability = source_cfg.get("reliability", 0.30)

        normalized = self._normalize(signal)
        anomaly_factor = signal.get("anomaly_factor", 1.0)
        weight = signal.get("weight", 1.0)
        quality = signal.get("quality_score", 1.0)

        composite = normalized * weight * reliability * anomaly_factor * quality

        return {
            **signal,
            "source_reliability": reliability,
            "source_tier": source_cfg.get("tier", 4),
            "normalized_value": normalized,
            "composite_score": round(composite, 4),
            "scored_at": datetime.now(timezone.utc).isoformat(),
        }

    def _normalize(self, signal: dict) -> float:
        value = signal.get("value", 0)
        min_val = signal.get("min", 0)
        max_val = signal.get("max", 100)
        if max_val == min_val:
            return 0.5
        return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))

    def check_thresholds(self, scored_signals: list) -> list:
        alerts = []
        for signal in scored_signals:
            category = signal.get("category", "")
            metric = signal.get("metric", "")
            value = signal.get("value", 0)
            threshold_cfg = self.thresholds.get(category, {})
            threshold = threshold_cfg.get(metric)
            if threshold and abs(value) >= threshold:
                alerts.append({
                    "signal": signal,
                    "threshold": threshold,
                    "exceeded_by": abs(value) - threshold,
                    "severity": self._severity(abs(value), threshold),
                })
        return alerts

    def _severity(self, value: float, threshold: float) -> str:
        ratio = value / threshold
        if ratio >= 2.0:
            return "critical"
        if ratio >= 1.5:
            return "high"
        if ratio >= 1.0:
            return "medium"
        return "low"
