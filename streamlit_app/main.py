"""
streamlit_app/main.py — Ana giriş noktası.
"""

import streamlit as st
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

st.set_page_config(
    page_title="SENTINEL — Enterprise Resilience",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from streamlit_app.pages import (
    dashboard, org_setup, scenarios,
    memory, settings
)

with st.sidebar:
    st.markdown("## 🛡️ SENTINEL")
    st.caption("AI-Powered Enterprise Resilience Platform")
    st.divider()
    page = st.radio("Menü", options=[
        "📡 Dashboard",
        "🏢 Org Setup",
        "⚡ Senaryolar",
        "🧠 Hafıza",
        "⚙️ Ayarlar",
    ], label_visibility="collapsed")
    st.divider()
    st.caption(f"Model: `{os.environ.get('LLM_MODEL_NAME', 'gpt-4o')}`")
    st.caption("Veri: Lokal · Harici veri çıkmaz")

PAGE_MAP = {
    "📡 Dashboard": dashboard.render,
    "🏢 Org Setup": org_setup.render,
    "⚡ Senaryolar": scenarios.render,
    "🧠 Hafıza": memory.render,
    "⚙️ Ayarlar": settings.render,
}

PAGE_MAP[page]()