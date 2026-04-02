"""
Background scheduler — runs periodic import and sync-checkin jobs.

Uses APScheduler with an in-process thread pool so no external queue
(Redis / Celery) is needed for the middleware itself.
"""

from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.clients.open_event import OpenEventClient, OpenEventError
from app.clients.khsc import KHSCClient, KHSCError
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_scheduler: BackgroundScheduler | None = None


# ── Job functions ─────────────────────────────────────────────────────────── #

def job_import_delegates() -> None:
    """
    Scheduled job: fetch all KHSC delegate UIDs and import any that are
    not yet in Open Event.
    """
    cfg = get_settings()
    logger.info("[SCHEDULER] Starting delegate import job for event %d", cfg.khsc_event_id)

    try:
        delegates = KHSCClient().search_delegates(" ")
        uids = [d["unique_id"] for d in delegates]
        logger.info("[SCHEDULER] Found %d delegates in KHSC", len(uids))
    except KHSCError as exc:
        logger.error("[SCHEDULER] Import job — could not fetch UIDs from KHSC: %s", exc)
        return

    if not uids:
        logger.warning("[SCHEDULER] Import job — no delegates returned from KHSC")
        return

    try:
        result = OpenEventClient().import_delegates(cfg.khsc_event_id, uids)
        logger.info(
            "[SCHEDULER] Import job complete — created=%d updated=%d failed=%d",
            result.get("created", 0),
            result.get("updated", 0),
            len(result.get("failed", [])),
        )
        for failure in result.get("failed", []):
            logger.warning("[SCHEDULER] Import failed for %s: %s", failure["uid"], failure["reason"])
    except OpenEventError as exc:
        logger.error("[SCHEDULER] Import job — Open Event error: %s", exc)


def job_sync_checkins() -> None:
    """
    Scheduled job: reconcile check-in state between KHSC and Open Event.
    KHSC is treated as the source of truth.
    """
    cfg = get_settings()
    logger.info("[SCHEDULER] Starting check-in sync job for event %d", cfg.khsc_event_id)

    try:
        result = OpenEventClient().sync_checkins(cfg.khsc_event_id)
        logger.info(
            "[SCHEDULER] Sync job complete — synced=%d already_in_sync=%d failed=%d",
            result.get("synced", 0),
            result.get("already_in_sync", 0),
            len(result.get("failed", [])),
        )
        for failure in result.get("failed", []):
            logger.warning("[SCHEDULER] Sync failed for %s: %s", failure["uid"], failure["reason"])
    except OpenEventError as exc:
        logger.error("[SCHEDULER] Sync job — Open Event error: %s", exc)


# ── Lifecycle ─────────────────────────────────────────────────────────────── #

def start_scheduler() -> BackgroundScheduler:
    global _scheduler
    cfg = get_settings()

    _scheduler = BackgroundScheduler(timezone="UTC")

    _scheduler.add_job(
        job_import_delegates,
        trigger=IntervalTrigger(seconds=cfg.import_interval_seconds),
        id="import_delegates",
        name="Import KHSC delegates → Open Event",
        replace_existing=True,
        max_instances=1,        # prevent overlap if a job runs long
    )
    logger.info(
        "Scheduled: import_delegates every %ds", cfg.import_interval_seconds
    )

    _scheduler.add_job(
        job_sync_checkins,
        trigger=IntervalTrigger(seconds=cfg.sync_interval_seconds),
        id="sync_checkins",
        name="Sync check-ins KHSC ↔ Open Event",
        replace_existing=True,
        max_instances=1,
    )
    logger.info(
        "Scheduled: sync_checkins every %ds", cfg.sync_interval_seconds
    )

    _scheduler.start()
    logger.info("Background scheduler started with %d job(s)", len(_scheduler.get_jobs()))
    return _scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Background scheduler stopped")


def get_scheduler_status() -> list[dict]:
    """Return a summary of all scheduled jobs (used by the /scheduler endpoint)."""
    if not _scheduler:
        return []
    jobs = []
    for job in _scheduler.get_jobs():
        next_run = job.next_run_time
        jobs.append({
            "id":           job.id,
            "name":         job.name,
            "next_run_utc": next_run.isoformat() if next_run else None,
        })
    return jobs
