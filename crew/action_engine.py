"""
crew/action_engine.py
Simülasyon sonuçlarından aksiyon önerileri.
Öncelik = (Etki × Güven) / (Maliyet × Süre)
"""

import logging
from app.utils.llm_client import chat_json

logger = logging.getLogger(__name__)

ACTION_TYPES = {
    "hedge": "Finansal koruma (forward, opsiyon, swap)",
    "delay": "Karar ertelemesi",
    "audit": "Acil denetim/inceleme",
    "diversify": "Tedarikçi/pazar çeşitlendirme",
    "stockpile": "Stok artırımı",
    "communicate": "Paydaş iletişimi",
    "escalate": "Üst yönetime taşıma",
    "insurance": "Sigorta poliçesi",
    "policy_change": "Politika/prosedür değişikliği",
    "investment": "Yatırım (sistem, eğitim, ekipman)",
}

SYSTEM = """Sen kurumsal risk aksiyon uzmanısın.
Simülasyon sonuçlarından somut ve uygulanabilir aksiyonlar üret.

Çıktı SADECE JSON:
{
  "actions": [
    {
      "type": "hedge|delay|audit|diversify|stockpile|communicate|escalate|insurance|policy_change|investment",
      "description": "somut aksiyon açıklaması",
      "expected_impact_pct": 0-100,
      "estimated_cost_try": sayı,
      "implementation_days": sayı,
      "responsible_role_id": "org_chart_id",
      "side_effects": ["yan etki 1"],
      "evidence": "Bu aksiyonu destekleyen kanıt"
    }
  ]
}"""


class ActionRecommendationEngine:
    def __init__(self, model: str = None):
        self.model = model

    def recommend(self, scenario: dict, simulation_result: str,
                  past_lessons: str = "") -> list:
        messages = [
            {"role": "system", "content": SYSTEM},
            {
                "role": "user",
                "content": (
                    f"Senaryo: {scenario.get('name')}\n"
                    f"Açıklama: {scenario.get('description')}\n\n"
                    f"Simülasyon sonucu:\n{simulation_result[:2000]}\n\n"
                    f"Geçmiş dersler:\n{past_lessons}\n\n"
                    f"Kullanılabilir aksiyon tipleri: {list(ACTION_TYPES.keys())}\n\n"
                    f"En fazla 5 aksiyon öner. Somut, uygulanabilir, ölçülebilir ol."
                ),
            },
        ]

        result = chat_json(messages, model=self.model, temperature=0.3)
        actions = result.get("actions", [])

        # Öncelik skoru hesapla
        for action in actions:
            action["priority_score"] = self._priority(action)

        actions.sort(key=lambda a: a["priority_score"], reverse=True)
        for i, action in enumerate(actions, 1):
            action["rank"] = i

        return actions

    def _priority(self, action: dict) -> float:
        impact = action.get("expected_impact_pct", 0) / 100
        confidence = 0.70  # Varsayılan — memory'den gelecek
        cost = max(action.get("estimated_cost_try", 1), 1) / 1_000_000
        days = max(action.get("implementation_days", 1), 1)
        cost_norm = max(cost, 0.001)
        return round((impact * confidence) / (cost_norm * days), 4)
