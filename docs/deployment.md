# Deployment Guide

## Local development (default)

```bash
cp .env.example .env          # fill in SERVER_HOST, ADMIN_EMAIL, ADMIN_PASSWORD, SECRET_KEY
python3 setup.py              # propagate config into all subprojects
cd open-event-server && docker compose up -d
cd ../intellisoft-middleware && ENABLE_SCHEDULER=false \
  .venv/bin/uvicorn app.main:app --reload --port 7000
```

Verify everything is up: `/health`

---

## Production checklist

### Open Event Server

- [ ] Set `APP_CONFIG=config.ProductionConfig` in environment
- [ ] `SECRET_KEY` is a 64-char random hex string: `python3 -c "import secrets; print(secrets.token_hex(32))"`
- [ ] `DATABASE_URL` points to a managed PostgreSQL instance (not the dev `opev_pass` password)
- [ ] `REDIS_URL` points to a managed Redis instance
- [ ] `ADMIN_EMAIL` / `ADMIN_PASSWORD` use a strong password
- [ ] All `localhost` references replaced with production hostnames
- [ ] `marshmallow_jsonapi_schema.py` bind mount present in `docker-compose.yml` (critical for mobile clients)
- [ ] Run migrations: `python manage.py db upgrade`
- [ ] HTTPS termination via nginx/caddy reverse proxy

### Intellisoft Middleware

- [ ] `KHSC_API_URL` points to `https://khsc.site/api/index.php` (not mock)
- [ ] `KHSC_AUTHORIZATION`, `KHSC_PASS_KEY`, `KHSC_SECRET_KEY` are real production keys from KHSC admin
- [ ] `OPEN_EVENT_BASE_URL` points to the production OE server
- [ ] `ENABLE_SCHEDULER=true` and scheduler intervals configured in `.env`
- [ ] Deploy behind the same nginx as OE or as a separate service on port 7000

### Android

- [ ] Update `buildConfigField "String", "DEFAULT_BASE_URL"` in `app/build.gradle` to production URL
- [ ] Build a **release** APK: `./gradlew assemblePlayStoreRelease`
- [ ] Sign the APK with the release keystore

### iOS

- [ ] Update `ControllerConstants.CommonURL.Release.baseURL` to production URL
- [ ] Archive and distribute via Xcode Organiser → App Store / Ad Hoc

---

## Resetting the dev environment

```bash
# Stop everything and remove volumes
cd open-event-server
docker compose down -v

# Restart fresh
docker compose up -d

# Re-seed admin user
docker exec opev-web python manage.py prepare_db "$ADMIN_EMAIL:$ADMIN_PASSWORD"

# Re-import delegates
curl -s -X POST http://localhost:7000/import -H "Content-Type: application/json" -d '{}'
```
