# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Open Event Server** is a Flask-based REST API backend for event management (conferences, concerts, etc.). It follows the [JSON:API specification](https://jsonapi.org/) and uses PostgreSQL with SQLAlchemy.

- **Framework:** Flask 1.1.2 with flask-rest-jsonapi (FOSSASIA custom fork)
- **Python:** 3.8 only (not compatible with 3.9+)
- **Database:** PostgreSQL with PostGIS + SQLAlchemy 1.3.x (pinned)
- **Task Queue:** Celery 5 with Redis
- **Package Manager:** Poetry

## Commands

### Setup
```bash
# Install dependencies
poetry install --with dev

# Set up pre-commit hooks
poetry run pre-commit install

# Create databases (requires PostgreSQL running)
psql -d postgres -c "CREATE USER open_event_user WITH PASSWORD 'opev_pass';"
psql -d postgres -c "CREATE DATABASE oevent WITH OWNER open_event_user;"
psql -d postgres -c "CREATE DATABASE opev_test WITH OWNER open_event_user;"

# Run migrations and seed data
python manage.py db upgrade
python manage.py prepare_db "admin@example.com:password"
```

### Running
```bash
# Development server
export APP_CONFIG=config.DevelopmentConfig
poetry run python -m flask run

# Via Docker (recommended — includes postgres and redis)
docker-compose up
```

### Testing
```bash
# Run all tests
pytest tests/

# Run a specific test file
pytest tests/all/integration/api/event/test_events.py -v

# Run a single test function
pytest tests/all/integration/api/event/test_events.py::test_event_creation -v

# Run with stdout visible
pytest tests/all/unit/api/helpers/test_auth.py -s

# Run with coverage
pytest tests/ --cov=app

# Use a fast test DB via Docker
./scripts/test_db.sh
export TEST_DATABASE_URL=postgresql://test@localhost:5433/test
```

### Database Migrations
```bash
python manage.py db migrate    # Generate migration from model changes
python manage.py db upgrade    # Apply pending migrations
python manage.py db downgrade  # Roll back one migration
```

### Linting / Formatting
Pre-commit hooks handle formatting automatically on `git commit`. To run manually:
```bash
poetry run black app/
poetry run isort app/
```
Black line length is 90. isort is black-compatible.

## Architecture

### Request Flow
1. Request hits a **Resource** class in `app/api/` (e.g., `app/api/events.py`)
2. flask-rest-jsonapi dispatches to `list` or `detail` methods
3. Permission checks run via `app/api/helpers/permission_manager.py`
4. SQLAlchemy queries `app/models/` — one model per file
5. Marshmallow schemas (defined in the same `app/api/` file as the resource) handle serialization

### `app/api/` — API Layer
Each file typically defines:
- A **Schema** (marshmallow-jsonapi) — field definitions and relationships
- A **ResourceList** endpoint — GET /collection, POST /collection
- A **ResourceDetail** endpoint — GET /item, PATCH /item, DELETE /item
- Optionally relationship endpoints

The pattern: one file per resource type (e.g., `events.py`, `attendees.py`, `orders.py`).

### `app/api/helpers/` — Shared Utilities
Key modules to know:
- **`permission_manager.py`** — RBAC; controls who can access what
- **`mail.py`** — Email sending (SMTP/SendGrid) and template rendering
- **`payment.py`** — Stripe and PayPal integration
- **`files.py`** — File uploads, image resizing, S3/GCS storage
- **`csv_jobs_util.py`** — CSV export logic
- **`export_helpers.py`** — Full event export (ZIP, iCal, xCal, Pentabarf XML)
- **`db.py`** — Shared database utilities

### `app/models/` — SQLAlchemy Models
~80+ models. Core ones: `User`, `Event`, `Session`, `Speaker`, `Ticket`, `Order`, `Attendee`. SQLAlchemy-Continuum is used for audit trail/versioning.

### `app/api/custom/` — Non-REST Endpoints
Custom endpoints that don't follow JSON:API conventions (e.g., bulk operations, special exports).

### Background Jobs
Celery tasks are defined throughout `app/api/helpers/` and dispatched for: email sending, image resizing, PDF generation, CSV exports. Redis is both the broker and result backend.

### GraphQL
A secondary GraphQL API lives in `app/graphql/` using graphene-sqlalchemy, exposed via a FastAPI ASGI app at `app/asgi.py`.

## Configuration

Set `APP_CONFIG` to one of:
- `config.DevelopmentConfig` — debug enabled, verbose
- `config.TestingConfig` — Celery runs synchronously (ALWAYS_EAGER), uses test DB
- `config.ProductionConfig` / `config.StagingConfig` — caching and minification on

Key environment variables: `DATABASE_URL`, `TEST_DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `SENTRY_DSN`. See `.env.example` for the full list including OAuth, payment, and storage credentials.

## Testing Patterns

Tests are in `tests/all/unit/` and `tests/all/integration/`. Fixtures are in `tests/all/conftest.py`:
- `client` — Flask test client
- `db` — database session (rolls back after each test)
- `jwt` / `admin_jwt` — pre-built auth headers
- `user` / `admin_user` — pre-created user objects

Test data factories (Factory Boy) are in `tests/factories/` — prefer these over creating models directly.

## Branching
- `development` — active development branch; auto-deploys to staging
- `master` — production releases
