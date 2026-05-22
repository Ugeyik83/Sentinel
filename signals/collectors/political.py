"""
signals/collectors/political.py
Türkiye haberleri — NewsAPI
"""

import logging
import os
import requests
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class PoliticalCollector:
    def __init__(self):
        self.newsapi_key = os.environ.get("NEWSAPI_KEY", "")

    def collect(self) -> list:
        if not self.newsapi_key:
            logger.info("NEWSAPI_KEY tanımlı değil — haber sinyali atlandı.")
            return []
        return self._newsapi_turkey()

    def _newsapi_turkey(self) -> list:
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": "Türkiye ekonomi OR Turkey economy OR dolar kur",
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
                    "metric": "tr_news",
                    "title": article.get("title", "")[:120],
                    "summary": article.get("description", "")[:200],
                    "url": article.get("url", ""),
                    "value": 1,
                    "min": 0,
                    "max": 1,
                    "weight": 0.7,
                    "collected_at": datetime.now(timezone.utc).isoformat(),
                })
            logger.info(f"NewsAPI: {len(signals)} haber alındı")
            return signals
        except Exception as e:
            logger.warning(f"NewsAPI hata: {e}")
            return []