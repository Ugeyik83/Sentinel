"""
streamlit_app/pages/dashboard.py
Sinyal akışı + risk skoru + zayıf sinyal radarı.
"""

import streamlit as st
import json
from pathlib import Path
from datetime import datetime, timezone
from signals.aggregator import SignalAggregator
from signals.weak_signal_detector import WeakSignalDetector


def _format_date(iso_str: str) -> str:
    """ISO tarih stringini Türkiye saatine (UTC+3) çevir."""
    try:
        from datetime import timedelta
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        dt_tr = dt + timedelta(hours=3)  # UTC → UTC+3 (Türkiye)
        return dt_tr.strftime("%d.%m.%Y %H:%M")
    except Exception:
        return iso_str[:16] if iso_str else "—"


def render():
    st.title("📡 Dashboard")
    st.caption("Canlı sinyal akışı ve risk görünümü")

    col1, col2, col3, col4 = st.columns(4)

    signals_path = Path("uploads/runs/latest_signals.json")
    if signals_path.exists():
        signals = json.loads(signals_path.read_text())
        high = [s for s in signals if s.get("composite_score", 0) > 0.7]
        medium = [s for s in signals if 0.4 < s.get("composite_score", 0) <= 0.7]

        col1.metric("Toplam Sinyal", len(signals))
        col2.metric("Yüksek Öncelik", len(high))
        col3.metric("Orta Öncelik", len(medium))
        col4.metric(
            "Son Güncelleme",
            _format_date(signals[0].get("scored_at", "")) if signals else "—"
        )

        st.divider()

        # Zayıf sinyal radarı
        st.subheader("🔍 Zayıf Sinyal Radarı")
        _render_weak_signals(signals)

        st.divider()

        # Sinyal tablosu
        st.subheader("📋 Sinyal Akışı")
        _render_signal_table(signals)
    else:
        st.info("Henüz sinyal toplanmadı. Ayarlar sayfasından manuel tetikleyebilirsiniz.")
        if st.button("🔄 Sinyalleri Şimdi Topla"):
            from scheduler.runner import _collect_signals
            with st.spinner("Sinyaller toplanıyor..."):
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
        color = "🔴" if score > 0.8 else "🟡"
        with st.container(border=True):
            st.markdown(f"{color} **{w.get('title', '?')}**")
            st.caption(f"Skor: {score:.2f} | {narrative}")


def _render_signal_table(signals: list):
    import pandas as pd
    rows = []
    for s in signals[:30]:
        rows.append({
            "Başlık": s.get("title", "")[:70],
            "Kaynak": s.get("source", ""),
            "Değer": s.get("value", 0),
            "Skor": f"{s.get('composite_score', 0):.3f}",
            "Güvenilirlik": f"{s.get('source_reliability', 0):.2f}",
            "Tarih": _format_date(s.get("collected_at", "")),
        })
    if rows:
        df = __import__("pandas").DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)