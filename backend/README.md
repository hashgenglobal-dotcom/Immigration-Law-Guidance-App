# Backend — Immigration Law Guidance App

Minimal FastAPI backend foundation. This step intentionally contains **no** ingestion, retrieval, authentication, LLM, or database session code — only the app skeleton, configuration loader, and a `/health` endpoint.

## Privacy rules (must remain true in every future PR)

- Real user questions are processed by **local models only** (Ollama / vLLM via `OLLAMA_BASE_URL`). No OpenAI / Anthropic / public AI API calls.
- **Full user question text and full generated answer text must not be stored by default.** Only privacy-safe metadata (hashes, citations used, retrieved chunk IDs, risk level, refusal flag, latency, etc.) may be persisted into the `privacy_safe_answer_logs` table.
- `STORE_USER_QUESTIONS` defaults to `false` in `app/core/config.py` and must stay that way unless an operator deliberately opts in.

## Environment variables

Loaded by `app/core/config.py` via `pydantic-settings`. The canonical template is `backend/.env.example`.

| Variable | Default | Purpose |
| --- | --- | --- |
| `APP_NAME` | `Immigration Law Guidance App` | Human-readable app name returned by `/health`. |
| `APP_ENV` | `development` | Environment label (`development`, `staging`, `production`). |
| `APP_DEBUG` | `true` | FastAPI debug flag. |
| `DATABASE_URL` | _(unset)_ | PostgreSQL DSN, e.g. `postgresql+psycopg://user@localhost:5432/immigration_law_dev`. Used by `/health/dependencies`. |
| `REDIS_URL` | _(unset)_ | Redis URL, e.g. `redis://localhost:6379/0`. Used by `/health/dependencies`. |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Local Ollama endpoint. Used by `/health/dependencies` (lists models only — no chat, no embeddings). |
| `STORE_USER_QUESTIONS` | `false` | **Must stay `false` by default.** Real user questions and full generated answers must not be persisted. |

`backend/.env` is git-ignored and must never be committed. Only `backend/.env.example` is checked in.

For guidance on pointing `DATABASE_URL` at a shared hosted PostgreSQL instance (what may go in it, what must not, provider and security requirements), see [`docs/cloud-shared-dev-database-plan.md`](../docs/cloud-shared-dev-database-plan.md).

## Environment Setup (local development)

```bash
cd backend

# 1. Copy the safe template and edit your local values.
cp .env.example .env

# 2. Open .env and replace YOUR_MAC_USERNAME in DATABASE_URL with your
#    local PostgreSQL role (often the output of `whoami`).
#    e.g. postgresql+psycopg://rishirajkanukuntla@localhost:5432/immigration_law_dev

# 3. Confirm the local services are running.
brew services start postgresql@17    # or @18
brew services start redis
brew services start ollama

# 4. Start the backend, then verify dependency connectivity.
uv sync
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
# In another terminal:
curl http://127.0.0.1:8000/health/dependencies
```

