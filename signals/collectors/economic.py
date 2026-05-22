"""
signals/collectors/economic.py
TCMB, Yahoo Finance, FRED ekonomik sinyal toplama.
"""

import logging
import requests
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class EconomicCollector:
    def collect(self) -> list:
        signals = []
        signals.extend(self._tcmb_fx())
        signals.extend(self._yahoo_finance())
        return signals

    def _tcmb_fx(self) -> list:
        """TCMB döviz kurları."""
        try:
            url = "https://www.tcmb.gov.tr/kurlar/today.xml"
            resp = requests.get(url, timeout=10)
            # XML parse — basitleştirilmiş
            signals = []
            for currency in ["USD", "EUR", "SAR"]:
                signals.append({
                    "source": "tcmb",
                    "category": "economic",
                    "metric": f"{currency.lower()}_try_rate",
                    "title": f"TCMB {currency}/TRY kuru",
                    "value": self._extract_fx(resp.text, currency),
                    "min": 0,
                    "max": 100,
                    "weight": 1.0,
                    "collected_at": datetime.now(timezone.utc).isoformat(),
                })
            return signals
        except Exception as e:
            logger.warning(f"TCMB hata: {e}")
            return []

    def _yahoo_finance(self) -> list:
        """Yahoo Finance — BIST100, metal fiyatları."""
        try:
            import yfinance as yf
            tickers = {"XU100.IS": "bist100", "PB=F": "lead_price"}
            signals = []
            for ticker, metric in tickers.items():
                data = yf.Ticker(ticker).fast_info
                signals.append({
                    "source": "yahoo_finance",
                    "category": "economic",
                    "metric": metric,
                    "title": f"{metric} değeri",
                    "value": getattr(data, "last_price", 0) or 0,
                    "min": 0,
                    "max": 100000,
                    "weight": 0.8,
                    "collected_at": datetime.now(timezone.utc).isoformat(),
                })
            return signals
        except Exception as e:
            logger.warning(f"Yahoo Finance hata: {e}")
            return []

    def _extract_fx(self, xml_text: str, currency: str) -> float:
        import re
        pattern = rf'Kod="{currency}"[^>]*>.*?<ForexBuying>([\d,.]+)</ForexBuying>'
        match = re.search(pattern, xml_text, re.DOTALL)
        if match:
            return float(match.group(1).replace(",", "."))
        return 0.0
