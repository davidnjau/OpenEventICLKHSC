# Security Rules

## Credentials — never hardcode

All secrets must come from environment variables or the root `.env` file.

| Secret | Variable | Where used |
|---|---|---|
| OE admin password | `ADMIN_PASSWORD` | `.env` → server + middleware |
| OE JWT secret | `SECRET_KEY` | `.env` → server |
| KHSC auth token | `KHSC_AUTHORIZATION` | `.env` → middleware |
| KHSC pass key | `KHSC_PASS_KEY` | `.env` → middleware |
| KHSC secret key | `KHSC_SECRET_KEY` | `.env` → middleware |
| DB password | `POSTGRES_PASSWORD` | docker-compose only |

The dev/mock values in `khsc_mock/mock_server.py` are intentionally visible — they are **not** real production keys.

## Auth header pattern (iOS)

JWT tokens are stored in **Keychain only**, accessed via `KeychainHelper`. Never use `UserDefaults`.

```swift
// Good
KeychainHelper.save(key: "jwt_token", value: token)

// Bad
UserDefaults.standard.set(token, forKey: "jwt_token")
```

## Auth header pattern (Android)

JWT is stored in the app's encrypted `SharedPreferences` via the existing `AuthHolder`.

## API auth — Open Event server

All protected endpoints require:
```
Authorization: JWT <token>
```

Token obtained from `POST /auth/session` with `{"email": "...", "password": "..."}`.

## What to check before any commit

- No raw passwords, tokens, or secret keys in source code
- `.env` is in `.gitignore` (it is — never remove this)
- No `print()` or `logger.debug()` statements outputting auth tokens
- `delegates.json` mock data does not contain real patient or person data