A healthy response has top-level `"status": "ok"` and every check reporting `"status": "ok"`. See the [`/health/dependencies`](#get-healthdependencies--postgres--redis--ollama) section below for the payload shape and degraded-mode behavior.

**Do not commit `backend/.env`.** It is intentionally git-ignored (see the root `.gitignore`) because it may contain local DB usernames, local connection details, or future credentials. Only `backend/.env.example` (placeholder values, safe to commit) is tracked.

## Run instructions

This project uses [`uv`](https://docs.astral.sh/uv/) for Python dependency management.

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Then verify the health endpoints.

### `GET /health` — service liveness

```bash
curl http://127.0.0.1:8000/health
```

Expected response (shape):

```json
{
  "status": "ok",
  "app_name": "Immigration Law Guidance App",
  "environment": "development",
  "privacy_mode": "local-first"
}
```

This endpoint never reaches out to PostgreSQL, Redis, or Ollama. It is safe to use as a fast liveness probe.

### `GET /health/dependencies` — Postgres + Redis + Ollama

```bash
curl http://127.0.0.1:8000/health/dependencies
```

Probes the three external dependencies in parallel with short (2s) timeouts.

- **Postgres**: connects via `psycopg` using `DATABASE_URL` (SQLAlchemy-style `postgresql+psycopg://...` URLs are normalized to `postgresql://...` internally) and runs `SELECT 1`.
- **Redis**: connects via `redis.asyncio` using `REDIS_URL` and issues `PING`.
- **Ollama**: HTTP `GET {OLLAMA_BASE_URL}/api/tags` and returns the list of locally installed model names. No chat completion or embeddings are called, and no user text is sent.

Expected response when everything is up:

```json
{
  "status": "ok",
  "checks": {
    "postgres": { "status": "ok", "detail": "connected" },
    "redis":    { "status": "ok", "detail": "connected" },
    "ollama":   {
      "status": "ok",
      "detail": "connected",
      "models": ["nomic-embed-text:latest", "llama3.1:8b"]
    }
  }
}
```

If one or more dependencies fail, the HTTP status code is still **200** and the top-level `status` becomes `"degraded"`:

```json
{
  "status": "degraded",
  "checks": {
    "postgres": { "status": "error", "detail": "postgres unreachable (OperationalError)" },
    "redis":    { "status": "ok", "detail": "connected" },
    "ollama":   { "status": "ok", "detail": "connected", "models": [] }
  }
}
```

Error messages are deliberately short and **never include the DSN, password, or stack trace**, because libpq error messages can otherwise echo back the full connection string.

### Quick local checklist before calling `/health/dependencies`

```bash
brew services start postgresql@17    # or @18
brew services start redis
brew services start ollama
```

### `GET /health/schema` — required migration tables present?

```bash
curl http://127.0.0.1:8000/health/schema
```

Verifies that the local PostgreSQL database has every table created by [`database/migrations/001-initial-schema.sql`](../database/migrations/001-initial-schema.sql). The probe only reads `information_schema.tables` — it **does not read or store user question text or generated answer text**, and it never touches the data tables themselves.

Healthy response when the migration has been applied (10 required tables):

```json
{
  "status": "ok",
  "required_tables_count": 10,
  "existing_tables_count": 10,
  "missing_tables": [],
  "privacy_safe_answer_logs_present": true
}
```

Degraded response when one or more tables are missing (HTTP is still 200):

```json
{
  "status": "degraded",
  "required_tables_count": 10,
  "existing_tables_count": 8,
  "missing_tables": ["privacy_safe_answer_logs", "ingestion_jobs"],
  "privacy_safe_answer_logs_present": false
}
```

If the database is unreachable, the response is also `200` with `"status": "degraded"` and a short, credential-free `detail` such as `"database unreachable (OperationalError)"` or `"DATABASE_URL is not configured"`. The DSN, password, and stack trace are never echoed back.

**Privacy note:** `privacy_safe_answer_logs` is **expected** — it stores only metadata (hashes, citations used, retrieved chunk IDs, risk level, refusal flag, latency). The legacy `answer_logs` table (which stored full `question_text` / `answer_text`) must **not** exist. If you ever need to apply the migration to a fresh database:

```bash
psql -d immigration_law_dev -f database/migrations/001-initial-schema.sql
```

OpenAPI docs are available at `http://127.0.0.1:8000/docs` while `APP_DEBUG=true`.

## Layout

```
backend/
├── pyproject.toml
├── README.md
├── .env.example
└── app/
    ├── __init__.py
    ├── main.py                       # FastAPI app factory + router wiring
    ├── api/
    │   ├── __init__.py
    │   └── routes/
    │       ├── __init__.py
    │       └── health.py             # GET /health, /health/dependencies, /health/schema
    ├── core/
    │   ├── __init__.py
    │   └── config.py                 # pydantic-settings Settings + get_settings()
    ├── db/
    │   ├── __init__.py
    │   └── connection.py             # DSN normalization + async psycopg helpers
    └── services/
        ├── __init__.py
        ├── dependency_health.py      # Postgres / Redis / Ollama probes
        └── schema_health.py          # Required-migration-tables probe
```

## What this step does NOT do

- No SQLAlchemy models, sessions, or migrations runtime wiring.
- No Alembic setup.
- No ingestion (eCFR / USCIS / INA / BIA fetchers).
- No retrieval, hybrid search, or LLM calls.
- No authentication or admin endpoints.
- No frontend changes.

Those land in subsequent feature branches.
