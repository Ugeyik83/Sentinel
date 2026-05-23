"""
streamlit_app/pages/simulate.py
Simülasyon sayfası — debate konuşma akışı + sonuç.
"""

import json
import time
from pathlib import Path
import streamlit as st


ROLE_COLORS = {
    "org_chart":    "#1f77b4",
    "devil_advocate": "#d62728",
    "red_team":     "#e07b00",
    "judge":        "#2ca02c",
    "crewai":       "#9467bd",
    "system":       "#7f7f7f",
}

ROLE_ICONS = {
    "org_chart":     "🏢",
    "devil_advocate": "😈",
    "red_team":      "🎯",
    "judge":         "⚖️",
    "crewai":        "🤖",
    "system":        "⚙️",
    "convergence_check": "📊",
}

ROUND_LABELS = {
    "opening":          "Tur 0 — Opening (Kör)",
    "rebuttal":         "Rebuttal",
    "judge":            "Judge — Final Karar",
    "crewai_summary":   "CrewAI Simülasyon",
    "convergence_check": "Konvergans Kontrolü",
    "system":           "Sistem",
    "summary":          "Özet",
}


def render():
    st.title("⚙️ Simülasyon")
    st.caption("MAD Debate + CrewAI hiyerarşik simülasyon")

    # Senaryo yükle
    scenario_path = Path("uploads/runs/latest_scenario.json")
    if not scenario_path.exists():
        st.warning("Önce Senaryolar sayfasından bir senaryo seçin.")
        return

    scenario = json.loads(scenario_path.read_text(encoding="utf-8"))

    # Senaryo bilgisi
    with st.expander("📋 Aktif Senaryo", expanded=True):
        col1, col2, col3 = st.columns(3)
        col1.metric("Senaryo", scenario.get("name", scenario.get("title", "—"))[:35])
        col2.metric("Etki", f"{scenario.get('impact_score', 0):.2f} ({scenario.get('impact_label', '')})")
        col3.metric("Belirsizlik", f"{scenario.get('uncertainty', 0):.2f} ({scenario.get('uncertainty_label', '')})")
        st.caption(scenario.get("description", "")[:200])

    st.divider()

    # Ayarlar
    col_a, col_b = st.columns([2, 1])
    with col_a:
        use_debate = st.toggle("MAD Debate Katmanı", value=True)
    with col_b:
        stream_mode = st.toggle("Canlı Akış", value=True,
                                help="Yanıtlar gelirken ekrana yaz")

    st.caption(
        "**Protokol otomatik:** Etki < 0.4 → fast | 0.4–0.7 → standard | > 0.7 → adversarial_deep"
    )

    # Başlat
    if st.button("▶ Simülasyonu Başlat", type="primary", use_container_width=True):
        _run_and_display(scenario, use_debate, stream_mode)
        return

    # Önceki sonuç
    st.divider()
    _show_saved_results()


# ── SİMÜLASYON ÇALIŞTIR ────────────────────────────────────────────────────

