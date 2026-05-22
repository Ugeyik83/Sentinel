"""
signals/geo/export_markets.py
config/export_markets.yaml'daki her pazar için sinyal toplar.
"""

import logging
import yaml
import requests
from pathlib import Path
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
MARKETS_PATH = Path("config/export_markets.yaml")


class ExportMarketCollector:
    def __init__(self):
        self.markets = self._load_markets()

    def _load_markets(self) -> list:
        if MARKETS_PATH.exists():
            return yaml.safe_load(MARKETS_PATH.read_text()).get("markets", [])
        return []

    def collect(self) -> list:
        signals = []
        for market in self.markets:
            signals.extend(self._collect_market(market))
        return signals

    def _collect_market(self, market: dict) -> list:
        country = market["country"]
        code = market["code"]
        currency = market["currency"]
        certs = market.get("certifications", [])
        signals = []

        # Kur sinyali
        try:
            rate = self._get_fx_rate(currency)
            if rate:
                signals.append({
                    "source": "yahoo_finance",
                    "category": "export_market",
                    "metric": f"{currency.lower()}_try_rate",
                    "title": f"{country} — {currency}/TRY kuru",
                    "value": rate,
                    "min": 0,
                    "max": 50,
                    "weight": 1.0,
                    "geo_scope": "export_market",
                    "country": country,
                    "country_code": code,
                    "collected_at": datetime.now(timezone.utc).isoformat(),
                })
        except Exception as e:
            logger.warning(f"Kur sinyali hatası [{country}]: {e}")

        # Sertifikasyon uyarısı (statik kontrol — gerçek veri bağlanabilir)
        for cert in certs:
            signals.append({
                "source": "internal",
                "category": "export_market",
                "metric": f"certification_{cert.lower()}",
                "title": f"{country} — {cert} sertifikasyon takibi",
                "value": 0,
                "min": 0,
                "max": 1,
                "weight": 0.9,
                "geo_scope": "export_market",
                "country": country,
                "country_code": code,
                "collected_at": datetime.now(timezone.utc).isoformat(),
            })

        return signals

    def _get_fx_rate(self, currency: str) -> float:
        if currency == "TRY":
            return 1.0
        try:
            import yfinance as yf
            ticker = f"{currency}TRY=X"
            data = yf.Ticker(ticker).fast_info
            return getattr(data, "last_price", 0) or 0
        except Exception:
            return 0.0
