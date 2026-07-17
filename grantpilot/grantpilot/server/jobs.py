"""Background job runner + nightly auto-run scheduler."""

from __future__ import annotations

import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta, timezone

from sqlalchemy import select

from .db import SessionLocal
from .engine import execute_run
from .models import Profile, Run, utcnow

log = logging.getLogger(__name__)

# Runs are model-heavy and long; two at a time keeps API usage sane.
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="grantpilot-run")
_scheduler_stop = threading.Event()


def enqueue_run(profile_id: int) -> int:
    """Create a queued Run row and hand it to the worker pool. Returns the run id."""
    db = SessionLocal()
    try:
        run = Run(profile_id=profile_id, status="queued")
        db.add(run)
        db.commit()
        run_id = run.id
    finally:
        db.close()
    _executor.submit(execute_run, run_id)
    return run_id


def _profiles_due(db) -> list[int]:
    """auto_run profiles whose latest completed run is older than ~23h (or never ran)."""
    due = []
    cutoff = utcnow() - timedelta(hours=23)
    for profile in db.scalars(select(Profile).where(Profile.auto_run.is_(True))):
        active = [r for r in profile.runs if r.status in ("queued", "running")]
        if active:
            continue
        finished = [
            f if f.tzinfo else f.replace(tzinfo=timezone.utc)  # SQLite returns naive datetimes
            for f in (r.finished_at for r in profile.runs)
            if f is not None
        ]
        if not finished or max(finished) < cutoff:
            due.append(profile.id)
    return due


def _scheduler_loop(interval_seconds: int = 3600) -> None:
    while not _scheduler_stop.wait(interval_seconds):
        try:
            db = SessionLocal()
            try:
                due = _profiles_due(db)
            finally:
                db.close()
            for profile_id in due:
                log.info("scheduler: enqueuing nightly run for profile %d", profile_id)
                enqueue_run(profile_id)
        except Exception:
            log.exception("scheduler tick failed")


def start_scheduler() -> None:
    thread = threading.Thread(target=_scheduler_loop, daemon=True, name="grantpilot-scheduler")
    thread.start()


def stop_scheduler() -> None:
    _scheduler_stop.set()
