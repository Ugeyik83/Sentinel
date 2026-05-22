"""
crew/org_loader.py
IGYA org chart JSON → CrewAI Agent hiyerarşisi
Dinamik yükleme — JSON değişince kod değişmez.
"""

import json
import logging
from pathlib import Path
from typing import Optional
from crewai import Agent, Crew, Process, Task
from app.utils.llm_client import get_llm

logger = logging.getLogger(__name__)


class OrgLoader:
    """
    Org chart JSON'dan CrewAI ajan hiyerarşisi kurar.
    Vacant pozisyonlar için geçici ajan oluşturur.
    """

    def __init__(self, org_chart_path: str, job_descriptions: dict = None):
        self.chart = self._load(org_chart_path)
        self.job_descriptions = job_descriptions or {}
        self.agents = {}        # id → Agent
        self.llm = get_llm()

    def _load(self, path: str) -> dict:
        return json.loads(Path(path).read_text(encoding="utf-8"))

    def build_agents(self) -> dict:
        """Tüm pozisyonlar için CrewAI Agent üret."""
        self._traverse(self.chart["hierarchy"])
        logger.info(f"{len(self.agents)} ajan oluşturuldu.")
        return self.agents

    def _traverse(self, node: dict, parent_role: str = None):
        """Recursive olarak tüm node'ları dolaş."""
        agent = self._create_agent(node, parent_role)
        self.agents[node["id"]] = agent

        for child in node.get("delegates_to", []):
            self._traverse(child, parent_role=node["role"])

    def _create_agent(self, node: dict, parent_role: str = None) -> Agent:
        """Tek bir pozisyon için CrewAI Agent oluştur."""
        role = node["role"]
        is_vacant = node.get("vacant", False)
        domains = node.get("domain", [])
        authority = node.get("decision_authority", "operational")
        level = node.get("level", 2)

        # Görev tanımı varsa kullan, yoksa domain'den türet
        job_desc = self.job_descriptions.get(node["id"], "")

        # Ajan backstory — kanıta dayalı persona
        backstory = self._build_backstory(
            role=role,
            domains=domains,
            authority=authority,
            level=level,
            is_vacant=is_vacant,
            job_desc=job_desc,
            parent_role=parent_role,
        )

        return Agent(
            role=role,
            goal=self._build_goal(role, domains, authority, is_vacant),
            backstory=backstory,
            llm=self.llm,
            verbose=True,
            allow_delegation=(level <= 1),   # Director ve üstü delege edebilir
            max_iter=5,
        )

    def _build_goal(self, role: str, domains: list, authority: str, is_vacant: bool) -> str:
        domain_str = ", ".join(domains)
        if is_vacant:
            return (
                f"[VEKİL] {role} pozisyonu şu an boş. "
                f"Mevcut bilgiye dayanarak {domain_str} alanında "
                f"en iyi kararı savun. Belirsizliği açıkça ifade et."
            )
        return (
            f"{domain_str} alanında şirketi koruma ve büyütme hedefiyle "
            f"verilen senaryoyu {authority} yetki seviyesinde değerlendir. "
            f"Kanıta dayalı, net pozisyon al."
        )

    def _build_backstory(
        self, role, domains, authority, level, is_vacant, job_desc, parent_role
    ) -> str:
        base = f"Sen {role} pozisyonundasın."

        if parent_role:
            base += f" {parent_role}'e raporluyorsun."

        if is_vacant:
            base += (
                " Bu pozisyon şu an boş — vekil olarak görev yapıyorsun. "
                "Belirsizlik durumunda üst yönetime eskalasyon önceliğin."
            )

        if job_desc:
            base += f" Görev tanımın: {job_desc[:300]}"
        else:
            base += (
                f" Temel sorumlulukların: {', '.join(domains)}. "
                f"Karar yetkin: {authority}."
            )

        if level == 0:
            base += (
                " Nihai karar merciisin. Çatışan görüşleri sentezler, "
                "organizasyonu yönetirsin. Kısa vadeli maliyet ile "
                "uzun vadeli sürdürülebilirlik arasında denge kurarsın."
            )
        elif level == 1:
            base += (
                " Kendi alanında stratejik kararlar alır, "
                "uygulamayı ekibine delege edersin. "
                "MD'ye eskalasyon eşiğin yüksektir — önce kendi çöz."
            )
        elif level == 2:
            base += (
                " Operasyonel kararlar alır, direktörüne raporlarsın. "
                "Saha gerçekliğini en iyi sen bilirsin — bunu savun."
            )

        return base

    def build_management_committee(self) -> list:
        """
        Konsensüs modu için yönetim komitesi ajanlarını döndür.
        simulation_config.consensus_roles'dan alınır.
        """
        committee_ids = self.chart["simulation_config"]["consensus_roles"]
        return [
            self.agents[aid]
            for aid in committee_ids
            if aid in self.agents
        ]

    def get_crisis_chain(self) -> list:
        """
        Kriz eskalasyon zincirini döndür.
        """
        path = self.chart["simulation_config"]["crisis_escalation_path"]
        chain = []
        for role_hint in path:
            for aid, agent in self.agents.items():
                if role_hint.lower() in aid.lower():
                    chain.append(agent)
                    break
        return chain

    def get_vacant_positions(self) -> list:
        """Boş pozisyonları listele."""
        return self.chart["simulation_config"]["vacant_positions"]

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        return self.agents.get(agent_id)

    def get_by_domain(self, domain: str) -> list:
        """Belirli bir domain'e sahip tüm ajanları getir."""
        result = []
        self._find_by_domain(self.chart["hierarchy"], domain, result)
        return [self.agents[aid] for aid in result if aid in self.agents]

    def _find_by_domain(self, node: dict, domain: str, result: list):
        if domain in node.get("domain", []):
            result.append(node["id"])
        for child in node.get("delegates_to", []):
            self._find_by_domain(child, domain, result)


