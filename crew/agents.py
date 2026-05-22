"""
crew/agents.py
Dinamik ajan üretimi — org_loader.py üzerinden çalışır.
"""

from crew.org_loader import OrgLoader


def build_agents(org_chart_path: str = "config/org_chart.json",
                 job_descriptions: dict = None) -> dict:
    loader = OrgLoader(org_chart_path, job_descriptions or {})
    return loader.build_agents()
