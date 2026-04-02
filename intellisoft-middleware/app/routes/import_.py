"""
Import route — pull KHSC delegates into Open Event as attendees.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.clients.khsc import KHSCClient, KHSCError
from app.clients.open_event import OpenEventClient, OpenEventError
from app.core.config import get_settings
from app.core.logging import get_logger

router = APIRouter(prefix="/import", tags=["Delegate Import"])
logger = get_logger(__name__)


# ── Request / Response models ─────────────────────────────────────────────── #

class ImportRequest(BaseModel):
    event_id: int | None = Field(
        default=None,
        description="Open Event event ID to import into. Defaults to KHSC_EVENT_ID in .env",
    )
    uids: list[str] | None = Field(
        default=None,
        description=(
            "Specific KHSC UIDs to import. "
            "If omitted, ALL delegates from KHSC are imported."
        ),
        examples=[["CONF-1001", "CONF-1002"]],
    )


class FailedDelegate(BaseModel):
    uid: str
    reason: str


class ImportResponse(BaseModel):
    event_id: int
    created: int
    updated: int
    failed: list[FailedDelegate]
    message: str


# ── Helpers ───────────────────────────────────────────────────────────────── #

def _resolve_uids(requested: list[str] | None) -> list[str]:
    """
    If the caller didn't supply UIDs, fetch the full delegate list from KHSC
    by searching with an empty-ish query (returns all).
    """
    if requested:
        return requested

    logger.info("No UIDs supplied — fetching all delegates from KHSC")
    khsc = KHSCClient()
    # All UIDs in KHSC follow the "CONF-" prefix pattern; this returns every delegate
    delegates = khsc.search_delegates("CONF-")
    uids = [d["unique_id"] for d in delegates]
    logger.info("Fetched %d UIDs from KHSC", len(uids))
    return uids


# ── Endpoints ─────────────────────────────────────────────────────────────── #

@router.post(
    "",
    response_model=ImportResponse,
    summary="Import KHSC delegates into Open Event",
    description=(
        "Fetches each delegate from the KHSC API and creates (or updates) the "
        "corresponding attendee record in Open Event. "
        "If **uids** is omitted every delegate registered in KHSC is imported."
    ),
)
def import_delegates(body: ImportRequest) -> ImportResponse:
    cfg = get_settings()
    event_id = body.event_id or cfg.khsc_event_id

    logger.info("==> Import request: event_id=%d uids=%s", event_id, body.uids or "ALL")

    try:
        uids = _resolve_uids(body.uids)
    except KHSCError as exc:
        logger.error("Failed to fetch UIDs from KHSC: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc))

    if not uids:
        logger.warning("No delegates found in KHSC — nothing to import")
        return ImportResponse(
            event_id=event_id, created=0, updated=0, failed=[],
            message="No delegates found in KHSC.",
        )

    try:
        result = OpenEventClient().import_delegates(event_id, uids)
    except OpenEventError as exc:
        logger.error("Open Event import failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc))

    failed = [FailedDelegate(**f) for f in result.get("failed", [])]
    if failed:
        logger.warning("%d delegate(s) failed to import: %s", len(failed), failed)

    return ImportResponse(
        event_id=event_id,
        created=result["created"],
        updated=result["updated"],
        failed=failed,
        message=(
            f"Import complete. "
            f"Created: {result['created']}, Updated: {result['updated']}, "
            f"Failed: {len(failed)}"
        ),
    )
