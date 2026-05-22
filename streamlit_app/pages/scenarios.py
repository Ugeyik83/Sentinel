"""
streamlit_app/pages/scenarios.py
Senaryo → Simülasyon → Rapor tek sayfada wizard akışı.
"""

import streamlit as st
import json
import uuid
from pathlib import Path


def render():
    # Sayfa Başlığı ve Açıklaması
    st.markdown("""
        <div style='margin-bottom: 20px;'>
            <h1 style='color: #1E3A8A; font-size: 32px; margin-bottom: 0;'>⚡ Senaryo & Simülasyon</h1>
            <p style='color: #64748B; font-size: 15px;'>Risk senaryoları oluşturun, Sentinel AI ile simüle edin ve etki raporlarını alın.</p>
        </div>
    """, unsafe_allow_html=True)

    # Adım göstergesi
    step = _current_step()
    _render_stepper(step)
    st.markdown("<br>", unsafe_allow_html=True)

    # İlgili adımı çalıştır
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
    # CSS ile modern bir stepper görünümü (Streamlit container'larını kullanarak)
    col1, col2, col3 = st.columns(3)
    
    def get_style(is_active, is_completed):
        if is_active:
            return "background-color: #EFF6FF; border: 2px solid #3B82F6; color: #1E3A8A; font-weight: bold;"
        elif is_completed:
            return "background-color: #F8FAFC; border: 1px solid #E2E8F0; color: #94A3B8; text-decoration: line-through;"
        else:
            return "background-color: #FFFFFF; border: 1px dashed #CBD5E1; color: #64748B;"

    with col1:
        st.markdown(f"""
        <div style='padding: 10px; border-radius: 8px; text-align: center; {get_style(step==1, step>1)}'>
            📝 1. Senaryo Tanımı
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style='padding: 10px; border-radius: 8px; text-align: center; {get_style(step==2, step>2)}'>
            ⚙️ 2. AI Simülasyonu
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div style='padding: 10px; border-radius: 8px; text-align: center; {get_style(step==3, False)}'>
            📊 3. Analiz & Rapor
        </div>
        """, unsafe_allow_html=True)


# ── ADIM 1: Senaryo ───────────────────────────────────────────────────────────

def _step1_scenario():
    # Sekmeleri modernleştir
    tab1, tab2 = st.tabs(["📚 Hazır Katalog", "🤖 AI Otomatik Üretim"])
    with tab1:
        _catalog()
    with tab2:
        _generator()


def _catalog():
    import yaml
    found = False
    
    st.markdown("##### Katalogdan Senaryo Seçin")
    st.caption("Önceden tanımlanmış risk şablonlarını kullanarak simülasyonu başlatabilirsiniz.")
    
    for yaml_file in Path("scenarios/catalog").glob("*.yaml"):
        try:
            data = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
            st.markdown(f"**{yaml_file.stem.replace('_', ' ').title()}**")
            found = True
            for scenario in data.get("scenarios", []):
                # Expander yerine Container kullanarak daha şık bir "Kart" görünümü
                with st.container(border=True):
                    col_title, col_btn = st.columns([4, 1])
                    with col_title:
                        st.markdown(f"**📋 {scenario['name']}**")
                        st.write(scenario.get("description", ""))
                        st.caption(f"⚙️ **Mod:** `{scenario.get('simulation_mode', '?')}`  |  ⏳ **Ufuk:** `{scenario.get('time_horizon_days', '?')} gün`")
                    with col_btn:
                        st.markdown("<br>", unsafe_allow_html=True) # Hizalama
                        if st.button("Seç & İlerle", key=f"cat_{scenario['id']}", type="primary", use_container_width=True):
                            scenario["confidence"] = {}
                            st.session_state["active_scenario"] = scenario
                            st.session_state.pop("active_run_id", None)
                            st.session_state.pop("report_ready", None)
                            st.rerun()
        except Exception:
            pass # Hatalı YAML dosyalarını yoksay

    if not found:
        st.warning("Katalog klasöründe (scenarios/catalog) okunabilir senaryo dosyası bulunamadı.")


