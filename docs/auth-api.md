# Auth API (POST-04)

## Endpoints

| Method | Path | Auth |
|--------|------|------|
| POST | `/api/auth/register` | No |
| POST | `/api/auth/login` | No |
| GET | `/api/auth/me` | Bearer token |

## Migration

```bash
psql "$DATABASE_URL" -f database/migrations/002-app-users.sql
```

## Mobile

Token stored in `expo-secure-store`; sent as `Authorization: Bearer <token>` on chat requests.
