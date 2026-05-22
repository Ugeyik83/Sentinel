"""
streamlit_app/main.py — Ana giriş noktası.
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# 1. Sayfa Yapılandırması
st.set_page_config(
    page_title="SENTINEL | Enterprise Resilience",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. Özel CSS Enjeksiyonu (Üst boşlukları daraltma ve kurumsal his)
st.markdown("""
    <style>
    /* Ana ekranın üst ve alt boşluklarını azaltır */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    /* Sidebar arka planını hafif grileştirir */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }
    /* Radio butonlarındaki boşlukları düzenler */
    .stRadio > div {
        gap: 15px;
    }
    </style>
""", unsafe_allow_html=True)

from streamlit_app.pages import (
    dashboard, org_setup, scenarios,
    memory, settings
)

# 3. Sidebar: Üst Kısım (Kurumsal Başlık)
with st.sidebar:
    st.markdown(
        """
        <div style='text-align: center; padding-bottom: 10px;'>
            <h1 style='color: #1E3A8A; margin-bottom: 0; font-size: 28px;'>🛡️ SENTINEL</h1>
            <p style='color: #64748B; font-size: 10px; font-weight: 600; letter-spacing: 1px;'>ENTERPRISE RESILIENCE PLATFORM</p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    st.markdown("---")
    
    # 4. Yönlendirme Menüsü (Orijinal, sağlam yapı)
    st.markdown("<p style='color: #64748B; font-size: 11px; font-weight: bold;'>ANA MENÜ</p>", unsafe_allow_html=True)
    page = st.radio("", options=[
        "📡 Dashboard",
        "🏢 Org Setup",
        "⚡ Senaryolar",
        "🧠 Hafıza",
        "⚙️ Ayarlar",
    ], label_visibility="collapsed")
    
    st.markdown("---")
    
    # 5. Sidebar: Alt Kısım (Model ve Veri Bilgisi)
    model_name = os.environ.get('LLM_MODEL_NAME', 'gpt-4o')
    st.markdown(
        f"""
        <div style='font-size: 13px; color: #64748B;'>
            <div style='margin-bottom: 8px;'>⚙️ <b>Model:</b> <code style='color:#0f172a; background:#e2e8f0; padding:2px 4px; border-radius:4px;'>{model_name}</code></div>
            <div>🔒 <b>Veri Politikası:</b> Lokal çalışır, harici veri çıkışı kapalıdır.</div>
        </div>
        """, 
        unsafe_allow_html=True
    )

# 6. Seçilen Sayfayı Render Etme
PAGE_MAP = {
    "📡 Dashboard": dashboard.render,
    "🏢 Org Setup": org_setup.render,
    "⚡ Senaryolar": scenarios.render,
    "🧠 Hafıza": memory.render,
    "⚙️ Ayarlar": settings.render,
}

PAGE_MAP[page]()