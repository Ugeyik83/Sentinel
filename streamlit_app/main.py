"""
streamlit_app/main.py — SENTINEL v6
"""

import streamlit as st
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

st.set_page_config(
    page_title="SENTINEL",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@500&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'IBM Plex Sans', sans-serif !important;
    background: #F0F2F5 !important;
}

#MainMenu, footer, [data-testid="stToolbar"] { display: none !important; }

[data-testid="stSidebar"] {
    background: #FFFFFF !important;
    border-right: 1px solid #E2E8F0 !important;
}

[data-testid="stMetric"] {
    background: white !important;
    border: 1px solid #E2E8F0 !important;
    border-top: 3px solid #0F62FE !important;
    padding: 16px 20px !important;
    border-radius: 8px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06) !important;
}

.stButton > button[kind="primary"] {
    background: #0F62FE !important;
    border: none !important;
    color: white !important;
    border-radius: 6px !important;
}

div[data-testid="stExpander"] {
    border: 1px solid #E2E8F0 !important;
    border-radius: 8px !important;
    background: white !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
    margin-bottom: 8px !important;
}

h1 { font-size: 22px !important; font-weight: 600 !important; color: #1A202C !important; }

[data-testid="stMetricValue"] { font-family: 'IBM Plex Mono', monospace !important; }
</style>
""", unsafe_allow_html=True)

from streamlit_app.pages import (
    dashboard, org_setup, scenarios,
    simulate, report, memory, settings
)

pages = [
    st.Page(dashboard.render,  title="Dashboard",   icon="📡", default=True),
    st.Page(org_setup.render,  title="Org Setup",   icon="🏢"),
    st.Page(scenarios.render,  title="Senaryolar",  icon="⚡"),
    st.Page(simulate.render,   title="Simülasyon",  icon="⚙️"),
    st.Page(report.render,     title="Rapor",       icon="📊"),
    st.Page(memory.render,     title="Hafıza",      icon="🧠"),
    st.Page(settings.render,   title="Ayarlar",     icon="🔧"),
]

with st.sidebar:
    st.markdown("""
    <div style="padding:20px 16px 16px; border-bottom:1px solid #EDF2F7; margin-bottom:8px;">
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:4px;">
            <div style="width:30px;height:30px;background:#0F62FE;border-radius:8px;
                        display:flex;align-items:center;justify-content:center;font-size:15px;">🛡️</div>
            <span style="color:#1A202C;font-size:16px;font-weight:600;letter-spacing:0.03em;">SENTINEL</span>
        </div>
        <div style="color:#A0AEC0;font-size:10px;letter-spacing:0.1em;text-transform:uppercase;margin-left:40px;">
            Enterprise Resilience
        </div>
    </div>
    """, unsafe_allow_html=True)

pg = st.navigation(pages)

with st.sidebar:
    st.markdown("""
    <div style="padding:12px 16px; border-top:1px solid #EDF2F7; margin-top:8px;">
        <div style="display:flex;align-items:center;gap:6px;margin-bottom:4px;">
            <div style="width:7px;height:7px;background:#48BB78;border-radius:50%;"></div>
            <span style="color:#718096;font-size:11px;">Sistem Aktif</span>
        </div>
        <div style="color:#0F62FE;font-family:monospace;font-size:11px;">gpt-4o</div>
        <div style="color:#A0AEC0;font-size:10px;margin-top:2px;">Lokal · Harici veri çıkmaz</div>
    </div>
    """, unsafe_allow_html=True)

pg.run()