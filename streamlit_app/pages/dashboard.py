import streamlit as st
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
from signals.weak_signal_detector import WeakSignalDetector

def _format_date(iso_str: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        dt_tr = dt + timedelta(hours=3)
        return dt_tr.strftime("%d.%m.%Y %H:%M")
    except Exception:
        return iso_str[:16] if iso_str else "—"

@st.cache_data(ttl=None, show_spinner=False)
def _load_signals():
    signals_path = Path("uploads/runs/latest_signals.json")
    if not signals_path.exists():
        return []
    return json.loads(signals_path.read_text())

def render():
    # 1. ÜST BAŞLIK VE YENİLEME BUTONU
    col_title, col_btn = st.columns([4, 1])
    with col_title:
        st.title("📡 Yönetim Paneli")
        st.markdown("Canlı sinyal akışı, risk öngörüleri ve piyasa radarı.")
    
    signals = _load_signals()

    # 2. BOŞ DURUM (EMPTY STATE) TASARIMI
    if not signals:
        st.info("Sistemde henüz analiz edilmiş bir sinyal bulunmuyor.", icon="ℹ️")
        st.markdown("<br>", unsafe_allow_html=True)
        col_empty_1, col_empty_2 = st.columns([1, 2])
        
        with col_empty_1:
            if st.button("📡 Sinyalleri Topla ve Analiz Et", type="primary", use_container_width=True):
                from scheduler.runner import _collect_signals
                with st.spinner("Dış kaynaklardan veriler çekiliyor ve analiz ediliyor..."):
                    _collect_signals()
                _load_signals.clear()
                st.rerun()
        return

    # Yenileme butonu (Dolu ekranda sağ üstte)
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True) # Hizalama için
        if st.button("🔄 Verileri Güncelle", type="primary", use_container_width=True):
            from scheduler.runner import _collect_signals
            with st.spinner("Güncel veriler taranıyor..."):
                _collect_signals()
            _load_signals.clear()
            st.rerun()

    fx_signals = [s for s in signals if s.get("type") == "fx"]
    idx_signals = [s for s in signals if s.get("type") == "index"]
    news_signals = [s for s in signals if s.get("category") == "political"]

    # 3. KPI KARTLARI (METRİKLER)
    col1, col2, col3 = st.columns(3)
    with col1:
        with st.container(border=True):
            st.metric("Döviz / Endeks Sinyali", len(fx_signals) + len(idx_signals))
    with col2:
        with st.container(border=True):
            st.metric("Siyasi / Ekonomik Haber", len(news_signals))
    with col3:
        with st.container(border=True):
            st.metric("Son Analiz Tarihi", _format_date(signals[0].get("scored_at", "")) if signals else "—")

    st.markdown("<br>", unsafe_allow_html=True)

    # 4. ZAYIF SİNYAL RADARI (YAPAY ZEKA ÇIKTILARI)
    st.subheader("🔍 Zayıf Sinyal Radarı", anchor=False)
    _render_weak_signals(fx_signals + idx_signals)

    st.divider()

    # 5. PİYASA VERİLERİ (KART GÖRÜNÜMÜ)
    if fx_signals or idx_signals:
        st.subheader("📈 Piyasalar", anchor=False)
        _render_market_cards(idx_signals + fx_signals)

    # 6. HABER AKIŞI
    if news_signals:
        st.divider()
        st.subheader("📰 Son Gelişmeler ve Haberler", anchor=False)
        _render_news(news_signals)


def _render_weak_signals(signals):
    detector = WeakSignalDetector()
    weak = []
    
    for s in signals:
        metric = s.get("metric", "")
        value = s.get("value", 0)
        if metric and value:
            result = detector.detect(metric, value)
            if result.get("is_weak_signal"):
                weak.append({**s, "weak_signal": result})
                
    if not weak:
        st.success("✅ Radarda kritik veya zayıf bir anomali tespit edilmedi.", icon="✅")
        return
        
    for w in weak[:5]:
        score = w["weak_signal"]["weak_signal_score"]
        narrative = w["weak_signal"]["narrative"]
        
        # Skorlara göre görsel uyarı seviyeleri
        if score > 0.8:
            st.error(f"**🔴 {w.get('title', '?')}** (Skor: {score})\n\n{narrative}")
        else:
            st.warning(f"**🟡 {w.get('title', '?')}** (Skor: {score})\n\n{narrative}")

def _render_market_cards(signals):
    cols = st.columns(min(len(signals), 4))
    for i, s in enumerate(signals):
        col = cols[i % len(cols)]
        title = s.get("title", "")
        value = s.get("value", 0)
        change_pct = s.get("change_pct", 0)
        prev_close = s.get("prev_close", 0)
        sig_type = s.get("type", "")

        val_str = f"{value:,.0f}" if sig_type == "index" else f"{value:.4f}"
        prev_str = f"{prev_close:,.0f}" if sig_type == "index" else f"{prev_close:.4f}"
        delta_str = f"{change_pct:+.2f}%" if change_pct else None

        with col:
            # Piyasaları kartlar içinde gösteriyoruz
            with st.container(border=True):
                st.metric(label=title, value=val_str, delta=delta_str)
                if prev_close:
                    st.caption(f"Önceki: {prev_str}")
                st.caption(f"Veri: {_format_date(s.get('collected_at', ''))}")

def _render_news(signals):
    label_colors = {"güncel": "🔵", "ekonomi-siyaset": "🟠", "iç siyaset": "🟣"}
    sorted_signals = sorted(
        signals,
        key=lambda x: x.get("published_at", x.get("collected_at", "")),
        reverse=True
    )
    
    # Haberleri daha şık bir yapıda alt alta sıralıyoruz
    for s in sorted_signals[:20]:
        title = s.get("title", "")
        url = s.get("url", "")
        label = s.get("label", "")
        date = _format_date(s.get("published_at", s.get("collected_at", "")))
        icon = label_colors.get(label, "⚪")
        
        with st.container():
            col1, col2 = st.columns([5, 1])
            with col1:
                if url:
                    st.markdown(f"{icon} **[{title}]({url})**")
                else:
                    st.markdown(f"{icon} **{title}**")
            with col2:
                st.caption(f"🕒 {date}")
            st.markdown("---") # Haberler arasına ince çizgi