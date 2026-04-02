# INTELLISOFT.md — Integration Handoff

This document is written specifically for the **Intellisoft team**. It explains the
full context of what you are building, how the local development environment works,
and exactly where your code lives.

---

## Background

There are two independent systems that need to be linked:

| System | What it owns | Run by |
|--------|-------------|--------|
| **KHSC** (`khsc.site`) | Delegate registration, payment records, conference check-in | KHSC (external) |
| **Open Event** (this repo) | Event management, organizer dashboard, Android check-in app | ICL / this team |

KHSC is the **source of truth for delegates**. Open Event is the **organizer-facing platform**. Your job is to build the bridge — a layer that pulls KHSC data into Open Event so that:

- Delegates registered in KHSC appear as attendees in Open Event
- When a delegate is checked in via either system, both sides reflect it
- Payment status flows from KHSC into Open Event orders
- The organizer dashboard in Open Event shows accurate live stats

---

## Setting Up Your Local Environment

### 1. Clone all three repos into the same parent folder

```
open-event/
├── open-event-server          ← Flask API backend
├── open-event-frontend        ← Ember.js organizer web app
└── open-event-organizer-android  ← Android check-in app
```

### 2. Copy and fill in the shared config

```bash
cd open-event
cp .env.example .env
```

Open `.env`. The values you care about for integration work are at the bottom in the
**KHSC Integration** section — they already contain the mock credentials so you can
start immediately without waiting for real keys from KHSC.

### 3. Run the setup script

```bash
python3 setup.py
```

This will:
- Detect your machine's LAN IP and write it everywhere it is needed
- Generate a Flask `SECRET_KEY`
- Propagate all config into each repo
- Ask if you want to start the Open Event server + frontend (say `y`)
- Prompt for an admin email and password, create the superuser, and mark it as
  verified (email delivery is disabled locally)

After this you will have:

| Service | URL |
|---------|-----|
| Open Event API | `http://localhost:8080/v1/` |
| Open Event frontend | `http://localhost:4200` |

### 4. Start the KHSC mock server (separate terminal)

```bash
python3 setup_mock_server_khsc.py
```

| Service | URL |
|---------|-----|
| KHSC mock API | `http://localhost:9090/api/index.php` |

The mock server is a local simulation of `https://khsc.site/api/index.php`. It has
12 pre-loaded delegates across three payment states and check-in states. State is
persisted to `open-event-server/khsc_mock/delegates.json` across requests.

To reset delegate state to the original data at any time:

```bash
python3 setup_mock_server_khsc.py --reset
```

---

## The KHSC API

### Authentication

Every request to KHSC must include all four headers:

```
X-API-Username:  admin_desk_1
Authorization:   Bearer tok_test_khsc_mock_2026
X-Pass-Key:      pk_test_khsc_mock_2026
X-Secret-Key:    sk_test_khsc_mock_2026
```

These values live in the root `.env` as `KHSC_API_USERNAME`, `KHSC_AUTHORIZATION`,
`KHSC_PASS_KEY`, and `KHSC_SECRET_KEY`. Always read them from the environment — never
hardcode them.

When moving to production, the KHSC admin will provide real keys. Swapping them in
`.env` is the only change needed.

### Endpoints

#### Verify a delegate
```
GET /api/index.php?endpoint=verify_delegate&uid=CONF-1001
```
Returns delegate details including `payment_status`, `is_checked_in`, and a computed
`can_enter` flag (`true` only when paid and not yet checked in).

#### Check in a delegate
```
POST /api/index.php?endpoint=check_in
{"uid": "CONF-1001"}
```
Marks the delegate as checked in on the KHSC side. Returns `403` if unpaid, `409` if
already checked in.

#### Search delegates
```
GET /api/index.php?endpoint=search_delegate&q=mwangi
```
Searches across name, email, organization, and UID. Used to find a delegate when the
QR code is damaged or unavailable.

#### Bulk offline sync
```
POST /api/index.php?endpoint=offline_sync
{"uids": ["CONF-1003", "CONF-1004", "CONF-1005"]}
```
For reconciling check-ins that were recorded offline (e.g. the Android app had no
internet). Send all pending UIDs in one call.

#### Mark paid on-site
```
POST /api/index.php?endpoint=mark_paid_onsite
{"uid": "CONF-1005", "payment_method": "On-Site Cash"}
```
Settles payment for delegates who pay at the door. `payment_method` is a free string
(e.g. `"On-Site Cash"`, `"On-Site PDQ Card"`).

#### Live event stats
```
GET /api/index.php?endpoint=event_stats
```
Returns `total_registered`, `total_paid`, `total_checked_in`, `total_unpaid`,
`total_revenue`.

### Delegate data shape

```json
{
  "unique_id":      "CONF-1001",
  "first_name":     "James",
  "last_name":      "Mwangi",
  "email":          "james.mwangi@knh.or.ke",
  "organization":   "Kenyatta National Hospital",
  "category":       "Doctor",
  "payment_status": "Paid",
  "is_checked_in":  false,
  "payment_method": null,
  "amount_paid":    10000
}
```

### Known gaps in KHSC documentation

`API_Documentation_KHSC.docx` (in `open-event-server/`) is the official contract
document from KHSC. However, KHSC has not yet provided complete documentation for
all edge cases. Where the document is silent, **treat the mock server as the reference
implementation**. Flag any discrepancy between the two to the project lead before
building against it, as the real KHSC API may differ.

---

## The Open Event API

Base URL (local): `http://localhost:8080/v1/`

All requests require a JWT `Authorization: JWT <token>` header. Obtain a token:

```
POST /auth/session
{"email": "your@email.com", "password": "yourpassword"}
```

