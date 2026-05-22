"""
signals/collectors/sectoral.py
Batarya, otomotiv, metal sektör sinyalleri — RSS.
"""

import logging
import feedparser
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

RSS_FEEDS = [
    {
        "url": "https://www.benchmarkminerals.com/feed/",
        "source": "benchmark_minerals",
        "category": "sectoral",
        "metric": "battery_news",
        "weight": 0.8,
    },
    {
        "url": "https://www.metalbulletin.com/rss",
        "source": "metal_bulletin",
        "category": "sectoral",
        "metric": "lead_market",
        "weight": 0.75,
    },
    {
        "url": "https://www.autonews.com/rss.xml",
        "source": "autonews",
        "category": "sectoral",
        "metric": "automotive_news",
        "weight": 0.65,
    },
]


class SectoralCollector:
    def collect(self) -> list:
        signals = []
        for feed_cfg in RSS_FEEDS:
            try:
                feed = feedparser.parse(feed_cfg["url"])
                for entry in feed.entries[:5]:
                    signals.append({
                        "source": feed_cfg["source"],
                        "category": feed_cfg["category"],
                        "metric": feed_cfg["metric"],
                        "title": entry.get("title", ""),
                        "summary": entry.get("summary", "")[:300],
                        "url": entry.get("link", ""),
                        "value": 1,
                        "min": 0,
                        "max": 1,
                        "weight": feed_cfg["weight"],
                        "collected_at": datetime.now(timezone.utc).isoformat(),
                    })
            except Exception as e:
                logger.warning(f"RSS hata [{feed_cfg['source']}]: {e}")
        return signals
