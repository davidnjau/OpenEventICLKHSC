# OpenEvent ICL KHSC — Monorepo

An integrated conference management platform that bridges the **KHSC delegate registration system** with the **Open Event organizer platform**, enabling real-time delegate import, check-in sync, and live event statistics.

---

## System Architecture

```
┌─────────────────────┐        ┌──────────────────────────┐
│   Android App        │        │       iOS App             │
│  (check-in, mgmt)   │        │   (check-in, mgmt)        │
└────────┬────────────┘        └────────────┬─────────────┘
         │                                  │
         ▼                                  ▼
┌─────────────────────────────────────────────────────────┐
│               Open Event Server  :8080                  │
│           (Flask · PostgreSQL · Redis · Celery)         │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│           Intellisoft Middleware  :7000                  │
│               (FastAPI · APScheduler)                    │
│  /import  /sync  /compare/diff  /events  /health        │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│              KHSC API  :9090 (mock in dev)               │
│        (Delegate registration · Payments · Check-in)     │
└─────────────────────────────────────────────────────────┘
```

**Source of truth:**
- Delegate registration & payments → **KHSC**
- Event programme & sessions → **Open Event**
- Check-in state → **KHSC** (middleware syncs to Open Event)

---

## Components

| Component | Stack | Port | Purpose |
|---|---|---|---|
| `open-event-server` | Flask 1.1, Python 3.8, PostgreSQL | 8080 | JSON:API backend — events, attendees, orders |
| `intellisoft-middleware` | FastAPI, Python 3.9+ | 7000 | KHSC ↔ Open Event bridge |
| `open-event-organizer-android` | Android, Java/Kotlin | — | Organiser app — check-ins, attendee management |
| `open-event-organizer-ios` | iOS 12+, Swift | — | iOS organiser app |
| `open-event-frontend` | Ember.js 4 | 4200 | Web frontend for event management |
| `khsc_mock` (inside server) | Flask | 9090 | Simulates the real KHSC API in development |

---

## First-Time Setup

### 1. Copy and fill in the shared config

```bash
cp .env.example .env
```

Edit `.env` and set:
- `SERVER_HOST` — your machine's LAN IP (not `localhost`) so Android/iOS can reach the server
- `ADMIN_EMAIL` / `ADMIN_PASSWORD` — initial superuser credentials
- `SECRET_KEY` — leave blank; the setup script generates one automatically

All KHSC mock credentials are pre-filled and match the mock server out of the box.

### 2. Run the setup script

```bash
python3 setup.py
```

This will:
- Detect your LAN IP and propagate it everywhere it is needed
- Generate a Flask `SECRET_KEY` if one is not set
- Write config into each subproject (`build.gradle`, `network_security_config.xml`, `.env` files)
- Optionally start the server stack and create the admin superuser

> **Why `is_verified` is set manually:** local machines have no mail server so the verification email is never delivered. The script sets `is_verified = true` directly in PostgreSQL. This only happens during local setup.

### 3. Start the Open Event stack

```bash
cd open-event-server
docker compose up -d
```

This starts: PostgreSQL, Redis, the Flask web server, Celery worker, and the KHSC mock server.

### 4. Start the Intellisoft middleware

```bash
cd intellisoft-middleware
# Copy and edit .env if not done already
cp .env .env.local

ENABLE_SCHEDULER=false \
.venv/bin/uvicorn app.main:app --reload --port 7000
```

Swagger UI is available at **http://localhost:7000/docs**

### 5. Start the frontend (optional)

```bash
cd open-event-frontend
yarn start
# Available at http://localhost:4200
```

---

## Running Services

| Service | Command | URL |
|---|---|---|
| Open Event stack | `cd open-event-server && docker compose up -d` | http://localhost:8080 |
| KHSC mock | Started automatically with docker compose | http://localhost:9090 |
| Middleware | `uvicorn app.main:app --reload --port 7000` | http://localhost:7000 |
| Middleware docs | — | http://localhost:7000/docs |
| Frontend | `cd open-event-frontend && yarn start` | http://localhost:4200 |

```bash
# Stop everything
cd open-event-server && docker compose down
kill $(lsof -ti:7000)   # middleware
```

---

## Middleware API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check — both APIs |
| `GET` | `/health/stats` | Live stats from KHSC + Open Event |
| `GET` | `/events?when=all\|past\|today\|upcoming` | List Open Event events by date |
| `POST` | `/import` | Import KHSC delegates → Open Event attendees |
| `POST` | `/sync/checkins` | Reconcile check-in state (KHSC is source of truth) |
| `POST` | `/sync/push-checkin` | Push a check-in from Open Event → KHSC |
| `GET` | `/khsc/delegates` | List all KHSC delegates |
| `GET` | `/khsc/delegate/{uid}` | Verify a single delegate |
| `GET` | `/khsc/search?q=` | Search KHSC delegates |
| `POST` | `/khsc/mark-paid` | Record an on-site cash payment |
| `POST` | `/khsc/offline-sync` | Bulk check-in (offline mode) |
| `GET` | `/compare/attendees` | List all Open Event attendees |
| `GET` | `/compare/diff` | Diff KHSC vs Open Event — shows mismatches |

---

## Android

The debug build reads `SERVER_HOST` and `SERVER_PORT` from the root `.env` at Gradle evaluation time:

```bash
cd open-event-organizer-android
./gradlew assembleDebug
```

Use your LAN IP for `SERVER_HOST` — the Android emulator cannot reach `localhost` on the host machine.

---

## iOS

```bash
cd open-event-organizer-ios
pod install
open EventyayOrganizer.xcworkspace
```

Always open the `.xcworkspace`, not the `.xcodeproj`.

---

## Claude Code

This repo is configured for Claude Code with:

- **`CLAUDE.md`** at the root and in each subproject — provides context per component
- **`.claude/commands/`** — project skills (slash commands):

| Command | What it does |
|---|---|
| `/health` | Check all services are reachable |
| `/import` | Import all KHSC delegates into Open Event |
| `/sync` | Reconcile check-in state |
| `/diff` | Compare KHSC vs Open Event and show mismatches |
| `/stack-up` | Start Docker stack + middleware |
| `/stack-down` | Stop all services |
| `/db-reset` | Wipe attendees and re-import (with confirmation) |
| `/lint` | Run linter for active subproject |
| `/test` | Run tests for active subproject |
| `/commit` | Stage, format, and commit changes |

- **`.claude/rules/`** — local-only coding conventions, testing rules, and code style (not committed)

---

## Docker Network

All containers share the `open-event-server_default` network. Inside the network:

| Container | Hostname | Port |
|---|---|---|
| Open Event web | `opev-web` | 8080 |
| KHSC mock | `opev-khsc-mock` / `khsc-mock` | 9090 |
| PostgreSQL | `opev-postgres` | 5432 |
| Redis | `opev-redis` | 6379 |

The middleware's `docker-compose.yml` joins this network automatically.

---

## Key Credentials (Development)

KHSC mock credentials (match `open-event-server/khsc_mock/mock_server.py`):

| Header | Value |
|---|---|
| `X-API-Username` | `admin_desk_1` |
| `Authorization` | `Bearer tok_test_khsc_mock_2026` |
| `X-Pass-Key` | `pk_test_khsc_mock_2026` |
| `X-Secret-Key` | `sk_test_khsc_mock_2026` |

Open Event admin credentials are set via `ADMIN_EMAIL` / `ADMIN_PASSWORD` in `.env`.

> Replace all credentials with production values before going live. Never commit `.env`.
