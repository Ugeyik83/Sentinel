"""signals/geo/global.py — Fed, petrol, küresel tedarik zinciri."""
import logging
from signals.collectors.economic import EconomicCollector
from signals.collectors.sectoral import SectoralCollector
logger = logging.getLogger(__name__)

class GlobalSignalCollector:
    def collect(self) -> list:
        signals = []
        signals.extend(EconomicCollector().collect())
        signals.extend(SectoralCollector().collect())
        for s in signals:
            s["geo_scope"] = "global"
        return signals
