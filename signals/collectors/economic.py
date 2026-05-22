"""
signals/collectors/economic.py
USD/TRY ve EUR/TRY — Yahoo Finance
"""

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class EconomicCollector:
    def collect(self) -> list:
        signals = []
        signals.extend(self._yahoo_fx())
        return signals

    def _yahoo_fx(self) -> list:
        try:
            import yfinance as yf
            pairs = {
                "USDTRY=X": ("USD/TRY", "usd_try_rate"),
                "EURTRY=X": ("EUR/TRY", "eur_try_rate"),
            }
            signals = []
            for ticker, (title, metric) in pairs.items():
                data = yf.Ticker(ticker).fast_info
                rate = getattr(data, "last_price", 0) or 0
                signals.append({
                    "source": "yahoo_finance",
                    "category": "economic",
                    "metric": metric,
                    "title": f"{title} kuru",
                    "value": float(rate),
                    "min": 0,
                    "max": 100,
                    "weight": 1.0,
                    "collected_at": datetime.now(timezone.utc).isoformat(),
                })
            return signals
        except Exception as e:
            logger.warning(f"Yahoo Finance hata: {e}")
            return []