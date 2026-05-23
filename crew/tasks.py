"""
crew/tasks.py
Senaryoya göre CrewAI görev üretimi.

org_loader.py'deki ScenarioTaskBuilder buraya taşındı.
org_loader.py'de stub bırakıldı — geriye dönük uyumluluk için.

Görev hiyerarşisi:
  Level 2 (Müdürler) → kendi domain analizi
  Level 1 (Direktörler) → departman özeti, upstream'e bakarak
  Level 0 (MD) → şirket geneli karar, tüm direktörlere bakarak
"""

import logging
from crewai import Task

logger = logging.getLogger(__name__)

# Level 2 — operasyonel müdürler
OPERATIONAL_ROLES = [
    "finance_control_manager",
    "internal_control_risk_manager",
    "it_manager",
    "quality_manager",
    "purchasing_manager",
    "hr_manager",
    "legal_counsel",
]

# Level 1 — direktörler
DIRECTOR_ROLES = [
    "director_factory_operations",
    "director_planning_logistics",
    "director_business_services_cfo",
    "director_sales_marketing",
    "director_rd",
]


class ScenarioTaskBuilder:
    """
    Senaryo + ajan dict'ten CrewAI görev listesi üret.
    Görevler hiyerarşik sırada — her katman bir üstünün context'i.
    """

    def build_tasks(self, scenario: dict, agents: dict) -> list[Task]:
        tasks = []
        scenario_text = scenario.get("description", scenario.get("name", ""))
        time_horizon = scenario.get("time_horizon_days", 90)
        impact_label = scenario.get("impact_label", "orta")
        dominant = scenario.get("dominant_signals", [])
        dominant_str = (
            ", ".join(s.get("title", "") for s in dominant[:3])
            if dominant else "Sinyal verisi yok"
        )

        # ── Level 2: Müdürler ────────────────────────────────────────────
        level2_tasks = self._build_operational_tasks(
            scenario_text, time_horizon, impact_label, dominant_str, agents
        )
        tasks.extend(level2_tasks)

        # ── Level 1: Direktörler ─────────────────────────────────────────
        level1_tasks = self._build_director_tasks(
            scenario_text, time_horizon, impact_label, agents, level2_tasks
        )
        tasks.extend(level1_tasks)

        # ── Level 0: MD ──────────────────────────────────────────────────
        md_task = self._build_md_task(
            scenario_text, time_horizon, agents, level1_tasks
        )
        if md_task:
            tasks.append(md_task)

        logger.info(
            f"Görev üretildi: {len(level2_tasks)} müdür + "
            f"{len(level1_tasks)} direktör + MD"
        )
        return tasks

    # ── LEVEL 2 ──────────────────────────────────────────────────────────

    def _build_operational_tasks(
        self, scenario: str, horizon: int,
        impact_label: str, dominant_signals: str, agents: dict
    ) -> list[Task]:
        tasks = []
        for role_id in OPERATIONAL_ROLES:
            if role_id not in agents:
                continue
            tasks.append(Task(
                description=(
                    f"SENARYO: {scenario}\n"
                    f"ETKİ SEVİYESİ: {impact_label} | ZAMAN UFKU: {horizon} gün\n"
                    f"AKTİF SİNYALLER: {dominant_signals}\n\n"
                    f"Kendi sorumluluk alanından bu senaryoyu analiz et:\n"
                    f"1. Bu senaryo seni nasıl etkiler? (somut rakam ver)\n"
                    f"2. En kritik 3 risk nedir?\n"
                    f"3. Önerdiğin 2 aksiyon — kısa vadeli + uzun vadeli\n"
                    f"4. Direktörüne iletmen gereken tek cümle özet\n\n"
                    f"Kısa ve net ol. Belirsiz ifade kullanma."
                ),
                agent=agents[role_id],
                expected_output=(
                    "Yapılandırılmış analiz:\n"
                    "ETKİ: [somut etki açıklaması]\n"
                    "RİSKLER: [1. ... 2. ... 3. ...]\n"
                    "AKSİYONLAR: [kısa: ... | uzun: ...]\n"
                    "ÖZET: [tek cümle direktör özeti]"
                ),
            ))
        return tasks

    # ── LEVEL 1 ──────────────────────────────────────────────────────────

    def _build_director_tasks(
        self, scenario: str, horizon: int,
        impact_label: str, agents: dict, upstream_tasks: list[Task]
    ) -> list[Task]:
        tasks = []
        for role_id in DIRECTOR_ROLES:
            if role_id not in agents:
                continue
            tasks.append(Task(
                description=(
                    f"SENARYO: {scenario}\n"
                    f"ETKİ: {impact_label} | ZAMAN UFKU: {horizon} gün\n\n"
                    f"Müdürlerinin analizlerini değerlendirerek departman risk özeti hazırla:\n"
                    f"1. Departman geneli etki seviyesi: DÜŞÜK / ORTA / YÜKSEK / KRİTİK\n"
                    f"2. Öncelikli 2 aksiyon — kim yapacak, ne zaman\n"
                    f"3. MD'ye eskalasyon gerekiyor mu? Neden?\n"
                    f"4. Bütçe etkisi var mı? Tahmini tutar (TL)\n\n"
                    f"Müdür görüşleriyle çelişiyorsan belirt."
                ),
                agent=agents[role_id],
                expected_output=(
                    "Departman risk özeti:\n"
                    "DEPARTMAN ETKİSİ: [seviye]\n"
                    "AKSİYON 1: [açıklama | sorumlu | süre]\n"
                    "AKSİYON 2: [açıklama | sorumlu | süre]\n"
                    "ESKALASYON: [Evet/Hayır — gerekçe]\n"
                    "BÜTÇE ETKİSİ: [tutar veya N/A]"
                ),
                context=upstream_tasks,   # Müdür analizlerini gör
            ))
        return tasks

    # ── LEVEL 0 ──────────────────────────────────────────────────────────

    def _build_md_task(
        self, scenario: str, horizon: int,
        agents: dict, upstream_tasks: list[Task]
    ) -> Task | None:
        md_agent = agents.get("managing_director")
        if not md_agent:
            logger.warning("managing_director ajanı bulunamadı — MD görevi atlandı")
            return None

        return Task(
            description=(
                f"SENARYO: {scenario}\n"
                f"ZAMAN UFKU: {horizon} gün\n\n"
                f"Tüm direktör raporlarını değerlendirerek şirket geneli karar al:\n"
                f"1. Genel risk skoru: 0–100\n"
                f"2. Öncelikli 3 aksiyon — her biri için sorumlu direktör\n"
                f"3. İnsan kaynağı veya bütçe transferi gerekiyor mu?\n"
                f"4. YK'ya iletilecek özet — max 5 madde, yönetici dili\n"
                f"5. Bir direktörün önerisiyle aynı fikirde değilsen açıkla\n\n"
                f"Kararlı ol. 'Değerlendirilmeli' gibi belirsiz ifade kullanma."
            ),
            agent=md_agent,
            expected_output=(
                "Yönetim kararı:\n"
                "RİSK SKORU: [0-100]\n"
                "AKSİYON 1: [açıklama | sorumlu direktör | süre]\n"
                "AKSİYON 2: [açıklama | sorumlu direktör | süre]\n"
                "AKSİYON 3: [açıklama | sorumlu direktör | süre]\n"
                "YK ÖZETİ: [5 madde]\n"
                "MUHALEFET: [varsa hangi direktörle ve neden]"
            ),
            context=upstream_tasks,
        )
