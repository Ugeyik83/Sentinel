"""
app/run_artifacts.py — Run dizin yönetimi.
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

RUNS_BASE = Path("uploads/runs")


class RunStore:
    def __init__(self):
        self.base = RUNS_BASE
        self.base.mkdir(parents=True, exist_ok=True)

    def create_run(self, run_id: str = None) -> Path:
        run_id = run_id or str(uuid.uuid4())[:8]
        run_dir = self.base / run_id
        for sub in ["input", "signals", "scenarios", "simulation", "report", "logs"]:
            (run_dir / sub).mkdir(parents=True, exist_ok=True)
        manifest = {
            "run_id": run_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "READY",
            "config": {},
        }
        (run_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2)
        )
        return run_dir

    def get_run_dir(self, run_id: str) -> Path:
        return self.base / run_id

    def get_manifest(self, run_id: str) -> dict:
        path = self.base / run_id / "manifest.json"
        return json.loads(path.read_text()) if path.exists() else {}

    def update_manifest(self, run_id: str, **kwargs):
        manifest = self.get_manifest(run_id)
        manifest.update(kwargs)
        manifest["updated_at"] = datetime.now(timezone.utc).isoformat()
        (self.base / run_id / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2)
        )

    def list_runs(self) -> list:
        runs = []
        for d in sorted(self.base.iterdir(), reverse=True):
            mp = d / "manifest.json"
            if mp.exists():
                try:
                    runs.append(json.loads(mp.read_text()))
                except Exception:
                    pass
        return runs
