"""
signals/collectors/economic.py
USD/TRY, EUR/TRY, BIST100 — Yahoo Finance
Günlük değişim ve önceki kapanış dahil.
"""

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class EconomicCollector:
    def collect(self) -> list:
        signals = []
        signals.extend(self._yahoo_fx())
        signals.extend(self._yahoo_bist())
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
                t = yf.Ticker(ticker)
                info = t.fast_info

                curr = getattr(info, "last_price", 0) or 0
                prev_close = getattr(info, "previous_close", 0) or 0

                signals.append({
                    "source": "yahoo_finance",
                    "category": "economic",
                    "type": "fx",
                    "metric": metric,
                    "title": f"{title} kuru",
                    "value": float(curr),
                    "prev_close": float(prev_close),
                    "change": float(curr - prev_close) if prev_close else 0,
                    "change_pct": float((curr - prev_close) / prev_close * 100) if prev_close else 0,
                    "min": 0,
                    "max": 100,
                    "weight": 1.0,
                    "collected_at": datetime.now(timezone.utc).isoformat(),
                })
            return signals
        except Exception as e:
            logger.warning(f"Yahoo Finance FX hata: {e}")
            return []

    def _yahoo_bist(self) -> list:
        try:
            import yfinance as yf
            t = yf.Ticker("XU100.IS")
            info = t.fast_info

            curr = getattr(info, "last_price", 0) or 0
            prev_close = getattr(info, "previous_close", 0) or 0

            return [{
                "source": "yahoo_finance",
                "category": "economic",
                "type": "index",
                "metric": "bist100",
                "title": "BIST 100",
                "value": float(curr),
                "prev_close": float(prev_close),
                "change": float(curr - prev_close) if prev_close else 0,
                "change_pct": float((curr - prev_close) / prev_close * 100) if prev_close else 0,
                "min": 0,
                "max": 15000,
                "weight": 0.9,
                "collected_at": datetime.now(timezone.utc).isoformat(),
            }]
        except Exception as e:
            logger.warning(f"Yahoo Finance BIST hata: {e}")
            return []