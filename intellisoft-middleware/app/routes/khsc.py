"""
Direct KHSC proxy routes — search, verify, mark paid, offline sync.
Useful for the Intellisoft admin dashboard or manual operations.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.clients.khsc import KHSCClient, KHSCError
from app.core.logging import get_logger

router = APIRouter(prefix="/khsc", tags=["KHSC Direct"])
logger = get_logger(__name__)


# ── Models ────────────────────────────────────────────────────────────────── #

class MarkPaidRequest(BaseModel):
    uid: str = Field(description="KHSC unique ID of the delegate")
    payment_method: str = Field(default="On-Site Cash", description="Payment method label")


class OfflineSyncRequest(BaseModel):
    uids: list[str] = Field(description="List of KHSC UIDs to check in")


# ── Endpoints ─────────────────────────────────────────────────────────────── #

@router.get(
    "/delegates",
    summary="List all KHSC delegates",
    description="Returns every delegate currently registered in KHSC.",
)
def list_delegates() -> list[dict]:
    logger.info("Fetching all KHSC delegates")
    try:
        delegates = KHSCClient().get_all_delegates()
        logger.info("Fetched %d delegates from KHSC", len(delegates))
        return delegates
    except KHSCError as exc:
        logger.error("list_delegates failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc))


@router.get(
    "/delegate/{uid}",
    summary="Verify a delegate",
    description="Fetch a single delegate's full details from KHSC by UID.",
)
def verify_delegate(uid: str) -> dict:
    logger.info("Verify delegate: %s", uid)
    try:
        return KHSCClient().verify_delegate(uid)
    except KHSCError as exc:
        logger.error("verify_delegate failed for %s: %s", uid, exc)
        raise HTTPException(status_code=404 if "not found" in str(exc).lower() else 502, detail=str(exc))


@router.get(
    "/search",
    summary="Search delegates",
    description="Search KHSC delegates by name, email, organization, or UID.",
)
def search_delegates(
    q: str = Query(description="Search term (name, email, org, or UID)")
) -> list[dict]:
    logger.info("Search delegates: %r", q)
    try:
        return KHSCClient().search_delegates(q)
    except KHSCError as exc:
        logger.error("search_delegates failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc))


@router.post(
    "/mark-paid",
    summary="Mark delegate as paid on-site",
    description="Record an on-site cash payment for a delegate in KHSC.",
)
def mark_paid(body: MarkPaidRequest) -> dict:
    logger.info("Mark paid: uid=%s method=%s", body.uid, body.payment_method)
    try:
        return KHSCClient().mark_paid_onsite(body.uid, body.payment_method)
    except KHSCError as exc:
        logger.error("mark_paid_onsite failed for %s: %s", body.uid, exc)
        raise HTTPException(status_code=502, detail=str(exc))


@router.post(
    "/offline-sync",
    summary="Offline bulk check-in",
    description=(
        "Check in multiple delegates at once. "
        "Used when devices have been operating offline and need to sync."
    ),
)
def offline_sync(body: OfflineSyncRequest) -> dict:
    logger.info("Offline sync for %d UIDs", len(body.uids))
    try:
        return KHSCClient().offline_sync(body.uids)
    except KHSCError as exc:
        logger.error("offline_sync failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc))
