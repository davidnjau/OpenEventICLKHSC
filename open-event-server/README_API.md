# Open Event Server — Local API Guide

Base URL: `http://localhost:8080/v1`

All endpoints follow the **JSON:API v1.0** specification.

---

## Required Headers

```
Content-Type: application/vnd.api+json
Authorization: JWT <access_token>
```

---

## 1. Authentication

### Login

`POST /v1/auth/login`

```json
{
  "email": "admin@example.com",
  "password": "password"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

Use the `access_token` as `Authorization: JWT <token>` on subsequent requests.

### Refresh Token

`POST /v1/auth/token/refresh`

Requires `Authorization: JWT <refresh_token>`.

### Change Password

`POST /v1/auth/change-password`

Requires a fresh login token (`POST /v1/auth/fresh-login` first).

```json
{
  "old-password": "current_password",
  "new-password": "new_secure_password"
}
```

### Logout

`POST /v1/auth/logout`

### Reset Password (Unauthenticated)

Request reset: `POST /v1/auth/reset-password`
```json
{ "email": "user@example.com" }
```

Complete reset: `PATCH /v1/auth/reset-password`
```json
{
  "token": "<reset_token_from_email>",
  "password": "new_secure_password"
}
```

---

## 2. Users

### Register a New User

`POST /v1/users`

```json
{
  "data": {
    "type": "user",
    "attributes": {
      "email": "jane@example.com",
      "password": "securePassword123",
      "first-name": "Jane",
      "last-name": "Doe"
    }
  }
}
```

**Required:** `email`, `password` (min 8 characters)

**Optional attributes:**
| Field | Type | Notes |
|---|---|---|
| `first-name` | string | |
| `last-name` | string | |
| `public-name` | string | Display name |
| `is-profile-public` | boolean | Default: `false` |
| `details` | string | Bio |
| `contact` | string | |
| `facebook-url`, `twitter-url`, `instagram-url`, `google-plus-url` | string | Social links |

### Get / Update User

```
GET    /v1/users/<id>
PATCH  /v1/users/<id>
GET    /v1/users   (admin only)
```

---

## 3. Events

### Create Event

`POST /v1/events`

```json
{
  "data": {
    "type": "event",
    "attributes": {
      "name": "KHSC 2026",
      "starts-at": "2026-05-05T08:00:00+03:00",
      "ends-at": "2026-05-08T17:00:00+03:00",
      "timezone": "Africa/Nairobi",
      "location-name": "Pride Inn Mombasa",
      "description": "Annual health sciences conference",
      "online": false,
      "state": "draft",
      "privacy": "public"
    }
  }
}
```

**Required:** `name`, `starts-at`, `ends-at`, `timezone`

> **Note:** `state` defaults to `"draft"` when omitted. Omitting it is safe.

**Optional attributes:**
| Field | Type | Notes |
|---|---|---|
| `description` | string | |
| `location-name` | string | Venue name |
| `latitude` / `longitude` | float | -90/90, -180/180 |
| `online` | boolean | Default: `false` |
| `state` | string | `"draft"` or `"published"` |
| `privacy` | string | `"public"` or `"private"` |
| `logo-url` | string | URL |
| `external-event-url` | string | URL |
| `ticket-url` | string | External ticketing URL |
| `payment-currency` | string | ISO 4217 e.g. `"KES"`, `"USD"` |
| `payment-country` | string | |
| `code-of-conduct` | string | |
| `refund-policy` | string | `"no-refunds"`, `"1-day"`, etc. |
| `is-sessions-speakers-enabled` | boolean | Default: `false` |
| `is-ticket-form-enabled` | boolean | Default: `true` |
| `is-map-shown` | boolean | Default: `false` |
| `is-badges-enabled` | boolean | Default: `true` |
| `show-remaining-tickets` | boolean | Default: `false` |
| `can-pay-by-stripe`, `can-pay-by-paypal`, `can-pay-by-bank`, `can-pay-by-cheque`, `can-pay-onsite`, `can-pay-by-invoice` | boolean | Payment methods |

**Read-only response fields:** `id`, `identifier`, `created-at`, `thumbnail-image-url`, `large-image-url`, `pentabarf-url`, `ical-url`, `xcal-url`

### Get / Update / Delete Event

```
GET    /v1/events/<id>
GET    /v1/events/<identifier>   (slug-style identifier also works)
GET    /v1/events/upcoming
PATCH  /v1/events/<id>
DELETE /v1/events/<id>
GET    /v1/events                (list all)
```

### Publish an Event

`PATCH /v1/events/<id>`

```json
{
  "data": {
    "type": "event",
    "id": "1",
    "attributes": {
      "state": "published"
    }
  }
}
```

---

## 4. Tickets

### Create Ticket

`POST /v1/tickets`

```json
{
  "data": {
    "type": "ticket",
    "attributes": {
      "name": "Early Bird",
      "type": "paid",
      "price": 2500.00,
      "quantity": 100,
      "sales-starts-at": "2026-04-01T00:00:00+03:00",
      "sales-ends-at": "2026-05-01T00:00:00+03:00",
      "min-order": 1,
      "max-order": 5,
      "is-hidden": false,
      "description": "Limited early bird tickets"
    },
    "relationships": {
      "event": {
        "data": { "type": "event", "id": "1" }
      }
    }
  }
}
```

**Required:** `name`, `type`, `sales-starts-at`, `sales-ends-at`, `event` relationship

**Ticket types:** `"free"` | `"paid"` | `"donation"`

**Optional attributes:**
| Field | Type | Notes |
|---|---|---|
| `price` | float | Required if type is `"paid"`, must be > 0 |
| `min-price` / `max-price` | float | For `"donation"` type |
| `quantity` | integer | |
| `min-order` / `max-order` | integer | Per-order limits |
| `description` | string | |
| `is-hidden` | boolean | Default: `false` |
| `is-fee-absorbed` | boolean | Absorb platform fee |
| `is-checkin-restricted` | boolean | Default: `true` |
| `auto-checkin-enabled` | boolean | Default: `false` |

**Validation rules:**
- `sales-starts-at` must be before `sales-ends-at`
- `max-order` must be >= `min-order`
- `quantity` must be >= `max-order`

### Get / Update Tickets

```
GET    /v1/tickets/<id>
GET    /v1/events/<event_id>/tickets
PATCH  /v1/tickets/<id>
DELETE /v1/tickets/<id>
GET    /v1/events/<event_id>/tickets/availability
```

---

## 5. Orders

### Create Order

`POST /v1/orders/create-order`

> This is a custom JSON endpoint (not JSON:API). Use `Content-Type: application/json`.

```json
{
  "tickets": [
    { "id": "1", "quantity": 2 },
    { "id": "2", "quantity": 1 }
  ],
  "discount-code": "DISC123"
}
```

**Response** (JSON:API):
```json
{
  "data": {
    "id": "...",
    "type": "order",
    "attributes": {
      "identifier": "ABC12345",
      "amount": 5000.00,
      "payment-mode": "free",
      "status": "initializing"
    }
  }
}
```

### Calculate Order Amount (Before Creating)

`POST /v1/orders/calculate-amount`

```json
{
  "tickets": [
    { "id": "1", "quantity": 2 }
  ],
  "discount-code": "DISC123"
}
```

### Get / Update Order

```
GET    /v1/orders/<identifier>
PATCH  /v1/orders/<identifier>
GET    /v1/orders                        (admin/organizer)
GET    /v1/events/<event_id>/orders
GET    /v1/users/<user_id>/orders
```

**Order statuses:** `initializing` → `pending` → `completed` / `cancelled` / `expired`

**Payment modes:** `"free"`, `"stripe"`, `"paypal"`, `"bank"`, `"cheque"`, `"onsite"`, `"invoice"`

---

## 6. Attendees

Attendees are automatically created when an order is placed. They can also be created directly.

### Create Attendee

`POST /v1/attendees`

```json
{
  "data": {
    "type": "attendee",
    "attributes": {
      "firstname": "John",
      "lastname": "Kamau",
      "email": "john.kamau@example.com",
      "address": "P.O. Box 12345",
      "city": "Nairobi",
      "country": "Kenya",
      "phone": "+254712345678",
      "job-title": "Researcher",
      "company": "KNH",
      "accept-receive-emails": true,
      "is-consent-of-refund-policy": true
    },
    "relationships": {
      "ticket": {
        "data": { "type": "ticket", "id": "1" }
      },
      "order": {
        "data": { "type": "order", "id": "order_identifier" }
      }
    }
  }
}
```

**Optional attributes:**
| Field | Type |
|---|---|
| `firstname`, `lastname` | string |
| `email` | string |
| `address`, `city`, `state`, `country` | string |
| `phone`, `job-title`, `company` | string |
| `gender` | string |
| `website`, `twitter`, `facebook`, `github`, `linkedin`, `instagram` | URL |
| `accept-video-recording`, `accept-share-details`, `accept-receive-emails` | boolean |
| `is-consent-of-refund-policy` | boolean |
| `attendee-notes` | string |
| `complex-field-values` | object | Custom form fields |

**Read-only:** `identifier`, `pdf-url`, `is-checked-in`, `checkin-times`, `is-badge-printed`

### Get / List Attendees

```
GET  /v1/attendees/<id>
GET  /v1/events/<event_id>/attendees
GET  /v1/orders/<order_identifier>/attendees
```

---

## 7. Sessions

### Create Session

`POST /v1/sessions`

```json
{
  "data": {
    "type": "session",
    "attributes": {
      "title": "Future of Digital Health in Kenya",
      "short-abstract": "Exploring digital health innovations",
      "long-abstract": "This session covers...",
      "level": "intermediate",
      "language": "en",
      "starts-at": "2026-05-06T10:00:00+03:00",
      "ends-at": "2026-05-06T11:00:00+03:00",
      "state": "draft",
      "slides-url": "https://example.com/slides.pdf"
    },
    "relationships": {
      "event": {
        "data": { "type": "event", "id": "1" }
      }
    }
  }
}
```

**Required:** `title`, `starts-at`, `ends-at`, `event` relationship

**Optional attributes:**
| Field | Type | Notes |
|---|---|---|
| `subtitle` | string | |
| `short-abstract` | string | |
| `long-abstract` | string | |
| `level` | string | `"beginner"`, `"intermediate"`, `"advanced"` |
| `language` | string | e.g. `"en"`, `"sw"` |
| `comments` | string | Reviewer notes |
| `slides-url`, `video-url`, `audio-url` | URL | |
| `state` | string | `"draft"`, `"pending"`, `"accepted"`, `"confirmed"`, `"rejected"`, `"canceled"`, `"withdrawn"` |

### Get / Update Sessions

```
GET    /v1/sessions/<id>
PATCH  /v1/sessions/<id>
DELETE /v1/sessions/<id>
GET    /v1/events/<event_id>/sessions
```

---

## 8. Speakers

### Create Speaker

`POST /v1/speakers`

```json
{
  "data": {
    "type": "speaker",
    "attributes": {
      "name": "Dr. Aisha Mohamed",
      "email": "aisha@example.com",
      "short-biography": "Consultant Physician, KNH",
      "organisation": "Kenyatta National Hospital",
      "country": "Kenya",
      "city": "Nairobi",
      "mobile": "+254700000000",
      "position": "Consultant Physician",
      "is-featured": false
    },
    "relationships": {
      "event": {
        "data": { "type": "event", "id": "1" }
      }
    }
  }
}
```

**Required:** `name`, `event` relationship

**Optional attributes:**
| Field | Type |
|---|---|
| `email` | string |
| `short-biography`, `long-biography` | string |
| `speaking-experience` | string |
| `organisation`, `position` | string |
| `country`, `city`, `address` | string |
| `mobile` | string |
| `website`, `twitter`, `facebook`, `github`, `linkedin`, `instagram` | URL |
| `gender` | string |
| `is-featured` | boolean |

### Get / Update Speakers

```
GET    /v1/speakers/<id>
PATCH  /v1/speakers/<id>
DELETE /v1/speakers/<id>
GET    /v1/events/<event_id>/speakers
```

---

## Typical Workflows

### Workflow A — Create and Publish an Event with Paid Tickets

```
1. POST /v1/auth/login              → get access_token
2. POST /v1/events                  → create event (state: "draft")
3. POST /v1/tickets                 → add ticket(s) to the event
4. PATCH /v1/events/<id>            → set state: "published"
```

### Workflow B — Register an Attendee

```
1. POST /v1/auth/login                      → get access_token
2. POST /v1/orders/create-order             → place order with ticket IDs
3. GET  /v1/orders/<identifier>/attendees   → retrieve created attendees
4. PATCH /v1/attendees/<id>                 → fill in attendee details
```

### Workflow C — Add Sessions and Speakers to an Event

```
1. POST /v1/auth/login       → get access_token
2. POST /v1/speakers         → create speaker (linked to event)
3. POST /v1/sessions         → create session (linked to event)
4. PATCH /v1/sessions/<id>   → link speaker relationship
```

---

## JSON:API Response Structure

**Single resource:**
```json
{
  "data": {
    "id": "1",
    "type": "event",
    "attributes": { "name": "KHSC 2026", ... },
    "relationships": { "tickets": { "data": [...] } }
  }
}
```

**List:**
```json
{
  "data": [ ... ],
  "meta": { "count": 25 },
  "links": { "self": "...", "next": "...", "prev": "..." }
}
```

**Error:**
```json
{
  "errors": [
    {
      "status": 422,
      "title": "Unprocessable Entity",
      "detail": "starts-at must be before ends-at"
    }
  ]
}
```

---

## Docker Setup Summary

The local server runs four containers managed by Docker Compose.

| Container | Role | Port |
|---|---|---|
| `opev-web` | Flask API server | `8080` |
| `opev-celery` | Background task worker | — |
| `opev-postgres` | PostgreSQL + PostGIS | `5432` (internal) |
| `opev-redis` | Redis (cache + queue) | `6379` (internal) |

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# View logs
docker-compose logs -f web

# Restart web after code changes
docker-compose restart web
```
