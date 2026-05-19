#!/usr/bin/env python3
"""Validate that the eCFR Title 8 sample was inserted correctly into PostgreSQL.

This script is read-only. It issues only SELECT queries and never inserts,
updates, or deletes anything. It replaces manual psql checks with a repeatable
validation that can be run after every ingestion to confirm the schema is intact.

Privacy
-------
This script validates public legal-source ingestion only.
- It does NOT read or store user questions.
- It does NOT read privacy_safe_answer_logs content — it only verifies the row
  count is 0, confirming that ingestion never wrote to that table.
- It does NOT generate embeddings.
- It does NOT call Ollama, OpenAI, Anthropic, or any public AI API.

Usage
-----
    # Auto-detect source_date from newest dataset_versions row, DB URL from backend/.env
    uv run --project backend python scripts/validate_ecfr_db_insert.py

    # Explicit source date
    uv run --project backend python scripts/validate_ecfr_db_insert.py \\
        --source-date 2026-05-12

    # Explicit database URL
    uv run --project backend python scripts/validate_ecfr_db_insert.py \\
        --database-url "postgresql://user@localhost:5432/immigration_law_dev"

Exit codes
----------
* 0 — all checks passed (PASS).
* 1 — one or more checks failed (FAIL), connection error, or bad arguments.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

# psycopg (v3) is the only non-stdlib dependency.
# Run with: uv run --project backend python scripts/validate_ecfr_db_insert.py
try:
    import psycopg
except ImportError:
    print(
        "ERROR: psycopg (v3) is not installed in the current Python environment.\n"
        "       Run this script with:\n"
        "         uv run --project backend python scripts/validate_ecfr_db_insert.py"
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BACKEND_ENV_PATH = Path("backend/.env")
SOURCE_NAME = "eCFR Title 8"

# The five MVP sections expected to be present after ingestion.
EXPECTED_SECTIONS: tuple[str, ...] = ("208.7", "208.4", "245.1", "274a.12", "239.1")

# Full citations matching legal_chunks.citation and legal_sections.citation.
EXPECTED_CITATIONS: tuple[str, ...] = (
    "8 CFR § 208.7",
    "8 CFR § 208.4",
    "8 CFR § 245.1",
    "8 CFR § 274a.12",
    "8 CFR § 239.1",
)

_DIVIDER = "-" * 72


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only validation of the eCFR Title 8 database insert. "
            "Checks public legal-source tables only; never reads user data."
        ),
    )
    parser.add_argument(
        "--database-url",
        default=None,
        help=(
            "PostgreSQL connection URL. Accepts postgresql://... or "
            "postgresql+psycopg://... (SQLAlchemy-style prefix is stripped). "
            "Default: DATABASE_URL env var, then backend/.env."
        ),
    )
    parser.add_argument(
        "--source-date",
        default=None,
        metavar="YYYY-MM-DD",
        help=(
            "Source date to validate (e.g. 2026-05-12). "
            "Default: newest ecfr-title8-sample-* row in dataset_versions."
        ),
    )
    return parser.parse_args(argv)


# ---------------------------------------------------------------------------
# .env parser (stdlib only — no dotenv dependency)
# ---------------------------------------------------------------------------


def _read_env_file(path: Path) -> dict[str, str]:
    """Parse KEY=value lines; handles double- and single-quoted values."""
    result: dict[str, str] = {}
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return result
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, raw_val = line.partition("=")
        key = key.strip()
        raw_val = raw_val.strip()
        if len(raw_val) >= 2 and raw_val[0] == raw_val[-1] and raw_val[0] in ('"', "'"):
            raw_val = raw_val[1:-1]
        result[key] = raw_val
    return result


def _resolve_database_url(arg_url: str | None) -> str | None:
    """Return DATABASE_URL from CLI arg, env var, or backend/.env (in that order)."""
    if arg_url:
        return arg_url
    env_val = os.environ.get("DATABASE_URL")
    if env_val:
        return env_val
    dotenv = _read_env_file(BACKEND_ENV_PATH)
    return dotenv.get("DATABASE_URL")


def _normalize_db_url(url: str) -> str:
    """Strip SQLAlchemy driver suffix: postgresql+psycopg://... → postgresql://..."""
    for prefix in ("postgresql+psycopg://", "postgres+psycopg://"):
        if url.startswith(prefix):
            scheme = prefix.split("+")[0]
            return scheme + "://" + url[len(prefix):]
    return url


