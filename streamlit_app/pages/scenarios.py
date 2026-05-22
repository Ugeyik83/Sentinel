"""
streamlit_app/pages/scenarios.py
Katalog + otomatik senaryo üretimi.
"""

import streamlit as st
import json
import uuid
from pathlib import Path


def render():
    st.title("⚡ Senaryolar")

    tab1, tab2 = st.tabs(["Katalog Senaryoları", "Otomatik Üretim"])

    with tab1:
        _render_catalog()

    with tab2:
        _render_generator()


def _render_catalog():
    import yaml
    found = False
    for yaml_file in Path("scenarios/catalog").glob("*.yaml"):
        data = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
        st.subheader(yaml_file.stem.replace("_", " ").title())
        found = True
        for scenario in data.get("scenarios", []):
            conf_badge = ""
            with st.expander(f"📋 {scenario['name']}"):
                st.write(scenario.get("description", ""))
                col1, col2, col3 = st.columns(3)
                col1.caption(f"**Mod:** {scenario.get('simulation_mode', '?')}")
                col2.caption(f"**Ufuk:** {scenario.get('time_horizon_days', '?')} gün")
                col3.caption(f"**Trigger:** `{scenario.get('trigger', '?')}`")

                if st.button("▶️ Bu senaryoyu çalıştır",
                             key=f"run_{scenario['id']}",
                             type="primary"):
                    scenario["confidence"] = {
                        "confidence": 0.85,
                        "signal_strength": "catalog"
                    }
                    st.session_state["active_scenario"] = scenario
                    st.success("✅ Senaryo seçildi. Sol menüden **Simülasyon** sekmesine geçin.")

    if not found:
        st.warning("Katalog dosyası bulunamadı.")


def _render_generator():
    st.info("Sinyalsiz de çalışır — LLM gereksinimi analiz eder ve senaryo üretir.")

    requirement = st.text_area(
        "Simülasyon gereksinimi",
        height=100,
        placeholder="Örnek: Türkiye'deki politik kaos IGYA'yı 90 günde nasıl etkiler?",
        value=st.session_state.get("last_requirement", ""),
    )

    col1, col2 = st.columns(2)
    count = col1.slider("Üretilecek senaryo sayısı", 1, 5, 3)
    time_horizon = col2.slider("Zaman ufuku (gün)", 7, 180, 90)

    if st.button("🔄 Senaryo Üret", type="primary", disabled=not requirement.strip()):
        st.session_state["last_requirement"] = requirement

        # Sinyal dosyası varsa yükle, yoksa boş liste
        signals_path = Path("uploads/runs/latest_signals.json")
        signals = []
        if signals_path.exists():
            try:
                signals = json.loads(signals_path.read_text())
                st.caption(f"📡 {len(signals)} sinyal kullanılıyor.")
            except Exception:
                pass
        else:
            st.caption("📡 Sinyal bulunamadı — LLM gereksinim bazlı üretecek.")

        # Boş graf — org chart node'larını ekle
        graph = _build_minimal_graph()

        from scenarios.generator import ScenarioGenerator
        with st.spinner("LLM senaryo üretiyor..."):
            try:
                generator = ScenarioGenerator()
                scenarios = generator.generate(
                    signals=signals,
                    graph=graph,
                    count=count,
                    requirement=requirement,
                )
                # Time horizon override
                for s in scenarios:
                    s["time_horizon_days"] = time_horizon

                # Session state'e kaydet
                st.session_state["generated_scenarios"] = scenarios

                # Diske kaydet
                _save_scenarios(scenarios, requirement)

            except Exception as e:
                st.error(f"Üretim hatası: {e}")
                return

    # Üretilen senaryoları göster
    scenarios = st.session_state.get("generated_scenarios", [])
    if scenarios:
        st.divider()
        st.subheader(f"✅ {len(scenarios)} Senaryo Üretildi")

        for i, scenario in enumerate(scenarios):
            conf = scenario.get("confidence", {})
            confidence = conf.get("confidence", 0)
            signal_strength = conf.get("signal_strength", "?")

            # Renk
            if confidence >= 0.7:
                icon = "🔴"
            elif confidence >= 0.4:
                icon = "🟡"
            else:
                icon = "🟢"

            with st.expander(
                f"{icon} **{scenario.get('name', f'Senaryo {i+1}')}** "
                f"— Güven: {confidence:.0%}",
                expanded=(i == 0)
            ):
                st.write(scenario.get("description", ""))

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Güven", f"{confidence:.0%}")
                col2.metric("Sinyal Gücü", signal_strength)
                col3.metric("Mod", scenario.get("simulation_mode", "?"))
                col4.metric("Ufuk", f"{scenario.get('time_horizon_days', '?')} gün")

                # Confidence breakdown
                if conf.get("breakdown"):
                    with st.expander("Güven Detayı"):
                        breakdown = conf["breakdown"]
                        for metric, value in breakdown.items():
                            st.progress(
                                float(value),
                                text=f"{metric.replace('_', ' ').title()}: {value:.2f}"
                            )

                # Etkilenen roller
                roles = scenario.get("affected_roles", [])
                if roles:
                    st.caption(f"**Etkilenen roller:** {', '.join(roles)}")

                # Senaryo seç
                if st.button(f"▶️ Bu senaryoyu simüle et",
                             key=f"gen_run_{scenario.get('id', i)}",
                             type="primary"):
                    st.session_state["active_scenario"] = scenario
                    st.success("✅ Senaryo seçildi. Sol menüden **Simülasyon** sekmesine geçin.")

        # JSON export
        st.divider()
        st.download_button(
            "📥 Senaryoları İndir (JSON)",
            data=json.dumps(scenarios, ensure_ascii=False, indent=2),
            file_name=f"sentinel_scenarios_{_today()}.json",
            mime="application/json",
        )


def _save_scenarios(scenarios: list, requirement: str):
    """Senaryoları diske kaydet."""
    run_id = str(uuid.uuid4())[:8]
    save_dir = Path("uploads/runs") / f"scenarios_{run_id}"
    save_dir.mkdir(parents=True, exist_ok=True)

    data = {
        "requirement": requirement,
        "generated_at": _now(),
        "count": len(scenarios),
        "scenarios": scenarios,
    }

    save_path = save_dir / "scenarios.json"
    save_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    # En son senaryoları da kaydet
    latest_path = Path("uploads/runs/latest_scenarios.json")
    latest_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def _build_minimal_graph() -> dict:
    """Org chart'tan minimal graf oluştur — confidence grounding için."""
    org_path = Path("config/org_chart.json")
    if not org_path.exists():
        return {"nodes": [], "edges": [], "metadata": {}}

    org = json.loads(org_path.read_text())
    nodes = []
    edges = []

    def traverse(node, parent_id=None):
        nodes.append({
            "id": node["id"],
            "label": node["role"],
            "type": "person",
            "importance": 5 - node.get("level", 2),
            "degree": 0,
        })
        if parent_id:
            edges.append({
                "source": parent_id,
                "target": node["id"],
                "relation": "DELEGATES_TO",
                "weight": 0.8,
            })
        for child in node.get("delegates_to", []):
            traverse(child, node["id"])

    traverse(org["hierarchy"])

    return {
        "nodes": nodes,
        "edges": edges,
        "metadata": {
            "domain": "ERM",
            "key_themes": ["risk", "operations", "finance", "HSE"],
        },
    }


def _today() -> str:
    from datetime import datetime
    return datetime.now().strftime("%Y%m%d")


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()