"""
streamlit_app/pages/simulate.py
State sayfa geçişinde korunur.
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
    mode = col1.selectbox(
        "Simülasyon modu",
        ["hierarchical", "consensus"],
        index=0 if scenario.get("simulation_mode") == "hierarchical" else 1,
        key="sim_mode"
    )
    horizon = col2.slider(
        "Zaman ufuku (gün)", 7, 180,
        scenario.get("time_horizon_days", 90),
        key="sim_horizon"
    )

    # Tamamlanan simülasyon varsa göster
    if st.session_state.get("active_run_id"):
        run_id = st.session_state["active_run_id"]
        st.success(f"✅ Son simülasyon tamamlandı. Run ID: `{run_id}`")
        st.caption("Rapor sekmesinden sonuçları görüntüleyebilirsiniz.")
        st.divider()

    col_run, col_clear = st.columns([3, 1])

    if col_run.button("▶️ Simülasyonu Başlat", type="primary"):
        scenario["simulation_mode"] = mode
        scenario["time_horizon_days"] = horizon

        store = RunStore()
        run_id = str(uuid.uuid4())[:8]
        run_dir = store.create_run(run_id)
        store.update_manifest(run_id, status="RUNNING", scenario=scenario)

        with st.spinner("Simülasyon çalışıyor... (1-2 dakika)"):
            try:
                from crew.runner import SimulationRunner
                runner = SimulationRunner(str(run_dir))
                result = runner.run(scenario)
                store.update_manifest(run_id, status="COMPLETED")
                # Session'a kaydet — sayfa geçişinde kaybolmaz
                st.session_state["active_run_id"] = run_id
                st.session_state["simulation_result"] = result
                st.rerun()
            except Exception as e:
                store.update_manifest(run_id, status="FAILED", error=str(e))
                st.error(f"Hata: {e}")

    if col_clear.button("🗑️ Senaryo Değiştir", type="secondary"):
        st.session_state.pop("active_scenario", None)
        st.session_state.pop("active_run_id", None)
        st.session_state.pop("simulation_result", None)
        st.rerun()