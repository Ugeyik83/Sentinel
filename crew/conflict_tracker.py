"""
crew/conflict_tracker.py
Ajan çatışma logu + kurumsal kültür analizi.
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter, defaultdict

logger = logging.getLogger(__name__)


class ConflictTracker:
    def __init__(self, run_dir: str):
        self.run_dir = Path(run_dir)
        self.log = []

    def record(self, agents: list, topic: str, positions: dict,
               resolution: dict, duration_turns: int):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agents": agents,
            "topic": topic,
            "positions": positions,
            "resolution": resolution,
            "duration_turns": duration_turns,
        }
        self.log.append(entry)
        self._save()

    def get_log(self) -> list:
        return self.log

    def _save(self):
        path = self.run_dir / "simulation" / "conflict_log.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.log, ensure_ascii=False, indent=2))

    @staticmethod
    def analyze_culture(conflict_logs: list) -> dict:
        """Tüm geçmiş çatışma loglarından kültür analizi."""
        if not conflict_logs:
            return {}

        winner_counts = Counter()
        bias_counts = defaultdict(int)
        total_turns = []

        for conflict in conflict_logs:
            resolution = conflict.get("resolution", {})
            winner = resolution.get("decided_by", "")
            if winner:
                winner_counts[winner] += 1

            for agent_id, position in conflict.get("positions", {}).items():
                for bias in position.get("bias_signals", []):
                    bias_counts[bias] += 1

            total_turns.append(conflict.get("duration_turns", 1))

        total = len(conflict_logs)
        return {
            "total_conflicts": total,
            "dominant_voices": [
                {"role": role, "win_rate": round(count / total, 2)}
                for role, count in winner_counts.most_common(5)
            ],
            "bias_distribution": {
                bias: round(count / sum(bias_counts.values()), 2)
                for bias, count in sorted(
                    bias_counts.items(), key=lambda x: x[1], reverse=True
                )
            },
            "avg_resolution_turns": round(
                sum(total_turns) / len(total_turns), 1
            ) if total_turns else 0,
        }
