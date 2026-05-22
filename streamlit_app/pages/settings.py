"""
streamlit_app/pages/settings.py
Zamanlama, bildirim, eşik ve ihracat pazarı konfigürasyonu.
"""

import streamlit as st
import yaml
import json
from pathlib import Path


def render():
    st.title("⚙️ Ayarlar")

    tab1, tab2, tab3, tab4 = st.tabs([
        "İhracat Pazarları", "Sinyal Eşikleri",
        "Bildirimler", "Manuel Tetikle"
    ])

    with tab1:
        _render_markets()

    with tab2:
        _render_thresholds()

    with tab3:
        _render_notifications()

    with tab4:
        _render_manual_trigger()


def _render_markets():
    st.subheader("İhracat Pazarları")
    path = Path("config/export_markets.yaml")
    config = yaml.safe_load(path.read_text()) if path.exists() else {"markets": []}

    st.dataframe(
        [{"Ülke": m["country"], "Kod": m["code"],
          "Para Birimi": m["currency"],
          "Sertifikalar": ", ".join(m.get("certifications", [])),
          "Öncelik": m.get("priority", "medium")}
         for m in config.get("markets", [])],
        use_container_width=True, hide_index=True
    )

    st.divider()
    st.subheader("Yeni Pazar Ekle")
    col1, col2, col3 = st.columns(3)
    country = col1.text_input("Ülke")
    code = col2.text_input("ISO Kodu (2 harf)")
    currency = col3.text_input("Para Birimi")
    certs = st.text_input("Sertifikalar (virgülle)", placeholder="SASO, CE")
    priority = st.selectbox("Öncelik", ["high", "medium", "low"])

    if st.button("➕ Ekle", disabled=not (country and code and currency)):
        config["markets"].append({
            "country": country,
            "code": code.upper(),
            "currency": currency.upper(),
            "certifications": [c.strip() for c in certs.split(",") if c.strip()],
            "priority": priority,
        })
        path.write_text(yaml.dump(config, allow_unicode=True, default_flow_style=False))
        st.success(f"✅ {country} eklendi.")
        st.rerun()


def _render_thresholds():
    st.subheader("Sinyal Eşik Değerleri")
    path = Path("config/thresholds.yaml")
    config = yaml.safe_load(path.read_text()) if path.exists() else {}

    changed = False
    new_config = {}
    for category, metrics in config.items():
        st.markdown(f"**{category.upper()}**")
        new_config[category] = {}
        for metric, value in metrics.items():
            new_val = st.number_input(
                f"{metric}", value=float(value), step=0.5,
                key=f"thresh_{category}_{metric}"
            )
            new_config[category][metric] = new_val
            if new_val != value:
                changed = True

    if changed and st.button("💾 Eşikleri Kaydet"):
        path.write_text(yaml.dump(new_config, allow_unicode=True, default_flow_style=False))
        st.success("✅ Eşikler güncellendi.")


def _render_notifications():
    st.subheader("Bildirim Kanalları")
    path = Path("config/notifications.yaml")
    config = yaml.safe_load(path.read_text()) if path.exists() else {}

    channels = config.get("channels", {})

    for channel, cfg in channels.items():
        with st.expander(f"{'✅' if cfg.get('enabled') else '⭕'} {channel.upper()}"):
            enabled = st.checkbox("Aktif", value=cfg.get("enabled", False), key=f"en_{channel}")
            channels[channel]["enabled"] = enabled
            if channel == "slack":
                url = st.text_input("Webhook URL", value=cfg.get("webhook_url", ""),
                                    type="password", key=f"wh_{channel}")
                channels[channel]["webhook_url"] = url
            elif channel == "email":
                recipients = st.text_input(
                    "Alıcılar (virgülle)",
                    value=", ".join(cfg.get("recipients", [])),
                    key=f"rc_{channel}"
                )
                channels[channel]["recipients"] = [r.strip() for r in recipients.split(",")]

    if st.button("💾 Bildirimleri Kaydet"):
        config["channels"] = channels
        path.write_text(yaml.dump(config, allow_unicode=True, default_flow_style=False))
        st.success("✅ Bildirim ayarları güncellendi.")


def _render_manual_trigger():
    st.subheader("Manuel Görev Tetikle")
    st.caption("Scheduler'ı beklemeden anında çalıştır.")

    col1, col2 = st.columns(2)

    if col1.button("📡 Sinyalleri Topla"):
        from scheduler.runner import _collect_signals
        with st.spinner("Sinyaller toplanıyor..."):
            _collect_signals()
        st.success("✅ Sinyaller toplandı.")

    if col2.button("⚠️ Eşik Kontrolü"):
        from scheduler.runner import _check_thresholds
        with st.spinner("Eşikler kontrol ediliyor..."):
            _check_thresholds()
        st.success("✅ Eşik kontrolü tamamlandı.")

    if col1.button("🔍 Zayıf Sinyal Tara"):
        from scheduler.runner import _weak_signal_check
        with st.spinner("Zayıf sinyaller taranıyor..."):
            _weak_signal_check()
        st.success("✅ Tarama tamamlandı.")

    if col2.button("📊 Haftalık Özet"):
        from scheduler.runner import _weekly_summary
        with st.spinner("Özet oluşturuluyor..."):
            _weekly_summary()
        st.success("✅ Haftalık özet oluşturuldu.")
