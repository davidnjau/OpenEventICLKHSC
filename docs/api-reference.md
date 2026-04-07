# API Reference

All Open Event endpoints are at `http://localhost:8080`. Protected routes require `Authorization: JWT <token>`.

## Authentication

```bash
POST /auth/session
Content-Type: application/json

{"email": "davidnjau21@gmail.com", "password": "<from .env>"}

→ {"access_token": "eyJ..."}
```

---

## Events

```bash
# List all events
GET /v1/events?page[size]=50&sort=starts-at
Authorization: JWT <token>

# Single event
GET /v1/events/{id}
```

Key attributes: `name`, `starts-at`, `ends-at`, `state`, `identifier`, `timezone`

---

## Attendees

```bash
# List attendees for an event
GET /v1/events/{event_id}/attendees?page[size]=100&sort=firstname
Authorization: JWT <token>

# Single attendee
GET /v1/attendees/{id}

# Check in an attendee
PATCH /v1/attendees/{id}
Content-Type: application/vnd.api+json
Authorization: JWT <token>

{
  "data": {
    "type": "attendee",
    "id": "{id}",
    "attributes": {
      "is-checked-in": true,
      "checkin-times": "2026-04-07T10:00:00",
      "device-name-checkin": "iOS-App"
    }
  }
}
```

Key attributes: `firstname`, `lastname`, `email`, `phone`, `company`, `job-title`,
`gender`, `city`, `state`, `country`, `address`, `identifier`,
`is-checked-in`, `checkin-times`, `device-name-checkin`

---

## KHSC Mock (`http://localhost:9090/api/index.php`)

All requests require these headers:
```
X-API-Username: admin_desk_1
Authorization: Bearer tok_test_khsc_mock_2026
X-Pass-Key: pk_test_khsc_mock_2026
X-Secret-Key: sk_test_khsc_mock_2026
```

```bash
# Verify a delegate
GET ?endpoint=verify_delegate&uid=CONF-1001

# Check in a delegate
POST ?endpoint=check_in
{"uid": "CONF-1001"}

# Search delegates
GET ?endpoint=search_delegate&q=james

# Offline bulk sync
POST ?endpoint=offline_sync
{"uids": ["CONF-1001", "CONF-1002"]}

# Mark paid on-site
POST ?endpoint=mark_paid_onsite
{"uid": "CONF-1005", "payment_method": "On-Site Cash"}

# Event stats
GET ?endpoint=event_stats

# Sandbox connectivity test
POST ?endpoint=sandbox_test
```

---

## Intellisoft Middleware (`http://localhost:7000`)

```bash
# Health check
GET /health

# Import KHSC delegates into Open Event
POST /import
{"uids": ["CONF-1001"]}    # omit uids to import all

# Sync check-in state (KHSC → OE)
POST /sync/checkins

# Diff KHSC vs OE
GET /compare/diff

# Swagger UI
GET /docs
```
