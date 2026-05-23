"""
crew/debate/roles.py
Sabit debate rolleri: Devil's Advocate + Red Team + Judge
"""

from app.utils.llm_client import chat


class DebateAgent:
    """Temel debate ajan sınıfı."""

    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = system_prompt
        self.memory = []

    def respond(self, context: str, history: list) -> str:
        messages = []

        # Geçmiş turlar
        for h in history:
            messages.append({"role": "user", "content": h["content"]})
            if "response" in h:
                messages.append({"role": "assistant", "content": h["response"]})

        # Mevcut tur — system prompt ilk mesaja prefix olarak eklenir
        user_content = "[GÖREV]\n" + self.system_prompt + "\n\n[BAĞLAM]\n" + context
        messages.append({"role": "user", "content": user_content})

        return chat(messages, temperature=0.4, max_tokens=1000)


class DevilsAdvocate(DebateAgent):
    """
    Devil's Advocate — konsensüse karşı çıkar.
    """

    SYSTEM = """Sen bir kurumsal risk tartışmasında Devil's Advocate rolündesin.

Görevin: Konsensüse karşı çık. Eksik perspektifi ortaya koy.

KURALLAR:
- Her zaman Türkçe yaz
- "Peki ya..." veya "Bunu hiç düşündünüz mü..." ile başla
- Bir tek güçlü itiraz üret, birden fazla değil
- Somut, senaryo-spesifik ol
- Maksimum 3 cümle"""

    def __init__(self):
        super().__init__("Devil's Advocate", self.SYSTEM)


class RedTeam(DebateAgent):
    """
    Red Team — 3 başarısızlık modunu üretir.
    """

    SYSTEM = """Sen bir kurumsal risk tartışmasında Red Team rolündesin.

Görevin: Önerilen aksiyonun nasıl başarısız olabileceğini göster.

KURALLAR:
- Her zaman Türkçe yaz
- TAM OLARAK 3 başarısızlık modu üret
- Format: "Başarısızlık 1: [başlık] — [tek cümle]"
- Farklı açılar: operasyonel, finansal, insan faktörü
- Her mod somut ve senaryo-spesifik olmalı"""

    def __init__(self):
        super().__init__("Red Team", self.SYSTEM)


class Judge(DebateAgent):
    """
    Judge — tartışmayı sentezler, muhalefet şerhiyle karar verir.
    """

    SYSTEM = """Sen bir kurumsal karar tartışmasının hakemisin.

Görevin: Tüm görüşleri değerlendirip final karar ver.

FORMAT (Türkçe, zorunlu):
KARAR: [tek cümle net karar]

GEREKÇE: [2-3 cümle]

MUHALEFET ŞERHİ: [varsa] veya Muhalefet yok.

SONRAKI ADIM: [kim ne yapmalı, ne zaman]

KURALLAR:
- Her zaman Türkçe yaz
- Karar belirsiz olamaz
- Escalation gerekiyorsa açıkça belirt"""

    def __init__(self):
        super().__init__("Judge", self.SYSTEM)
