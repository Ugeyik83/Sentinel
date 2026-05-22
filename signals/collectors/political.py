"""
signals/collectors/political.py
GDELT ve NewsAPI politik sinyal toplama.
"""

import logging
import os
import requests
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


class PoliticalCollector:
    def __init__(self):
        self.newsapi_key = os.environ.get("NEWSAPI_KEY", "")

    def collect(self) -> list:
        signals = []
        signals.extend(self._gdelt())
        if self.newsapi_key:
            signals.extend(self._newsapi())
        return signals

    def _gdelt(self) -> list:
        """GDELT conflict score — Türkiye odaklı."""
        try:
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d%H%M%S")
            url = (
                f"https://api.gdeltproject.org/api/v2/tv/tv?"
                f"query=Turkey+economy&mode=timelinevolinfo&format=json"
                f"&startdatetime={yesterday}&timespan=24h"
            )
            resp = requests.get(url, timeout=15)
            data = resp.json()
            value = len(data.get("timeline", []))
            return [{
                "source": "gdelt",
                "category": "geopolitical",
                "metric": "gdelt_conflict_score",
                "title": "GDELT Türkiye çatışma skoru",
                "value": min(value, 10),
                "min": 0,
                "max": 10,
                "weight": 0.9,
                "collected_at": datetime.now(timezone.utc).isoformat(),
            }]
        except Exception as e:
            logger.warning(f"GDELT hata: {e}")
            return []

    def _newsapi(self) -> list:
        """NewsAPI — Türkiye ekonomi ve siyaset haberleri."""
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": "Turkey economy OR Türkiye ekonomi",
                "language": "tr",
                "sortBy": "publishedAt",
                "pageSize": 10,
                "apiKey": self.newsapi_key,
            }
            resp = requests.get(url, params=params, timeout=10)
            articles = resp.json().get("articles", [])
            signals = []
            for article in articles:
                signals.append({
                    "source": "newsapi",
                    "category": "political",
                    "metric": "news_volume",
                    "title": article.get("title", ""),
                    "summary": article.get("description", ""),
                    "url": article.get("url", ""),
                    "value": 1,
                    "min": 0,
                    "max": 1,
                    "weight": 0.6,
                    "collected_at": datetime.now(timezone.utc).isoformat(),
                })
            return signals
        except Exception as e:
            logger.warning(f"NewsAPI hata: {e}")
            return []
