"""
app/utils/llm_client.py
Multi-provider LLM wrapper.

Provider seçimi (öncelik sırası):
1. LLM_PROVIDER env değişkeni: "openai" | "groq" | "gemini" | "mistral"
2. Yoksa: mevcut API key'e göre otomatik seç
3. Hiçbiri yoksa: fallback
"""

import os
import json
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)


# ── Provider tespiti ──────────────────────────────────────────────────────────

def _detect_provider() -> str:
    """Hangi provider kullanılacak — env'den veya mevcut key'den."""
    explicit = os.environ.get("LLM_PROVIDER", "").lower()
    if explicit in ("openai", "groq", "gemini", "mistral"):
        return explicit

    # Otomatik tespit — hangi key varsa onu kullan
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    if os.environ.get("GROQ_API_KEY"):
        return "groq"
    if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
        return "gemini"
    if os.environ.get("MISTRAL_API_KEY"):
        return "mistral"

    return "openai"  # fallback


def get_provider() -> str:
    return _detect_provider()


# ── Default model per provider ────────────────────────────────────────────────

DEFAULT_MODELS = {
    "openai":  "gpt-4o",
    "groq":    "llama-3.3-70b-versatile",
    "gemini":  "gemini-1.5-flash",
    "mistral": "mistral-large-latest",
}


def _default_model(provider: str) -> str:
    env_model = os.environ.get("LLM_MODEL_NAME", "")
    return env_model or DEFAULT_MODELS.get(provider, "gpt-4o")


# ── Client factory (SDK) ──────────────────────────────────────────────────────

_clients: dict = {}


def _get_client(provider: str):
    global _clients
    if provider in _clients:
        return _clients[provider]

    if provider == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))

    elif provider == "groq":
        from groq import Groq
        client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))

    elif provider == "gemini":
        import google.generativeai as genai
        genai.configure(
            api_key=os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")
        )
        client = genai  # Gemini farklı API — özel handler

    elif provider == "mistral":
        from mistralai import Mistral
        client = Mistral(api_key=os.environ.get("MISTRAL_API_KEY", ""))

    else:
        raise ValueError(f"Bilinmeyen provider: {provider}")

    _clients[provider] = client
    return client


# ── CrewAI için LLM (CrewAI 1.14.5 uyumlu) ────────────────────────────────────
# NOT: CrewAI 1.14.5'te Agent(llm=...) artık LangChain Chat* nesnelerini
# (ChatGroq/ChatOpenAI vb.) kabul etmeyebilir. Bu nedenle CrewAI'ye string model
# kimliği dönüyoruz. CrewAI bu string'i provider/model formatıyla yönlendirebilir. [1](https://deepwiki.com/crewAIInc/crewAI/4-llm-integration)[2](https://pypi.org/project/crewai/)

def get_llm():
    """CrewAI ajanları için LLM tanımı (string model id döndürür)."""
    provider = get_provider()
    model = _default_model(provider)

    # LiteLLM/provider routing için yaygın format: "<provider>/<model>"
    # openai için prefix zorunlu değil; istersen "openai/gpt-4o" da verebilirsin.
    if provider in ("groq", "gemini", "mistral"):
        return f"{provider}/{model}"

    return model


# ── chat() — tüm senkron LLM çağrıları (SDK) ──────────────────────────────────

def chat(messages: list, model: str = None, temperature: float = 0.7,
         max_tokens: int = 4096, max_retries: int = 3) -> str:

    provider = get_provider()
    model = model or _default_model(provider)

    for attempt in range(1, max_retries + 1):
        try:
            if provider == "gemini":
                return _chat_gemini(messages, model, temperature, max_tokens)

            client = _get_client(provider)

            if provider in ("openai", "groq"):
                resp = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return resp.choices[0].message.content

            elif provider == "mistral":
                resp = client.chat.complete(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return resp.choices[0].message.content

        except Exception as e:
            logger.warning(f"LLM hata [{provider}] (deneme {attempt}/{max_retries}): {e}")
            if attempt == max_retries:
                raise
            time.sleep(2 ** attempt)


def _chat_gemini(messages: list, model: str,
                 temperature: float, max_tokens: int) -> str:
    """Gemini API farklı format kullanır."""
    import google.generativeai as genai

    gmodel = genai.GenerativeModel(
        model_name=model,
        generation_config={
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
    )
    # OpenAI formatını Gemini formatına çevir
    prompt = "\n\n".join([
        f"[{m['role'].upper()}]\n{m['content']}"
        for m in messages
    ])
    response = gmodel.generate_content(prompt)
    return response.text


# ── chat_json() — JSON çıktı garantili ───────────────────────────────────────

def chat_json(messages: list, model: str = None,
              temperature: float = 0.3, max_tokens: int = 4096) -> dict:

    provider = get_provider()
    model = model or _default_model(provider)

    # JSON mode — sadece OpenAI ve Groq destekliyor
    if provider in ("openai", "groq"):
        client = _get_client(provider)
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content

    else:
        # Gemini ve Mistral — JSON talebi prompt'a ekle
        json_messages = messages.copy()
        json_messages[-1]["content"] += (
            "\n\nÖNEMLİ: Sadece geçerli JSON döndür. "
            "Başında veya sonunda markdown, açıklama veya ``` olmamalı."
        )
        raw = chat(json_messages, model=model,
                   temperature=temperature, max_tokens=max_tokens)

    # Temizle ve parse et
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    return json.loads(raw)