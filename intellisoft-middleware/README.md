# Intellisoft Middleware

Integration layer that bridges the **KHSC conference management system** and the **Open Event organizer platform**.

---

## What it does

```
KHSC System                    Intellisoft Middleware              Open Event
(delegates.json / API)  ◄────►  (this service, port 7000)  ◄────►  (port 8080)
```

| Job | Trigger | What happens |
|-----|---------|-------------|
| **Import delegates** | Every 5 min (+ manual) | Fetches all KHSC registered delegates → creates/updates attendees in Open Event |
| **Sync check-ins** | Every 2 min (+ manual) | KHSC check-in state → copied into Open Event. KHSC is the source of truth |
| **Push check-in** | On demand (Android app) | A check-in recorded in Open Event → forwarded to KHSC |

---

## Architecture

```
intellisoft-middleware/
├── app/
│   ├── main.py              # FastAPI entry point, Swagger docs, middleware
│   ├── scheduler.py         # APScheduler background jobs (import + sync)
│   ├── core/
│   │   ├── config.py        # All settings read from .env
│   │   └── logging.py       # Coloured console + rotating file logging
│   ├── clients/
│   │   ├── khsc.py          # KHSC API client (4-header auth, all endpoints)
│   │   └── open_event.py    # Open Event API client (JWT auth, auto-refresh)
│   └── routes/
│       ├── import_.py       # POST /import
│       ├── sync.py          # POST /sync/checkins  POST /sync/push-checkin
│       ├── khsc.py          # GET /khsc/delegate/:uid  GET /khsc/search  etc.
│       └── health.py        # GET /health  GET /health/stats
├── logs/
│   └── middleware.log       # Rotating log file (10 MB × 5 backups)
├── .env                     # Configuration (see below)
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Quick start

### 1. Prerequisites

The Open Event stack must already be running:

```bash
cd open-event-server
docker-compose up -d
```

### 2. Configure

Copy and edit the environment file:

```bash
cd intellisoft-middleware
cp .env .env.local   # optional — .env is already pre-filled for local dev
```

Key variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `KHSC_API_URL` | KHSC API endpoint | `http://khsc-mock:9090/api/index.php` |
| `KHSC_API_USERNAME` | KHSC auth username | `admin_desk_1` |
| `KHSC_AUTHORIZATION` | KHSC Bearer token | `Bearer tok_test_...` |
| `KHSC_PASS_KEY` | KHSC pass key | `pk_test_...` |
| `KHSC_SECRET_KEY` | KHSC secret key | `sk_test_...` |
| `OPEN_EVENT_BASE_URL` | Open Event API URL | `http://opev-web:8080/v1` |
| `OPEN_EVENT_ADMIN_EMAIL` | Open Event admin email | — |
| `OPEN_EVENT_ADMIN_PASSWORD` | Open Event admin password | — |
| `KHSC_EVENT_ID` | Event ID to sync delegates into | `1` |
| `IMPORT_INTERVAL_SECONDS` | How often to import | `300` (5 min) |
| `SYNC_INTERVAL_SECONDS` | How often to sync check-ins | `120` (2 min) |
| `LOG_LEVEL` | `DEBUG` / `INFO` / `WARNING` / `ERROR` | `INFO` |
| `ENABLE_SCHEDULER` | Enable background jobs | `true` |

### 3. Run with Docker (recommended)

```bash
docker-compose up -d
```

Check it's running:

```bash
curl http://localhost:7000/health
```

### 4. Run locally (development)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Point to local services instead of Docker hostnames
OPEN_EVENT_BASE_URL=http://localhost:8080/v1 \
KHSC_API_URL=http://localhost:9090/api/index.php \
uvicorn app.main:app --reload --port 7000
```

---

## API Reference

Interactive Swagger docs are available at **http://localhost:7000/docs** when the service is running.

### Import delegates

```bash
# Import all KHSC delegates into Open Event event 1
curl -X POST http://localhost:7000/import \
  -H "Content-Type: application/json" \
  -d '{"event_id": 1}'

# Import specific UIDs only
curl -X POST http://localhost:7000/import \
  -H "Content-Type: application/json" \
  -d '{"event_id": 1, "uids": ["CONF-1001", "CONF-1002"]}'
```

Response:
```json
{
  "event_id": 1,
  "created": 10,
  "updated": 2,
  "failed": [],
  "message": "Import complete. Created: 10, Updated: 2, Failed: 0"
}
```

### Sync check-ins

```bash
curl -X POST http://localhost:7000/sync/checkins \
  -H "Content-Type: application/json" \
  -d '{"event_id": 1}'
