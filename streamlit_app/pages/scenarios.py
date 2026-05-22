"""
streamlit_app/pages/scenarios.py
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
            with st.expander(f"📋 {scenario['name']}"):
                st.write(scenario.get("description", ""))
                col1, col2 = st.columns(2)
                col1.caption(f"**Mod:** {scenario.get('simulation_mode', '?')}")
                col2.caption(f"**Ufuk:** {scenario.get('time_horizon_days', '?')} gün")
                if st.button("▶️ Çalıştır", key=f"run_{scenario['id']}", type="primary"):
                    scenario["confidence"] = {}
                    st.session_state["active_scenario"] = scenario
                    st.success("✅ Simülasyon sekmesine geçin.")
    if not found:
        st.warning("Katalog dosyası bulunamadı.")


def _render_generator():
    st.info("Sinyalsiz de çalışır — LLM gereksinimi analiz eder ve senaryo üretir.")

    # Haber seçici
    news_signals = _load_news_signals()
    if news_signals:
        with st.expander(f"📰 Güncel Haberlerden Seç ({len(news_signals)} haber)", expanded=False):
            st.caption("Seçtiğin haberler gereksinim kutusuna eklenir.")
            selected_news = []
            label_colors = {"güncel": "🔵", "ekonomi-siyaset": "🟠", "iç siyaset": "🟣"}
            for i, news in enumerate(news_signals[:20]):
                title = news.get("title", "")
                label = news.get("label", "")
                icon = label_colors.get(label, "⚪")
                if st.checkbox(f"{icon} {title}", key=f"news_sel_{i}"):
                    selected_news.append(news)
            if selected_news:
                st.caption(f"✅ {len(selected_news)} haber seçildi")
                if st.button("➕ Gereksinime Ekle", type="secondary"):
                    news_text = _build_news_context(selected_news)
                    existing = st.session_state.get("last_requirement", "")
                    if existing and not existing.endswith("\n"):
                        existing += "\n"
                    st.session_state["last_requirement"] = existing + news_text
                    st.session_state["news_added"] = True
                    st.rerun()

    if st.session_state.pop("news_added", False):
        st.success("✅ Haberler eklendi.")

    requirement = st.text_area(
        "Simülasyon gereksinimi",
        height=150,
        placeholder="Örnek: Türkiye'deki kur krizi IGYA'yı 90 günde nasıl etkiler?",
        value=st.session_state.get("last_requirement", ""),
    )

    with st.expander("📎 Ek Kaynak (opsiyonel)", expanded=False):
        col_f, col_u = st.columns(2)
        with col_f:
            uploaded_file = st.file_uploader("Dosya", type=["pdf", "docx", "txt", "md", "xlsx"])
        with col_u:
            url_input = st.text_input("URL", placeholder="https://...")

    col1, col2 = st.columns(2)
    count = col1.slider("Senaryo sayısı", 1, 5, 3)
    time_horizon = col2.slider("Zaman ufuku (gün)", 7, 180, 90)

    if st.button("🔄 Senaryo Üret", type="primary", disabled=not requirement.strip()):
        st.session_state["last_requirement"] = requirement

        extra_context = ""
        if uploaded_file:
            with st.spinner(f"📄 `{uploaded_file.name}` okunuyor..."):
                extra_context += _extract_file(uploaded_file)
        if url_input and url_input.strip().startswith("http"):
            with st.spinner("🌐 URL çekiliyor..."):
                extra_context += _extract_url(url_input.strip())

        full_requirement = requirement
        if extra_context:
            full_requirement = f"{requirement}\n\n--- Ek Kaynak ---\n{extra_context[:6000]}"

        signals_path = Path("uploads/runs/latest_signals.json")
        signals = json.loads(signals_path.read_text()) if signals_path.exists() else []
        graph = _build_minimal_graph()

        from scenarios.generator import ScenarioGenerator
        with st.spinner("LLM senaryo üretiyor..."):
            try:
                generator = ScenarioGenerator()
                scenarios = generator.generate(
                    signals=signals, graph=graph,
                    count=count, requirement=full_requirement,
                )
                for s in scenarios:
                    s["time_horizon_days"] = time_horizon
                    s.pop("confidence", None)  # Güven skoru kaldır
                st.session_state["generated_scenarios"] = scenarios
                _save_scenarios(scenarios, requirement)
            except Exception as e:
                st.error(f"Üretim hatası: {e}")
                return

    # Üretilen senaryolar
    scenarios = st.session_state.get("generated_scenarios", [])
    if scenarios:
        st.divider()
        st.subheader(f"✅ {len(scenarios)} Senaryo Üretildi")
        for i, scenario in enumerate(scenarios):
            with st.expander(
                f"📋 {scenario.get('name', f'Senaryo {i+1}')}",
                expanded=(i == 0)
            ):
                st.write(scenario.get("description", ""))

                col1, col2 = st.columns(2)
                col1.caption(f"**Mod:** {scenario.get('simulation_mode', '?')}")
                col2.caption(f"**Ufuk:** {scenario.get('time_horizon_days', '?')} gün")

                roles = scenario.get("affected_roles", [])
                if roles:
                    st.caption(f"**Etkilenen roller:** {', '.join(roles)}")

                if st.button("▶️ Simüle et",
                             key=f"gen_run_{scenario.get('id', i)}", type="primary"):
                    st.session_state["active_scenario"] = scenario
                    st.success("✅ Simülasyon sekmesine geçin.")

        st.divider()
        st.download_button(
            "📥 İndir (JSON)",
            data=json.dumps(scenarios, ensure_ascii=False, indent=2),
            file_name=f"sentinel_scenarios_{_today()}.json",
            mime="application/json",
        )


def _load_news_signals() -> list:
    signals_path = Path("uploads/runs/latest_signals.json")
    if not signals_path.exists():
        return []
    try:
        all_signals = json.loads(signals_path.read_text())
        news = [s for s in all_signals if s.get("category") == "political"]
        news.sort(key=lambda x: x.get("published_at", x.get("collected_at", "")), reverse=True)
        return news
    except Exception:
        return []


def _build_news_context(selected_news: list) -> str:
    lines = ["Aşağıdaki güncel Türkiye haberleri dikkate alınarak IGYA'ya etkisi analiz edilsin:\n"]
    for news in selected_news:
        title = news.get("title", "")
        summary = news.get("summary", "")
        pub = news.get("published_at", "")[:10]
        lines.append(f"• [{pub}] {title}")
        if summary:
            lines.append(f"  {summary}")
    return "\n".join(lines)


def _extract_file(uploaded_file) -> str:
    try:
        import tempfile, os
        suffix = Path(uploaded_file.name).suffix.lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name
        from seed.file_parser import parse_file
        text = parse_file(tmp_path)
        os.unlink(tmp_path)
        return f"\n[Dosya: {uploaded_file.name}]\n{text}\n"
    except Exception as e:
        return f"\n[Dosya okunamadı: {e}]\n"


def _extract_url(url: str) -> str:
    try:
        import requests
        from bs4 import BeautifulSoup
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        lines = [l for l in soup.get_text(separator="\n", strip=True).splitlines() if len(l.strip()) > 30]
        return f"\n[URL: {url}]\n" + "\n".join(lines[:200]) + "\n"
    except Exception as e:
        return f"\n[URL okunamadı: {e}]\n"


def _save_scenarios(scenarios: list, requirement: str):
    run_id = str(uuid.uuid4())[:8]
    save_dir = Path("uploads/runs") / f"scenarios_{run_id}"
    save_dir.mkdir(parents=True, exist_ok=True)
    data = {"requirement": requirement, "generated_at": _now(),
            "count": len(scenarios), "scenarios": scenarios}
    (save_dir / "scenarios.json").write_text(json.dumps(data, ensure_ascii=False, indent=2))
    Path("uploads/runs/latest_scenarios.json").write_text(json.dumps(data, ensure_ascii=False, indent=2))


def _build_minimal_graph() -> dict:
    org_path = Path("config/org_chart.json")
    if not org_path.exists():
        return {"nodes": [], "edges": [], "metadata": {}}
    org = json.loads(org_path.read_text())
    nodes, edges = [], []
    def traverse(node, parent_id=None):
        nodes.append({"id": node["id"], "label": node["role"],
                      "type": "person", "importance": 5 - node.get("level", 2), "degree": 0})
        if parent_id:
            edges.append({"source": parent_id, "target": node["id"],
                          "relation": "DELEGATES_TO", "weight": 0.8})
        for child in node.get("delegates_to", []):
            traverse(child, node["id"])
    traverse(org["hierarchy"])
    return {"nodes": nodes, "edges": edges,
            "metadata": {"domain": "ERM", "key_themes": ["risk", "operations", "finance", "HSE"]}}


def _today() -> str:
    from datetime import datetime
    return datetime.now().strftime("%Y%m%d")


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()