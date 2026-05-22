"""
streamlit_app/pages/scenarios.py
Katalog + otomatik senaryo üretimi.
"""

import streamlit as st
import json
from pathlib import Path


def render():
    st.title("⚡ Senaryolar")

    tab1, tab2 = st.tabs(["Katalog Senaryoları", "Otomatik Üretim"])

    with tab1:
        import yaml
        for yaml_file in Path("scenarios/catalog").glob("*.yaml"):
            data = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
            st.subheader(yaml_file.stem.replace("_", " ").title())
            for scenario in data.get("scenarios", []):
                with st.expander(f"📋 {scenario['name']}"):
                    st.write(scenario.get("description", ""))
                    col1, col2 = st.columns(2)
                    col1.caption(f"Mod: {scenario.get('simulation_mode', '?')}")
                    col2.caption(f"Ufuk: {scenario.get('time_horizon_days', '?')} gün")
                    if st.button("Bu senaryoyu çalıştır", key=f"run_{scenario['id']}"):
                        st.session_state["active_scenario"] = scenario
                        st.success("Simülasyon sekmesine geçin.")

    with tab2:
        st.info("Sinyal toplanıp eşik aşılınca otomatik senaryo üretilir. Manuel tetiklemek için:")
        requirement = st.text_area("Simülasyon gereksinimi", height=80,
                                   placeholder="Türkiye'deki politik kaos IGYA'yı 90 günde nasıl etkiler?")
        if st.button("🔄 Senaryo Üret", type="primary", disabled=not requirement.strip()):
            signals_path = Path("uploads/runs/latest_signals.json")
            signals = json.loads(signals_path.read_text()) if signals_path.exists() else []
            from scenarios.generator import ScenarioGenerator
            with st.spinner("LLM senaryo üretiyor..."):
                generator = ScenarioGenerator()
                scenarios = generator.generate(signals, {}, count=3)
            st.session_state["generated_scenarios"] = scenarios
            for s in scenarios:
                conf = s.get("confidence", {})
                with st.expander(f"📋 {s['name']} (güven: {conf.get('confidence', 0):.2f})"):
                    st.write(s.get("description", ""))
                    st.caption(f"Sinyal gücü: {conf.get('signal_strength', '?')}")
