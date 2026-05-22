"""
crew/persona_builder.py
Kanıta dayalı persona üretimi.
Görev tanımı (DOCX) + geçmiş karar geçmişi → ajan kişiliği.
Şu an: görev tanımı DOCX bekleniyor (henüz yüklenmedi).
"""
import logging
logger = logging.getLogger(__name__)

class PersonaBuilder:
    def build(self, role_id: str, job_description: str = "",
              decision_history: list = None) -> dict:
        """
        Görev tanımı gelince bu metod LLM ile zenginleştirilecek.
        Şu an org_loader.py'deki temel backstory kullanılıyor.
        """
        return {
            "role_id": role_id,
            "job_description": job_description,
            "stated_priorities": [],
            "observed_behavior": None,
            "uncertainty": "high" if not job_description else "medium",
        }
