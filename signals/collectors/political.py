"""
signals/collectors/political.py
Türkiye haberleri — NewsAPI
Çoklu query: ekonomi + siyaset + jeopolitik + acil gelişmeler
"""

import logging
import os
import requests
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Arama sorguları — öncelik sırasına göre
QUERIES = [
    {
        "q": "Türkiye OR Turkey",
        "sortBy": "publishedAt",   # En güncel
        "pageSize": 5,
        "label": "güncel"
    },
    {
        "q": "Erdoğan OR CHP ORTCMB OR TL OR dolar kur faiz enflasyon",
        "sortBy": "publishedAt",
        "pageSize": 5,
        "label": "ekonomi-siyaset"
    },
    {
        "q": "İstanbul OR Ankara OR seçim OR meclis OR hükümet",
        "sortBy": "publishedAt",
        "pageSize": 5,
        "label": "iç siyaset"
    },
]


class PoliticalCollector:
    def __init__(self):
        self.newsapi_key = os.environ.get("NEWSAPI_KEY", "")

    def collect(self) -> list:
        if not self.newsapi_key:
            logger.info("NEWSAPI_KEY tanımlı değil.")
            return []
        return self._newsapi_multi()

    def _newsapi_multi(self) -> list:
        all_signals = []
        seen_titles = set()

        for query_cfg in QUERIES:
            try:
                params = {
                    "q": query_cfg["q"],
                    "language": "tr",
                    "sortBy": query_cfg.get("sortBy", "publishedAt"),
                    "pageSize": query_cfg.get("pageSize", 5),
                    "apiKey": self.newsapi_key,
                }
                resp = requests.get(
                    "https://newsapi.org/v2/everything",
                    params=params,
                    timeout=10
                )
                articles = resp.json().get("articles", [])

                for article in articles:
                    title = article.get("title", "")
                    if not title or title in seen_titles:
                        continue
                    # Reklam/spam filtresi
                    if "[Removed]" in title or len(title) < 10:
                        continue
                    seen_titles.add(title)
                    all_signals.append({
                        "source": "newsapi",
                        "category": "political",
                        "label": query_cfg["label"],
                        "metric": "tr_news",
                        "title": title[:150],
                        "summary": article.get("description", "")[:200],
                        "url": article.get("url", ""),
                        "published_at": article.get("publishedAt", ""),
                        "value": 1,
                        "min": 0,
                        "max": 1,
                        "weight": 0.7,
                        "collected_at": datetime.now(timezone.utc).isoformat(),
                    })
            except Exception as e:
                logger.warning(f"NewsAPI hata [{query_cfg['q'][:30]}]: {e}")

        # Yayın tarihine göre sırala — en yeni önce
        all_signals.sort(
            key=lambda x: x.get("published_at", ""),
            reverse=True
        )

        logger.info(f"NewsAPI: {len(all_signals)} haber toplandı")
        return all_signals