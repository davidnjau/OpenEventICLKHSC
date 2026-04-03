# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A monorepo that integrates five components for the **KHSC conference management system**:

| Component | Stack | Purpose |
|---|---|---|
| `open-event-server/` | Flask 1.1, Python 3.8, PostgreSQL | JSON:API backend — events, attendees, orders |
| `intellisoft-middleware/` | FastAPI, Python 3.9+ | Bridges KHSC ↔ Open Event (import, sync, diff) |
| `open-event-organizer-android/` | Android, Kotlin/Java | Organiser app — check-ins, attendee management |
| `open-event-organizer-ios/` | iOS 12+, Swift, Alamofire | iOS organiser app |
| `open-event-frontend/` | Ember.js 4 | Web frontend for event management |

## How the pieces connect

```
Android / iOS app  ──────────────────────────────────┐
                                                      ▼
KHSC API ──► intellisoft-middleware (port 7000) ──► open-event-server (port 8080)
                                                      ▼
                                                 PostgreSQL (port 5432)
KHSC mock (port 9090) simulates the real KHSC API during development.
```

- KHSC is the source of truth for **registrations and payments**
- Open Event is the source of truth for **event programme and sessions**
- **Check-in state** flows: Android/iOS app → Open Event → middleware → KHSC

## First-time setup

```bash
# 1. Copy and fill in root config
cp .env.example .env
# Set SERVER_HOST to your LAN IP (not localhost) so Android/iOS can reach it
# Set ADMIN_EMAIL and ADMIN_PASSWORD
# Set SECRET_KEY (generate with: python3 -c "import secrets; print(secrets.token_hex(32))")

# 2. Propagate config into all subprojects
python3 setup.py

# 3. Start the Open Event stack (server + postgres + redis + KHSC mock)
cd open-event-server
docker compose up -d

# 4. Start the middleware (separate terminal)
cd intellisoft-middleware
cp .env.example .env   # edit with same credentials
ENABLE_SCHEDULER=false .venv/bin/uvicorn app.main:app --reload --port 7000
```

## Running services

| Service | Command | URL |
|---|---|---|
| Open Event server | `cd open-event-server && docker compose up -d` | http://localhost:8080 |
| KHSC mock | Started automatically with docker compose above | http://localhost:9090 |
| Middleware | See `intellisoft-middleware/CLAUDE.md` | http://localhost:7000 |
| Frontend | `cd open-event-frontend && yarn start` | http://localhost:4200 |

## Key credentials (local/dev)

These match the KHSC mock server in `open-event-server/khsc_mock/`:
- **KHSC username:** `admin_desk_1`
- **KHSC auth token:** `Bearer tok_test_khsc_mock_2026`
- **KHSC pass key:** `pk_test_khsc_mock_2026`
- **KHSC secret key:** `sk_test_khsc_mock_2026`

Open Event admin credentials are set via `ADMIN_EMAIL` / `ADMIN_PASSWORD` in `.env`.
If the OE password stops working, reset it — see `intellisoft-middleware/CLAUDE.md`.

## Docker network

All containers share the `open-event-server_default` network. Inside that network:
- Open Event server → `opev-web:8080`
- KHSC mock → `opev-khsc-mock:9090` (or `khsc-mock:9090`)
- PostgreSQL → `opev-postgres:5432`

The middleware's `docker-compose.yml` joins this external network automatically.

## setup.py

Reads the root `.env` and propagates shared values into:
- `open-event-organizer-android/app/build.gradle` → API base URL, Mapbox token
- `open-event-organizer-android/.../network_security_config.xml` → trusted host
- `open-event-frontend/.env` → API host
- `open-event-server/.env` → DB URL, admin credentials

Run it again any time you change `SERVER_HOST` or credentials.

## CLAUDE.md files per subproject

Each component has its own `CLAUDE.md` with component-specific commands and architecture:
- `open-event-server/CLAUDE.md` — Flask routes, marshmallow schemas, migrations
- `intellisoft-middleware/CLAUDE.md` — FastAPI routes, KHSC client, scheduler
- `open-event-organizer-android/CLAUDE.md` — Gradle commands, DBFlow, RxJava
- `open-event-organizer-ios/CLAUDE.md` — Xcode, CocoaPods, Alamofire
- `open-event-frontend/CLAUDE.md` — Ember.js, ember-data, JSON:API adapter
