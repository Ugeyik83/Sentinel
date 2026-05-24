"""
streamlit_app/pages/settings.py
"""

import streamlit as st
import os


PROVIDERS = {
    "openai":  {"name": "OpenAI",         "key_env": "OPENAI_API_KEY",  "model_env": "LLM_MODEL_NAME",  "default_model": "gpt-4o",                    "free": False},
    "groq":    {"name": "Groq (Ücretsiz)","key_env": "GROQ_API_KEY",    "model_env": "LLM_MODEL_NAME",  "default_model": "llama-3.1-70b-versatile",    "free": True},
    "gemini":  {"name": "Google Gemini",  "key_env": "GEMINI_API_KEY",  "model_env": "LLM_MODEL_NAME",  "default_model": "gemini-1.5-flash",           "free": True},
    "mistral": {"name": "Mistral AI",     "key_env": "MISTRAL_API_KEY", "model_env": "LLM_MODEL_NAME",  "default_model": "mistral-large-latest",       "free": True},
}

GROQ_MODELS    = ["llama-3.1-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768", "gemma2-9b-it"]
OPENAI_MODELS  = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]
GEMINI_MODELS  = ["gemini-1.5-flash", "gemini-1.5-pro"]
MISTRAL_MODELS = ["mistral-large-latest", "mistral-small-latest", "open-mistral-7b"]


def render():
    st.title("⚙️ Ayarlar")

    # ── LLM Provider ──────────────────────────────────────────────────────────
    st.subheader("🤖 LLM Provider")

    current_provider = os.environ.get("LLM_PROVIDER", _detect_active())

    provider_options = list(PROVIDERS.keys())
    provider_labels  = [
        f"{v['name']} {'✅ Ücretsiz' if v['free'] else '💳 Ücretli'}"
        for v in PROVIDERS.values()
    ]

    selected_idx = provider_options.index(current_provider) if current_provider in provider_options else 0
    selected_label = st.radio(
        "Provider seç",
        provider_labels,
        index=selected_idx,
        horizontal=True,
    )
    selected_provider = provider_options[provider_labels.index(selected_label)]
    cfg = PROVIDERS[selected_provider]

    st.divider()

    # ── API Key ───────────────────────────────────────────────────────────────
    st.subheader(f"🔑 {cfg['name']} API Key")

    current_key = os.environ.get(cfg["key_env"], "")
    masked = f"{'*' * (len(current_key) - 4)}{current_key[-4:]}" if len(current_key) > 4 else ""

    if current_key:
        st.success(f"✅ API key mevcut: `{masked}`")
    else:
        st.warning("⚠️ API key tanımlı değil.")

    with st.expander("API Key değiştir"):
        new_key = st.text_input("Yeni API Key", type="password", placeholder="sk-...")
        if st.button("💾 Kaydet", type="primary") and new_key:
            os.environ[cfg["key_env"]] = new_key
            os.environ["LLM_PROVIDER"] = selected_provider
            st.success("✅ Kaydedildi. Sayfa yenilenene kadar geçerli.")
            st.caption("⚠️ Kalıcı için Streamlit Cloud → Secrets → ekle.")

    st.divider()

    # ── Model Seçimi ──────────────────────────────────────────────────────────
    st.subheader("🧠 Model")

    model_list = {
        "openai":  OPENAI_MODELS,
        "groq":    GROQ_MODELS,
        "gemini":  GEMINI_MODELS,
        "mistral": MISTRAL_MODELS,
    }.get(selected_provider, [])

    current_model = os.environ.get("LLM_MODEL_NAME", cfg["default_model"])
    if current_model not in model_list:
        model_list = [current_model] + model_list

    selected_model = st.selectbox("Model", model_list,
                                  index=model_list.index(current_model))

    if st.button("Model Güncelle"):
        os.environ["LLM_MODEL_NAME"] = selected_model
        os.environ["LLM_PROVIDER"]   = selected_provider
        st.success(f"✅ Model: `{selected_model}` | Provider: `{selected_provider}`")

    st.divider()

    # ── Aktif Durum ───────────────────────────────────────────────────────────
    st.subheader("📊 Aktif Konfigürasyon")

    active = _detect_active()
    col1, col2, col3 = st.columns(3)
    col1.metric("Provider", PROVIDERS.get(active, {}).get("name", active))
    col2.metric("Model", os.environ.get("LLM_MODEL_NAME", "—"))
    col3.metric("Ücretsiz mi?", "✅ Evet" if PROVIDERS.get(active, {}).get("free") else "💳 Hayır")

    st.divider()

    # ── Hızlı Başlangıç ───────────────────────────────────────────────────────
    with st.expander("📖 Ücretsiz Provider Kurulum Rehberi"):
        st.markdown("""
**Groq (Önerilen — En Hızlı)**
1. https://console.groq.com → Ücretsiz hesap aç
2. API Keys → Create API Key
3. Yukarıdan Groq seç → Key gir → Kaydet
4. Streamlit Cloud → Settings → Secrets:
```
GROQ_API_KEY = "gsk_..."
LLM_PROVIDER = "groq"
```

**Google Gemini**
1. https://aistudio.google.com → Get API Key
2. Yukarıdan Gemini seç → Key gir
3. Secrets:
```
GEMINI_API_KEY = "AIza..."
LLM_PROVIDER = "gemini"
```

**Mistral AI**
1. https://console.mistral.ai → Free tier
2. API Keys → Create
3. Secrets:
```
MISTRAL_API_KEY = "..."
LLM_PROVIDER = "mistral"
```
        """)


def _detect_active() -> str:
    explicit = os.environ.get("LLM_PROVIDER", "").lower()
    if explicit in PROVIDERS:
        return explicit
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    if os.environ.get("GROQ_API_KEY"):
        return "groq"
    if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
        return "gemini"
    if os.environ.get("MISTRAL_API_KEY"):
        return "mistral"
    return "openai"