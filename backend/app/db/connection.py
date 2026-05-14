"""PostgreSQL connection helpers (psycopg v3, async).

Responsibilities:

    * `normalize_database_url` — convert a SQLAlchemy-style DSN such as
      ``postgresql+psycopg://user@host/db`` into the plain
      ``postgresql://user@host/db`` form libpq/psycopg expects.
    * `get_database_dsn` — read `Settings.database_url`, validate it,
      and return the normalized DSN. Raises `DatabaseConfigError` (with
      a credential-free message) when `DATABASE_URL` is not configured.
    * `connect` — async context manager that yields a
      `psycopg.AsyncConnection` with a short connect timeout.
    * `fetch_existing_tables` — return the subset of supplied table
      names that actually exist in a given schema (default `"public"`).

Privacy / safety:

    * Errors raised from here never include the DSN, password, or any
      part of the connection string. Callers that surface errors to
      HTTP responses should still wrap unknown exceptions with a
      generic, scrubbed message (see `app.services.schema_health`).
    * This module never reads, writes, or transmits user question
      text or generated answer text. Real user content must not flow
      through this file.
"""

from __future__ import annotations

import re
from contextlib import asynccontextmanager
from typing import AsyncIterator, Iterable

import psycopg

from app.core.config import Settings

# Conservative liveness timeout. Health-style probes must never block.
_PG_CONNECT_TIMEOUT_SECONDS = 2


class DatabaseConfigError(RuntimeError):
    """Raised when `DATABASE_URL` is missing or unusable.

    The message is intentionally generic and contains no DSN content,
    so it is safe to bubble up into HTTP responses.
    """


def normalize_database_url(database_url: str) -> str:
    """Convert SQLAlchemy-style ``postgresql+driver://...`` to plain ``postgresql://...``.

    SQLAlchemy URLs of the form ``postgresql+psycopg://...`` are
    incompatible with libpq and the plain psycopg client. This helper
    strips the ``+driver`` suffix so the same env var (`DATABASE_URL`)
    works for both SQLAlchemy and direct psycopg usage.
    """
    return re.sub(r"^postgresql\+[a-zA-Z0-9_]+://", "postgresql://", database_url)


def get_database_dsn(settings: Settings) -> str:
    """Return a psycopg-ready DSN derived from `settings.database_url`."""
    if not settings.database_url:
        raise DatabaseConfigError("DATABASE_URL is not configured")
    return normalize_database_url(settings.database_url)


@asynccontextmanager
async def connect(settings: Settings) -> AsyncIterator[psycopg.AsyncConnection]:
    """Open a short-lived async psycopg connection."""
    dsn = get_database_dsn(settings)
    async with await psycopg.AsyncConnection.connect(
        dsn, connect_timeout=_PG_CONNECT_TIMEOUT_SECONDS
    ) as conn:
        yield conn


async def fetch_existing_tables(
    settings: Settings,
    table_names: Iterable[str],
    schema: str = "public",
) -> set[str]:
    """Return the subset of `table_names` that exist in `schema`.

    Uses `information_schema.tables`, which is read-only metadata and
    contains no user content.
    """
    names = list(table_names)
    if not names:
        return set()

    async with connect(settings) as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = %s
                  AND table_name = ANY(%s)
                """,
                (schema, names),
            )
            rows = await cur.fetchall()

    return {row[0] for row in rows}
