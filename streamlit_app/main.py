"""
streamlit_app/main.py — Ana giriş noktası.
"""

import streamlit as st
import sys
import os

# Proje root'unu path'e ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# --- HOTFIX: CrewAI cache_breakpoint -> Groq API rejects it -------------------
# CrewAI 1.14.x bazı provider'larda (Groq gibi) mesajlara cache_breakpoint ekliyor.
# Groq API: "'messages.0' ... property 'cache_breakpoint' is unsupported" hatası veriyor.
# Workaround: cache_breakpoint işaretleyicisini ekleyen fonksiyonu no-op yapıyoruz.
# Bu hata log'larda açıkça görülüyor. [1](https://inciholding-my.sharepoint.com/personal/ugeyik_incigsyuasa_com/Documents/Microsoft%20Copilot%20Chat%20Dosyalar%C4%B1/main.py)[2](https://huggingface.co/spaces/Shyamnath/inferencing-llm/blob/main/litellm/caching/Readme.md)
try:
    import crewai.llms.cache as _crewai_cache
    _crewai_cache.mark_cache_breakpoint = lambda msg: msg
except Exception:
    pass
# -----------------------------------------------------------------------------


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