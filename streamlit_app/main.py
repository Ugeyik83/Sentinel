"""
streamlit_app/main.py — SENTINEL UI v2 (FIXED DARK SIDEBAR)
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

/* Base */
html, body, [data-testid="stAppViewContainer"] {
    font-family: 'IBM Plex Sans', sans-serif !important;
    background-color: #F4F4F4 !important;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }
.stDeployButton { display: none; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: #161616 !important;
    width: 240px !important;
}

/* ✅ CRITICAL FIX: TEXT CONTRAST */
[data-testid="stSidebar"] * {
    color: #E0E0E0 !important;
}

/* Navigation items */
[data-testid="stSidebar"] .stRadio > div > label {
    display: flex !important;
    align-items: center !important;
    padding: 11px 20px !important;
    cursor: pointer !important;
    background: transparent !important;
    font-size: 13px !important;
    border-left: 3px solid transparent !important;
    color: #C6C6C6 !important;
}

/* Hover */
[data-testid="stSidebar"] .stRadio > div > label:hover {
    background: #262626 !important;
    color: #FFFFFF !important;
    border-left-color: #0F62FE !important;
}

/* Active item */
[data-testid="stSidebar"] .stRadio > div > label:has(input:checked) {
    background: #0F62FE !important;
    color: #FFFFFF !important;
    border-left-color: #0353E9 !important;
    font-weight: 500 !important;
}

/* Main content */
[data-testid="stMainBlockContainer"] {
    padding: 2rem 2.5rem !important;
    max-width: 1200px !important;
}

/* Metrics */
[data-testid="stMetric"] {
    background: white !important;
    border: 1px solid #E0E0E0 !important;
    border-left: 3px solid #0F62FE !important;
}

/* Buttons */
.stButton > button[kind="primary"] {
    background: #0F62FE !important;
    border: 1px solid #0F62FE !important;
    color: white !important;
}

/* Headings */
h1 {
    font-size: 24px !important;
    font-weight: 600 !important;
    border-bottom: 1px solid #E0E0E0 !important;
    padding-bottom: 12px !important;
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:

    st.markdown("""
    <div style="padding: 24px 20px; border-bottom: 1px solid #262626;">
        <div style="display:flex; align-items:center; gap:10px;">
            <div style="width:28px;height:28px;background:#0F62FE;display:flex;align-items:center;justify-content:center;">
                🛡️
            </div>
            <span style="color:#FFFFFF;font-size:16px;font-weight:600;">
                SENTINEL
            </span>
        </div>
        <div style="color:#8D8D8D;font-size:10px;margin-top:4px;">
            ENTERPRISE RESILIENCE
        </div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "",
        [
            "📡 Dashboard",
            "🏢 Org Setup",
            "⚡ Senaryolar",
            "⚙️ Simülasyon",
            "📊 Rapor",
            "🧠 Hafıza",
            "🔧 Ayarlar",
        ]
    )

# ── Dummy pages (örnek) ───────────────────────────────────────────────────────
if page == "📡 Dashboard":
    st.title("Dashboard")

elif page == "🏢 Org Setup":
    st.title("Org Setup")

elif page == "⚡ Senaryolar":
    st.title("Senaryolar")

elif page == "⚙️ Simülasyon":
    st.title("Simülasyon")

elif page == "📊 Rapor":
    st.title("Rapor")

elif page == "🧠 Hafıza":
    st.title("Hafıza")

elif page == "🔧 Ayarlar":
    st.title("Ayarlar")
