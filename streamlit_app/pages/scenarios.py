"""
streamlit_app/pages/scenarios.py
Senaryo → Simülasyon → Rapor tek sayfada wizard akışı.
"""

import streamlit as st
import json
import uuid
from pathlib import Path


def render():
    st.title("⚡ Senaryo & Simülasyon")

    # Adım göstergesi
    step = _current_step()
    _render_stepper(step)
    st.divider()

    if step == 1:
        _step1_scenario()
    elif step == 2:
        _step2_simulation()
    elif step == 3:
        _step3_report()


# ── Adım yönetimi ─────────────────────────────────────────────────────────────

def _current_step() -> int:
    if st.session_state.get("report_ready"):
        return 3
    if st.session_state.get("active_run_id"):
        return 3
    if st.session_state.get("active_scenario"):
        return 2
    return 1


def _render_stepper(step: int):
    col1, col2, col3 = st.columns(3)
    steps = [
        (1, "1. Senaryo"),
        (2, "2. Simülasyon"),
        (3, "3. Rapor"),
    ]
    cols = [col1, col2, col3]
    for i, (num, label) in enumerate(steps):
        with cols[i]:
            if num < step:
                st.markdown(f"✅ ~~{label}~~")
            elif num == step:
                st.markdown(f"**🔵 {label}**")
            else:
                st.markdown(f"⬜ {label}")


# ── ADIM 1: Senaryo ───────────────────────────────────────────────────────────

def _step1_scenario():
    tab1, tab2 = st.tabs(["Katalog", "Otomatik Üretim"])
    with tab1:
        _catalog()
    with tab2:
        _generator()


def _catalog():
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
                if st.button("▶️ Bu senaryoyla devam et",
                             key=f"cat_{scenario['id']}", type="primary"):
                    scenario["confidence"] = {}
                    st.session_state["active_scenario"] = scenario
                    st.session_state.pop("active_run_id", None)
                    st.session_state.pop("report_ready", None)
                    st.rerun()
    if not found:
        st.warning("Katalog dosyası bulunamadı.")


def _generator():
    st.info("Sinyalsiz de çalışır — LLM gereksinimi analiz eder.")

    # Haber seçici
    news_signals = _load_news_signals()
    if news_signals:
        with st.expander(f"📰 Güncel Haberlerden Seç ({len(news_signals)} haber)"):
            st.caption("Seçtiğin haberler gereksinim kutusuna eklenir.")
            selected_news = []
            label_colors = {"güncel": "🔵", "ekonomi-siyaset": "🟠", "iç siyaset": "🟣"}
            for i, news in enumerate(news_signals[:20]):
                title = news.get("title", "")
                icon = label_colors.get(news.get("label", ""), "⚪")
                if st.checkbox(f"{icon} {title}", key=f"ns_{i}"):
                    selected_news.append(news)
            if selected_news:
                if st.button("➕ Gereksinime Ekle", type="secondary"):
                    news_text = _build_news_context(selected_news)
                    existing = st.session_state.get("last_requirement", "")
                    st.session_state["last_requirement"] = (existing + "\n" + news_text).strip()
                    st.rerun()

    requirement = st.text_area(
        "Simülasyon gereksinimi",
        height=130,
        placeholder="Örnek: Türkiye'deki kur krizi IGYA'yı 90 günde nasıl etkiler?",
        value=st.session_state.get("last_requirement", ""),
    )

    with st.expander("📎 Ek Kaynak (opsiyonel)"):
        col_f, col_u = st.columns(2)
        with col_f:
            uploaded_file = st.file_uploader("Dosya", type=["pdf", "docx", "txt", "md", "xlsx"])
        with col_u:
            url_input = st.text_input("URL", placeholder="https://...")

    col1, col2 = st.columns(2)
    count = col1.slider("Senaryo sayısı", 1, 5, 3)
    time_horizon = col2.slider("Zaman ufku (gün)", 7, 180, 90)

    if st.button("🔄 Senaryo Üret", type="primary", disabled=not requirement.strip()):
        st.session_state["last_requirement"] = requirement

        extra_context = ""
        if uploaded_file:
            with st.spinner(f"📄 Okunuyor..."):
                extra_context += _extract_file(uploaded_file)
        if url_input and url_input.strip().startswith("http"):
            with st.spinner("🌐 URL çekiliyor..."):
                extra_context += _extract_url(url_input.strip())

        full_req = requirement
        if extra_context:
            full_req = f"{requirement}\n\n--- Ek Kaynak ---\n{extra_context[:6000]}"

        signals = _load_signals()
        graph = _build_graph()

        from scenarios.generator import ScenarioGenerator
        with st.spinner("Senaryo üretiliyor..."):
            try:
                gen = ScenarioGenerator()
                scenarios = gen.generate(signals=signals, graph=graph,
                                         count=count, requirement=full_req)
                for s in scenarios:
                    s["time_horizon_days"] = time_horizon
                    s.pop("confidence", None)
                st.session_state["generated_scenarios"] = scenarios
            except Exception as e:
                st.error(f"Hata: {e}")
                return

    # Üretilen senaryolar
    scenarios = st.session_state.get("generated_scenarios", [])
    if scenarios:
        st.divider()
        st.subheader(f"✅ {len(scenarios)} Senaryo")
        for i, s in enumerate(scenarios):
            with st.expander(f"📋 {s.get('name', f'Senaryo {i+1}')}", expanded=(i == 0)):
                st.write(s.get("description", ""))
                col1, col2 = st.columns(2)
                col1.caption(f"**Mod:** {s.get('simulation_mode', '?')}")
                col2.caption(f"**Ufuk:** {s.get('time_horizon_days', '?')} gün")
                roles = s.get("affected_roles", [])
                if roles:
                    st.caption(f"**Roller:** {', '.join(roles)}")
                if st.button("▶️ Bu senaryoyla devam et",
                             key=f"gen_{s.get('id', i)}", type="primary"):
                    st.session_state["active_scenario"] = s
                    st.session_state.pop("active_run_id", None)
                    st.session_state.pop("report_ready", None)
                    st.rerun()


