# Render Backend Deployment

This backend is a FastAPI service located in `backend/`.

## Render service settings

Service type: Web Service
Runtime: Python
Root Directory: backend

## Build Command

pip install uv && uv sync --frozen

## Start Command

uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT

## Required environment variables for Stage 1

APP_NAME=Immigration Law Guidance App
APP_ENV=production
APP_DEBUG=false
STORE_USER_QUESTIONS=false
PYTHON_VERSION=3.13.5

## Later required variables for full chat

DATABASE_URL=
REDIS_URL=
OLLAMA_BASE_URL=
OLLAMA_CHAT_BASE_URL=
OLLAMA_CHAT_MODEL=
OLLAMA_API_KEY=
OLLAMA_EMBED_MODEL=nomic-embed-text

Do not commit real secrets or API keys.

## Stage 1 validation

After deployment, these should load successfully:

GET /health
GET /docs

## Stage 2 validation

After database and Ollama variables are configured, these should work:

GET /health/dependencies
POST /api/chat
