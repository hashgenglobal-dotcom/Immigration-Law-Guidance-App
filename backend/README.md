# Backend — Immigration Law Guidance App

Minimal FastAPI backend foundation. This step intentionally contains **no** ingestion, retrieval, authentication, LLM, or database session code — only the app skeleton, configuration loader, and a `/health` endpoint.

## Privacy rules (must remain true in every future PR)

- Real user questions are processed by **local models only** (Ollama / vLLM via `OLLAMA_BASE_URL`). No OpenAI / Anthropic / public AI API calls.
- **Full user question text and full generated answer text must not be stored by default.** Only privacy-safe metadata (hashes, citations used, retrieved chunk IDs, risk level, refusal flag, latency, etc.) may be persisted into the `privacy_safe_answer_logs` table.
- `STORE_USER_QUESTIONS` defaults to `false` in `app/core/config.py` and must stay that way unless an operator deliberately opts in.

## Environment variables

Loaded by `app/core/config.py` via `pydantic-settings`. The canonical template lives at the repo root in `.env.example`.

| Variable | Default | Purpose |
| --- | --- | --- |
| `APP_NAME` | `Immigration Law Guidance App` | Human-readable app name returned by `/health`. |
| `APP_ENV` | `development` | Environment label (`development`, `staging`, `production`). |
| `APP_DEBUG` | `true` | FastAPI debug flag. |
| `DATABASE_URL` | _(unset)_ | PostgreSQL DSN, e.g. `postgresql+psycopg://user@localhost:5432/immigration_law_dev`. Not used yet. |
| `REDIS_URL` | _(unset)_ | Redis URL, e.g. `redis://localhost:6379/0`. Not used yet. |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Local Ollama endpoint. Not called yet. |
| `STORE_USER_QUESTIONS` | `false` | Must stay `false` by default. |

Copy `.env.example` to `.env` at the repo root (or to `backend/.env`) and edit as needed. `.env` files are git-ignored.

## Run instructions

This project uses [`uv`](https://docs.astral.sh/uv/) for Python dependency management.

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Then verify the health endpoint:

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

OpenAPI docs are available at `http://127.0.0.1:8000/docs` while `APP_DEBUG=true`.

## Layout

```
backend/
├── pyproject.toml
├── README.md
└── app/
    ├── __init__.py
    ├── main.py                  # FastAPI app factory + /health wiring
    ├── api/
    │   ├── __init__.py
    │   └── routes/
    │       ├── __init__.py
    │       └── health.py        # GET /health
    └── core/
        ├── __init__.py
        └── config.py            # pydantic-settings Settings + get_settings()
```

## What this step does NOT do

- No SQLAlchemy models, sessions, or migrations runtime wiring.
- No Alembic setup.
- No ingestion (eCFR / USCIS / INA / BIA fetchers).
- No retrieval, hybrid search, or LLM calls.
- No authentication or admin endpoints.
- No frontend changes.

Those land in subsequent feature branches.
