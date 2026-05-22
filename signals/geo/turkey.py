"""
signals/geo/turkey.py
Türkiye odaklı sinyal toplama.
"""

import logging
from signals.collectors.economic import EconomicCollector
from signals.collectors.political import PoliticalCollector

logger = logging.getLogger(__name__)


class TurkeySignalCollector:
    def collect(self) -> list:
        signals = []
        signals.extend(EconomicCollector().collect())
        signals.extend(PoliticalCollector().collect())
        for s in signals:
            s["geo_scope"] = "turkey"
        return signals
