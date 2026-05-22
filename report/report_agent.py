"""
report/report_agent.py
"""

import json
import logging
from pathlib import Path
from app.utils.llm_client import chat, chat_json

logger = logging.getLogger(__name__)

REPORT_SYSTEM = """Sen kurumsal yönetim kurulu raporu yazarısın.
Simülasyon verilerinden net, somut ve uygulanabilir bir YK raporu yaz.

Rapor bölümleri:
1. Yönetici Özeti (max 5 madde)
2. Tetikleyen Sinyaller
3. Risk Propagasyon Zinciri
4. Simülasyon Bulguları
5. Önerilen Aksiyonlar (sorumlu direktör + süre — maliyet tahmini yazma)
7. Sonraki Adımlar

KURALLAR:
- MUTLAKA Türkçe yaz
- Aksiyon başlıkları Türkçe olsun (HEDGE → Döviz Koruması, COMMUNICATE → Paydaş İletişimi, DIVERSIFY → Tedarik Çeşitlendirme, STOCKPILE → Stok Güçlendirme, INVESTMENT → Teknoloji Yatırımı, DELAY → Karar Erteleme, AUDIT → Denetim, ESCALATE → Üst Yönetime Eskalasyon, INSURANCE → Sigorta, POLICY_CHANGE → Politika Değişikliği)
- Maliyet tahmini yazma — gerçekçi değil
- Risk skoru veya güven skoru sayısal olarak yazma — bu değerler hesaplanamaz
- Net, aksiyon odaklı yaz"""

VERDICT_SYSTEM = """Rapor ve simülasyondan makine-okunabilir verdict üret.
MUTLAKA Türkçe yaz.

SADECE JSON döndür:
{
  "predicted_outcome": "kısa Türkçe tahmin özeti (max 60 karakter)",
  "time_horizon": "30 gün veya 90 gün veya 180 gün",
  "key_signals": [
    {
      "signal": "sinyal adı (Türkçe)",
      "severity": "high veya medium veya low",
      "description": "kısa Türkçe açıklama"
    }
  ],
  "recommended_actions": ["Türkçe aksiyon 1", "Türkçe aksiyon 2"]
}"""

ACTION_NAME_MAP = {
    "hedge": "Döviz Koruması",
    "communicate": "Paydaş İletişimi",
    "diversify": "Tedarik Çeşitlendirme",
    "stockpile": "Stok Güçlendirme",
    "investment": "Teknoloji Yatırımı",
    "delay": "Karar Erteleme",
    "audit": "Denetim",
    "escalate": "Üst Yönetime Eskalasyon",
    "insurance": "Sigorta",
    "policy_change": "Politika Değişikliği",
}


class ReportAgent:
    def __init__(self, run_dir: str, model: str = None):
        self.run_dir = Path(run_dir)
        self.model = model

    def generate(self, scenario: dict, simulation_result: dict,
                 actions: list, confidence: dict) -> dict:
        # Aksiyon isimlerini Türkçeye çevir
        for action in actions:
            action_type = action.get("type", "").lower()
            if action_type in ACTION_NAME_MAP:
                action["type"] = ACTION_NAME_MAP[action_type]

        context = self._build_context(scenario, simulation_result, actions)

        messages = [
            {"role": "system", "content": REPORT_SYSTEM},
            {"role": "user", "content": context},
        ]

        report_md = chat(messages, model=self.model, max_tokens=4096, temperature=0.3)
        verdict = self._generate_verdict(scenario, report_md)

        report_dir = self.run_dir / "report"
        report_dir.mkdir(parents=True, exist_ok=True)
        (report_dir / "report.md").write_text(report_md, encoding="utf-8")
        (report_dir / "verdict.json").write_text(
            json.dumps(verdict, ensure_ascii=False, indent=2)
        )

        return {"report_md": report_md, "verdict": verdict}

    def _build_context(self, scenario, result, actions) -> str:
        top_actions = "\n".join([
            f"  {i+1}. {a.get('type','?')}: {a.get('description','')}"
            f" — Sorumlu: {a.get('responsible_role_id','?')}"
            f", Süre: {a.get('implementation_days','?')} gün"
            for i, a in enumerate(actions[:5])
        ]) if actions else "Henüz aksiyon üretilmedi."

        return (
            f"Senaryo: {scenario.get('name')}\n"
            f"Açıklama: {scenario.get('description')}\n\n"
            f"Simülasyon sonucu:\n{result.get('result', '')[:2000]}\n\n"
            f"Önerilen aksiyonlar:\n{top_actions}"
        )

    def _generate_verdict(self, scenario, report_md) -> dict:
        messages = [
            {"role": "system", "content": VERDICT_SYSTEM},
            {"role": "user", "content": f"Senaryo: {scenario.get('name')}\n\nRapor:\n{report_md[:2000]}"},
        ]
        try:
            return chat_json(messages, model=self.model, temperature=0.2)
        except Exception as e:
            logger.error(f"Verdict hatası: {e}")
            return {
                "predicted_outcome": scenario.get("name", ""),
                "time_horizon": f"{scenario.get('time_horizon_days', 90)} gün",
                "key_signals": [],
                "recommended_actions": [],
            }