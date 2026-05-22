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


@st.cache_data(ttl=None, show_spinner=False)
def _load_signals():
    signals_path = Path("uploads/runs/latest_signals.json")
    if not signals_path.exists():
        return []
    return json.loads(signals_path.read_text())


def render():
    st.title("📡 Dashboard")
    st.caption("Canlı sinyal akışı ve risk görünümü")

    signals = _load_signals()

    if not signals:
        st.info("Henüz sinyal toplanmadı.")
        if st.button("🔄 Sinyalleri Topla", type="primary"):
            from scheduler.runner import _collect_signals
            with st.spinner("Toplanıyor..."):
                _collect_signals()
            _load_signals.clear()
            st.rerun()
        return

    fx_signals = [s for s in signals if s.get("type") == "fx"]
    idx_signals = [s for s in signals if s.get("type") == "index"]
    news_signals = [s for s in signals if s.get("category") == "political"]

    col1, col2, col3 = st.columns(3)
    col1.metric("Döviz", len(fx_signals))
    col2.metric("Haber", len(news_signals))
    col3.metric("Güncelleme",
                _format_date(signals[0].get("scored_at", "")) if signals else "—")

    st.divider()
    st.subheader("🔍 Zayıf Sinyal Radarı")
    _render_weak_signals(fx_signals + idx_signals)

    st.divider()
    if fx_signals or idx_signals:
        st.subheader("📈 Piyasalar")
        _render_market_cards(idx_signals + fx_signals)

    if news_signals:
        st.divider()
        st.subheader("📰 Haberler")
        _render_news(news_signals)

    # Manuel yenile butonu — alta sabit
    st.divider()
    if st.button("🔄 Sinyalleri Yenile", type="secondary"):
        from scheduler.runner import _collect_signals
        with st.spinner("Güncelleniyor..."):
            _collect_signals()
        _load_signals.clear()
        st.rerun()


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
        st.success("✅ Zayıf sinyal tespit edilmedi.")
        return
    for w in weak[:5]:
        score = w["weak_signal"]["weak_signal_score"]
        narrative = w["weak_signal"]["narrative"]
        icon = "🔴" if score > 0.8 else "🟡"
        with st.container(border=True):
            st.markdown(f"{icon} **{w.get('title', '?')}**")
            st.caption(narrative)


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
            st.metric(label=title, value=val_str, delta=delta_str)
            if prev_close:
                st.caption(f"Önceki kapanış: {prev_str}")
            st.caption(_format_date(s.get("collected_at", "")))


def _render_news(signals):
    label_colors = {"güncel": "🔵", "ekonomi-siyaset": "🟠", "iç siyaset": "🟣"}
    sorted_signals = sorted(
        signals,
        key=lambda x: x.get("published_at", x.get("collected_at", "")),
        reverse=True
    )
    for s in sorted_signals[:20]:
        title = s.get("title", "")
        url = s.get("url", "")
        label = s.get("label", "")
        date = _format_date(s.get("published_at", s.get("collected_at", "")))
        icon = label_colors.get(label, "⚪")
        col1, col2 = st.columns([5, 1])
        with col1:
            if url:
                st.markdown(f"{icon} [{title}]({url})")
            else:
                st.write(f"{icon} {title}")
        with col2:
            st.caption(date)