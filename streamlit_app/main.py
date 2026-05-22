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

# 2. Özel CSS Enjeksiyonu (Üst boşlukları daraltma ve font ayarları)
st.markdown("""
    <style>
    /* Ana ekranın üst ve alt boşluklarını azaltır, daha ferah yapar */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    /* Sidebar arka planını hafif grileştirir (Kurumsal his) */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
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
            <p style='color: #64748B; font-size: 12px; font-weight: 600; letter-spacing: 1px;'>ENTERPRISE RESILIENCE</p>
        </div>
        """, 
        unsafe_allow_html=True
    )

# 4. Sayfaları ve Kategorileri Tanımlama (Streamlit 1.36+ Native Navigation)
# Sayfaları kategorize ederek daha profesyonel bir menü elde ediyoruz.
pages = {
    "YÖNETİM PANELİ": [
        st.Page(dashboard.render, title="Dashboard", icon="📡"),
    ],
    "OPERASYON & ANALİZ": [
        st.Page(org_setup.render, title="Org Setup", icon="🏢"),
        st.Page(scenarios.render, title="Senaryolar", icon="⚡"),
    ],
    "SİSTEM ALTYAPISI": [
        st.Page(memory.render, title="Hafıza", icon="🧠"),
        st.Page(settings.render, title="Ayarlar", icon="⚙️"),
    ]
}

pg = st.navigation(pages)

# 5. Sidebar: Alt Kısım (Bilgi ve Güvenlik Uyarıları)
with st.sidebar:
    st.markdown('<div style="margin-top: 50px;"></div>', unsafe_allow_html=True) # Araya boşluk
    st.divider()
    model_name = os.environ.get('LLM_MODEL_NAME', 'gpt-4o')
    st.markdown(
        f"""
        <div style='font-size: 13px; color: #64748B;'>
            <div style='margin-bottom: 8px;'>⚙️ <b>Model:</b> <code style='color:#0f172a; background:#e2e8f0; padding:2px 4px; border-radius:4px;'>{model_name}</code></div>
            <div>🔒 <b>Veri Politikası:</b> Lokal çalışır, harici ağa veri çıkışı kapalıdır.</div>
        </div>
        """, 
        unsafe_allow_html=True
    )

# 6. Seçilen Sayfayı Çalıştır
pg.run()