# Rate limiting (POST-03)

Server-side limits complement the mobile guest chat cap.

## Endpoints

| Endpoint | Default limit | Env var |
|----------|---------------|---------|
| `POST /api/chat` | 10 / minute / client | `RATE_LIMIT_CHAT_PER_MINUTE` |
| `POST /api/retrieve` | 30 / minute / client | `RATE_LIMIT_RETRIEVE_PER_MINUTE` |

## Client identity

1. Authenticated user id (POST-04), when present
2. `X-Client-Id` header (opaque, max 128 chars)
3. Hashed client IP

Keys in Redis use SHA-256 prefixes only — not raw questions.

## Development

When `APP_ENV=development`, limits are not enforced (guest/mobile testing).

## Disable

`RATE_LIMIT_ENABLED=false` or omit `REDIS_URL` (limits skipped if Redis unavailable).