def _run_and_display(scenario: dict, use_debate: bool, stream_mode: bool):
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from crew.runner import run_full

    org_chart_path = Path("config/org_chart.json")
    if not org_chart_path.exists():
        st.error("config/org_chart.json bulunamadı.")
        return

    run_dir = "uploads/runs/latest"
    Path(run_dir).mkdir(parents=True, exist_ok=True)

    # Konuşma akışı container'ı
    st.subheader("🗣 Konuşma Akışı")
    conv_container = st.container()
    status = st.empty()

    if stream_mode:
        # Streaming — şimdilik simüle et, gerçek streaming Faz 2
        status.info("🔵 Simülasyon başlatılıyor...")
        with st.spinner("Debate ve simülasyon çalışıyor..."):
            result = run_full(
                scenario=scenario,
                run_dir=run_dir,
                use_debate=use_debate,
            )
        status.success("✅ Tamamlandı!")
    else:
        with st.spinner("Simülasyon çalışıyor..."):
            result = run_full(
                scenario=scenario,
                run_dir=run_dir,
                use_debate=use_debate,
            )
        status.success("✅ Tamamlandı!")

    # Kaydet
    Path("uploads/runs/latest_result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )

    # Konuşma akışını göster
    with conv_container:
        _render_conversation(result.get("conversation_log", []))

    # Özet metrikler
    _render_summary(result)


# ── KONUŞMA AKIŞI RENDER ────────────────────────────────────────────────────

def _render_conversation(conversation_log: list):
    if not conversation_log:
        st.info("Konuşma kaydı bulunamadı.")
        return

    current_round = -99
    current_round_type = ""

    for msg in sorted(conversation_log, key=lambda x: x.get("turn", 0)):
        round_num = msg.get("round", -1)
        round_type = msg.get("round_type", "")
        agent = msg.get("agent", "?")
        role_type = msg.get("role_type", "org_chart")
        message = msg.get("message", "")
        confidence = msg.get("confidence")

        # Yeni tur başlığı
        if round_num != current_round or round_type != current_round_type:
            current_round = round_num
            current_round_type = round_type
            label = ROUND_LABELS.get(round_type, round_type)
            if round_num >= 0:
                st.markdown(f"#### {label} {round_num if round_type != 'opening' else ''}")
            elif round_type not in ("system",):
                st.markdown(f"#### {label}")
            st.divider()

        # Sistem mesajları — küçük
        if role_type == "system":
            if round_type == "convergence_check":
                st.caption(f"📊 {message}")
            continue

        # Ajan mesajı
        icon = ROLE_ICONS.get(role_type, "👤")
        color = ROLE_COLORS.get(role_type, "#333")

        with st.container():
            col_icon, col_content = st.columns([1, 11])
            with col_icon:
                st.markdown(f"<div style='font-size:24px;margin-top:8px'>{icon}</div>",
                            unsafe_allow_html=True)
            with col_content:
                # Ajan adı + güven skoru
                header = f"**{agent}**"
                if confidence is not None:
                    header += f" &nbsp; <span style='color:{color};font-size:12px'>güven: {confidence:.2f}</span>"
                st.markdown(header, unsafe_allow_html=True)

                # Mesaj içeriği
                if role_type == "judge":
                    # Judge çıktısını parse et — bölümlere ayır
                    _render_judge_message(message)
                elif role_type == "red_team":
                    st.error(message)
                elif role_type == "devil_advocate":
                    st.warning(message)
                else:
                    st.info(message)

        st.write("")   # Boşluk


def _render_judge_message(message: str):
    """Judge çıktısını etiketlere göre parse et ve göster."""
    sections = {
        "[KARAR]": ("✅ Karar", "success"),
        "[GEREKÇE]": ("📋 Gerekçe", "info"),
        "[MUHALİF]": ("⚠️ Muhalefet", "warning"),
        "[ESCALASYON]": ("🚨 Escalasyon", None),
    }
    lines = message.split("\n")
    for line in lines:
        for tag, (label, style) in sections.items():
            if line.startswith(tag):
                content = line.replace(tag, "").strip()
                if style == "success":
                    st.success(f"**{label}:** {content}")
                elif style == "warning":
                    st.warning(f"**{label}:** {content}")
                elif style == "info":
                    st.info(f"**{label}:** {content}")
                else:
                    if "YK" in content:
                        st.error(f"**{label}:** {content}")
                    else:
                        st.caption(f"**{label}:** {content}")
                break


# ── ÖZET ────────────────────────────────────────────────────────────────────

def _render_summary(result: dict):
    st.divider()
    st.subheader("📌 Simülasyon Özeti")

    debate = result.get("debate_result") or {}

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Güven", f"{result.get('confidence', 0):.2f}")
    col2.metric("Protokol", debate.get("protocol", "—"))
    col3.metric("Tur Sayısı", debate.get("rounds_completed", "—"))
    escalation = result.get("escalation", "OTONOM")
    col4.metric(
        "Escalation", escalation,
        delta="YK gerekli" if escalation == "YK_GEREKLI" else None,
        delta_color="inverse",
    )

    if result.get("final_decision"):
        st.success(f"**Final Karar:** {result['final_decision']}")

    # Konvergans grafiği
    trajectory = debate.get("convergence_trajectory", [])
    if trajectory:
        import pandas as pd
        df = pd.DataFrame(trajectory).set_index("round")
        st.line_chart(df[["score"]], use_container_width=True)
        st.caption("Konvergans eğrisi — 1.0 = tam konsensüs")

    # Katılan ajanlar
    agents = debate.get("agents_participated", [])
    if agents:
        st.caption(f"**Katılımcılar:** {', '.join(agents)}")

    if debate.get("memory_context_used"):
        st.caption(f"🧠 {len(debate.get('similar_debates', []))} geçmiş debate referans alındı")

    # Audit trail
    if debate.get("trace_path"):
        st.caption(f"📁 Audit: `{debate['trace_path']}`")


# ── ÖNCEKİ SONUÇ ────────────────────────────────────────────────────────────

def _show_saved_results():
    result_path = Path("uploads/runs/latest_result.json")
    if not result_path.exists():
        st.info("Henüz simülasyon çalıştırılmadı.")
        return

    result = json.loads(result_path.read_text(encoding="utf-8"))

    st.subheader("📂 Son Simülasyon")
    with st.expander("Konuşma Akışını Göster", expanded=False):
        _render_conversation(result.get("conversation_log", []))
    _render_summary(result)
