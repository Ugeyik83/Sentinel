"""
streamlit_app/pages/dashboard.py
"""

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


def render():
    st.title("📡 Dashboard")
    st.caption("Canlı sinyal akışı ve risk görünümü")

    signals_path = Path("uploads/runs/latest_signals.json")

    if not signals_path.exists():
        st.info("Henüz sinyal toplanmadı.")
        if st.button("🔄 Sinyalleri Şimdi Topla"):
            from scheduler.runner import _collect_signals
            with st.spinner("Sinyaller toplanıyor..."):
                _collect_signals()
            st.rerun()
        return

    signals = json.loads(signals_path.read_text())
    fx_signals = [s for s in signals if s.get("type") == "fx"]
    idx_signals = [s for s in signals if s.get("type") == "index"]
    news_signals = [s for s in signals if s.get("category") == "political"]

    # Özet metrikler
    col1, col2, col3 = st.columns(3)
    col1.metric("Döviz", len(fx_signals))
    col2.metric("Haber", len(news_signals))
    col3.metric("Güncelleme",
                _format_date(signals[0].get("scored_at", "")) if signals else "—")

    st.divider()

    # Zayıf sinyal radarı
    st.subheader("🔍 Zayıf Sinyal Radarı")
    _render_weak_signals(fx_signals + idx_signals)

    st.divider()

    # Borsa + Döviz kartları
    all_market = idx_signals + fx_signals
    if all_market:
        st.subheader("📈 Piyasalar")
        _render_market_cards(all_market)

    # Haberler
    if news_signals:
        st.divider()
        st.subheader("📰 Haberler")
        _render_news(news_signals)

    st.divider()
    if st.button("🔄 Sinyalleri Güncelle"):
        from scheduler.runner import _collect_signals
        with st.spinner("Güncelleniyor..."):
            _collect_signals()
        st.rerun()


def _render_weak_signals(signals: list):
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
        st.success("✅ Zayıf sinyal tespit edilmedi.")
        return

    for w in weak[:5]:
        score = w["weak_signal"]["weak_signal_score"]
        narrative = w["weak_signal"]["narrative"]
        icon = "🔴" if score > 0.8 else "🟡"
        with st.container(border=True):
            st.markdown(f"{icon} **{w.get('title', '?')}**")
            st.caption(narrative)


def _render_market_cards(signals: list):
    cols = st.columns(len(signals)) if len(signals) <= 4 else st.columns(4)

    for i, s in enumerate(signals):
        col = cols[i % len(cols)]
        title = s.get("title", "")
        value = s.get("value", 0)
        change = s.get("change", 0)
        change_pct = s.get("change_pct", 0)
        prev_close = s.get("prev_close", 0)
        sig_type = s.get("type", "")

        # Değer formatı
        if sig_type == "index":
            val_str = f"{value:,.0f}"
            prev_str = f"{prev_close:,.0f}"
        else:
            val_str = f"{value:.4f}"
            prev_str = f"{prev_close:.4f}"

        # Delta string
        if change_pct > 0:
            delta_str = f"+{change_pct:.2f}%"
        elif change_pct < 0:
            delta_str = f"{change_pct:.2f}%"
        else:
            delta_str = None

        with col:
            st.metric(
                label=title,
                value=val_str,
                delta=delta_str,
            )
            if prev_close:
                st.caption(f"Önceki kapanış: {prev_str}")
            st.caption(_format_date(s.get("collected_at", "")))


def _render_news(signals: list):
    label_colors = {
        "güncel": "🔵",
        "ekonomi-siyaset": "🟠",
        "iç siyaset": "🟣",
    }
    # Yayın tarihine göre sırala
    sorted_signals = sorted(
        signals,
        key=lambda x: x.get("published_at", x.get("collected_at", "")),
        reverse=True
    )
    for s in sorted_signals[:20]:
        title = s.get("title", "")
        url = s.get("url", "")
        label = s.get("label", "")
        pub = s.get("published_at", s.get("collected_at", ""))
        date = _format_date(pub)
        icon = label_colors.get(label, "⚪")

        col1, col2 = st.columns([5, 1])
        with col1:
            prefix = f"{icon} " if label else ""
            if url:
                st.markdown(f"{prefix}[{title}]({url})")
            else:
                st.write(f"{prefix}{title}")
        with col2:
            st.caption(date)

# _render_news fonksiyonunu güncelle — published_at sıralaması + etiket