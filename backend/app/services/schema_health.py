"""Schema health probe.

Verifies that the local PostgreSQL database has all tables defined in
``database/migrations/001-initial-schema.sql``.

Privacy expectation enforced by this probe:

    * ``privacy_safe_answer_logs`` is REQUIRED. It is the privacy-safe
      audit table that stores only metadata (hashes, citations used,
      retrieved chunk IDs, risk level, refusal flag, latency, etc.).
    * Older designs persisted full ``question_text`` and ``answer_text``
      in an ``answer_logs`` table — that table must NOT exist in this
      database. If you ever see ``answer_logs`` in the public schema
      it indicates a regression of the privacy model.

The probe only reads ``information_schema.tables``. It never executes
queries against the data tables themselves, and it cannot read any
user question text or generated answer text. It also never returns
the DSN, password, or any part of the connection string in its
response.
"""

from __future__ import annotations

from typing import Any

from app.core.config import Settings
from app.db.connection import DatabaseConfigError, fetch_existing_tables

# Tables created by `database/migrations/001-initial-schema.sql`.
# Order is fixed (and matches the migration) so that `missing_tables`
# in the response is deterministic across runs.
REQUIRED_TABLES: tuple[str, ...] = (
    "source_registry",
    "raw_documents",
    "legal_documents",
    "legal_sections",
    "legal_chunks",
    "scenario_guides",
    "dataset_versions",
    "ingestion_jobs",
    "privacy_safe_answer_logs",
    "admin_users",
)

PRIVACY_SAFE_LOG_TABLE = "privacy_safe_answer_logs"


def _degraded_payload(missing: list[str], detail: str) -> dict[str, Any]:
    """Build a degraded response when the DB cannot be inspected at all."""
    return {
        "status": "degraded",
        "required_tables_count": len(REQUIRED_TABLES),
        "existing_tables_count": 0,
        "missing_tables": missing,
        "privacy_safe_answer_logs_present": False,
        "detail": detail,
    }


async def run_schema_health(settings: Settings) -> dict[str, Any]:
    """Probe the public schema for the required migration tables."""
    required = list(REQUIRED_TABLES)

    try:
        existing = await fetch_existing_tables(settings, required)
    except DatabaseConfigError as exc:
        # `DatabaseConfigError` messages are pre-scrubbed (no DSN content).
        return _degraded_payload(missing=list(required), detail=str(exc))
    except Exception as exc:  # noqa: BLE001 — probe must not raise
        # Surface only the exception class name; libpq error strings can
        # otherwise echo back the DSN (including any password).
        return _degraded_payload(
            missing=list(required),
            detail=f"database unreachable ({type(exc).__name__})",
        )

    missing = [t for t in required if t not in existing]
    return {
        "status": "ok" if not missing else "degraded",
        "required_tables_count": len(required),
        "existing_tables_count": len(existing),
        "missing_tables": missing,
        "privacy_safe_answer_logs_present": PRIVACY_SAFE_LOG_TABLE in existing,
    }
