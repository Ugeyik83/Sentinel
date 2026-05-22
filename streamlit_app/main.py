"""
streamlit_app/main.py — SENTINEL UI v2
Kurumsal, temiz, IBM Carbon Design System ilhamı.
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

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

/* ── Reset & Base ── */
* { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'IBM Plex Sans', sans-serif !important;
    background-color: #F4F4F4 !important;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }
.stDeployButton { display: none; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #161616 !important;
    border-right: none !important;
    width: 240px !important;
}

[data-testid="stSidebar"] > div:first-child {
    padding: 0 !important;
}

/* ── Main content ── */
[data-testid="stMainBlockContainer"] {
    padding: 2rem 2.5rem !important;
    max-width: 1200px !important;
}

/* ── Radio buttons (nav) ── */
[data-testid="stSidebar"] .stRadio > label {
    display: none !important;
}

[data-testid="stSidebar"] .stRadio > div {
    gap: 0 !important;
    flex-direction: column !important;
}

[data-testid="stSidebar"] .stRadio > div > label {
    display: flex !important;
    align-items: center !important;
    padding: 11px 20px !important;
    margin: 0 !important;
    cursor: pointer !important;
    border-radius: 0 !important;
    border: none !important;
    background: transparent !important;
    color: #A8A8A8 !important;
    font-size: 13px !important;
    font-weight: 400 !important;
    letter-spacing: 0.01em !important;
    transition: all 0.15s ease !important;
    border-left: 3px solid transparent !important;
}

[data-testid="stSidebar"] .stRadio > div > label:hover {
    background: #262626 !important;
    color: #F4F4F4 !important;
    border-left-color: #0F62FE !important;
}

[data-testid="stSidebar"] .stRadio > div > label[data-baseweb="radio"]:has(input:checked),
[data-testid="stSidebar"] .stRadio > div > label:has(input[type="radio"]:checked) {
    background: #0F62FE !important;
    color: #FFFFFF !important;
    border-left-color: #0353E9 !important;
    font-weight: 500 !important;
}

[data-testid="stSidebar"] .stRadio > div > label > div:first-child {
    display: none !important;
}

/* ── Cards / Containers ── */
[data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] {
    background: white;
    border-radius: 2px;
}

div[data-testid="stExpander"] {
    border: 1px solid #E0E0E0 !important;
    border-radius: 2px !important;
    background: white !important;
    box-shadow: none !important;
}

div[data-testid="stExpander"]:hover {
    border-color: #0F62FE !important;
}

/* ── Metrics ── */
[data-testid="stMetric"] {
    background: white !important;
    border: 1px solid #E0E0E0 !important;
    border-left: 3px solid #0F62FE !important;
    padding: 16px 20px !important;
    border-radius: 2px !important;
}

[data-testid="stMetricLabel"] {
    font-size: 11px !important;
    font-weight: 500 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    color: #6F6F6F !important;
}

[data-testid="stMetricValue"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 28px !important;
    font-weight: 400 !important;
    color: #161616 !important;
}

/* ── Buttons ── */
.stButton > button {
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    letter-spacing: 0.01em !important;
    border-radius: 2px !important;
    padding: 10px 20px !important;
    transition: all 0.15s !important;
}

.stButton > button[kind="primary"] {
    background: #0F62FE !important;
    border: 1px solid #0F62FE !important;
    color: white !important;
}

.stButton > button[kind="primary"]:hover {
    background: #0353E9 !important;
    border-color: #0353E9 !important;
}

.stButton > button[kind="secondary"] {
    background: white !important;
    border: 1px solid #8D8D8D !important;
    color: #161616 !important;
}

.stButton > button[kind="secondary"]:hover {
    background: #E8E8E8 !important;
}

/* ── Inputs ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    border-radius: 2px !important;
    border: 1px solid #8D8D8D !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 13px !important;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #0F62FE !important;
    box-shadow: 0 0 0 2px rgba(15,98,254,0.15) !important;
}

/* ── Alerts / Info boxes ── */
[data-testid="stAlert"] {
    border-radius: 2px !important;
    border-left-width: 3px !important;
    font-size: 13px !important;
}

/* ── Divider ── */
hr {
    border-color: #E0E0E0 !important;
    margin: 1.5rem 0 !important;
}

/* ── Tables ── */
[data-testid="stDataFrame"] {
    border: 1px solid #E0E0E0 !important;
    border-radius: 2px !important;
}

/* ── Progress bars ── */
.stProgress > div > div {
    border-radius: 0 !important;
    height: 6px !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    border-bottom: 2px solid #E0E0E0 !important;
    gap: 0 !important;
}

.stTabs [data-baseweb="tab"] {
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 10px 20px !important;
    border-radius: 0 !important;
    color: #6F6F6F !important;
}

.stTabs [aria-selected="true"] {
    border-bottom: 2px solid #0F62FE !important;
    color: #161616 !important;
    background: transparent !important;
}

/* ── Slider ── */
.stSlider [data-baseweb="slider"] div[role="slider"] {
    background: #0F62FE !important;
    border: 2px solid #0F62FE !important;
}

/* ── Headings ── */
h1 {
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 24px !important;
    font-weight: 600 !important;
    color: #161616 !important;
    letter-spacing: -0.01em !important;
    border-bottom: 1px solid #E0E0E0 !important;
    padding-bottom: 12px !important;
    margin-bottom: 20px !important;
}

h2 {
    font-size: 18px !important;
    font-weight: 600 !important;
    color: #161616 !important;
}

h3 {
    font-size: 14px !important;
    font-weight: 600 !important;
    color: #393939 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}

/* ── Caption / small text ── */
[data-testid="stCaptionContainer"] {
    font-size: 11px !important;
    color: #6F6F6F !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #F4F4F4; }
::-webkit-scrollbar-thumb { background: #C6C6C6; border-radius: 0; }
::-webkit-scrollbar-thumb:hover { background: #8D8D8D; }

</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    # Logo alanı
    st.markdown("""
    <div style="
        padding: 24px 20px 20px;
        border-bottom: 1px solid #262626;
        margin-bottom: 8px;
    ">
        <div style="
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 4px;
        ">
            <div style="
                width: 28px; height: 28px;
                background: #0F62FE;
                display: flex; align-items: center; justify-content: center;
                font-size: 14px;
            ">🛡️</div>
            <span style="
                color: #F4F4F4;
                font-family: 'IBM Plex Sans', sans-serif;
                font-size: 16px;
                font-weight: 600;
                letter-spacing: 0.05em;
            ">SENTINEL</span>
        </div>
        <div style="
            color: #6F6F6F;
            font-size: 10px;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            padding-left: 38px;
        ">Enterprise Resilience</div>
    </div>
    """, unsafe_allow_html=True)

    # Grup başlığı
    st.markdown("""
    <div style="
        padding: 16px 20px 6px;
        color: #525252;
        font-size: 10px;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        font-family: 'IBM Plex Sans', sans-serif;
    ">Ana Menü</div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "Navigasyon",
        options=[
            "  📡  Dashboard",
            "  🏢  Org Setup",
            "  ⚡  Senaryolar",
            "  ⚙️  Simülasyon",
            "  📊  Rapor",
            "  🧠  Hafıza",
            "  🔧  Ayarlar",
        ],
        label_visibility="collapsed"
    )

    # Alt bilgi
    st.markdown("""
    <div style="
        position: absolute;
        bottom: 0; left: 0; right: 0;
        padding: 16px 20px;
        border-top: 1px solid #262626;
    ">
        <div style="color: #525252; font-size: 10px; letter-spacing: 0.05em; margin-bottom: 4px;">
            MODEL
        </div>
        <div style="
            color: #0F62FE;
            font-family: 'IBM Plex Mono', monospace;
            font-size: 11px;
        ">gpt-4o</div>
        <div style="color: #525252; font-size: 10px; margin-top: 6px;">
            Veri lokal · Harici çıkmaz
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── Sayfa yönlendirme ─────────────────────────────────────────────────────────
from streamlit_app.pages import (
    dashboard, org_setup, scenarios,
    simulate, report, memory, settings
)

PAGE_MAP = {
    "  📡  Dashboard": dashboard.render,
    "  🏢  Org Setup": org_setup.render,
    "  ⚡  Senaryolar": scenarios.render,
    "  ⚙️  Simülasyon": simulate.render,
    "  📊  Rapor": report.render,
    "  🧠  Hafıza": memory.render,
    "  🔧  Ayarlar": settings.render,
}

PAGE_MAP[page]()