# ---------------------------------------------------------------------------
# Validation checks (all read-only SELECT queries)
# ---------------------------------------------------------------------------


def _run_checks(
    cur: Any,
    source_date: str,
) -> tuple[list[str], dict[str, Any]]:
    """Run all validation SELECT queries. Returns (failures, details)."""
    failures: list[str] = []
    details: dict[str, Any] = {"source_date": source_date}

    version_name = f"ecfr-title8-sample-{source_date}"

    # ------------------------------------------------------------------
    # 1. source_registry — must have eCFR Title 8 seed row
    # ------------------------------------------------------------------
    cur.execute(
        "SELECT id FROM source_registry WHERE source_name = %s",
        (SOURCE_NAME,),
    )
    row = cur.fetchone()
    if row is None:
        failures.append(
            f"source_registry: row for {SOURCE_NAME!r} not found "
            "(migration seed missing)"
        )
        details["source_registry_id"] = None
    else:
        details["source_registry_id"] = row[0]

    # ------------------------------------------------------------------
    # 2. dataset_versions — must have the expected version row
    # ------------------------------------------------------------------
    cur.execute(
        "SELECT id, status FROM dataset_versions WHERE version_name = %s",
        (version_name,),
    )
    row = cur.fetchone()
    if row is None:
        failures.append(
            f"dataset_versions: row {version_name!r} not found — "
            "run insert_ecfr_preview_to_db.py first"
        )
        details["dataset_version_id"] = None
        details["dataset_version_status"] = None
    else:
        dv_id, dv_status = row
        details["dataset_version_id"] = dv_id
        details["dataset_version_status"] = dv_status
        if dv_status not in ("ready", "active"):
            failures.append(
                f"dataset_versions: status is {dv_status!r}; expected 'ready' or 'active'"
            )

    # ------------------------------------------------------------------
    # 3. raw_documents — one row for citation '8 CFR Title 8' + version_date
    # ------------------------------------------------------------------
    cur.execute(
        """
        SELECT id, content_hash
        FROM raw_documents
        WHERE citation = '8 CFR Title 8'
          AND version_date = %s::date
        """,
        (source_date,),
    )
    raw_rows = cur.fetchall()
    details["raw_documents_count"] = len(raw_rows)
    details["raw_document_id"] = raw_rows[0][0] if raw_rows else None
    details["raw_document_hash"] = raw_rows[0][1] if raw_rows else None
    if len(raw_rows) == 0:
        failures.append(
            f"raw_documents: no row found for citation '8 CFR Title 8' "
            f"and version_date {source_date!r}"
        )
    elif len(raw_rows) > 1:
        failures.append(
            f"raw_documents: expected 1 row, found {len(raw_rows)} "
            f"for citation '8 CFR Title 8' / version_date {source_date!r}"
        )

    # ------------------------------------------------------------------
    # 4. legal_documents — one row pointing at that raw_document
    # ------------------------------------------------------------------
    if details.get("raw_document_id") is not None:
        cur.execute(
            """
            SELECT id
            FROM legal_documents
            WHERE raw_document_id = %s AND citation = '8 CFR Title 8'
            """,
            (details["raw_document_id"],),
        )
        ld_rows = cur.fetchall()
        details["legal_documents_count"] = len(ld_rows)
        details["legal_document_id"] = ld_rows[0][0] if ld_rows else None
        if len(ld_rows) == 0:
            failures.append(
                "legal_documents: no row found for raw_document_id "
                f"{details['raw_document_id']}"
            )
        elif len(ld_rows) > 1:
            failures.append(
                f"legal_documents: expected 1 row, found {len(ld_rows)} "
                f"for raw_document_id {details['raw_document_id']}"
            )
    else:
        details["legal_documents_count"] = 0
        details["legal_document_id"] = None

    # ------------------------------------------------------------------
    # 5. legal_sections — must have exactly the five expected section numbers
    # ------------------------------------------------------------------
    if details.get("legal_document_id") is not None:
        cur.execute(
            """
            SELECT section_number, topic, subtopic
            FROM legal_sections
            WHERE document_id = %s
            ORDER BY section_number
            """,
            (details["legal_document_id"],),
        )
        sec_rows = cur.fetchall()
    else:
        sec_rows = []

    found_sections = {r[0] for r in sec_rows}
    missing_sections = [s for s in EXPECTED_SECTIONS if s not in found_sections]
    unexpected_sections = sorted(found_sections - set(EXPECTED_SECTIONS))

    details["legal_sections_count"] = len(sec_rows)
    details["found_sections"] = sorted(found_sections)
    details["missing_sections"] = missing_sections
    details["unexpected_sections"] = unexpected_sections
    details["section_details"] = [
        {"section_number": r[0], "topic": r[1], "subtopic": r[2]} for r in sec_rows
    ]

    if missing_sections:
        failures.append(
            f"legal_sections: missing expected sections: {', '.join(missing_sections)}"
        )
    if unexpected_sections:
        failures.append(
            f"legal_sections: unexpected sections present: {', '.join(unexpected_sections)}"
        )

    # ------------------------------------------------------------------
    # 6. legal_chunks — one chunk per expected citation, all with
    #    embedding IS NULL and is_active = FALSE (first milestone)
    # ------------------------------------------------------------------
    if details.get("dataset_version_id") is not None and details.get("legal_document_id") is not None:
        cur.execute(
            """
            SELECT lc.citation, lc.is_active, lc.embedding IS NULL AS emb_null
            FROM legal_chunks lc
            JOIN legal_sections ls ON ls.id = lc.section_id
            WHERE ls.document_id = %s
              AND lc.dataset_version_id = %s
              AND lc.chunk_index = 0
            ORDER BY lc.citation
            """,
            (details["legal_document_id"], details["dataset_version_id"]),
        )
        chunk_rows = cur.fetchall()
    else:
        chunk_rows = []

    found_citations = {r[0] for r in chunk_rows}
    missing_chunks = [c for c in EXPECTED_CITATIONS if c not in found_citations]
    chunks_with_active = [r[0] for r in chunk_rows if r[1] is True]
    chunks_with_embedding = [r[0] for r in chunk_rows if r[2] is False]

    details["legal_chunks_count"] = len(chunk_rows)
    details["found_chunk_citations"] = sorted(found_citations)
    details["missing_chunks"] = missing_chunks
    details["chunks_with_active_true"] = chunks_with_active
    details["chunks_with_embedding_set"] = chunks_with_embedding

    if missing_chunks:
        failures.append(
            f"legal_chunks: missing chunks for citations: {', '.join(missing_chunks)}"
        )
    if chunks_with_active:
        failures.append(
            "legal_chunks: is_active = TRUE on chunks that should still be FALSE: "
            + ", ".join(chunks_with_active)
        )
    if chunks_with_embedding:
        failures.append(
            "legal_chunks: embedding is NOT NULL on chunks that should be NULL at this milestone: "
            + ", ".join(chunks_with_embedding)
        )

    # ------------------------------------------------------------------
    # 7. privacy_safe_answer_logs — ingestion must never write to this table
    # ------------------------------------------------------------------
    cur.execute("SELECT COUNT(*) FROM privacy_safe_answer_logs")
    psal_count: int = cur.fetchone()[0]
    details["privacy_safe_answer_logs_count"] = psal_count
    # Any rows here were not inserted by ingestion, but we flag it as
    # unexpected for this milestone where no Q&A features are active yet.
    if psal_count != 0:
        failures.append(
            f"privacy_safe_answer_logs: expected 0 rows at this milestone, "
            f"found {psal_count}"
        )

    return failures, details