# ── ADIM 2: Simülasyon ────────────────────────────────────────────────────────

def _step2_simulation():
    scenario = st.session_state["active_scenario"]

    with st.container(border=True):
        st.markdown(f"**Senaryo:** {scenario['name']}")
        st.caption(scenario.get("description", "")[:200])

    col1, col2, col3 = st.columns([2, 2, 1])
    mode = col1.selectbox("Mod", ["hierarchical", "consensus"],
                          index=0 if scenario.get("simulation_mode") == "hierarchical" else 1)
    horizon = col2.slider("Ufuk (gün)", 7, 180, scenario.get("time_horizon_days", 90))

    with col3:
        st.write("")
        st.write("")
        if st.button("← Geri", type="secondary"):
            st.session_state.pop("active_scenario", None)
            st.rerun()

    st.divider()

    if st.button("▶️ Simülasyonu Başlat", type="primary", use_container_width=True):
        scenario["simulation_mode"] = mode
        scenario["time_horizon_days"] = horizon

        from app.run_artifacts import RunStore
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
                st.session_state["active_run_id"] = run_id
                st.session_state["simulation_result"] = result
                st.rerun()
            except Exception as e:
                store.update_manifest(run_id, status="FAILED", error=str(e))
                st.error(f"Hata: {e}")


# ── ADIM 3: Rapor ─────────────────────────────────────────────────────────────

def _step3_report():
    from app.run_artifacts import RunStore

    run_id = st.session_state["active_run_id"]
    scenario = st.session_state.get("active_scenario", {})
    result = st.session_state.get("simulation_result", {})

    store = RunStore()
    run_dir = store.get_run_dir(run_id)
    report_path = run_dir / "report" / "report.md"
    verdict_path = run_dir / "report" / "verdict.json"

    # Geri butonu
    col_title, col_back = st.columns([5, 1])
    with col_back:
        if st.button("← Yeni Senaryo", type="secondary"):
            st.session_state.pop("active_scenario", None)
            st.session_state.pop("active_run_id", None)
            st.session_state.pop("simulation_result", None)
            st.session_state.pop("report_ready", None)
            st.session_state.pop("generated_scenarios", None)
            st.rerun()

    if not report_path.exists():
        st.info("Simülasyon tamamlandı. Raporu oluşturmak için butona basın.")
        if st.button("📝 Raporu Oluştur", type="primary", use_container_width=True):
            with st.spinner("Rapor oluşturuluyor..."):
                try:
                    from crew.action_engine import ActionRecommendationEngine
                    from report.report_agent import ReportAgent
                    from memory.tracker import OutcomeTracker

                    actions = ActionRecommendationEngine().recommend(
                        scenario, result.get("result", ""), "")
                    agent = ReportAgent(str(run_dir))
                    agent.generate(scenario, result, actions, {})
                    OutcomeTracker().record_prediction(run_id, {
                        "scenario": scenario.get("name"),
                        "risk_level": "high",
                    })
                    st.session_state["report_ready"] = True
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
    col1, col2 = st.columns(2)
    col1.download_button("📥 MD İndir", report_text,
                         f"sentinel_{run_id}.md", "text/markdown")

    if col2.button("📄 PDF Oluştur"):
        try:
            from report.pdf_exporter import export_pdf
            pdf_path = str(run_dir / "report" / "report.pdf")
            export_pdf(report_text, pdf_path)
            with open(pdf_path, "rb") as f:
                col2.download_button("📥 PDF İndir", f.read(),
                                     f"sentinel_{run_id}.pdf", "application/pdf")
        except Exception as e:
            st.error(f"PDF hatası: {e}")


# ── Yardımcılar ───────────────────────────────────────────────────────────────

def _load_signals() -> list:
    p = Path("uploads/runs/latest_signals.json")
    return json.loads(p.read_text()) if p.exists() else []


def _load_news_signals() -> list:
    signals = _load_signals()
    news = [s for s in signals if s.get("category") == "political"]
    news.sort(key=lambda x: x.get("published_at", x.get("collected_at", "")), reverse=True)
    return news


def _build_news_context(selected: list) -> str:
    lines = ["Aşağıdaki güncel haberler dikkate alınarak IGYA'ya etkisi analiz edilsin:\n"]
    for n in selected:
        pub = n.get("published_at", "")[:10]
        lines.append(f"• [{pub}] {n.get('title', '')}")
        if n.get("summary"):
            lines.append(f"  {n['summary']}")
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
        lines = [l for l in soup.get_text(separator="\n", strip=True).splitlines()
                 if len(l.strip()) > 30]
        return f"\n[URL: {url}]\n" + "\n".join(lines[:200]) + "\n"
    except Exception as e:
        return f"\n[URL okunamadı: {e}]\n"


def _build_graph() -> dict:
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
            "metadata": {"domain": "ERM", "key_themes": ["risk", "operations", "finance"]}}