"""
streamlit_app/pages/dashboard.py
"""

import streamlit as st
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
from signals.weak_signal_detector import WeakSignalDetector

HISTORY_PATH = Path("uploads/runs/fx_history.json")


def _format_date(iso_str: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        dt_tr = dt + timedelta(hours=3)
        return dt_tr.strftime("%d.%m.%Y %H:%M")
    except Exception:
        return iso_str[:16] if iso_str else "—"


def _load_fx_history() -> dict:
    if HISTORY_PATH.exists():
        return json.loads(HISTORY_PATH.read_text())
    return {}


def _save_fx_history(signals: list):
    history = _load_fx_history()
    for s in signals:
        metric = s.get("metric", "")
        value = s.get("value", 0)
        if metric and value:
            prev = history.get(metric, {})
            history[metric] = {
                "prev_value": prev.get("curr_value", value),
                "prev_date": prev.get("curr_date", s.get("collected_at", "")),
                "curr_value": value,
                "curr_date": s.get("collected_at", ""),
            }
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_PATH.write_text(json.dumps(history, ensure_ascii=False, indent=2))


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
    fx_signals = [s for s in signals if s.get("category") == "economic"]
    news_signals = [s for s in signals if s.get("category") == "political"]

    # Geçmiş kaydet
    if fx_signals:
        _save_fx_history(fx_signals)

    # Özet
    col1, col2, col3 = st.columns(3)
    col1.metric("Döviz Sinyali", len(fx_signals))
    col2.metric("Haber", len(news_signals))
    col3.metric("Son Güncelleme",
                _format_date(signals[0].get("scored_at", "")) if signals else "—")

    st.divider()

    # Zayıf sinyal radarı
    st.subheader("🔍 Zayıf Sinyal Radarı")
    _render_weak_signals(fx_signals)

    st.divider()

    # Döviz tablosu
    if fx_signals:
        st.subheader("💱 Döviz Kurları")
        _render_fx_table(fx_signals)

    # Haberler
    if news_signals:
        st.divider()
        st.subheader("📰 Haberler")
        _render_news_table(news_signals)

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


def _render_fx_table(signals: list):
    history = _load_fx_history()
    rows = []

    for s in signals:
        metric = s.get("metric", "")
        value = s.get("value", 0)
        title = s.get("title", "").replace(" kuru", "")
        source = s.get("source", "").upper()
        date = _format_date(s.get("collected_at", ""))

        # Değişim hesapla
        hist = history.get(metric, {})
        prev = hist.get("prev_value", 0)
        delta = None
        delta_pct = None
        delta_str = "—"
        delta_pct_str = ""

        if prev and prev != value:
            delta = value - prev
            delta_pct = (delta / prev) * 100
            arrow = "▲" if delta > 0 else "▼"
            delta_str = f"{arrow} {abs(delta):.4f}"
            delta_pct_str = f"({delta_pct:+.2f}%)"

        rows.append({
            "Parite": title,
            "Değer": f"{value:.4f}" if value else "—",
            "Değişim": delta_str,
            "%": delta_pct_str,
            "Kaynak": source,
            "Tarih": date,
        })

    if not rows:
        return

    import pandas as pd
    df = pd.DataFrame(rows)

    # Renkli gösterim
    for row in rows:
        cols = st.columns([2, 2, 2, 1, 2, 3])
        cols[0].markdown(f"**{row['Parite']}**")
        cols[1].markdown(f"`{row['Değer']}`")

        degisim = row['Değişim']
        pct = row['%']
        if "▲" in degisim:
            cols[2].markdown(f"🟢 {degisim}")
            cols[3].caption(pct)
        elif "▼" in degisim:
            cols[2].markdown(f"🔴 {degisim}")
            cols[3].caption(pct)
        else:
            cols[2].markdown("—")
            cols[3].caption("")

        cols[4].caption(row['Kaynak'])
        cols[5].caption(row['Tarih'])


def _render_news_table(signals: list):
    for s in signals[:15]:
        title = s.get("title", "")
        url = s.get("url", "")
        date = _format_date(s.get("collected_at", ""))
        source = s.get("source", "").upper()

        col1, col2 = st.columns([5, 1])
        with col1:
            if url:
                st.markdown(f"[{title}]({url})")
            else:
                st.write(title)
        with col2:
            st.caption(f"{source} · {date}")