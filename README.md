# Open Event – Local Development Setup

Three repos managed together:

| Repo | Stack | Default URL |
|------|-------|-------------|
| `open-event-server` | Flask + PostgreSQL + Redis (Docker) | http://localhost:8080 |
| `open-event-frontend` | Ember.js | http://localhost:4200 |
| `open-event-organizer-android` | Android (Java) | connects to `SERVER_HOST:8080` |

## First-time setup

**1. Copy and fill in the shared config**

```bash
cp .env.example .env
```

Open `.env` and set at minimum:
- `POSTGRES_PASSWORD` — change from the default if you prefer
- `SECRET_KEY` — leave blank; the script generates one automatically
- `ADMIN_EMAIL` / `ADMIN_PASSWORD` — leave blank; the script prompts for these

**2. Run the setup script**

```bash
python3 setup.py
```

The script will:
- Detect your machine's LAN IP and write it to `SERVER_HOST`
- Generate a `SECRET_KEY` if one isn't already set
- Propagate `API_HOST`, database credentials, and `SECRET_KEY` into each repo's config
- Ask whether to start services
- If yes, prompt for admin email and password, then:
  - Start the server stack via `docker-compose up -d` (postgres, redis, web, celery)
  - Start the frontend via `yarn start` (logs → `open-event-frontend/yarn-start.log`)
  - Create the initial superuser inside the running container
  - Set `is_verified = true` directly in postgres

**Why `is_verified` is set manually:**
Local machines do not run a mail server, so the verification email is never delivered.
The script connects to the `opev-postgres` container and runs:
```sql
UPDATE users SET is_verified=true WHERE email='<your email>';
```
This only happens during local setup. In staging/production the email flow runs normally.

## Subsequent runs

Running `setup.py` again is safe — it only updates values that have changed (e.g. if your LAN IP changed after switching networks). Admin credentials already stored in `.env` are not re-prompted.

## Starting services manually

If you skipped the prompt or need to restart:

```bash
# Server (postgres + redis + web + celery)
cd open-event-server && docker-compose up -d

# Frontend
cd open-event-frontend && yarn start

# Stop server
cd open-event-server && docker-compose down
```

## Android

The debug build reads `SERVER_HOST` and `SERVER_PORT` from the root `.env` at Gradle
evaluation time — no manual export needed:

```bash
cd open-event-organizer-android
./gradlew assembleDebug
```

The release build always points to `https://api.eventyay.com/v1/` regardless of `.env`.

## Accessing services

| Service | Local browser | Android device (same WiFi) |
|---------|--------------|---------------------------|
| Frontend | http://localhost:4200 | http://`SERVER_HOST`:4200 |
| API | http://localhost:8080/v1/ | http://`SERVER_HOST`:8080/v1/ |
