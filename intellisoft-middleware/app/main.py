"""
Intellisoft Middleware — FastAPI application entry point.

Swagger UI:  http://localhost:7000/docs
ReDoc:       http://localhost:7000/redoc
OpenAPI JSON: http://localhost:7000/openapi.json
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.routes import compare, events, health, import_, khsc, sync
from app.scheduler import get_scheduler_status, start_scheduler, stop_scheduler

# ── Bootstrap logging before anything else ───────────────────────────────── #
cfg = get_settings()
setup_logging(cfg.log_level)
logger = get_logger(__name__)


# ── Application lifespan ──────────────────────────────────────────────────── #

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info("  Intellisoft Middleware starting up")
    logger.info("  Open Event URL : %s", cfg.open_event_base_url)
    logger.info("  KHSC API URL   : %s", cfg.khsc_api_url)
    logger.info("  Target event   : %d", cfg.khsc_event_id)
    logger.info("  Log level      : %s", cfg.log_level)
    logger.info("=" * 60)

    if cfg.enable_scheduler:
        start_scheduler()
    else:
        logger.warning("Scheduler disabled via ENABLE_SCHEDULER=false")

    yield  # application runs here

    logger.info("Intellisoft Middleware shutting down")
    stop_scheduler()


# ── FastAPI app ───────────────────────────────────────────────────────────── #

app = FastAPI(
    title="Intellisoft Middleware",
    description="""
## Intellisoft KHSC ↔ Open Event Integration Layer

This middleware bridges the **KHSC conference management system** and the
**Open Event organizer platform**.

### What it does

| Job | Schedule | Description |
|-----|----------|-------------|
| Import delegates | Every 5 min | Pulls new KHSC registrations into Open Event as attendees |
| Sync check-ins   | Every 2 min | Reconciles check-in state — KHSC is the source of truth |
| Push check-in    | On demand   | Forwards a check-in from Open Event back to KHSC |

### Authentication

All API calls to KHSC use four headers (`X-API-Username`, `Authorization`,
`X-Pass-Key`, `X-Secret-Key`). Open Event uses JWT auth. Both are configured
via environment variables — no credentials are hard-coded.

### Source of truth

- **Delegate registration / payment** → KHSC owns this
- **Check-in state** → KHSC is the source of truth; Open Event follows
- **Event programme / sessions** → Open Event owns this
    """,
    version="1.0.0",
    contact={
        "name":  "Intellisoft",
        "email": "dev@intellisoft.co.ke",
    },
    license_info={
        "name": "MIT",
    },
    lifespan=lifespan,
)


# ── CORS ──────────────────────────────────────────────────────────────────── #

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request logging middleware ─────────────────────────────────────────────── #

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info("→ %s %s", request.method, request.url.path)
    response = await call_next(request)
    logger.info("← %s %s  [%d]", request.method, request.url.path, response.status_code)
    return response


# ── Global exception handler ──────────────────────────────────────────────── #

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Check middleware logs for details."},
    )


# ── Routers ───────────────────────────────────────────────────────────────── #

app.include_router(health.router)
app.include_router(events.router)
app.include_router(import_.router)
app.include_router(sync.router)
app.include_router(khsc.router)
app.include_router(compare.router)


# ── Extra convenience endpoints ───────────────────────────────────────────── #

@app.get("/", include_in_schema=False)
def root():
    return {
        "service": "Intellisoft Middleware",
        "version": "1.0.0",
        "docs":    "/docs",
        "health":  "/health",
    }


@app.get(
    "/scheduler",
    tags=["Health & Diagnostics"],
    summary="Scheduler status",
    description="Returns the next scheduled run time for each background job.",
)
def scheduler_status() -> list[dict]:
    jobs = get_scheduler_status()
    logger.debug("Scheduler status requested — %d job(s)", len(jobs))
    return jobs
