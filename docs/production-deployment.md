# Production deployment (POST-07)

## Prerequisites

- MVP + post-MVP branches merged and tested on `main`
- `JWT_SECRET` set via secret manager (`openssl rand -hex 32`)
- `STORE_USER_QUESTIONS=false`
- TLS terminator (nginx, Caddy, or cloud LB) in front of FastAPI
- Private network access to Ollama for embeddings + chat

## Database

1. Run `database/migrations/001-initial-schema.sql`
2. Run `database/migrations/002-app-users.sql`
3. Enable automated backups (daily minimum)

## Template

See `infra/docker-compose.prod.yml` for a starting compose file. Replace passwords and wire your Ollama endpoint via `OLLAMA_BASE_URL` / `OLLAMA_CHAT_BASE_URL`.

## Health checks

- Liveness: `GET /health`
- Dependencies: `GET /health/dependencies`
- Schema: `GET /health/schema`

## Post-deploy smoke

1. Register + login (`POST /api/auth/register`, `/login`)
2. `POST /api/chat` with token
3. Confirm rate limit returns 429 under load test (staging only)
4. Confirm `X-Request-Id` on responses

## Not in scope

- Mobile app store release pipeline
- Attorney sign-off (see `docs/legal-review-process.md`)
