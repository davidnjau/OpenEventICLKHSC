# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

FastAPI middleware that bridges the **KHSC conference registration system** and **Open Event**. It imports KHSC delegates as Open Event attendees and keeps check-in state in sync between the two systems.

## Running Locally

```bash
# Create virtualenv (Python 3.9+)
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Start (scheduler disabled for dev)
KHSC_API_URL=http://localhost:9090/api/index.php \
OPEN_EVENT_BASE_URL=http://localhost:8080/v1 \
KHSC_API_USERNAME=admin_desk_1 \
KHSC_AUTHORIZATION="Bearer tok_test_khsc_mock_2026" \
KHSC_PASS_KEY=pk_test_khsc_mock_2026 \
KHSC_SECRET_KEY=sk_test_khsc_mock_2026 \
OPEN_EVENT_ADMIN_EMAIL=<email> \
OPEN_EVENT_ADMIN_PASSWORD=<password> \
ENABLE_SCHEDULER=false \
uvicorn app.main:app --reload --port 7000
```

Swagger UI: http://localhost:7000/docs

## Docker (Production)

```bash
# Joins the open-event-server Docker network to reach opev-web and khsc-mock by hostname
docker compose up -d
```

The container reads all credentials from `.env` (copy from `.env.example` or the file in the repo).

## Verify Import Works

```bash
# Import all KHSC delegates into Open Event event ID 1
curl -s -X POST http://localhost:7000/import -H "Content-Type: application/json" -d '{}'
```

## Architecture

```
Android App → Open Event Server (Flask/PostgreSQL)
                     ↑
              Intellisoft Middleware (this repo, FastAPI)
                     ↑
              KHSC Mock / Real KHSC API
```

**Key design decisions:**
- `app/clients/khsc.py` — all KHSC calls go through `KHSCClient`; all 4 auth headers injected automatically
- `app/clients/open_event.py` — JWT auth with thread-safe auto-refresh on 401; uses `JWT` prefix (not `Bearer`)
- `app/scheduler.py` — APScheduler `BackgroundScheduler` runs `job_import_delegates` and `job_sync_checkins` on configurable intervals
- `from __future__ import annotations` + `eval-type-backport` — required for Python 3.9 compatibility with Pydantic v2's `X | None` union syntax

## KHSC Mock Credentials

The mock server (`opev-khsc-mock` container, port 9090) requires exactly these headers:
- `X-API-Username: admin_desk_1`
- `Authorization: Bearer tok_test_khsc_mock_2026`
- `X-Pass-Key: pk_test_khsc_mock_2026`
- `X-Secret-Key: sk_test_khsc_mock_2026`

All KHSC delegates have UIDs starting with `CONF-`. To fetch all delegates, search with `q=CONF-`.

## Open Event Password Reset

If the OE admin password becomes invalid, reset it inside the `opev-web` container:

```python
# docker exec -it opev-web python3
from flask_scrypt import generate_password_hash, generate_random_salt
salt = str(generate_random_salt(), 'utf-8')
hashed = str(generate_password_hash('newpassword', salt), 'utf-8')
# Then UPDATE users SET _password='<hashed>', salt='<salt>' WHERE _email='...'
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `KHSC_API_URL` | `http://localhost:9090/api/index.php` | KHSC base URL |
| `KHSC_API_USERNAME` | — | Required |
| `KHSC_AUTHORIZATION` | — | Bearer token, e.g. `Bearer tok_...` |
| `KHSC_PASS_KEY` | — | Required |
| `KHSC_SECRET_KEY` | — | Required |
| `OPEN_EVENT_BASE_URL` | `http://localhost:8080/v1` | OE API root |
| `OPEN_EVENT_ADMIN_EMAIL` | — | Required |
| `OPEN_EVENT_ADMIN_PASSWORD` | — | Required |
| `KHSC_EVENT_ID` | `1` | Target OE event ID |
| `IMPORT_INTERVAL_SECONDS` | `300` | Scheduler: import frequency |
| `SYNC_INTERVAL_SECONDS` | `120` | Scheduler: sync frequency |
| `ENABLE_SCHEDULER` | `true` | Set to `false` for dev |
| `LOG_LEVEL` | `INFO` | DEBUG/INFO/WARNING/ERROR |
| `MIDDLEWARE_PORT` | `7000` | Uvicorn bind port |
