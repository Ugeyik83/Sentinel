"""
streamlit_app/pages/simulate.py
"""

import streamlit as st
import uuid
from pathlib import Path
from app.run_artifacts import RunStore


def render():
    st.title("⚙️ Simülasyon")

    scenario = st.session_state.get("active_scenario")
    if not scenario:
        st.warning("Senaryolar sekmesinden bir senaryo seçin.")
        return

    st.info(f"**Senaryo:** {scenario['name']}")

    col1, col2 = st.columns(2)
    mode = col1.selectbox("Simülasyon modu",
                          ["hierarchical", "consensus"],
                          index=0 if scenario.get("simulation_mode") == "hierarchical" else 1)
    horizon = col2.slider("Zaman ufku (gün)", 7, 180,
                          scenario.get("time_horizon_days", 90))

    scenario["simulation_mode"] = mode
    scenario["time_horizon_days"] = horizon

    if st.button("▶️ Simülasyonu Başlat", type="primary"):
        store = RunStore()
        run_id = str(uuid.uuid4())[:8]
        run_dir = store.create_run(run_id)
        store.update_manifest(run_id, status="RUNNING", scenario=scenario)

        with st.spinner("Simülasyon çalışıyor..."):
            try:
                from crew.runner import SimulationRunner
                runner = SimulationRunner(str(run_dir))
                result = runner.run(scenario)
                store.update_manifest(run_id, status="COMPLETED")
                st.session_state["active_run_id"] = run_id
                st.session_state["simulation_result"] = result
                st.success(f"✅ Tamamlandı. Run ID: `{run_id}`")
            except Exception as e:
                store.update_manifest(run_id, status="FAILED", error=str(e))
                st.error(f"Hata: {e}")