def _generator():
    st.info("💡 **İpucu:** Sisteme topladığınız sinyalleri veya harici bir dosyayı vererek LLM'in sizin için özel bir risk senaryosu üretmesini sağlayabilirsiniz.")

    # Haber seçici
    news_signals = _load_news_signals()
    if news_signals:
        with st.expander(f"📰 Radardaki Haberleri Ekle ({len(news_signals)} haber)"):
            st.caption("Seçtiğiniz haberler prompt (gereksinim) kutusuna otomatik eklenir.")
            selected_news = []
            label_colors = {"güncel": "🔵", "ekonomi-siyaset": "🟠", "iç siyaset": "🟣"}
            for i, news in enumerate(news_signals[:20]):
                title = news.get("title", "")
                icon = label_colors.get(news.get("label", ""), "⚪")
                if st.checkbox(f"{icon} {title}", key=f"ns_{i}"):
                    selected_news.append(news)
            if selected_news:
                if st.button("➕ Seçilenleri Prompt'a Ekle", type="secondary"):
                    news_text = _build_news_context(selected_news)
                    existing = st.session_state.get("last_requirement", "")
                    st.session_state["last_requirement"] = (existing + "\n" + news_text).strip()
                    st.rerun()

    # Prompt Alanı (Ana girdi)
    requirement = st.text_area(
        "Senaryo Promptu (Gereksinim)",
        height=150,
        placeholder="Örnek: Lityum batarya (GTİP 8507) ihracatındaki A.TR belgesi süreçlerinde yaşanacak 1 haftalık bir gecikme, üretim ve lojistik senkronizasyonumuzu nasıl etkiler?",
        value=st.session_state.get("last_requirement", ""),
    )

    # Ek Kaynaklar ve Ayarlar
    col_upload, col_settings = st.columns([1, 1])
    
    with col_upload:
        with st.container(border=True):
            st.markdown("**📎 Harici Kaynak Bağla**")
            uploaded_file = st.file_uploader("Dosya (PDF, DOCX vb.)", type=["pdf", "docx", "txt", "md", "xlsx"], label_visibility="collapsed")
            url_input = st.text_input("URL Veri Kaynağı", placeholder="https://...")

    with col_settings:
        with st.container(border=True):
            st.markdown("**⚙️ Üretim Ayarları**")
            count = st.slider("Üretilecek Varyasyon Sayısı", 1, 5, 3)
            time_horizon = st.slider("Simülasyon Ufku (Gün)", 7, 180, 90)

    # Üret Butonu
    if st.button("✨ Yapay Zeka İle Senaryo Üret", type="primary", use_container_width=True, disabled=not requirement.strip()):
        st.session_state["last_requirement"] = requirement

        extra_context = ""
        if uploaded_file:
            with st.spinner(f"📄 Dosya analiz ediliyor..."):
                extra_context += _extract_file(uploaded_file)
        if url_input and url_input.strip().startswith("http"):
            with st.spinner("🌐 Web sayfası ayrıştırılıyor..."):
                extra_context += _extract_url(url_input.strip())

        full_req = requirement
        if extra_context:
            full_req = f"{requirement}\n\n--- Ek Kaynak ---\n{extra_context[:6000]}"

        signals = _load_signals()
        graph = _build_graph()

        from scenarios.generator import ScenarioGenerator
        with st.spinner("LLM senaryo varyasyonlarını kurguluyor..."):
            try:
                gen = ScenarioGenerator()
                scenarios = gen.generate(signals=signals, graph=graph,
                                         count=count, requirement=full_req)
                for s in scenarios:
                    s["time_horizon_days"] = time_horizon
                    s.pop("confidence", None)
                st.session_state["generated_scenarios"] = scenarios
            except Exception as e:
                st.error(f"Hata oluştu: {e}")
                return

    # Üretilen senaryoları göster
    scenarios = st.session_state.get("generated_scenarios", [])
    if scenarios:
        st.success(f"✅ Başarıyla {len(scenarios)} adet senaryo varyasyonu üretildi.")
        for i, s in enumerate(scenarios):
            with st.container(border=True):
                col_info, col_btn2 = st.columns([4, 1])
                with col_info:
                    st.markdown(f"**⚡ {s.get('name', f'Varyasyon {i+1}')}**")
                    st.write(s.get("description", ""))
                    roles = s.get("affected_roles", [])
                    if roles:
                        st.caption(f"👥 **Etkilenen Roller:** {', '.join(roles)}")
                with col_btn2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("Seç & İlerle", key=f"gen_{s.get('id', i)}", type="primary", use_container_width=True):
                        st.session_state["active_scenario"] = s
                        st.session_state.pop("active_run_id", None)
                        st.session_state.pop("report_ready", None)
                        st.rerun()


# ── ADIM 2: Simülasyon ────────────────────────────────────────────────────────

