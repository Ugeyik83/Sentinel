import streamlit as st
import pandas as pd

def render():
    st.title("📡 Yönetim Paneli")
    st.markdown("Gerçek zamanlı risk öngörüleri ve tesis güvenlik durumu.")
    
    # Sistemin dolu/boş durumunu simüle etmek için Session State kullanımı
    if "demo_aktif" not in st.session_state:
        st.session_state.demo_aktif = False

    # ---------------------------------------------------------
    # DURUM 1: SİSTEMDE VERİ YOKSA (EMPTY STATE)
    # ---------------------------------------------------------
    if not st.session_state.demo_aktif:
        st.info("Sistemde henüz çalıştırılmış bir risk analizi veya aktif senaryo bulunmuyor.", icon="ℹ️")
        
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 🚀 Başlamak İçin Adımlar:
            1. Sol menüden **🏢 Org Setup** kısmına giderek tesis ve departmanları tanımlayın.
            2. **⚡ Senaryolar** sekmesinden kaza verilerini (örn: REBA skorları, psikososyal anket verileri) yükleyin.
            3. Sentinel AI analizini başlatın.
            """)
            
        with col2:
            st.markdown("""
            ### 💡 Test Etmek İster misiniz?
            Yapay zeka modelini bağlamadan önce, arayüzün kaza kök neden analizlerini 
            ve metrikleri nasıl görselleştireceğini görmek için demo verisini yükleyebilirsiniz.
            """)
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Örnek Panel Görünümünü Yükle", type="primary", use_container_width=True):
                st.session_state.demo_aktif = True
                st.rerun()

    # ---------------------------------------------------------
    # DURUM 2: SİSTEMDE VERİ VARSA (DASHBOARD GÖRÜNÜMÜ)
    # ---------------------------------------------------------
    else:
        # Üst Metrik Kartları
        col1, col2, col3, col4 = st.columns(4)
        col1.metric(label="İncelenen Kayıt", value="503", delta="Psikososyal Veri Seti", delta_color="off")
        col2.metric(label="Aktif Risk Faktörü", value="3", delta="2 Kritik Seviye", delta_color="inverse")
        col3.metric(label="Model Doğruluğu", value="%94.2", delta="XGBoost Aktif")
        col4.metric(label="Sistem Durumu", value="İzleniyor", delta="Sorun Yok", delta_color="normal")
        
        st.divider()

        # Alt Sekmeler
        tab1, tab2 = st.tabs(["📊 Risk Dağılımı", "⚠️ Aktif AI Uyarıları"])
        
        with tab1:
            col_chart, col_data = st.columns([2, 1])
            with col_chart:
                st.markdown("**Departman Bazlı Risk Skorları (0-100)**")
                # Basit ve ekstra kütüphane gerektirmeyen Streamlit grafiği
                chart_data = pd.DataFrame({
                    "Risk Skoru": [82, 45, 68, 25]
                }, index=["Hücre Üretim Hattı", "İhracat / Lojistik", "Depo Operasyonları", "Ofis"])
                st.bar_chart(chart_data, color="#ff4b4b")
                
            with col_data:
                st.markdown("**Son Değerlendirmeler**")
                # Pandas tablosunun arayüze entegresi
                df_son = pd.DataFrame({
                    "Tarih": ["22 May", "21 May", "19 May"],
                    "Konu": ["Ergonomi", "Senkronizasyon", "Gümrük"],
                    "Skor": [82, 45, 25]
                })
                st.dataframe(df_son, use_container_width=True, hide_index=True)

        with tab2:
            st.error("**Kritik Uyarı:** Lityum batarya (GTİP 8507.60.00.00.21) sevkiyat hazırlık alanında tespit edilen psikososyal stres ve yorgunluk belirtileri, operasyonel hata riskini %14 artırıyor.")
            st.warning("**Dikkat:** Üretim hattındaki 4. istasyonda REBA analiz skorlarında sapma gözlemlendi. Kök neden tespiti için eklem açısı verilerinin sisteme yüklenmesi bekleniyor.")
            st.info("**Bilgi:** DİİB kapsamındaki ürünlerin giriş işlemleri tamamlandı, üretim-sevkiyat senkronizasyonunda veri anormalliği tespit edilmedi.")
            
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Görünümü Sıfırla (Boş Ekrana Dön)"):
            st.session_state.demo_aktif = False
            st.rerun()