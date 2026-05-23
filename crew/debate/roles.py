"""
crew/debate/roles.py
Sabit debate rolleri: Devil's Advocate + Red Team + Judge
Org chart ajanlarından bağımsız — her simülasyona eklenir.
"""

import os
from anthropic import Anthropic

client = Anthropic()
MODEL = os.environ.get("LLM_MODEL_NAME", "claude-sonnet-4-6")


class DebateAgent:
    """Temel debate ajan sınıfı."""

    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = system_prompt
        self.memory = []  # Son 5 tartışmadan pozisyon hafızası

    def respond(self, context: str, history: list) -> str:
        messages = []
        for h in history:
            messages.append({"role": "user", "content": h["content"]})
            if "response" in h:
                messages.append({"role": "assistant", "content": h["response"]})
        messages.append({"role": "user", "content": context})

        response = client.messages.create(
            model=MODEL,
            max_tokens=1000,
            system=self.system_prompt,
            messages=messages,
        )
        return response.content[0].text


class DevilsAdvocate(DebateAgent):
    """
    Devil's Advocate — konsensüse karşı çıkar.
    Argümanı değil pozisyonu rotasyonlu — hafızadan farklı olanı seçer.
    """

    SYSTEM = """Sen bir kurumsal risk tartışmasında Devil's Advocate rolündesin.

    Görevin: Konsensüse karşı çık. Eksik perspektifi ortaya koy.
    Pozisyon rotasyonu: Önceki tartışmalarda hangi tezi savunduysan, bu kez farklı olanı seç.
    
    KURALLAR:
    - Her zaman Türkçe yaz
    - "Peki ya..." veya "Bunu hiç düşündünüz mü..." ile başla
    - Bir tek güçlü itiraz üret, birden fazla değil
    - Somut, senaryo-spesifik ol — genel laflardan kaçın
    - Maksimum 3 cümle"""

    def __init__(self):
        super().__init__("Devil's Advocate", self.SYSTEM)


class RedTeam(DebateAgent):
    """
    Red Team — başarısızlık modlarını üretir.
    En az 3 farklı açıdan saldırır.
    """

    SYSTEM = """Sen bir kurumsal risk tartışmasında Red Team rolündesin.

    Görevin: Önerilen aksiyonun veya kararın nasıl başarısız olabileceğini göster.
    
    KURALLAR:
    - Her zaman Türkçe yaz
    - TAM OLARAK 3 başarısızlık modu üret — ne daha az ne daha fazla
    - Format: "Başarısızlık 1: [kısa başlık] — [tek cümle açıklama]"
    - Farklı açılardan saldır: operasyonel, finansal, davranışsal/insan faktörü
    - Her başarısızlık modu somut ve senaryo-spesifik olmalı"""

    def __init__(self):
        super().__init__("Red Team", self.SYSTEM)


class Judge(DebateAgent):
    """
    Judge — tartışmayı sentezler, muhalefet şerhiyle karar verir.
    Hierarchical: en üst yetkili ajan tartar.
    """

    SYSTEM = """Sen bir kurumsal karar tartışmasının hakemisin.

    Görevin: Tüm görüşleri değerlendirip final karar ver.
    
    FORMAT (Türkçe, zorunlu):
    KARAR: [tek cümle net karar]
    
    GEREKÇE: [2-3 cümle — hangi argümanlar belirleyici oldu]
    
    MUHALEFET ŞERHİ: [varsa — hangi ajan hangi konuda haklıydı ama genel karar bu yönde değil]
    
    SONRAKI ADIM: [kim ne yapmalı, ne zaman]
    
    KURALLAR:
    - Her zaman Türkçe yaz
    - Karar belirsiz olamaz — "değerlendireceğiz" kabul edilmez
    - Muhalefet şerhi varsa mutlaka yaz — yoksa "Muhalefet yok" yaz
    - Escalation gerekiyorsa açıkça belirt"""

    def __init__(self):
        super().__init__("Judge", self.SYSTEM)
