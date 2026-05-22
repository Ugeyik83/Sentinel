"""
streamlit_app/pages/memory.py
Geçmiş olaylar, outcome girişi, kurumsal kültür analizi.
"""

import streamlit as st
import json
from pathlib import Path
from memory.tracker import OutcomeTracker
from memory.decision_parameters import DecisionParameterStore
from crew.conflict_tracker import ConflictTracker


def render():
    st.title("🧠 Hafıza")

    tab1, tab2, tab3 = st.tabs(["Geçmiş Çalıştırmalar", "Outcome Giriş", "Kültür Analizi"])

    with tab1:
        _render_history()

    with tab2:
        _render_outcome_entry()

    with tab3:
        _render_culture()


def _render_history():
    tracker = OutcomeTracker()
    runs = tracker.list_runs()

    if not runs:
        st.info("Henüz kayıtlı çalıştırma yok.")
        return

    st.caption(f"Toplam {len(runs)} çalıştırma")

    STATUS_ICON = {"READY": "🟡", "RUNNING": "⏳", "COMPLETED": "✅", "FAILED": "❌"}

    for run in sorted(runs, key=lambda r: r.get("predicted_at", ""), reverse=True):
        run_id = run.get("run_id", "?")
        prediction = run.get("prediction", {})
        actual = run.get("actual")
        accuracy = run.get("accuracy")

        with st.expander(
            f"{'✅' if actual else '🟡'} `{run_id}` — {prediction.get('scenario', '?')}"
        ):
            col1, col2, col3 = st.columns(3)
            col1.metric("Risk Seviyesi", prediction.get("risk_level", "—"))
            col2.metric("Gerçek Sonuç", actual.get("risk_level", "Girilmedi") if actual else "Girilmedi")
            col3.metric("Doğruluk", f"{accuracy:.0%}" if accuracy else "—")

            if run.get("predicted_at"):
                st.caption(f"Tahmin tarihi: {run['predicted_at'][:16]}")


def _render_outcome_entry():
    st.subheader("Gerçek Sonuç Gir")
    st.caption("Simülasyon tahminini gerçek sonuçla karşılaştır — sistem öğrenir.")

    tracker = OutcomeTracker()
    runs = [r for r in tracker.list_runs() if not r.get("actual")]

    if not runs:
        st.success("Tüm çalıştırmaların outcome'u girilmiş.")
        return

    run_options = {r["run_id"]: r.get("prediction", {}).get("scenario", r["run_id"])
                  for r in runs}
    selected = st.selectbox("Çalıştırma seç", options=list(run_options.keys()),
                            format_func=lambda x: run_options[x])

    col1, col2 = st.columns(2)
    actual_risk = col1.selectbox("Gerçek risk seviyesi",
                                 ["low", "medium", "high", "critical"])
    actual_desc = col2.text_input("Kısa açıklama", placeholder="Ne oldu?")

    if st.button("💾 Kaydet", type="primary"):
        accuracy = tracker.update_actual(selected, {
            "risk_level": actual_risk,
            "description": actual_desc,
        })

        # Karar parametresi olarak sakla
        store = DecisionParameterStore()
        run_data = tracker.list_runs()
        run = next((r for r in run_data if r["run_id"] == selected), {})
        store.store({
            "context": run.get("prediction", {}).get("scenario", ""),
            "decision": {"action": "simulation_based", "magnitude": 1.0},
            "outcome": {
                "success_score": accuracy,
                "actual_impact": actual_desc,
                "predicted_impact": run.get("prediction", {}).get("risk_level", ""),
                "accuracy": accuracy,
            },
            "applicable_when": {"signals": [], "entity_types": []},
        })

        st.success(f"✅ Kaydedildi. Doğruluk: {accuracy:.0%}")
        st.rerun()


def _render_culture():
    st.subheader("Kurumsal Kültür Analizi")

    # Tüm conflict loglarını birleştir
    all_conflicts = []
    for conflict_file in Path("uploads/runs").rglob("conflict_log.json"):
        try:
            conflicts = json.loads(conflict_file.read_text())
            all_conflicts.extend(conflicts)
        except Exception:
            pass

    if not all_conflicts:
        st.info("Henüz yeterli çatışma logu yok. Simülasyonlar çalıştıkça dolacak.")
        return

    analysis = ConflictTracker.analyze_culture(all_conflicts)

    col1, col2, col3 = st.columns(3)
    col1.metric("Toplam Çatışma", analysis.get("total_conflicts", 0))
    col2.metric("Ort. Karar Süresi", f"{analysis.get('avg_resolution_turns', 0)} tur")
    col3.metric("Analiz Edilen Run", len(list(Path("uploads/runs").rglob("conflict_log.json"))))

    st.divider()

    dominant = analysis.get("dominant_voices", [])
    if dominant:
        st.subheader("En Etkili Sesler")
        for voice in dominant:
            st.progress(voice["win_rate"],
                        text=f"{voice['role']} — %{voice['win_rate']*100:.0f} kazanma oranı")

    bias = analysis.get("bias_distribution", {})
    if bias:
        st.divider()
        st.subheader("Karar Bias Dağılımı")
        import pandas as pd
        df = pd.DataFrame(
            [(k, v) for k, v in bias.items()],
            columns=["Bias", "Oran"]
        )
        st.bar_chart(df.set_index("Bias"))
