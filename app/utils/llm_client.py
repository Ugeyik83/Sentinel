"""
app/utils/llm_client.py — OpenAI API wrapper. Tüm LLM çağrıları buradan.
"""

import os
import json
import time
import logging
from typing import Optional
from openai import OpenAI

logger = logging.getLogger(__name__)
_client: Optional[OpenAI] = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
    return _client


def get_llm():
    """CrewAI için LLM nesnesi."""
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=os.environ.get("LLM_MODEL_NAME", "gpt-4o"),
        api_key=os.environ.get("OPENAI_API_KEY", ""),
        temperature=float(os.environ.get("LLM_TEMPERATURE", "0.7")),
    )


def chat(messages: list, model: str = None, temperature: float = 0.7,
         max_tokens: int = 4096, max_retries: int = 3) -> str:
    model = model or os.environ.get("LLM_MODEL_NAME", "gpt-4o")
    client = get_client()
    for attempt in range(1, max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.warning(f"LLM hata (deneme {attempt}/{max_retries}): {e}")
            if attempt == max_retries:
                raise
            time.sleep(2 ** attempt)


def chat_json(messages: list, model: str = None, temperature: float = 0.3,
              max_tokens: int = 4096) -> dict:
    model = model or os.environ.get("LLM_MODEL_NAME", "gpt-4o")
    client = get_client()
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)
