# KHSC ↔ Open Event Integration

## What KHSC is

KHSC (Kenya Health Sciences Conference) is an external conference registration system at `https://khsc.site/api/index.php`. It handles:
- Delegate registration and profiles
- Payment processing (M-Pesa, Bank Transfer, Credit Card, On-Site Cash)
- Check-in state tracking

Open Event handles event programme management. The two systems must stay in sync.

## Field mapping

| KHSC field | Open Event field | Notes |
|---|---|---|
| `unique_id` | `khsc_uid` (TicketHolder) | KHSC's primary identifier |
| `first_name` + `last_name` | `firstname` + `lastname` | Split on space for single-name delegates |
| `email` | `email` | |
| `organization` | `company` | `None` if empty, never `""` |
| `category` | `job_title` | e.g. "Doctor", "Nurse", "Researcher" |
| `gender` | `gender` | |
| `phone` | `phone` | |
| `address` | `address` | |
| `city` | `city` | |
| `state` | `state` | |
| `country` | `country` | ISO 2-letter code e.g. "KE" |
| `payment_status` | Order `status` | "Paid" → `completed`, else `pending` |
| `amount_paid` | Order `amount` | Float |
| `payment_method` | Order `paid_via` | |
| `is_checked_in` | `is_checked_in` | KHSC is source of truth |

## Three sync operations

### 1. `import_delegates(event_id, uids)`
`open-event-server/app/khsc/sync.py`

- Fetches each UID from KHSC via `verify_delegate`
- Creates or updates a `TicketHolder` (attendee) in OE
- Creates an `Order` for new attendees
- If no ticket exists for the event, auto-creates a free "KHSC Delegate" ticket

Trigger: `POST http://localhost:7000/import`

### 2. `sync_checkins(event_id)`
`open-event-server/app/khsc/sync.py`

- Iterates all OE attendees with a `khsc_uid`
- Calls KHSC `verify_delegate` for each
- Updates `is_checked_in` if different (KHSC wins)

Trigger: `POST http://localhost:7000/sync/checkins`

### 3. `push_checkin_to_khsc(uid)`
`open-event-server/app/khsc/sync.py`

- Called when check-in is recorded in OE (e.g. via Android/iOS scan)
- Calls KHSC `check_in` endpoint to mirror the state

## QR code format

The barcodes on KHSC delegate badges encode:
```
{order_identifier}-{attendee_id}
```
Example: `e87b03-1`

The Android and iOS apps parse this to look up the attendee and trigger the PATCH check-in call.

## Mock server vs production

| | Mock (`khsc_mock/`) | Production |
|---|---|---|
| URL | `http://localhost:9090/api/index.php` | `https://khsc.site/api/index.php` |
| Auth | Fixed test headers | Real credentials from KHSC admin |
| Data | `delegates.json` (bind-mounted, editable) | Live KHSC DB |
| `mock_server.py` | Baked into Docker image | N/A |

**To change mock data:** edit `open-event-server/khsc_mock/delegates.json` — changes take effect immediately (bind-mounted volume, no rebuild needed).

**To change mock server logic:** edit `mock_server.py`, then `docker compose build khsc-mock && docker compose up -d khsc-mock`.
