"""memory/retriever.py — Semantic search — benzer geçmiş bul."""
from memory.decision_parameters import DecisionParameterStore

class MemoryRetriever:
    def __init__(self):
        self.store = DecisionParameterStore()

    def retrieve(self, context: str, top_k: int = 5) -> str:
        return self.store.retrieve_for_prompt(context, top_k)
