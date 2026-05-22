"""
streamlit_app/main.py — SENTINEL UI v4
Açık sidebar — yazılar her zaman okunabilir.
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
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'IBM Plex Sans', sans-serif !important;
    background: #F0F2F5 !important;
}

#MainMenu, footer, header,
[data-testid="stToolbar"], .stDeployButton { display: none !important; }

/* ── Sidebar — açık tema ── */
[data-testid="stSidebar"] {
    background: #FFFFFF !important;
    border-right: 1px solid #E2E8F0 !important;
    min-width: 230px !important;
    max-width: 230px !important;
}

[data-testid="stSidebar"] > div { padding-top: 0 !important; }

/* Radio label gizle */
[data-testid="stSidebar"] .stRadio > label { display: none !important; }

/* Radio grup */
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] {
    gap: 2px !important;
    padding: 0 12px !important;
}

/* Her nav item */
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
    background: transparent !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 9px 14px !important;
    margin: 0 !important;
    color: #4A5568 !important;
    font-size: 13.5px !important;
    font-weight: 400 !important;
    cursor: pointer !important;
    transition: all 0.12s !important;
    width: 100% !important;
}

[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:hover {
    background: #EBF4FF !important;
    color: #0F62FE !important;
}

[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:has(input:checked) {
    background: #EBF4FF !important;
    color: #0F62FE !important;
    font-weight: 600 !important;
    border-left: 3px solid #0F62FE !important;
}

/* Radio dot gizle */
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label > div:first-child {
    display: none !important;
}

/* ── Ana içerik ── */
[data-testid="stMainBlockContainer"] {
    padding: 2.5rem 3rem !important;
}

/* ── Metrikler ── */
[data-testid="stMetric"] {
    background: white !important;
    border: 1px solid #E2E8F0 !important;
    border-top: 3px solid #0F62FE !important;
    padding: 16px 20px !important;
    border-radius: 8px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06) !important;
}

[data-testid="stMetricLabel"] p {
    font-size: 11px !important;
    font-weight: 600 !important;
    letter-spacing: 0.07em !important;
    text-transform: uppercase !important;
    color: #718096 !important;
}

[data-testid="stMetricValue"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 26px !important;
    color: #1A202C !important;
}

/* ── Butonlar ── */
.stButton > button {
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    border-radius: 6px !important;
    padding: 8px 20px !important;
}

.stButton > button[kind="primary"] {
    background: #0F62FE !important;
    border: none !important;
    color: white !important;
    box-shadow: 0 2px 8px rgba(15,98,254,0.25) !important;
}

.stButton > button[kind="primary"]:hover {
    background: #0353E9 !important;
}

/* ── Expander ── */
div[data-testid="stExpander"] {
    border: 1px solid #E2E8F0 !important;
    border-radius: 8px !important;
    background: white !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
    margin-bottom: 8px !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab"] {
    font-size: 13px !important;
    font-weight: 500 !important;
    color: #718096 !important;
}

.stTabs [aria-selected="true"] {
    color: #0F62FE !important;
    border-bottom: 2px solid #0F62FE !important;
}

/* ── Inputs ── */
.stTextArea textarea, .stTextInput input {
    border-radius: 6px !important;
    border: 1px solid #CBD5E0 !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 13px !important;
}

.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: #0F62FE !important;
    box-shadow: 0 0 0 3px rgba(15,98,254,0.12) !important;
}

/* ── Alert ── */
[data-testid="stAlert"] {
    border-radius: 6px !important;
    font-size: 13px !important;
}

/* ── H1 ── */
h1 {
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 22px !important;
    font-weight: 600 !important;
    color: #1A202C !important;
    letter-spacing: -0.01em !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-thumb { background: #CBD5E0; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="
        padding: 24px 20px 20px;
        border-bottom: 1px solid #EDF2F7;
        margin-bottom: 12px;
    ">
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:4px;">
            <div style="
                width:32px; height:32px;
                background:#0F62FE;
                border-radius:8px;
                display:flex; align-items:center;
                justify-content:center; font-size:16px;
            ">🛡️</div>
            <span style="
                color:#1A202C;
                font-family:'IBM Plex Sans',sans-serif;
                font-size:17px; font-weight:600;
                letter-spacing:0.03em;
            ">SENTINEL</span>
        </div>
        <div style="
            color:#A0AEC0; font-size:10px;
            letter-spacing:0.1em; text-transform:uppercase;
            margin-left:42px;
        ">Enterprise Resilience</div>
    </div>
    <div style="
        padding: 0 24px 8px;
        color: #A0AEC0; font-size:10px;
        letter-spacing:0.1em; text-transform:uppercase; font-weight:600;
    ">Menü</div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "Navigasyon",
        options=[
            "📡  Dashboard",
            "🏢  Org Setup",
            "⚡  Senaryolar",
            "⚙️  Simülasyon",
            "📊  Rapor",
            "🧠  Hafıza",
            "🔧  Ayarlar",
        ],
        label_visibility="collapsed"
    )

    st.markdown("""
    <div style="
        margin-top: 24px;
        padding: 16px 20px;
        border-top: 1px solid #EDF2F7;
    ">
        <div style="display:flex; align-items:center; gap:6px; margin-bottom:6px;">
            <div style="width:7px;height:7px;background:#48BB78;border-radius:50%;"></div>
            <span style="color:#718096; font-size:11px; font-weight:500;">Sistem Aktif</span>
        </div>
        <div style="color:#0F62FE; font-family:'IBM Plex Mono',monospace; font-size:11px; margin-bottom:2px;">gpt-4o</div>
        <div style="color:#A0AEC0; font-size:10px;">Lokal · Harici veri çıkmaz</div>
    </div>
    """, unsafe_allow_html=True)

# ── Sayfa yönlendirme ─────────────────────────────────────────────────────────
from streamlit_app.pages import (
    dashboard, org_setup, scenarios,
    simulate, report, memory, settings
)

PAGE_MAP = {
    "📡  Dashboard": dashboard.render,
    "🏢  Org Setup": org_setup.render,
    "⚡  Senaryolar": scenarios.render,
    "⚙️  Simülasyon": simulate.render,
    "📊  Rapor": report.render,
    "🧠  Hafıza": memory.render,
    "🔧  Ayarlar": settings.render,
}

PAGE_MAP[page]()