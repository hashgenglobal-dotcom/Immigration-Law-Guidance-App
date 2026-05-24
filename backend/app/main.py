"""FastAPI application entry point.

This is the minimal backend foundation for the Immigration Law Guidance App.

Scope of this file (intentionally small):
    * Construct the FastAPI app.
    * Register the `/health` route.
    * Nothing else — no ingestion, no retrieval, no auth, no LLM,
      no database session wiring yet.

PRIVACY RULES (must remain true as more code is added):
    * Full user question text and full generated answer text must NOT
      be stored by default. Only privacy-safe metadata may be logged
      (see `privacy_safe_answer_logs` in the database schema).
    * Real user questions must be processed by LOCAL models only
      (Ollama / vLLM). Do NOT call OpenAI, Anthropic, or any other
      public AI API from this backend.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import chat, health, retrieval
from app.core.config import get_settings


def create_app() -> FastAPI:
    """Build and return the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        debug=settings.app_debug,
        description=(
            "Privacy-first, local-first immigration law information "
            "assistant. Answers are produced only from retrieved official "
            "legal sources. Full user questions and full generated answers "
            "are not stored by default."
        ),
    )

    # Dev-safe CORS — allows the local Vite dev server to reach the API.
    # Origins are restricted to localhost only; no wildcard.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type"],
    )

    app.include_router(health.router)
    app.include_router(retrieval.router)
    app.include_router(chat.router)

    return app


app = create_app()
