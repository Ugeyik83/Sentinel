"""
scenarios/confidence.py
Scenario Confidence Score — 6 metrik.
"""

import logging
from datetime import datetime, timezone, timedelta
from statistics import mean

logger = logging.getLogger(__name__)


class ConfidenceScorer:
    WEIGHTS = {
        "evidence_count":        0.25,
        "signal_freshness":      0.15,
        "source_diversity":      0.20,
        "historical_precedent":  0.20,
        "graph_grounding":       0.15,
        "llm_certainty":         0.05,
    }

    def score(self, scenario: dict, signals: list, graph: dict,
              past_runs: list = None) -> dict:
        supporting = [
            s for s in signals
            if any(t.lower() in s.get("title", "").lower()
                   for t in scenario.get("trigger_signals", []))
        ]

        scores = {
            "evidence_count":       self._evidence_count(supporting),
            "signal_freshness":     self._freshness(supporting),
            "source_diversity":     self._diversity(supporting),
            "historical_precedent": self._precedent(scenario, past_runs or []),
            "graph_grounding":      self._grounding(scenario, graph),
            "llm_certainty":        0.60,  # Sabit — en az güvenilir
        }

        final = sum(scores[k] * self.WEIGHTS[k] for k in scores)

        return {
            "confidence": round(final, 3),
            "breakdown": {k: round(v, 3) for k, v in scores.items()},
            "evidence_count": len(supporting),
            "signal_strength": "high" if final > 0.7 else "medium" if final > 0.4 else "low",
            "hallucination_risk": "low" if scores["graph_grounding"] > 0.7 else "medium",
        }

    def _evidence_count(self, supporting: list) -> float:
        return min(len(supporting) / 10, 1.0)

    def _freshness(self, supporting: list) -> float:
        if not supporting:
            return 0.0
        now = datetime.now(timezone.utc)
        ages = []
        for s in supporting:
            try:
                ts = datetime.fromisoformat(s.get("collected_at", ""))
                ages.append((now - ts).total_seconds() / 3600)
            except Exception:
                ages.append(168)
        avg_age = mean(ages)
        return max(0.0, 1.0 - avg_age / 168)

    def _diversity(self, supporting: list) -> float:
        sources = set(s.get("source", "") for s in supporting)
        return min(len(sources) / 5, 1.0)

    def _precedent(self, scenario: dict, past_runs: list) -> float:
        similar = [
            r for r in past_runs
            if scenario.get("name", "").lower()[:20] in r.get("scenario_name", "").lower()
        ]
        return min(len(similar) / 3, 1.0)

    def _grounding(self, scenario: dict, graph: dict) -> float:
        entities = scenario.get("affected_risks", []) + scenario.get("affected_roles", [])
        if not entities:
            return 0.5
        node_ids = {n["id"] for n in graph.get("nodes", [])}
        grounded = sum(1 for e in entities if e in node_ids)
        return grounded / len(entities)
