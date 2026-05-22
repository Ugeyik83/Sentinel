"""
signals/weak_signal_detector.py
Eşik bazlı değil, pattern bazlı erken uyarı.
Anomaly detection ile reaktiften proaktife geçiş.
"""

import logging
import numpy as np
from collections import deque
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class WeakSignalDetector:
    def __init__(self, lookback_days: int = 90, min_confidence: float = 0.60):
        self.lookback = lookback_days
        self.min_confidence = min_confidence
        self.history: dict[str, deque] = {}

    def update(self, signal_name: str, value: float):
        if signal_name not in self.history:
            self.history[signal_name] = deque(maxlen=self.lookback)
        self.history[signal_name].append(value)

    def detect(self, signal_name: str, current_value: float) -> dict:
        self.update(signal_name, current_value)
        series = list(self.history[signal_name])

        if len(series) < 14:
            return {"is_weak_signal": False, "reason": "Yeterli geçmiş yok"}

        arr = np.array(series)
        mean = np.mean(arr[:-1])
        std = np.std(arr[:-1]) or 1e-6
        z_score = (current_value - mean) / std

        recent_vol = np.std(arr[-7:]) or 1e-6
        baseline_vol = np.std(arr[:-7]) or 1e-6
        vol_ratio = recent_vol / baseline_vol

        # Isolation Forest
        try:
            from sklearn.ensemble import IsolationForest
            features = arr.reshape(-1, 1)
            model = IsolationForest(contamination=0.05, random_state=42)
            model.fit(features[:-1])
            is_anomaly = model.predict([[current_value]])[0] == -1
        except Exception:
            is_anomaly = abs(z_score) > 2.5

        score = self._combine(z_score, vol_ratio, is_anomaly)
        is_weak = score >= self.min_confidence

        result = {
            "signal": signal_name,
            "current_value": current_value,
            "is_weak_signal": is_weak,
            "weak_signal_score": round(score, 3),
            "indicators": {
                "z_score": round(z_score, 2),
                "volatility_ratio": round(vol_ratio, 2),
                "anomaly_detected": is_anomaly,
            },
            "narrative": self._explain(signal_name, z_score, vol_ratio, is_anomaly),
            "detected_at": datetime.now(timezone.utc).isoformat(),
        }

        if is_weak:
            logger.warning(f"ZayıF sinyal: {signal_name} (skor: {score:.2f})")

        return result

    def _combine(self, z: float, vol_ratio: float, anomaly: bool) -> float:
        score = 0.0
        if abs(z) > 1.5:
            score += 0.35
        if abs(z) > 2.5:
            score += 0.20
        if vol_ratio > 1.5:
            score += 0.25
        if vol_ratio > 2.0:
            score += 0.15
        if anomaly:
            score += 0.25
        return min(score, 1.0)

    def _explain(self, name: str, z: float, vol_ratio: float, anomaly: bool) -> str:
        parts = []
        if abs(z) > 2.0:
            direction = "yukarı" if z > 0 else "aşağı"
            parts.append(f"{name} normalin {abs(z):.1f}σ {direction}sında")
        if vol_ratio > 1.5:
            parts.append(f"volatilite {vol_ratio:.1f}× arttı")
        if anomaly:
            parts.append("pattern anomalisi tespit edildi")
        return "; ".join(parts) if parts else "normal seyir"
