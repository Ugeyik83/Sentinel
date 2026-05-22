"""
seed/entity_extractor.py
LLM ile belgeden typed edge ontoloji çıkarımı.
"""

import json
import logging
from app.utils.llm_client import chat_json

logger = logging.getLogger(__name__)

SYSTEM = """Sen kurumsal risk ontolojisi uzmanısın.
Verilen belgeden varlıkları ve aralarındaki TYPED ilişkileri çıkar.

İlişki tipleri (sadece bunları kullan):
SUPPLIES, DEPENDS_ON, OWNS, REQUIRES, BLOCKS,
APPROVES, DELEGATES_TO, REPORTS_TO, AUDITS,
IMPACTS, TRIGGERS, MITIGATES, ESCALATES,
PRECEDES, CONCURRENT_WITH

Çıktı SADECE JSON:
{
  "entities": [
    {
      "id": "benzersiz_id",
      "name": "varlık adı",
      "type": "person|organization|process|risk|event|regulation|system|concept",
      "description": "kısa açıklama",
      "importance": 1-5
    }
  ],
  "relationships": [
    {
      "source": "entity_id",
      "target": "entity_id",
      "relation": "TYPED_EDGE",
      "weight": 0.0-1.0,
      "description": "açıklama"
    }
  ],
  "summary": "belge özeti",
  "domain": "ERM|finance|HSE|logistics|IT|general",
  "key_themes": ["tema1", "tema2"]
}"""


class EntityExtractor:
    def __init__(self, model: str = None):
        self.model = model

    def extract(self, text: str, requirement: str = "") -> dict:
        max_chars = 80_000
        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n[metin kesildi]"

        messages = [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"Gereksinim: {requirement}\n\nBelge:\n{text}"},
        ]

        result = chat_json(messages, model=self.model, temperature=0.2)
        result.setdefault("entities", [])
        result.setdefault("relationships", [])

        logger.info(
            f"Çıkarım: {len(result['entities'])} varlık, "
            f"{len(result['relationships'])} ilişki"
        )
        return result