class ScenarioTaskBuilder:
    """
    Senaryo + ajan → CrewAI Task üretici.
    Her ajan senaryoyu kendi perspektifinden değerlendirir.
    """

    def build_tasks(self, scenario: dict, agents: dict) -> list:
        tasks = []
        scenario_text = scenario.get("description", "")
        time_horizon = scenario.get("time_horizon_days", 90)

        # Seviye 2 ajanlar — saha analizi
        level2_tasks = self._build_operational_tasks(
            scenario_text, time_horizon, agents
        )
        tasks.extend(level2_tasks)

        # Seviye 1 direktörler — departman değerlendirmesi
        level1_tasks = self._build_director_tasks(
            scenario_text, time_horizon, agents, level2_tasks
        )
        tasks.extend(level1_tasks)

        # MD — nihai karar
        md_task = self._build_md_task(
            scenario_text, time_horizon, agents, level1_tasks
        )
        tasks.append(md_task)

        return tasks

    def _build_operational_tasks(self, scenario, horizon, agents) -> list:
        operational_roles = [
            "finance_control_manager",
            "internal_control_risk_manager",
            "it_manager",
            "quality_manager",
            "purchasing_manager",
        ]
        tasks = []
        for role_id in operational_roles:
            if role_id not in agents:
                continue
            agent = agents[role_id]
            tasks.append(Task(
                description=(
                    f"Senaryo: {scenario}\n\n"
                    f"Kendi sorumluluk alanından {horizon} günlük etkiyi analiz et:\n"
                    f"1. Bu senaryo seni nasıl etkiler?\n"
                    f"2. En büyük 3 risk nedir?\n"
                    f"3. Önerdiğin aksiyonlar?\n"
                    f"4. Hangi kaynağa/veriye dayanıyorsun?\n"
                    f"Net ve somut ol. Tahmin değil, analiz yap."
                ),
                agent=agent,
                expected_output=(
                    "Yapılandırılmış analiz: etki özeti, "
                    "3 risk maddesi, aksiyon önerileri, kanıt."
                ),
            ))
        return tasks

    def _build_director_tasks(self, scenario, horizon, agents, upstream_tasks) -> list:
        director_roles = [
            "director_factory_operations",
            "director_planning_logistics",
            "director_business_services_cfo",
            "director_sales_marketing",
            "director_rd",
        ]
        tasks = []
        for role_id in director_roles:
            if role_id not in agents:
                continue
            agent = agents[role_id]
            tasks.append(Task(
                description=(
                    f"Senaryo: {scenario}\n\n"
                    f"Ekibinin analizlerini ve kendi değerlendirmeni birleştir.\n"
                    f"{horizon} günlük departman risk özeti hazırla:\n"
                    f"1. Departman üzerindeki toplam etki (düşük/orta/yüksek/kritik)\n"
                    f"2. Öncelikli 2 aksiyon önerisi\n"
                    f"3. Diğer direktörlerle koordinasyon gereken konular\n"
                    f"4. MD'ye eskalasyon gereken karar var mı?\n"
                    f"Boş pozisyon varsa bunu risk olarak işaretle."
                ),
                agent=agent,
                expected_output=(
                    "Departman risk özeti: etki seviyesi, "
                    "2 aksiyon, koordinasyon ihtiyacı, eskalasyon."
                ),
                context=upstream_tasks,
            ))
        return tasks

    def _build_md_task(self, scenario, horizon, agents, upstream_tasks) -> Task:
        md_agent = agents.get("managing_director")
        return Task(
            description=(
                f"Senaryo: {scenario}\n\n"
                f"Tüm direktörlerin analizlerini değerlendirerek "
                f"şirket geneli {horizon} günlük karar al:\n"
                f"1. Genel risk seviyesi (0-100)\n"
                f"2. Öncelikli 3 organizasyonel aksiyon\n"
                f"3. Hangi direktöre ne görev veriyorsun?\n"
                f"4. YK'ya iletilecek özet (max 5 madde)\n"
                f"5. Boş pozisyonların bu senaryodaki kritikliği\n\n"
                f"Kesin, uygulanabilir kararlar al. "
                f"'Değerlendireceğiz' değil, 'yapacağız' de."
            ),
            agent=md_agent,
            expected_output=(
                "Yönetim kararı: risk skoru, 3 aksiyon + sorumlu direktör, "
                "YK özeti, boş pozisyon kritiklik değerlendirmesi."
            ),
            context=upstream_tasks,
        )
