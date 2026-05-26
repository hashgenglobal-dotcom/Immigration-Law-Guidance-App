# Web app — local full stack and Vercel testing

## What runs where

| Piece | Local | Vercel testers |
|-------|--------|----------------|
| **Web UI** | Next.js `http://localhost:3000` | Vercel (set project root to `frontend/`) |
| **API** | FastAPI `http://127.0.0.1:8000` | Public host (Railway, Fly, Render, VM) — **not** on Vercel |
| **Database** | `DATABASE_URL` in `backend/.env` | Same DSN on API host |
| **LLM** | Local Ollama `llama3.2:latest` | Ollama on API host or `OLLAMA_CHAT_BASE_URL` |

Vercel only hosts the Next.js frontend. The browser calls `/api/*` on the same origin; Next **rewrites** those requests to `BACKEND_URL`.

## Local full stack

```bash
# 1. Ollama (chat + embeddings)
ollama serve
# Ensure: ollama pull llama3.2:latest && ollama pull nomic-embed-text

# 2. Redis (optional but recommended)
redis-server

# 3. Backend
cd backend
cp .env.example .env   # set DATABASE_URL, OLLAMA_CHAT_MODEL=llama3.2:latest
uv sync
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 4. Frontend
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Open **http://localhost:3000** → **Ask a question** → submit (first answer may take 1–2 minutes).

Health checks:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/health/dependencies
curl -X POST http://127.0.0.1:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"What is a Notice to Appear?"}'
```

## Vercel deployment (frontend only)

1. Push branch that includes the `frontend/` directory.
2. Import repo in Vercel → **Root Directory**: `frontend`.
3. Environment variable:
   - `BACKEND_URL` = `https://your-public-api.example.com` (no trailing slash)
4. Deploy. Share the `*.vercel.app` URL for testers.

## API host requirements (for shared testing)

Your public backend must:

- Expose `GET /health` and `POST /api/chat`
- Reach PostgreSQL (`DATABASE_URL`) with active `legal_chunks` data
- Reach Ollama for chat + embeddings (local or cloud)
- Allow HTTPS from Vercel (CORS on backend if you call API directly; rewrites avoid browser CORS)

## Scenarios page

Scenario guides on the web app use **mock content** in `frontend/src/lib/mockData.ts` until a `GET /api/scenarios` route is wired. Ask + retrieval use the real backend.

## Privacy

Do not commit `backend/.env` or `frontend/.env.local`. No user questions are stored by default.
