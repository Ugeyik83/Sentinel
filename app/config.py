"""
app/config.py — Ortam değişkenleri ve uygulama ayarları.
"""

import os
from dataclasses import dataclass


@dataclass
class Config:
    openai_api_key: str = ""
    llm_model: str = "gpt-4o"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4096
    newsapi_key: str = ""
    runs_dir: str = "uploads/runs"
    graph_backend: str = "networkx"

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
            llm_model=os.environ.get("LLM_MODEL_NAME", "gpt-4o"),
            llm_temperature=float(os.environ.get("LLM_TEMPERATURE", "0.7")),
            llm_max_tokens=int(os.environ.get("LLM_MAX_TOKENS", "4096")),
            newsapi_key=os.environ.get("NEWSAPI_KEY", ""),
            runs_dir=os.environ.get("RUNS_DIR", "uploads/runs"),
            graph_backend=os.environ.get("GRAPH_BACKEND", "networkx"),
        )

    def validate(self):
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY tanımlı değil")


config = Config.from_env()
