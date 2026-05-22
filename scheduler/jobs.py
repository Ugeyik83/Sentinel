"""
scheduler/jobs.py
APScheduler görev tanımları.
"""

import logging
import yaml
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)
SCHEDULER_PATH = Path("config/scheduler.yaml")


def build_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="Europe/Istanbul")
    config = yaml.safe_load(SCHEDULER_PATH.read_text()) if SCHEDULER_PATH.exists() else {}

    for job in config.get("jobs", []):
        if not job.get("enabled", True):
            continue
        trigger = CronTrigger.from_crontab(job["schedule"])
        scheduler.add_job(
            func=_dispatch,
            trigger=trigger,
            kwargs={"tasks": job["tasks"]},
            id=job["name"],
            name=job["name"],
            replace_existing=True,
        )
        logger.info(f"Görev eklendi: {job['name']} — {job['schedule']}")

    return scheduler


def _dispatch(tasks: list):
    from scheduler.runner import run_tasks
    run_tasks(tasks)
