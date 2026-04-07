# System Architecture

## Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                         │
│  Android App (Kotlin/Java)    iOS App (Swift)               │
│  open-event-organizer-android  open-event-organizer-ios     │
└───────────────────────┬─────────────────────┬───────────────┘
                        │ JWT REST             │ JWT REST
                        ▼                     ▼
┌───────────────────────────────────────────────────────────────┐
│              Open Event Server  (port 8080)                   │
│              Flask 1.1 · Python 3.8 · JSON:API                │
│              open-event-server/                               │
│                                                               │
│   /v1/events        /v1/attendees       /auth/session         │
│   /v1/orders        /v1/tickets                               │
└───────┬───────────────────────┬───────────────────────────────┘
        │ SQLAlchemy            │
        ▼                       ▼
┌───────────────┐   ┌───────────────────────────────────────────┐
│  PostgreSQL   │   │   Intellisoft Middleware  (port 7000)      │
│  (port 5432)  │   │   FastAPI · Python 3.9+                    │
│  PostGIS 12   │   │   intellisoft-middleware/                  │
└───────────────┘   │                                           │
                    │  POST /import          GET /compare/diff   │
                    │  POST /sync/checkins   GET /health         │
                    └────────────┬──────────────────────────────┘
                                 │ HTTP (auth headers)
                                 ▼
                    ┌────────────────────────────┐
                    │   KHSC API  (port 9090 dev) │
                    │   khsc_mock/ (Flask mock)   │
                    │   Real: https://khsc.site/  │
                    └────────────────────────────┘
```

## Data ownership

| System | Owns |
|---|---|
| KHSC | Registrations, payments, delegate profiles |
| Open Event | Event programme, sessions, speakers, tickets |
| Both | Check-in state (KHSC is source of truth) |

## Docker network

All containers share `open-event-server_default`:

| Container | Hostname | Port |
|---|---|---|
| `opev-web` | `opev-web` | 8080 |
| `opev-postgres` | `postgres` | 5432 |
| `opev-redis` | `redis` | 6379 |
| `opev-khsc-mock` | `khsc-mock` | 9090 |
| `opev-celery` | — | — |

The middleware runs **outside Docker** on the host at port 7000 and reaches OE via `localhost:8080`.

## Check-in flow

```
1. Organiser scans QR on Android/iOS app
2. App reads barcode: {order_identifier}-{attendee_id}
3. App calls PATCH /v1/attendees/{id} with is-checked-in=true
4. (Optional) App notifies middleware → middleware calls KHSC check_in endpoint
5. KHSC and OE are now in sync
```

## Key files

| File | Purpose |
|---|---|
| `open-event-server/app/khsc/sync.py` | Import delegates, sync check-ins, push check-in to KHSC |
| `open-event-server/app/khsc/client.py` | KHSC HTTP client |
| `intellisoft-middleware/app/main.py` | FastAPI entry point, route definitions |
| `intellisoft-middleware/app/compare.py` | Diff KHSC ↔ OE attendees |
| `open-event-server/marshmallow_jsonapi_schema.py` | Patched schema (always-emit `attributes`) |
| `open-event-server/khsc_mock/mock_server.py` | Local KHSC mock (baked into Docker image) |
| `open-event-server/khsc_mock/delegates.json` | Mock delegate data (bind-mounted, editable) |
