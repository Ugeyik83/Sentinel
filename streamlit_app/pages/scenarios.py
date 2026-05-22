"""
streamlit_app/pages/scenarios.py
Katalog + otomatik senaryo üretimi.
Seçili haberlerden gereksinim oluşturma eklendi.
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
                col1, col2, col3 = st.columns(3)
                col1.caption(f"**Mod:** {scenario.get('simulation_mode', '?')}")
                col2.caption(f"**Ufuk:** {scenario.get('time_horizon_days', '?')} gün")
                col3.caption(f"**Trigger:** `{scenario.get('trigger', '?')}`")
                if st.button("▶️ Bu senaryoyu çalıştır",
                             key=f"run_{scenario['id']}", type="primary"):
                    scenario["confidence"] = {"confidence": 0.85, "signal_strength": "catalog"}
                    st.session_state["active_scenario"] = scenario
                    st.success("✅ Senaryo seçildi. Sol menüden **Simülasyon** sekmesine geçin.")
    if not found:
        st.warning("Katalog dosyası bulunamadı.")


def _render_generator():
    st.info("Sinyalsiz de çalışır — LLM gereksinimi analiz eder ve senaryo üretir.")

    # ── Haber seçici ─────────────────────────────────────────────────────────
    news_signals = _load_news_signals()
    if news_signals:
        with st.expander(f"📰 Güncel Haberlerden Seç ({len(news_signals)} haber)", expanded=False):
            st.caption("Seçtiğin haberler otomatik olarak gereksinim kutusuna eklenir.")

            selected_news = []
            label_colors = {"güncel": "🔵", "ekonomi-siyaset": "🟠", "iç siyaset": "🟣"}

            for i, news in enumerate(news_signals[:20]):
                title = news.get("title", "")
                label = news.get("label", "")
                icon = label_colors.get(label, "⚪")
                checked = st.checkbox(
                    f"{icon} {title}",
                    key=f"news_sel_{i}",
                    value=False
                )
                if checked:
                    selected_news.append(news)

            if selected_news:
                st.caption(f"✅ {len(selected_news)} haber seçildi")
                if st.button("➕ Seçili Haberleri Gereksinime Ekle", type="secondary"):
                    news_text = _build_news_context(selected_news)
                    existing = st.session_state.get("last_requirement", "")
                    if existing and not existing.endswith("\n"):
                        existing += "\n"
                    st.session_state["last_requirement"] = existing + news_text
                    st.session_state["news_added"] = True
                    st.rerun()

        if st.session_state.get("news_added"):
            st.success("✅ Haberler gereksinim kutusuna eklendi.")
            st.session_state["news_added"] = False

    # ── Gereksinim kutusu ─────────────────────────────────────────────────────
    requirement = st.text_area(
        "Simülasyon gereksinimi",
        height=150,
        placeholder="Örnek: Türkiye'deki politik kaos IGYA'yı 90 günde nasıl etkiler?\n\nYa da üstten haber seçip buraya ekleyebilirsin.",
        value=st.session_state.get("last_requirement", ""),
        key="req_input"
    )

    # ── Ek kaynak ─────────────────────────────────────────────────────────────
    with st.expander("📎 Ek Kaynak Ekle (opsiyonel)", expanded=False):
        st.caption("Dosya veya URL eklerseniz içerik gereksinimle birlikte analiz edilir.")
        col_f, col_u = st.columns(2)
        with col_f:
            uploaded_file = st.file_uploader(
                "Dosya yükle",
                type=["pdf", "docx", "txt", "md", "csv", "xlsx"],
            )
        with col_u:
            url_input = st.text_input(
                "Web sitesi URL'si",
                placeholder="https://...",
            )

    col1, col2 = st.columns(2)
    count = col1.slider("Üretilecek senaryo sayısı", 1, 5, 3)
    time_horizon = col2.slider("Zaman ufuku (gün)", 7, 180, 90)

    if st.button("🔄 Senaryo Üret", type="primary", disabled=not requirement.strip()):
        st.session_state["last_requirement"] = requirement

        # Ek içerik
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
            st.caption(f"✅ Ek içerik: {len(extra_context):,} karakter")

        # Sinyaller
        signals_path = Path("uploads/runs/latest_signals.json")
        signals = []
        if signals_path.exists():
            try:
                signals = json.loads(signals_path.read_text())
            except Exception:
                pass

        graph = _build_minimal_graph()

        from scenarios.generator import ScenarioGenerator
        with st.spinner("LLM senaryo üretiyor..."):
            try:
                generator = ScenarioGenerator()
                scenarios = generator.generate(
                    signals=signals,
                    graph=graph,
                    count=count,
                    requirement=full_requirement,
                )
                for s in scenarios:
                    s["time_horizon_days"] = time_horizon
                st.session_state["generated_scenarios"] = scenarios
                _save_scenarios(scenarios, requirement)
            except Exception as e:
                st.error(f"Üretim hatası: {e}")
                return

    # ── Üretilen senaryolar ───────────────────────────────────────────────────
    scenarios = st.session_state.get("generated_scenarios", [])
    if scenarios:
        st.divider()
        st.subheader(f"✅ {len(scenarios)} Senaryo Üretildi")
        for i, scenario in enumerate(scenarios):
            conf = scenario.get("confidence", {})
            confidence = conf.get("confidence", 0)
            signal_strength = conf.get("signal_strength", "?")
            icon = "🔴" if confidence >= 0.7 else "🟡" if confidence >= 0.4 else "🟢"
            with st.expander(
                f"{icon} **{scenario.get('name', f'Senaryo {i+1}')}** — Güven: {confidence:.0%}",
                expanded=(i == 0)
            ):
                st.write(scenario.get("description", ""))
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Güven", f"{confidence:.0%}")
                col2.metric("Sinyal Gücü", signal_strength)
                col3.metric("Mod", scenario.get("simulation_mode", "?"))
                col4.metric("Ufuk", f"{scenario.get('time_horizon_days', '?')} gün")
                if conf.get("breakdown"):
                    with st.expander("Güven Detayı"):
                        for metric, value in conf["breakdown"].items():
                            st.progress(float(value),
                                       text=f"{metric.replace('_', ' ').title()}: {value:.2f}")
                roles = scenario.get("affected_roles", [])
                if roles:
                    st.caption(f"**Etkilenen roller:** {', '.join(roles)}")
                if st.button("▶️ Bu senaryoyu simüle et",
                             key=f"gen_run_{scenario.get('id', i)}", type="primary"):
                    st.session_state["active_scenario"] = scenario
                    st.success("✅ Senaryo seçildi. Sol menüden **Simülasyon** sekmesine geçin.")

        st.divider()
        st.download_button(
            "📥 Senaryoları İndir (JSON)",
            data=json.dumps(scenarios, ensure_ascii=False, indent=2),
            file_name=f"sentinel_scenarios_{_today()}.json",
            mime="application/json",
        )


def _load_news_signals() -> list:
    """latest_signals.json'dan haber sinyallerini çek."""
    signals_path = Path("uploads/runs/latest_signals.json")
    if not signals_path.exists():
        return []
    try:
        all_signals = json.loads(signals_path.read_text())
        news = [s for s in all_signals if s.get("category") == "political"]
        # Yayın tarihine göre sırala
        news.sort(
            key=lambda x: x.get("published_at", x.get("collected_at", "")),
            reverse=True
        )
        return news
    except Exception:
        return []


def _build_news_context(selected_news: list) -> str:
    """Seçili haberlerden gereksinim metni oluştur."""
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
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, timeout=10, headers=headers)
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        lines = [l for l in text.splitlines() if len(l.strip()) > 30]
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
    Path("uploads/runs/latest_scenarios.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2))


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