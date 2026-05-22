"""
streamlit_app/pages/report.py
"""

import streamlit as st
import json
from pathlib import Path
from app.run_artifacts import RunStore


def render():
    st.title("📊 Rapor")

    run_id = st.session_state.get("active_run_id")
    if not run_id:
        st.warning("Önce simülasyon çalıştırın.")
        return

    store = RunStore()
    run_dir = store.get_run_dir(run_id)
    report_path = run_dir / "report" / "report.md"
    verdict_path = run_dir / "report" / "verdict.json"

    if not report_path.exists():
        scenario = st.session_state.get("active_scenario", {})
        result = st.session_state.get("simulation_result", {})

        if st.button("📝 Rapor Üret", type="primary"):
            from crew.action_engine import ActionRecommendationEngine
            from report.report_agent import ReportAgent
            from memory.tracker import OutcomeTracker

            with st.spinner("Rapor üretiliyor..."):
                actions = ActionRecommendationEngine().recommend(
                    scenario, result.get("result", ""), ""
                )
                agent = ReportAgent(str(run_dir))
                output = agent.generate(
                    scenario, result, actions,
                    scenario.get("confidence", {})
                )
                OutcomeTracker().record_prediction(run_id, {
                    "scenario": scenario.get("name"),
                    "risk_level": "high",
                })
            st.success("✅ Rapor hazır!")
            st.rerun()
        return

    # Verdict
    if verdict_path.exists():
        verdict = json.loads(verdict_path.read_text())
        col1, col2, col3 = st.columns(3)
        col1.metric("Güven Skoru", f"{verdict.get('confidence_score', 0):.0%}")
        col2.metric("Tahmin", verdict.get("predicted_outcome", "—")[:30])
        col3.metric("Kritik Sinyal", len(verdict.get("key_signals", [])))

    st.divider()
    st.markdown(report_path.read_text())

    st.divider()
    col1, col2 = st.columns(2)
    col1.download_button("📥 MD İndir", report_path.read_text(),
                         f"sentinel_rapor_{run_id}.md", "text/markdown")

    if col2.button("📄 PDF Oluştur"):
        from report.pdf_exporter import export_pdf
        pdf_path = str(run_dir / "report" / "report.pdf")
        export_pdf(report_path.read_text(), pdf_path)
        with open(pdf_path, "rb") as f:
            col2.download_button("📥 PDF İndir", f.read(),
                                 f"sentinel_rapor_{run_id}.pdf", "application/pdf")
