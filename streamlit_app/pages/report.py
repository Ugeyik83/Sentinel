"""
streamlit_app/pages/report.py
State sayfa geçişinde korunur — run_id session'da.
"""

import streamlit as st
import json
from pathlib import Path
from app.run_artifacts import RunStore


def _format_date(iso_str: str) -> str:
    from datetime import datetime, timedelta
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return (dt + timedelta(hours=3)).strftime("%d.%m.%Y %H:%M")
    except Exception:
        return iso_str[:16] if iso_str else "—"


def render():
    st.title("📊 Rapor")

    run_id = st.session_state.get("active_run_id")
    if not run_id:
        st.warning("Önce Simülasyon sekmesinden bir simülasyon çalıştırın.")
        return

    store = RunStore()
    run_dir = store.get_run_dir(run_id)
    report_path = run_dir / "report" / "report.md"
    verdict_path = run_dir / "report" / "verdict.json"

    st.caption(f"Run ID: `{run_id}`")

    if not report_path.exists():
        scenario = st.session_state.get("active_scenario", {})
        result = st.session_state.get("simulation_result", {})

        st.info("Simülasyon tamamlandı. Raporu oluşturmak için butona basın.")

        if st.button("📝 Raporu Oluştur", type="primary"):
            from crew.action_engine import ActionRecommendationEngine
            from report.report_agent import ReportAgent
            from memory.tracker import OutcomeTracker

            with st.spinner("Rapor oluşturuluyor..."):
                try:
                    actions = ActionRecommendationEngine().recommend(
                        scenario, result.get("result", ""), ""
                    )
                    agent = ReportAgent(str(run_dir))
                    agent.generate(scenario, result, actions, {})
                    OutcomeTracker().record_prediction(run_id, {
                        "scenario": scenario.get("name"),
                        "risk_level": "high",
                    })
                    st.rerun()
                except Exception as e:
                    st.error(f"Hata: {e}")
        return

    # Verdict özet
    if verdict_path.exists():
        try:
            verdict = json.loads(verdict_path.read_text())
            col1, col2 = st.columns(2)
            col1.metric("Tahmin", verdict.get("predicted_outcome", "—")[:50])
            col2.metric("Zaman Ufku", verdict.get("time_horizon", "—"))
        except Exception:
            pass

    st.divider()

    # Rapor içeriği
    report_text = report_path.read_text(encoding="utf-8")
    st.markdown(report_text)

    st.divider()

    # İndirme
    col1, col2, col3 = st.columns(3)
    col1.download_button(
        "📥 MD İndir",
        report_text,
        f"sentinel_rapor_{run_id}.md",
        "text/markdown"
    )

    if col2.button("📄 PDF Oluştur"):
        try:
            from report.pdf_exporter import export_pdf
            pdf_path = str(run_dir / "report" / "report.pdf")
            export_pdf(report_text, pdf_path)
            with open(pdf_path, "rb") as f:
                col2.download_button(
                    "📥 PDF İndir", f.read(),
                    f"sentinel_rapor_{run_id}.pdf",
                    "application/pdf"
                )
        except Exception as e:
            st.error(f"PDF hatası: {e}")

    if col3.button("🔄 Yeni Rapor", type="secondary"):
        if report_path.exists():
            report_path.unlink()
        st.rerun()