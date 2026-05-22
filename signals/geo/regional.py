"""signals/geo/regional.py — Orta Doğu, AB, Orta Asya sinyalleri."""
import logging
from signals.collectors.political import PoliticalCollector
logger = logging.getLogger(__name__)

class RegionalSignalCollector:
    REGIONS = ["Middle East", "European Union", "Central Asia"]
    def collect(self) -> list:
        signals = PoliticalCollector().collect()
        for s in signals:
            s["geo_scope"] = "regional"
        return signals