# ---------------------------------------------------------------------------
# Report printing
# ---------------------------------------------------------------------------


def _print_report(
    failures: list[str],
    details: dict[str, Any],
    source_date: str,
) -> None:
    print(_DIVIDER)
    print("eCFR Title 8 DB insert validation")
    print("(Read-only. Validates public legal-source ingestion only.)")
    print(_DIVIDER)

    print(f"\n  source_date checked          : {source_date}")
    print(f"  dataset_version_id           : {details.get('dataset_version_id')}")
    print(f"  dataset_version_status       : {details.get('dataset_version_status')}")
    print(f"  source_registry_id           : {details.get('source_registry_id')}")
    print(f"  raw_document_id              : {details.get('raw_document_id')}")
    print(f"  raw_document sha256 (first8) : "
          + (details["raw_document_hash"][:8] + "..." if details.get("raw_document_hash") else "n/a"))
    print(f"  legal_document_id            : {details.get('legal_document_id')}")

    print(f"\n  Counts:")
    print(f"    raw_documents              : {details.get('raw_documents_count', 0)}")
    print(f"    legal_documents            : {details.get('legal_documents_count', 0)}")
    print(f"    legal_sections             : {details.get('legal_sections_count', 0)}")
    print(f"    legal_chunks               : {details.get('legal_chunks_count', 0)}")
    print(f"    privacy_safe_answer_logs   : {details.get('privacy_safe_answer_logs_count', 'n/a')}")

    sec_details = details.get("section_details", [])
    if sec_details:
        print(f"\n  Sections found ({len(sec_details)}):")
        for s in sec_details:
            marker = "OK" if s["section_number"] in details.get("found_sections", []) else "MISSING"
            print(
                f"    [{marker}] {s['section_number']:<10} "
                f"topic={s['topic'] or '<null>'}  subtopic={s['subtopic'] or '<null>'}"
            )

    missing_secs = details.get("missing_sections", [])
    if missing_secs:
        print(f"\n  Missing sections: {', '.join(missing_secs)}")

    missing_chunks = details.get("missing_chunks", [])
    if missing_chunks:
        print(f"\n  Missing chunks for: {', '.join(missing_chunks)}")

    active_chunks = details.get("chunks_with_active_true", [])
    if active_chunks:
        print(f"\n  Chunks unexpectedly active: {', '.join(active_chunks)}")

    emb_chunks = details.get("chunks_with_embedding_set", [])
    if emb_chunks:
        print(f"\n  Chunks unexpectedly have embeddings: {', '.join(emb_chunks)}")

    print()
    if failures:
        print(f"  status : FAIL ({len(failures)} issue(s))")
        for f in failures:
            print(f"    - {f}")
    else:
        print("  status : PASS")

    print(_DIVIDER)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    # ---- resolve database URL ----
    raw_url = _resolve_database_url(args.database_url)
    if not raw_url:
        print("ERROR: no DATABASE_URL found.")
        print(
            "       Set DATABASE_URL in the environment, pass --database-url, "
            "or add DATABASE_URL to backend/.env."
        )
        return 1
    db_url = _normalize_db_url(raw_url)

    # ---- connect and optionally resolve source_date ----
    try:
        with psycopg.connect(db_url, autocommit=True) as conn:
            with conn.cursor() as cur:

                # Resolve source_date from CLI arg or newest dataset_version
                if args.source_date:
                    source_date: str = args.source_date
                else:
                    cur.execute(
                        """
                        SELECT version_name
                        FROM dataset_versions
                        WHERE version_name LIKE 'ecfr-title8-sample-%'
                        ORDER BY started_at DESC
                        LIMIT 1
                        """,
                    )
                    row = cur.fetchone()
                    if row is None:
                        print(
                            "ERROR: no dataset_versions row matching "
                            "'ecfr-title8-sample-*' found in the database."
                        )
                        print(
                            "       Run insert_ecfr_preview_to_db.py first, "
                            "or pass --source-date YYYY-MM-DD."
                        )
                        return 1
                    # version_name is 'ecfr-title8-sample-YYYY-MM-DD'
                    source_date = row[0].removeprefix("ecfr-title8-sample-")

                failures, details = _run_checks(cur, source_date)

    except psycopg.OperationalError:
        print("ERROR: could not connect to PostgreSQL (psycopg.OperationalError).")
        print(
            "       Check that PostgreSQL is running and DATABASE_URL points to "
            "the correct host/database."
        )
        return 1
    except psycopg.Error as exc:
        print(f"ERROR: database query failed ({type(exc).__name__}): {exc}")
        return 1

    _print_report(failures, details, source_date)
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
