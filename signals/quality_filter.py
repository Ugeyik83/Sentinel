"""
signals/quality_filter.py
Clickbait, spam ve duplikasyon filtresi.
Reliability skorunu içerik kalitesine göre düşürür.
"""

import re
import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

CLICKBAIT_PATTERNS = [
    r"SON DAKİKA|BREAKING|ŞOK|FLAŞ",
    r"İŞTE|İNANILMAZ|MUTLAKA|KAÇIRMA",
    r"\d+\s*(SEBEP|NEDEN|MADDE|YOL)",
    r"BU.*BİLMİYORDUNUZ",
    r"GÖRENLER.*ŞAŞIRDI",
    r"BOMBA\s+AÇIKLAMA",
    r"HERKES\s+MERAK\s+ETTİ",
]


class SignalQualityFilter:
    def __init__(self):
        self._recent_signals = []

    def filter(self, signals: list) -> list:
        filtered = []
        for signal in signals:
            quality = self.score_quality(signal)
            signal["quality_score"] = quality["quality_score"]
            signal["quality_penalties"] = quality["penalties"]
            if quality["quality_score"] > 0.1:
                filtered.append(signal)
            else:
                logger.debug(f"Sinyal filtrelendi: {signal.get('title', '')[:50]}")
        return filtered

    def score_quality(self, signal: dict) -> dict:
        text = (signal.get("title", "") + " " + signal.get("summary", "")).upper()
        penalties = {}

        # Clickbait
        hits = sum(1 for p in CLICKBAIT_PATTERNS if re.search(p, text))
        if hits:
            penalties["clickbait"] = min(hits * 0.20, 0.80)

        # Caps oranı
        alpha = [c for c in text if c.isalpha()]
        if alpha:
            caps_ratio = sum(1 for c in alpha if c.isupper()) / len(alpha)
            if caps_ratio > 0.60:
                penalties["caps"] = min((caps_ratio - 0.60) * 2, 0.40)

        # Ünlem sayısı
        excl = text.count("!")
        if excl > 2:
            penalties["exclamation"] = min((excl - 2) * 0.10, 0.30)

        # Tier 1 kaynak clickbait kullanırsa şüpheli
        if signal.get("source_tier", 4) == 1 and hits > 0:
            penalties["tier_mismatch"] = 0.50

        # Duplikasyon
        if self._is_duplicate(signal):
            penalties["duplicate"] = 0.50

        quality_score = max(0.0, 1.0 - sum(penalties.values()))

        # Sonucu son sinyaller listesine ekle
        self._recent_signals.append({
            "title": signal.get("title", ""),
            "source": signal.get("source", ""),
            "timestamp": datetime.now(timezone.utc),
        })

        return {"quality_score": round(quality_score, 3), "penalties": penalties}

    def _is_duplicate(self, signal: dict) -> bool:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        recent = [s for s in self._recent_signals if s["timestamp"] > cutoff]
        title = signal.get("title", "").lower()
        for r in recent:
            if self._similarity(title, r["title"].lower()) > 0.85:
                return True
        return False

    def _similarity(self, a: str, b: str) -> float:
        if not a or not b:
            return 0.0
        words_a = set(a.split())
        words_b = set(b.split())
        if not words_a or not words_b:
            return 0.0
        return len(words_a & words_b) / len(words_a | words_b)
