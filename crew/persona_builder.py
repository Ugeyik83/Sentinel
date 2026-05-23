"""
crew/persona_builder.py
Kanıta dayalı persona üretimi.

Görev tanımı (DOCX'ten parse edilmiş metin) +
geçmiş karar geçmişi (memory/incidents/) → ajan kişiliği.

Çıktı org_loader.py'deki _build_backstory'ye ek olarak kullanılır.
"""

import logging
from app.utils.llm_client import chat_json

logger = logging.getLogger(__name__)

SYSTEM = """Sen kurumsal ajan persona uzmanısın.
Verilen görev tanımı ve karar geçmişinden yönetici kişiliği üret.

Çıktı SADECE JSON:
{
  "stated_priorities": ["öncelik 1", "öncelik 2", "öncelik 3"],
  "decision_style": "analytical|intuitive|consensus|authoritative",
  "risk_appetite": "low|medium|high",
  "primary_bias": "cost|growth|safety|compliance|innovation",
  "conflict_tendency": "avoidant|collaborative|assertive|dominant",
  "backstory_addition": "tek paragraf — ajan kişiliğini derinleştiren metin"
}"""


class PersonaBuilder:
    """
    Ajan kişiliğini görev tanımı + karar geçmişinden türet.
    LLM ile zenginleştirilmiş — org_loader'daki temel backstory'ye ek katman.
    """

    def __init__(self, model: str = None):
        self.model = model

    def build(
        self,
        role_id: str,
        job_description: str = "",
        decision_history: list = None,
    ) -> dict:
        """
        Args:
            role_id: Org chart ID (örn. "director_business_services_cfo")
            job_description: DOCX'ten parse edilmiş görev tanımı metni
            decision_history: memory/incidents/ içindeki geçmiş kararlar

        Returns:
            Persona dict — org_loader._create_agent() içinde backstory'ye eklenir
        """
        # Görev tanımı veya geçmiş yoksa — temel stub döndür
        if not job_description and not decision_history:
            return self._stub(role_id)

        history_text = self._format_history(decision_history or [])

        messages = [
            {"role": "system", "content": SYSTEM},
            {
                "role": "user",
                "content": (
                    f"Pozisyon: {role_id}\n\n"
                    f"Görev tanımı:\n{job_description[:1500] if job_description else 'Mevcut değil'}\n\n"
                    f"Geçmiş kararlar:\n{history_text if history_text else 'Kayıt yok'}\n\n"
                    f"Bu yöneticinin kişiliğini ve önceliklerini analiz et."
                ),
            },
        ]

        try:
            result = chat_json(messages, model=self.model, temperature=0.4)
            result["role_id"] = role_id
            result["job_description"] = job_description[:300] if job_description else ""
            result["uncertainty"] = "low" if job_description else "medium"
            result["source"] = "llm_enriched"
            return result
        except Exception as e:
            logger.warning(f"Persona üretimi başarısız [{role_id}]: {e}")
            return self._stub(role_id)

    def _format_history(self, history: list) -> str:
        """
        memory/incidents/ formatındaki geçmiş kararları özetle.
        Beklenen format: [{"scenario": "...", "decision": "...", "outcome": "..."}]
        """
        if not history:
            return ""
        lines = []
        for i, h in enumerate(history[-5:], 1):   # Son 5 karar
            lines.append(
                f"{i}. Senaryo: {h.get('scenario', '?')[:80]} | "
                f"Karar: {h.get('decision', '?')[:60]} | "
                f"Sonuç: {h.get('outcome', '?')[:60]}"
            )
        return "\n".join(lines)

    def _stub(self, role_id: str) -> dict:
        """Veri yokken temel persona."""
        return {
            "role_id": role_id,
            "job_description": "",
            "stated_priorities": [],
            "decision_style": "analytical",
            "risk_appetite": "medium",
            "primary_bias": "growth",
            "conflict_tendency": "collaborative",
            "backstory_addition": "",
            "uncertainty": "high",
            "source": "stub",
        }

    def enrich_backstory(self, base_backstory: str, persona: dict) -> str:
        """
        org_loader._build_backstory() çıktısına persona katmanını ekle.
        org_loader.py'de _create_agent() içinde çağrılır.
        """
        addition = persona.get("backstory_addition", "")
        style = persona.get("decision_style", "")
        bias = persona.get("primary_bias", "")
        appetite = persona.get("risk_appetite", "")

        enrichment = []
        if style:
            enrichment.append(f"Karar alma stili: {style}.")
        if bias:
            enrichment.append(f"Öncelikli odak: {bias}.")
        if appetite:
            enrichment.append(f"Risk iştahı: {appetite}.")
        if addition:
            enrichment.append(addition)

        if not enrichment:
            return base_backstory

        return base_backstory + " " + " ".join(enrichment)
