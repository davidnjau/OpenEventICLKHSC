"""
Events routes — browse Open Event events filtered by date.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from fastapi import APIRouter, HTTPException, Query

from app.clients.open_event import OpenEventClient, OpenEventError
from app.core.logging import get_logger

router = APIRouter(prefix="/events", tags=["Events"])
logger = get_logger(__name__)


class When(str, Enum):
    all      = "all"
    past     = "past"
    today    = "today"
    upcoming = "upcoming"


def _parse_dt(value: str | None) -> datetime | None:
    """Parse an ISO-8601 datetime string into an aware datetime."""
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def _flatten_event(item: dict) -> dict:
    """Collapse JSON:API event object into a flat dict."""
    attrs = item.get("attributes", {})
    return {
        "id":            item.get("id"),
        "name":          attrs.get("name"),
        "state":         attrs.get("state"),
        "starts_at":     attrs.get("starts-at"),
        "ends_at":       attrs.get("ends-at"),
        "timezone":      attrs.get("timezone"),
        "location":      attrs.get("location-name") or attrs.get("searchable-location-name"),
        "description":   attrs.get("description"),
        "identifier":    attrs.get("identifier"),
        "logo_url":      attrs.get("logo-url"),
        "thumbnail_url": attrs.get("thumbnail-image-url"),
        "privacy":       attrs.get("privacy"),
        "online":        attrs.get("online"),
    }


@router.get(
    "",
    summary="List Open Event events",
    description=(
        "Returns events from Open Event. Use **when** to filter:\n\n"
        "- `all` — every event (default)\n"
        "- `past` — events that ended before today\n"
        "- `today` — events running right now (started ≤ today ≤ ends)\n"
        "- `upcoming` — events that start after today"
    ),
)
def list_events(
    when: When = Query(default=When.all, description="Date filter"),
) -> list[dict]:
    logger.info("Fetching events — filter: %s", when.value)

    try:
        raw = OpenEventClient().get_events()
    except OpenEventError as exc:
        logger.error("list_events failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc))

    now = datetime.now(timezone.utc)
    results = []

    for item in raw:
        event   = _flatten_event(item)
        starts  = _parse_dt(event["starts_at"])
        ends    = _parse_dt(event["ends_at"])

        if when == When.past:
            # ended before start of today
            if ends and ends < now.replace(hour=0, minute=0, second=0, microsecond=0):
                results.append(event)

        elif when == When.today:
            # started on or before now AND ends on or after now
            if starts and ends and starts.date() <= now.date() <= ends.date():
                results.append(event)

        elif when == When.upcoming:
            # starts strictly after today
            if starts and starts.date() > now.date():
                results.append(event)

        else:  # all
            results.append(event)

    logger.info("Events returned: %d (filter=%s)", len(results), when.value)
    return results
