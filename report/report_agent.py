"""
report/report_agent.py
LLM → YK raporu (Markdown + PDF).
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
5. Önerilen Aksiyonlar (sorumlu + süre + maliyet)
6. Güven Değerlendirmesi
7. Sonraki Adımlar

Türkçe, net, aksiyon odaklı yaz."""


class ReportAgent:
    def __init__(self, run_dir: str, model: str = None):
        self.run_dir = Path(run_dir)
        self.model = model

    def generate(self, scenario: dict, simulation_result: dict,
                 actions: list, confidence: dict) -> dict:
        context = self._build_context(scenario, simulation_result, actions, confidence)

        messages = [
            {"role": "system", "content": REPORT_SYSTEM},
            {"role": "user", "content": context},
        ]

        report_md = chat(messages, model=self.model, max_tokens=4096, temperature=0.3)

        verdict = self._generate_verdict(scenario, report_md, actions, confidence)

        # Kaydet
        report_dir = self.run_dir / "report"
        report_dir.mkdir(parents=True, exist_ok=True)
        (report_dir / "report.md").write_text(report_md, encoding="utf-8")
        (report_dir / "verdict.json").write_text(
            json.dumps(verdict, ensure_ascii=False, indent=2)
        )

        return {"report_md": report_md, "verdict": verdict}

    def _build_context(self, scenario, result, actions, confidence) -> str:
        top_actions = "\n".join([
            f"  {a['rank']}. {a['type'].upper()}: {a['description']} "
            f"(etki: %{a.get('expected_impact_pct', 0)}, "
            f"maliyet: {a.get('estimated_cost_try', 0):,} TL, "
            f"süre: {a.get('implementation_days', 0)} gün)"
            for a in actions[:5]
        ])
        return (
            f"Senaryo: {scenario.get('name')}\n"
            f"Açıklama: {scenario.get('description')}\n"
            f"Güven skoru: {confidence.get('confidence', 0)}\n"
            f"Sinyal gücü: {confidence.get('signal_strength', '?')}\n\n"
            f"Simülasyon sonucu:\n{result.get('result', '')[:2000]}\n\n"
            f"Önerilen aksiyonlar:\n{top_actions}"
        )

    def _generate_verdict(self, scenario, report_md, actions, confidence) -> dict:
        messages = [
            {
                "role": "system",
                "content": (
                    "Rapor ve simülasyondan makine-okunabilir verdict üret. "
                    "SADECE JSON: {predicted_outcome, confidence_score, "
                    "time_horizon, key_signals: [{signal, severity, description}], "
                    "risk_scores: {kategori: 0-100}, recommended_actions: [str]}"
                )
            },
            {
                "role": "user",
                "content": (
                    f"Senaryo: {scenario.get('name')}\n"
                    f"Özet rapor:\n{report_md[:2000]}"
                )
            },
        ]
        return chat_json(messages, model=self.model, temperature=0.2)
