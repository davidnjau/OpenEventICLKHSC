"""
Health check and diagnostics routes.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from app.clients.khsc import KHSCClient, KHSCError
from app.clients.open_event import OpenEventClient, OpenEventError
from app.core.config import get_settings
from app.core.logging import get_logger

router = APIRouter(prefix="/health", tags=["Health & Diagnostics"])
logger = get_logger(__name__)


class ServiceStatus(BaseModel):
    status: str          # "ok" | "error"
    message: str


class HealthResponse(BaseModel):
    status: str          # "healthy" | "degraded" | "unhealthy"
    timestamp: str
    khsc_api: ServiceStatus
    open_event_api: ServiceStatus
    event_id: int


@router.get(
    "",
    response_model=HealthResponse,
    summary="Service health check",
    description=(
        "Pings both the KHSC API and the Open Event API. "
        "Returns **healthy** if both are reachable, **degraded** if one is down, "
        "**unhealthy** if both are down."
    ),
)
def health_check() -> HealthResponse:
    cfg = get_settings()
    logger.debug("Health check requested")

    # Check KHSC
    khsc_status: ServiceStatus
    try:
        KHSCClient().sandbox_test()
        khsc_status = ServiceStatus(status="ok", message="KHSC API reachable")
        logger.debug("KHSC health: OK")
    except KHSCError as exc:
        khsc_status = ServiceStatus(status="error", message=str(exc))
        logger.warning("KHSC health check failed: %s", exc)

    # Check Open Event
    oe_status: ServiceStatus
    try:
        OpenEventClient().get_event(cfg.khsc_event_id)
        oe_status = ServiceStatus(status="ok", message="Open Event API reachable")
        logger.debug("Open Event health: OK")
    except OpenEventError as exc:
        oe_status = ServiceStatus(status="error", message=str(exc))
        logger.warning("Open Event health check failed: %s", exc)

    services_up = sum(1 for s in [khsc_status, oe_status] if s.status == "ok")
    overall = "healthy" if services_up == 2 else ("degraded" if services_up == 1 else "unhealthy")

    if overall != "healthy":
        logger.error("Health check result: %s (KHSC=%s, OE=%s)", overall, khsc_status.status, oe_status.status)

    return HealthResponse(
        status=overall,
        timestamp=datetime.now(timezone.utc).isoformat(),
        khsc_api=khsc_status,
        open_event_api=oe_status,
        event_id=cfg.khsc_event_id,
    )


@router.get(
    "/stats",
    summary="Live event statistics",
    description="Returns combined statistics from both KHSC and Open Event for the configured event.",
)
def get_stats() -> dict:
    cfg = get_settings()
    logger.info("Stats requested for event %d", cfg.khsc_event_id)

    stats: dict = {"event_id": cfg.khsc_event_id}

    try:
        stats["khsc"] = KHSCClient().get_event_stats()
    except KHSCError as exc:
        logger.warning("Could not fetch KHSC stats: %s", exc)
        stats["khsc"] = {"error": str(exc)}

    try:
        stats["open_event"] = OpenEventClient().get_event_stats(cfg.khsc_event_id)
    except OpenEventError as exc:
        logger.warning("Could not fetch Open Event stats: %s", exc)
        stats["open_event"] = {"error": str(exc)}

    return stats
