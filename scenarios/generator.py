"""
scenarios/generator.py
LLM + memory few-shot + sinyal → otomatik senaryo üretimi.
"""

import json
import logging
import yaml
from pathlib import Path
from datetime import datetime, timezone
from app.utils.llm_client import chat_json
from scenarios.confidence import ConfidenceScorer
from scenarios.validator import ScenarioValidator

logger = logging.getLogger(__name__)
CATALOG_DIR = Path("scenarios/catalog")

SYSTEM = """Sen IGYA (İnci GS Yuasa) şirketi için kurumsal risk senaryosu uzmanısın.
IGYA Manisa'da kurulu, endüstriyel ve otomotiv bataryası üretiyor.

Kullanıcının verdiği GEREKSİNİMİ dikkate alarak DOĞRUDAN O KONUYA özgü 
risk senaryoları üret. Genel şirket riskleri değil, gereksinimde belirtilen 
spesifik olayın IGYA'ya etkilerini senaryo olarak yaz.

Örneğin gereksinim "Türkiye'de politik kriz" ise:
- "Kur baskısı ve ihracat geliri erimesi" senaryo olabilir
- "Tedarik zinciri kesintisi" çok genel — kabul etme

Her senaryo için şu JSON formatını kullan:
{
  "id": "sc_YYYYMMDD_NNN",
  "name": "Gereksinimle doğrudan bağlantılı senaryo adı",
  "description": "Gereksinimde belirtilen olayın IGYA'ya spesifik etkisi",
  "affected_risks": ["spesifik risk id'leri"],
  "affected_roles": ["etkilenen org chart rolleri"],
  "simulation_mode": "hierarchical veya consensus",
  "time_horizon_days": sayı,
  "trigger_signals": ["tetikleyici sinyal isimleri"],
  "supporting_evidence": ["kanıt 1", "kanıt 2", "kanıt 3"],
  "source_references": ["kaynak"]
}

KRİTİK: Senaryo adı ve açıklaması mutlaka kullanıcının gereksinimini yansıtmalı."""


class ScenarioGenerator:
    def __init__(self, model: str = None):
        self.model = model
        self.scorer = ConfidenceScorer()
        self.validator = ScenarioValidator()

    def generate(self, signals: list, graph: dict,
                 past_lessons: str = "", count: int = 3,
                 requirement: str = "") -> list:
        signal_summary = self._summarize_signals(signals)
        graph_summary = self._summarize_graph(graph)

        messages = [
            {"role": "system", "content": SYSTEM},
            {
                "role": "user",
                "content": (
                    f"GEREKSİNİM (BU KONUDA SENARYO ÜRETECEKSİN):\n{requirement}\n\n"
                    f"---\n"
                    f"Mevcut sinyaller:\n{signal_summary if signal_summary else 'Sinyal yok — gereksinime göre üret'}\n\n"
                    f"Şirket yapısı:\n{graph_summary}\n\n"
                    f"Geçmiş dersler:\n{past_lessons if past_lessons else 'Henüz yok'}\n\n"
                    f"TALİMAT: Yukarıdaki GEREKSİNİM ile doğrudan ilgili {count} senaryo üret. "
                    f"Her senaryo gereksinimde belirtilen olayın IGYA'ya farklı bir etkisini göstermeli. "
                    f"Çıktı: {{\"scenarios\": [...]}}"
                ),
            },
        ]

        result = chat_json(messages, model=self.model, temperature=0.5)
        raw_scenarios = result.get("scenarios", [])

        validated = []
        for scenario in raw_scenarios:
            scenario["id"] = self._gen_id()
            scenario["generated_at"] = datetime.now(timezone.utc).isoformat()
            scenario["confidence"] = self.scorer.score(scenario, signals, graph)
            validation = self.validator.validate(scenario, graph, signals)
            if validation["valid"]:
                validated.append(scenario)
            else:
                logger.warning(f"Senaryo reddedildi [{scenario.get('name')}]: {validation['errors']}")

        # Katalog senaryolarını da ekle
        catalog = self._load_catalog_scenarios(signals)
        validated.extend(catalog)

        validated.sort(key=lambda s: s.get("confidence", {}).get("confidence", 0), reverse=True)
        logger.info(f"{len(validated)} senaryo üretildi")
        return validated

    def _summarize_signals(self, signals: list) -> str:
        if not signals:
            return ""
        top = sorted(signals, key=lambda s: s.get("composite_score", 0), reverse=True)[:10]
        return "\n".join(
            f"- {s.get('title', '?')} (skor: {s.get('composite_score', 0):.2f}, "
            f"kaynak: {s.get('source', '?')})"
            for s in top
        )

    def _summarize_graph(self, graph: dict) -> str:
        meta = graph.get("metadata", {})
        top_nodes = sorted(
            graph.get("nodes", []),
            key=lambda n: n.get("degree", 0),
            reverse=True
        )[:8]
        nodes_str = ", ".join(n.get("label", n.get("id", "?")) for n in top_nodes)

        # İhracat pazarlarını config'den dinamik çek
        markets_str = ""
        try:
            import yaml
            markets_path = Path("config/export_markets.yaml")
            if markets_path.exists():
                markets = yaml.safe_load(markets_path.read_text()).get("markets", [])
                if markets:
                    market_names = [m["country"] for m in markets[:5]]
                    markets_str = f", İhracat pazarları: {', '.join(market_names)}"
        except Exception:
            pass

        return (
            f"Domain: {meta.get('domain', 'ERM')}, "
            f"Temalar: {', '.join(meta.get('key_themes', ['risk', 'finance', 'operations']))}, "
            f"Pozisyonlar: {nodes_str}"
            f"{markets_str}"
        )

    def _load_catalog_scenarios(self, signals: list) -> list:
        catalog = []
        if not CATALOG_DIR.exists():
            return catalog
        for yaml_file in CATALOG_DIR.glob("*.yaml"):
            try:
                data = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
                for scenario in data.get("scenarios", []):
                    if self._is_triggered(scenario, signals):
                        scenario["source"] = "catalog"
                        scenario["confidence"] = {
                            "confidence": 0.85,
                            "signal_strength": "catalog"
                        }
                        scenario["generated_at"] = datetime.now(timezone.utc).isoformat()
                        catalog.append(scenario)
            except Exception as e:
                logger.warning(f"Katalog yüklenemedi [{yaml_file}]: {e}")
        return catalog

    def _is_triggered(self, scenario: dict, signals: list) -> bool:
        trigger = scenario.get("trigger", "")
        if not trigger or not signals:
            return False
        signal_metrics = {s.get("metric", ""): s.get("composite_score", 0) for s in signals}
        for metric, score in signal_metrics.items():
            if metric in trigger and score > 0.5:
                return True
        return False

    def _gen_id(self) -> str:
        import random
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"sc_{ts}_{random.randint(100, 999)}"