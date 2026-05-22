"""
streamlit_app/pages/org_setup.py
PPTX / DOCX / JSON org chart yükleme.
"""

import streamlit as st
import json
from pathlib import Path
from crew.org_loader import OrgLoader


def render():
    st.title("🏢 Org Setup")
    st.caption("Organizasyon şemasını yükleyin — CrewAI ajan hiyerarşisi otomatik kurulur.")

    # Mevcut org chart
    org_path = Path("config/org_chart.json")
    if org_path.exists():
        with st.expander("✅ Mevcut Org Chart", expanded=False):
            st.json(json.loads(org_path.read_text()))

    st.divider()

    tab1, tab2 = st.tabs(["JSON Yükle", "Görsel Kontrol"])

    with tab1:
        uploaded = st.file_uploader("Org chart JSON yükle", type=["json"])
        if uploaded:
            data = json.loads(uploaded.read())
            org_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
            st.success("✅ Org chart güncellendi.")

    with tab2:
        if org_path.exists():
            loader = OrgLoader(str(org_path))
            agents = loader.build_agents()
            st.metric("Toplam Pozisyon", len(agents))
            vacants = loader.get_vacant_positions()
            if vacants:
                st.warning(f"Boş pozisyonlar: {', '.join(vacants)}")
            for agent_id, agent in agents.items():
                st.caption(f"✓ `{agent_id}` — {agent.role}")
