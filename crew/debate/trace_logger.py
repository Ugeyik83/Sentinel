"""
crew/debate/trace_logger.py
Audit trail — her tur, her ajan, her mesaj kaydedilir.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


class TraceLogger:
    def __init__(self, run_dir: str):
        self.run_dir = Path(run_dir)
        self.log = []

    def log_turn(self, round_num: int, agent: str,
                 turn_type: str, content: str):
        entry = {
            "round": round_num,
            "agent": agent,
            "type": turn_type,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.log.append(entry)
        self._save()

    def get_log(self) -> list:
        return self.log

    def _save(self):
        path = self.run_dir / "simulation" / "debate_trace.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.log, ensure_ascii=False, indent=2))