def _step2_simulation():
    scenario = st.session_state["active_scenario"]

    st.markdown("#### Simülasyon Parametreleri")
    
    with st.container(border=True):
        st.markdown(f"**Seçili Senaryo:** {scenario['name']}")
        st.info(scenario.get("description", "")[:300] + "...")

    col1, col2 = st.columns(2)
    with col1:
        mode = st.selectbox("Çalışma Modu", 
                          options=["hierarchical", "consensus"],
                          format_func=lambda x: "Hiyerarşik (Ajanlar Amirlerine Raporlar)" if x == "hierarchical" else "Uzlaşma (Konsensüs Arayışı)",
                          index=0 if scenario.get("simulation_mode") == "hierarchical" else 1)
    with col2:
        horizon = st.slider("Simülasyon Etki Ufku (Gün)", 7, 180, scenario.get("time_horizon_days", 90))

    st.markdown("<br>", unsafe_allow_html=True)

    col_back, col_run = st.columns([1, 4])
    with col_back:
        if st.button("← Senaryo Seçimine Dön", use_container_width=True):
            st.session_state.pop("active_scenario", None)
            st.rerun()
            
    with col_run:
        if st.button("🚀 Sentinel Simülasyonunu Başlat", type="primary", use_container_width=True):
            scenario["simulation_mode"] = mode
            scenario["time_horizon_days"] = horizon

            from app.run_artifacts import RunStore
            store = RunStore()
            run_id = str(uuid.uuid4())[:8]
            run_dir = store.create_run(run_id)
            store.update_manifest(run_id, status="RUNNING", scenario=scenario)

            # Daha şık bir spinner
            with st.status("Simülasyon Çalıştırılıyor...", expanded=True) as status:
                st.write("Ajanlar (Crew) uyandırılıyor...")
                try:
                    from crew.runner import SimulationRunner
                    runner = SimulationRunner(str(run_dir))
                    
                    st.write("Risk modeli işletiliyor...")
                    result = runner.run(scenario)
                    
                    store.update_manifest(run_id, status="COMPLETED")
                    st.session_state["active_run_id"] = run_id
                    st.session_state["simulation_result"] = result
                    status.update(label="Simülasyon Tamamlandı!", state="complete", expanded=False)
                    st.rerun()
                except Exception as e:
                    store.update_manifest(run_id, status="FAILED", error=str(e))
                    status.update(label=f"Simülasyon Başarısız: {e}", state="error")


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

    # Üst Kontroller
    col_title, col_back = st.columns([4, 1])
    with col_title:
        st.markdown("#### Analiz ve Aksiyon Raporu")
    with col_back:
        if st.button("➕ Yeni Senaryo", type="secondary", use_container_width=True):
            st.session_state.pop("active_scenario", None)
            st.session_state.pop("active_run_id", None)
            st.session_state.pop("simulation_result", None)
            st.session_state.pop("report_ready", None)
            st.session_state.pop("generated_scenarios", None)
            st.rerun()

    if not report_path.exists():
        st.warning("Veriler simüle edildi. Nihai raporu oluşturmak için aşağıdaki butona tıklayın.")
        if st.button("📝 Yönetici Raporunu (Executive Summary) Oluştur", type="primary", use_container_width=True):
            with st.spinner("AI Rapor Ajanı verileri derliyor..."):
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
                    st.error(f"Rapor üretim hatası: {e}")
        return

    # Rapor Hazırsa Gösterilecek Kısım
    st.success("Rapor başarıyla oluşturuldu.", icon="✅")

    # Verdict (Karar) Özeti Metrikleri
    if verdict_path.exists():
        try:
            verdict = json.loads(verdict_path.read_text())
            col_v1, col_v2, col_v3 = st.columns(3)
            with col_v1:
                with st.container(border=True):
                    st.metric("Olası Sonuç (Tahmin)", verdict.get("predicted_outcome", "—")[:40] + "...")
            with col_v2:
                with st.container(border=True):
                    st.metric("Risk Süresi", f"{verdict.get('time_horizon', '—')} Gün")
            with col_v3:
                with st.container(border=True):
                    st.metric("Run ID", f"#{run_id.upper()}")
        except Exception:
            pass

    # Rapor İçeriği Görüntüleme Alanı
    report_text = report_path.read_text(encoding="utf-8")
    
    with st.container(border=True):
        st.markdown(report_text)

    st.markdown("<br>", unsafe_allow_html=True)

    # İndirme Seçenekleri (Modern butonlar)
    col_d1, col_d2, col_empty = st.columns([1, 1, 2])
    with col_d1:
        st.download_button("📥 Markdown (MD) Olarak İndir", report_text, f"sentinel_rapor_{run_id}.md", "text/markdown", use_container_width=True)

    with col_d2:
        if st.button("📄 PDF Oluştur & İndir", use_container_width=True):
            try:
                from report.pdf_exporter import export_pdf
                pdf_path = str(run_dir / "report" / "report.pdf")
                export_pdf(report_text, pdf_path)
                with open(pdf_path, "rb") as f:
                    st.download_button("📥 PDF İndir", f.read(), f"sentinel_rapor_{run_id}.pdf", "application/pdf", key="dl_pdf")
            except Exception as e:
                st.error(f"PDF dönüştürme hatası: Sisteme 'Weasyprint' veya 'pdfkit' gibi bir paket kurulu olmayabilir. Detay: {e}")


# ── Yardımcılar (Değiştirilmedi) ───────────────────────────────────────────────────────────────

def _load_signals() -> list:
    p = Path("uploads/runs/latest_signals.json")
    return json.loads(p.read_text()) if p.exists() else []

def _load_news_signals() -> list:
    signals = _load_signals()
    news = [s for s in signals if s.get("category") == "political"]
    news.sort(key=lambda x: x.get("published_at", x.get("collected_at", "")), reverse=True)
    return news

def _build_news_context(selected: list) -> str:
    lines = ["Aşağıdaki güncel haberler dikkate alınarak etki analiz edilsin:\n"]
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