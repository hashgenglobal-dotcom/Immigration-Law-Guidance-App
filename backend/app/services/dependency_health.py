"""Dependency connectivity checks for PostgreSQL, Redis, and local Ollama.

This module performs *lightweight* liveness probes only:

    * PostgreSQL: open a connection and run ``SELECT 1``.
    * Redis: ``PING``.
    * Ollama: HTTP ``GET {OLLAMA_BASE_URL}/api/tags`` and return model
      names. No chat completion, no embeddings, no user text is sent.

Privacy / safety rules enforced here:

    * No DSN, password, token, or full URL is ever included in the
      response. On failure we surface only a short, generic message
      ("postgres unreachable (OperationalError)") so operators can
      see *something* failed without leaking credentials or stack
      traces.
    * No user data is logged or transmitted. These probes hit only
      local infrastructure.
    * The function always returns — it never raises — so the HTTP
      route can always answer with 200 and a ``degraded`` status.
"""

from __future__ import annotations

import asyncio
import re
from typing import Any

import httpx
import psycopg
from redis import asyncio as redis_asyncio

from app.core.config import Settings

# Short, conservative timeouts. A health probe must never block the
# event loop or stall the /health/dependencies endpoint.
_PG_CONNECT_TIMEOUT_SECONDS = 2
_REDIS_CONNECT_TIMEOUT_SECONDS = 2
_OLLAMA_HTTP_TIMEOUT_SECONDS = 2.0


def _to_psycopg_dsn(database_url: str) -> str:
    """Normalize a SQLAlchemy-style URL to a libpq/psycopg-compatible DSN.

    ``postgresql+psycopg://user@host/db`` -> ``postgresql://user@host/db``
    """
    return re.sub(r"^postgresql\+[a-zA-Z0-9_]+://", "postgresql://", database_url)


def _safe_error(component: str, exc: BaseException) -> str:
    """Return a short, credential-free error message.

    We intentionally do *not* include ``str(exc)`` because some
    drivers (notably libpq) embed the DSN — which may contain a
    password — in their error messages.
    """
    return f"{component} unreachable ({type(exc).__name__})"


async def check_postgres(settings: Settings) -> dict[str, str]:
    """Open a connection and run ``SELECT 1``."""
    if not settings.database_url:
        return {"status": "error", "detail": "DATABASE_URL not configured"}

    dsn = _to_psycopg_dsn(settings.database_url)
    try:
        async with await psycopg.AsyncConnection.connect(
            dsn, connect_timeout=_PG_CONNECT_TIMEOUT_SECONDS
        ) as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT 1")
                await cur.fetchone()
        return {"status": "ok", "detail": "connected"}
    except Exception as exc:  # noqa: BLE001 — health probe must not raise
        return {"status": "error", "detail": _safe_error("postgres", exc)}


async def check_redis(settings: Settings) -> dict[str, str]:
    """Issue a Redis ``PING``."""
    if not settings.redis_url:
        return {"status": "error", "detail": "REDIS_URL not configured"}

    client: redis_asyncio.Redis | None = None
    try:
        client = redis_asyncio.from_url(
            settings.redis_url,
            socket_connect_timeout=_REDIS_CONNECT_TIMEOUT_SECONDS,
            socket_timeout=_REDIS_CONNECT_TIMEOUT_SECONDS,
        )
        await client.ping()
        return {"status": "ok", "detail": "connected"}
    except Exception as exc:  # noqa: BLE001 — health probe must not raise
        return {"status": "error", "detail": _safe_error("redis", exc)}
    finally:
        if client is not None:
            try:
                await client.aclose()
            except Exception:  # noqa: BLE001
                pass


async def check_ollama(settings: Settings) -> dict[str, Any]:
    """Hit ``GET {OLLAMA_BASE_URL}/api/tags`` and return model names.

    This call only lists locally installed models — no prompt, no
    embedding request, no user text is transmitted.
    """
    base = settings.ollama_base_url.rstrip("/")
    url = f"{base}/api/tags"
    try:
        async with httpx.AsyncClient(timeout=_OLLAMA_HTTP_TIMEOUT_SECONDS) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            payload = resp.json()
        models = [
            m["name"]
            for m in payload.get("models", [])
            if isinstance(m, dict) and isinstance(m.get("name"), str)
        ]
        return {"status": "ok", "detail": "connected", "models": models}
    except Exception as exc:  # noqa: BLE001 — health probe must not raise
        return {
            "status": "error",
            "detail": _safe_error("ollama", exc),
            "models": [],
        }


async def run_dependency_checks(settings: Settings) -> dict[str, Any]:
    """Run all dependency checks in parallel and aggregate results."""
    postgres, redis_result, ollama = await asyncio.gather(
        check_postgres(settings),
        check_redis(settings),
        check_ollama(settings),
    )

    overall = (
        "ok"
        if all(c["status"] == "ok" for c in (postgres, redis_result, ollama))
        else "degraded"
    )

    return {
        "status": overall,
        "checks": {
            "postgres": postgres,
            "redis": redis_result,
            "ollama": ollama,
        },
    }