```

### Push a check-in from Open Event → KHSC

```bash
curl -X POST http://localhost:7000/sync/push-checkin \
  -H "Content-Type: application/json" \
  -d '{"uid": "CONF-1001"}'
```

### Health check

```bash
curl http://localhost:7000/health
```

```json
{
  "status": "healthy",
  "timestamp": "2026-04-02T10:30:00+00:00",
  "khsc_api": {"status": "ok", "message": "KHSC API reachable"},
  "open_event_api": {"status": "ok", "message": "Open Event API reachable"},
  "event_id": 1
}
```

### Scheduler status

```bash
curl http://localhost:7000/scheduler
```

```json
[
  {"id": "import_delegates", "name": "Import KHSC delegates → Open Event", "next_run_utc": "2026-04-02T10:35:00+00:00"},
  {"id": "sync_checkins",    "name": "Sync check-ins KHSC ↔ Open Event",   "next_run_utc": "2026-04-02T10:32:00+00:00"}
]
```

### KHSC direct endpoints

```bash
# Look up a delegate
curl http://localhost:7000/khsc/delegate/CONF-1001

# Search delegates
curl "http://localhost:7000/khsc/search?q=james"

# Mark paid on-site
curl -X POST http://localhost:7000/khsc/mark-paid \
  -H "Content-Type: application/json" \
  -d '{"uid": "CONF-1001", "payment_method": "M-Pesa"}'
```

---

## Logging

Logs are written in two places simultaneously:

### Console (coloured)

```
2026-04-02 10:23:45.123 | INFO     | app.scheduler:job_import_delegates:44 | [SCHEDULER] Starting delegate import job for event 1
2026-04-02 10:23:45.891 | INFO     | app.scheduler:job_import_delegates:56 | [SCHEDULER] Import job complete — created=2 updated=10 failed=0
2026-04-02 10:25:45.003 | INFO     | app.scheduler:job_sync_checkins:72    | [SCHEDULER] Sync job complete — synced=3 already_in_sync=9 failed=0
2026-04-02 10:30:01.445 | WARNING  | app.routes.health:health_check:42     | KHSC health check failed: KHSC network error
2026-04-02 10:30:01.446 | ERROR    | app.routes.health:health_check:50     | Health check result: degraded (KHSC=error, OE=ok)
```

### File (`logs/middleware.log`)

Same format, no colours, rotates at 10 MB with 5 backups kept. Mount the `logs/` directory from Docker to persist across container restarts.

To tail the log in real-time:

```bash
tail -f logs/middleware.log

# Or from Docker
docker logs -f intellisoft-middleware
```

To increase verbosity (shows every HTTP call):

```bash
LOG_LEVEL=DEBUG uvicorn app.main:app --port 7000
```

---

## How the data flows

### Delegate import

```
1. Middleware calls  GET  KHSC /api/index.php?endpoint=search_delegate&q= 
   → gets list of all UIDs

2. Middleware calls  POST open-event-server /v1/khsc/import
   body: { event_id: 1, uids: ["CONF-1001", ...] }

3. Open Event server calls KHSC verify_delegate for each UID
   → creates/updates TicketHolder (attendee) + Order in its PostgreSQL DB

4. Android organizer app calls GET /v1/events/1/attendees
   → displays the imported delegates as attendees
```

### Check-in sync

```
1. Scheduler (every 2 min) calls POST /v1/khsc/sync-checkins
2. Open Event server queries all attendees with a khsc_uid
3. For each: calls KHSC verify_delegate
4. If is_checked_in differs → updates Open Event attendee record
5. Android app sees updated check-in state on next refresh
```

### Push check-in (Android → KHSC)

```
1. Organizer swipes an attendee to check them in (Android app)
2. Android app calls PATCH /v1/attendees/:id  on Open Event
3. Open Event records the check-in locally
4. Android (or middleware) calls POST /v1/khsc/push-checkin  { uid: "CONF-1001" }
5. Middleware calls KHSC POST check_in  { uid: "CONF-1001" }
6. KHSC records the check-in
```

---

## Docker network

The middleware joins the `open-event-server_default` network that is created by the Open Event `docker-compose.yml`. This lets it reach:

| Hostname | Service |
|----------|---------|
| `opev-web` | Open Event API (port 8080) |
| `khsc-mock` | KHSC mock server (port 9090) |
| `opev-postgres` | PostgreSQL (internal only) |

If the network name is different on your machine, check with:

```bash
docker network ls | grep open-event
```

Then update `docker-compose.yml` → `networks.opev_default.name`.
