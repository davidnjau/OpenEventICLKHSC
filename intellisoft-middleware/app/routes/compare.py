"""
Comparison routes — inspect and diff KHSC delegates vs Open Event attendees.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.clients.khsc import KHSCClient, KHSCError
from app.clients.open_event import OpenEventClient, OpenEventError
from app.core.config import get_settings
from app.core.logging import get_logger

router = APIRouter(prefix="/compare", tags=["Data Comparison"])
logger = get_logger(__name__)


# ── Response models ───────────────────────────────────────────────────────── #

class FieldMismatch(BaseModel):
    field: str
    khsc_value: str | None
    oe_value: str | None


class MatchedRecord(BaseModel):
    uid: str
    email: str
    in_sync: bool
    mismatches: list[FieldMismatch]
    khsc: dict
    oe: dict


class DiffResponse(BaseModel):
    event_id: int
    total_khsc: int
    total_oe: int
    matched: int
    fully_in_sync: int
    has_mismatches: int
    only_in_khsc: list[dict]
    only_in_oe: list[dict]
    comparison: list[MatchedRecord]
    summary: str


# ── Helpers ───────────────────────────────────────────────────────────────── #

_COMPARE_FIELDS = [
    ("first_name",     "firstname",     "first_name"),
    ("last_name",      "lastname",      "last_name"),
    ("organization",   "company",       "organization / company"),
    ("is_checked_in",  "is_checked_in", "is_checked_in"),
]


def _normalize(value) -> str | None:
    if value is None:
        return None
    return str(value).strip().lower()


# ── Endpoints ─────────────────────────────────────────────────────────────── #

@router.get(
    "/attendees",
    summary="List all Open Event attendees",
    description=(
        "Returns every attendee registered in Open Event for the configured event, "
        "with fields normalised for easy reading."
    ),
)
def list_attendees() -> list[dict]:
    cfg = get_settings()
    logger.info("Fetching all OE attendees for event %d", cfg.khsc_event_id)
    try:
        attendees = OpenEventClient().get_all_attendees(cfg.khsc_event_id)
        logger.info("Fetched %d attendees from Open Event", len(attendees))
        return attendees
    except OpenEventError as exc:
        logger.error("list_attendees failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc))


@router.get(
    "/diff",
    response_model=DiffResponse,
    summary="Diff KHSC delegates vs Open Event attendees",
    description=(
        "Fetches both lists and compares them by email. "
        "Reports delegates present in only one system, "
        "and field-level mismatches for matched records."
    ),
)
def diff() -> DiffResponse:
    cfg = get_settings()
    event_id = cfg.khsc_event_id
    logger.info("Running diff for event %d", event_id)

    # Fetch both lists
    try:
        khsc_delegates = KHSCClient().get_all_delegates()
    except KHSCError as exc:
        logger.error("diff: KHSC fetch failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"KHSC error: {exc}")

    try:
        oe_attendees = OpenEventClient().get_all_attendees(event_id)
    except OpenEventError as exc:
        logger.error("diff: OE fetch failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"Open Event error: {exc}")

    # Index both by email (lower-cased)
    khsc_by_email: dict[str, dict] = {
        d["email"].strip().lower(): d for d in khsc_delegates if d.get("email")
    }
    oe_by_email: dict[str, dict] = {
        a["email"].strip().lower(): a for a in oe_attendees if a.get("email")
    }

    all_emails = set(khsc_by_email) | set(oe_by_email)

    only_in_khsc = []
    only_in_oe   = []
    comparison: list[MatchedRecord] = []

    for email in sorted(all_emails):
        in_khsc = email in khsc_by_email
        in_oe   = email in oe_by_email

        if in_khsc and not in_oe:
            only_in_khsc.append(khsc_by_email[email])
            continue

        if in_oe and not in_khsc:
            only_in_oe.append(oe_by_email[email])
            continue

        # Both present — compare fields
        k = khsc_by_email[email]
        o = oe_by_email[email]

        mismatches: list[FieldMismatch] = []
        for khsc_field, oe_field, label in _COMPARE_FIELDS:
            kv = _normalize(k.get(khsc_field))
            ov = _normalize(o.get(oe_field))
            if kv != ov:
                mismatches.append(FieldMismatch(
                    field=label,
                    khsc_value=k.get(khsc_field),
                    oe_value=o.get(oe_field),
                ))

        comparison.append(MatchedRecord(
            uid=k.get("unique_id", ""),
            email=email,
            in_sync=len(mismatches) == 0,
            mismatches=mismatches,
            khsc=k,
            oe=o,
        ))

    matched          = len(comparison)
    fully_in_sync    = sum(1 for r in comparison if r.in_sync)
    has_mismatches   = matched - fully_in_sync

    logger.info(
        "Diff complete — KHSC: %d, OE: %d, matched: %d, in-sync: %d, "
        "mismatches: %d, only-KHSC: %d, only-OE: %d",
        len(khsc_delegates), len(oe_attendees), matched,
        fully_in_sync, has_mismatches, len(only_in_khsc), len(only_in_oe),
    )

    summary = (
        f"KHSC: {len(khsc_delegates)} delegates | "
        f"OE: {len(oe_attendees)} attendees | "
        f"Matched: {matched} | "
        f"Fully in sync: {fully_in_sync} | "
        f"Field mismatches: {has_mismatches} | "
        f"Only in KHSC: {len(only_in_khsc)} | "
        f"Only in OE: {len(only_in_oe)}"
    )

    return DiffResponse(
        event_id=event_id,
        total_khsc=len(khsc_delegates),
        total_oe=len(oe_attendees),
        matched=matched,
        fully_in_sync=fully_in_sync,
        has_mismatches=has_mismatches,
        only_in_khsc=only_in_khsc,
        only_in_oe=only_in_oe,
        comparison=comparison,
        summary=summary,
    )