Response contains `access_token`. Include it as `Authorization: JWT <access_token>`
on every subsequent request.

### Endpoints your integration will use

#### List attendees for an event
```
GET /v1/events/{event_id}/attendees
```
Returns all `TicketHolder` records for the event.
Key fields: `id`, `firstname`, `lastname`, `email`, `is-checked-in`, `checkin-times`,
`device-name-checkin`.

#### Get a single attendee
```
GET /v1/attendees/{id}
```

#### Update an attendee (mark checked in)
```
PATCH /v1/attendees/{id}
Content-Type: application/vnd.api+json

{
  "data": {
    "type": "attendee",
    "id": "123",
    "attributes": {
      "is-checked-in": true,
      "checkin-times": "2026-04-01T09:00:00",
      "device-name-checkin": "KHSC-Sync"
    }
  }
}
```

#### Create an attendee (import from KHSC)
```
POST /v1/attendees
```
Required relationships: `event`, `ticket`, `order`.
Map KHSC fields as follows:

| KHSC field | Open Event field |
|---|---|
| `first_name` | `firstname` |
| `last_name` | `lastname` |
| `email` | `email` |
| `unique_id` | `reference` (use this to look up the attendee later) |
| `organization` | `company` |
| `payment_status == "Paid"` | order `status: completed` |
| `is_checked_in` | `is-checked-in` |

#### Check attendee state
```
GET /v1/states?event_id={event_id}&attendee_id={attendee_id}
```
Returns `is_registered` and `register_times`.

#### Check-in stats for an event
```
GET /v1/user-check-in/stats/event/{event_id}
```
Returns `total_attendee`, `total_registered`, `total_not_checked_in`, and per-session
/ per-track breakdowns. This is what feeds the organizer dashboard.

---

## What You Are Building

Your integration lives in a new directory inside the server repo:

```
open-event-server/
└── app/
    └── khsc/               ← create this
        ├── __init__.py
        ├── client.py       ← KHSC HTTP client (reads credentials from env)
        ← sync.py          ← import + sync logic
        └── routes.py       ← Flask blueprint exposing sync endpoints
```

### client.py — KHSC HTTP client

A thin wrapper around the KHSC API. Reads all four auth headers from the environment.
Every other file goes through this client — nothing else should know how KHSC auth works.

```python
import os, requests

class KHSCClient:
    def __init__(self):
        self.base_url = os.environ['KHSC_API_URL']
        self.headers = {
            'X-API-Username': os.environ['KHSC_API_USERNAME'],
            'Authorization':  os.environ['KHSC_AUTHORIZATION'],
            'X-Pass-Key':     os.environ['KHSC_PASS_KEY'],
            'X-Secret-Key':   os.environ['KHSC_SECRET_KEY'],
        }

    def verify_delegate(self, uid): ...
    def check_in(self, uid): ...
    def search(self, q): ...
    def offline_sync(self, uids): ...
    def mark_paid_onsite(self, uid, payment_method): ...
    def event_stats(self): ...
```

### sync.py — import and sync logic

The core business logic. Three operations:

1. **`import_delegates(event_id)`**
   Pull all delegates from KHSC via `search_delegate` (or a full-list endpoint if
   KHSC provides one), then for each delegate either create or update the corresponding
   Open Event attendee. Store `unique_id` in the attendee's `reference` field so you
   can always look it up later.

2. **`sync_checkins(event_id)`**
   For each attendee in Open Event whose `reference` matches a KHSC `unique_id`,
   call `verify_delegate` and reconcile `is_checked_in` between the two systems.
   Decide on the conflict rule with the project lead (KHSC wins? most-recent wins?).

3. **`push_checkin_to_khsc(uid)`**
   Called when a check-in is recorded in Open Event (e.g. via the Android app). Calls
   KHSC `check_in` so both systems stay in sync.

### routes.py — Flask blueprint

Expose sync operations as internal API endpoints so the frontend or a scheduled job
can trigger them:

```
POST /v1/khsc/import?event_id={id}    ← import all delegates from KHSC
POST /v1/khsc/sync?event_id={id}      ← reconcile check-in state
POST /v1/khsc/push-checkin            ← push a single check-in to KHSC
GET  /v1/khsc/stats                   ← proxy KHSC event_stats
```

Register the blueprint in `app/instance.py` alongside the existing blueprints.

---

## Running Tests Against the Mock

```bash
# Terminal 1 — start mock server
python3 setup_mock_server_khsc.py

# Terminal 2 — run the built-in mock test suite
python3 setup_mock_server_khsc.py --test

# Terminal 2 — run your own integration tests
cd open-event-server
pytest tests/ -k khsc -v
```

Write your tests in `open-event-server/tests/all/integration/khsc/`. Point them at
`http://localhost:9090` (mock) by default, controlled via the `KHSC_API_URL` env var.

---

## Credential Handoff for Production

When KHSC provides real production keys, update only the five `KHSC_*` values in the
root `.env` and re-run `python3 setup.py`. Nothing else changes.

```
KHSC_API_URL=https://khsc.site/api/index.php
KHSC_API_USERNAME=<real username>
KHSC_AUTHORIZATION=Bearer <real token>
KHSC_PASS_KEY=<real pass key>
KHSC_SECRET_KEY=<real secret key>
```

---

## Key Contacts

| Role | Responsibility |
|------|---------------|
| Project lead (ICL) | Overall direction, KHSC relationship, Open Event architecture |
| Intellisoft | KHSC ↔ Open Event integration layer (`app/khsc/`) |
| KHSC admin | Production credentials, API clarifications, `API_Documentation_KHSC.docx` |
