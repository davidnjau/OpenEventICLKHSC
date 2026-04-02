"""
Sync routes — reconcile check-in state between KHSC and Open Event.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.clients.open_event import OpenEventClient, OpenEventError
from app.core.config import get_settings
from app.core.logging import get_logger

router = APIRouter(prefix="/sync", tags=["Check-in Sync"])
logger = get_logger(__name__)


# ── Request / Response models ─────────────────────────────────────────────── #

class SyncRequest(BaseModel):
    event_id: int | None = Field(
        default=None,
        description="Open Event event ID. Defaults to KHSC_EVENT_ID in .env",
    )


class FailedSync(BaseModel):
    uid: str
    reason: str


class SyncResponse(BaseModel):
    event_id: int
    synced: int
    already_in_sync: int
    failed: list[FailedSync]
    message: str


class CheckinPushRequest(BaseModel):
    uid: str = Field(description="KHSC unique ID of the delegate being checked in")


class CheckinPushResponse(BaseModel):
    uid: str
    message: str
    khsc_data: dict


# ── Endpoints ─────────────────────────────────────────────────────────────── #

@router.post(
    "/checkins",
    response_model=SyncResponse,
    summary="Reconcile check-in state with KHSC",
    description=(
        "For every attendee in Open Event that has a KHSC UID, this endpoint "
        "calls the KHSC verify_delegate API and updates the is_checked_in flag "
        "in Open Event to match. KHSC is the source of truth."
    ),
)
def sync_checkins(body: SyncRequest) -> SyncResponse:
    cfg = get_settings()
    event_id = body.event_id or cfg.khsc_event_id

    logger.info("==> Sync check-ins request: event_id=%d", event_id)

    try:
        result = OpenEventClient().sync_checkins(event_id)
    except OpenEventError as exc:
        logger.error("Check-in sync failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc))

    failed = [FailedSync(**f) for f in result.get("failed", [])]
    if failed:
        logger.warning("%d attendee(s) failed to sync: %s", len(failed), failed)

    return SyncResponse(
        event_id=event_id,
        synced=result["synced"],
        already_in_sync=result["already_in_sync"],
        failed=failed,
        message=(
            f"Sync complete. "
            f"Synced: {result['synced']}, "
            f"Already in sync: {result['already_in_sync']}, "
            f"Failed: {len(failed)}"
        ),
    )


@router.post(
    "/push-checkin",
    response_model=CheckinPushResponse,
    summary="Push a check-in from Open Event → KHSC",
    description=(
        "Called when an attendee is checked in via the Android organizer app. "
        "Forwards the check-in to KHSC so both systems stay in sync."
    ),
)
def push_checkin(body: CheckinPushRequest) -> CheckinPushResponse:
    logger.info("==> Push check-in request: uid=%s", body.uid)

    try:
        data = OpenEventClient().push_checkin(body.uid)
    except OpenEventError as exc:
        logger.error("Push check-in failed for %s: %s", body.uid, exc)
        raise HTTPException(status_code=502, detail=str(exc))

    logger.info("Check-in pushed successfully for %s", body.uid)
    return CheckinPushResponse(
        uid=body.uid,
        message=f"Check-in for {body.uid} pushed to KHSC successfully.",
        khsc_data=data,
    )
