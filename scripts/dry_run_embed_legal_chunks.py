#!/usr/bin/env python3
"""Dry-run inspection of legal_chunks that need embeddings.

This script connects to PostgreSQL (read-only) and prints which public eCFR
legal_chunks have embedding IS NULL for a given dataset version, along with
what the embedding step would do. It does NOT call Ollama, does NOT generate
embeddings, and does NOT write to the database.

Privacy
-------
This script inspects public eCFR regulatory text only.
- It does NOT read user questions.
- It does NOT read or write privacy_safe_answer_logs content — it only
  checks the row count as a safety invariant.
- It does NOT generate embeddings.
- It does NOT call Ollama, OpenAI, Anthropic, or any public AI API.
- No database writes happen in this dry-run.

Usage
-----
    # Auto-detect dataset version and DB URL from backend/.env
    uv run --project backend python scripts/dry_run_embed_legal_chunks.py

    # Explicit dataset version name
    uv run --project backend python scripts/dry_run_embed_legal_chunks.py \\
        --dataset-version-name ecfr-title8-sample-2026-05-12

    # Explicit DB URL and limit output to first 3 chunks
    uv run --project backend python scripts/dry_run_embed_legal_chunks.py \\
        --database-url "postgresql://user@localhost:5432/immigration_law_dev" \\
        --limit 3

Exit codes
----------
* 0 — dry-run completed successfully; report printed.
* 1 — database config missing, connection failed, dataset not found, or
      query failed.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

# psycopg (v3) is the only non-stdlib dependency.
# Run with: uv run --project backend python scripts/dry_run_embed_legal_chunks.py
try:
    import psycopg
except ImportError:
    print(
        "ERROR: psycopg (v3) is not installed in the current Python environment.\n"
        "       Run this script with:\n"
        "         uv run --project backend python scripts/dry_run_embed_legal_chunks.py"
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BACKEND_ENV_PATH = Path("backend/.env")

# Planned embedding model for the embed_legal_chunks.py step.
# Shown in the dry-run report so it is easy to verify before running.
EMBEDDING_MODEL = "nomic-embed-text"
EMBEDDING_DIM = 768

_DIVIDER = "-" * 72


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Dry-run inspection of legal_chunks needing embeddings. "
            "Read-only: no Ollama calls, no database writes."
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
        "--dataset-version-name",
        default=None,
        metavar="ecfr-title8-sample-YYYY-MM-DD",
        help=(
            "dataset_versions.version_name to inspect. "
            "Default: newest ecfr-title8-sample-* row in the database."
        ),
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help=(
            "Limit the number of chunks shown in the per-chunk detail section. "
            "Does not affect counts or the JSON summary."
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
# Database queries (all read-only SELECT queries)
# ---------------------------------------------------------------------------


def _resolve_dataset_version(
    cur: Any,
    version_name_arg: str | None,
) -> tuple[int, str, str] | None:
    """Return (dataset_version_id, version_name, status) or None if not found."""
    if version_name_arg:
        cur.execute(
            "SELECT id, version_name, status FROM dataset_versions WHERE version_name = %s",
            (version_name_arg,),
        )
    else:
        cur.execute(
            """
            SELECT id, version_name, status
            FROM dataset_versions
            WHERE version_name LIKE 'ecfr-title8-sample-%'
            ORDER BY started_at DESC
            LIMIT 1
            """,
        )
    row = cur.fetchone()
    if row is None:
        return None
    return row[0], row[1], row[2]


def _fetch_null_embedding_chunks(
    cur: Any,
    dataset_version_id: int,
) -> list[dict[str, Any]]:
    """Fetch legal_chunks where embedding IS NULL for the given dataset version.

    Only public eCFR regulatory text from legal_chunks is queried here.
    No user questions and no private data are accessed.
    """
    cur.execute(
        """
        SELECT
            lc.id,
            lc.citation,
            lc.topic,
            lc.subtopic,
            lc.risk_level,
            lc.is_active,
            lc.chunk_text,
            octet_length(lc.chunk_text::bytea) AS text_byte_len
        FROM legal_chunks lc
        WHERE lc.dataset_version_id = %s
          AND lc.embedding IS NULL
        ORDER BY lc.id
        """,
        (dataset_version_id,),
    )
    rows = cur.fetchall()
    results = []
    for row in rows:
        chunk_id, citation, topic, subtopic, risk_level, is_active, chunk_text, byte_len = row
        text_str: str = chunk_text or ""
        results.append(
            {
                "id": chunk_id,
                "citation": citation,
                "topic": topic,
                "subtopic": subtopic,
                "risk_level": risk_level,
                "is_active": is_active,
                "text_length": byte_len,
                "text_preview": text_str[:160],
            }
        )
    return results


def _fetch_embedded_count(cur: Any, dataset_version_id: int) -> int:
    """Count legal_chunks where embedding IS NOT NULL for the given dataset version."""
    cur.execute(
        """
        SELECT COUNT(*)
        FROM legal_chunks
        WHERE dataset_version_id = %s
          AND embedding IS NOT NULL
        """,
        (dataset_version_id,),
    )
    return cur.fetchone()[0]


def _fetch_active_count(cur: Any, dataset_version_id: int) -> int:
    """Count legal_chunks where is_active = TRUE for the given dataset version."""
    cur.execute(
        """
        SELECT COUNT(*)
        FROM legal_chunks
        WHERE dataset_version_id = %s
          AND is_active = TRUE
        """,
        (dataset_version_id,),
    )
    return cur.fetchone()[0]


def _fetch_psal_count(cur: Any) -> int:
    """Count rows in privacy_safe_answer_logs (should be 0 at this milestone).

    This is a safety invariant check only — no content is read from this table.
    """
    cur.execute("SELECT COUNT(*) FROM privacy_safe_answer_logs")
    return cur.fetchone()[0]


# ---------------------------------------------------------------------------
# Report printing
# ---------------------------------------------------------------------------


def _print_report(
    version_id: int,
    version_name: str,
    version_status: str,
    null_chunks: list[dict[str, Any]],
    embedded_count: int,
    active_count: int,
    psal_count: int,
    limit: int | None,
) -> None:
    print(_DIVIDER)
    print("DRY-RUN: legal_chunks embedding inspection")
    print("(No Ollama calls. No embeddings generated. No database writes.)")
    print(_DIVIDER)

    print(f"\n[Dataset version]")
    print(f"  dataset_version_id   : {version_id}")
    print(f"  dataset_version_name : {version_name}")
    print(f"  status               : {version_status}")

    print(f"\n[Planned embedding model]")
    print(f"  model                : {EMBEDDING_MODEL}")
    print(f"  expected dimension   : {EMBEDDING_DIM}")
    print(f"  Ollama endpoint      : http://localhost:11434 (local only)")

    print(f"\n[Chunk summary]")
    print(f"  chunks needing embedding (embedding IS NULL) : {len(null_chunks)}")
    print(f"  chunks already embedded  (embedding NOT NULL): {embedded_count}")
    print(f"  chunks with is_active = TRUE                 : {active_count}")
    print(f"  privacy_safe_answer_logs row count           : {psal_count}")

    # ---- warnings ----
    warnings: list[str] = []
    if len(null_chunks) == 0:
        warnings.append(
            "No chunks need embeddings for this dataset version. "
            "Either embeddings are already complete or no chunks were inserted."
        )
    already_active = [c for c in null_chunks if c["is_active"]]
    if already_active:
        warnings.append(
            f"{len(already_active)} chunk(s) have is_active = TRUE but embedding IS NULL. "
            "Chunks should not be active before embeddings are generated."
        )
    if psal_count != 0:
        warnings.append(
            f"privacy_safe_answer_logs has {psal_count} row(s). "
            "Expected 0 at this milestone (no Q&A features active yet)."
        )

    if warnings:
        print(f"\n[WARNINGS — {len(warnings)}]")
        for w in warnings:
            print(f"  ! {w}")

    # ---- per-chunk detail ----
    display_chunks = null_chunks[:limit] if limit is not None else null_chunks
    truncated = limit is not None and limit < len(null_chunks)

    if display_chunks:
        shown_label = f"{len(display_chunks)} of {len(null_chunks)}" if truncated else str(len(display_chunks))
        print(f"\n[Chunks needing embedding — showing {shown_label}]")
        for i, chunk in enumerate(display_chunks, 1):
            print(f"\n  --- chunk {i} ---")
            print(f"    id           : {chunk['id']}")
            print(f"    citation     : {chunk['citation']}")
            print(f"    topic        : {chunk['topic'] or '<null>'}")
            print(f"    subtopic     : {chunk['subtopic'] or '<null>'}")
            print(f"    risk_level   : {chunk['risk_level'] or '<null>'}")
            print(f"    text_length  : {chunk['text_length']} bytes")
            print(f"    is_active    : {chunk['is_active']}")
            preview = chunk["text_preview"].replace("\n", " ")
            print(f"    text_preview : {preview!r}")
        if truncated:
            print(f"\n  (... {len(null_chunks) - len(display_chunks)} more chunks — remove --limit to see all)")

    print()
    print(_DIVIDER)


def _print_json_summary(
    version_id: int,
    version_name: str,
    version_status: str,
    null_count: int,
    embedded_count: int,
    active_count: int,
    psal_count: int,
) -> None:
    summary: dict[str, Any] = {
        "status": "dry_run_ok",
        "dataset_version_id": version_id,
        "dataset_version_name": version_name,
        "dataset_version_status": version_status,
        "embedding_model": EMBEDDING_MODEL,
        "expected_dimension": EMBEDDING_DIM,
        "chunks_needing_embedding": null_count,
        "chunks_already_embedded": embedded_count,
        "chunks_active": active_count,
        "privacy_safe_answer_logs_count": psal_count,
        "would_write": False,
        "would_call_ollama": False,
    }
    print(json.dumps(summary, indent=2))


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

    # ---- connect and query ----
    try:
        with psycopg.connect(db_url, autocommit=True) as conn:
            with conn.cursor() as cur:

                # Resolve dataset version
                version_row = _resolve_dataset_version(cur, args.dataset_version_name)
                if version_row is None:
                    if args.dataset_version_name:
                        print(
                            f"ERROR: dataset_versions row {args.dataset_version_name!r} not found."
                        )
                    else:
                        print(
                            "ERROR: no dataset_versions row matching "
                            "'ecfr-title8-sample-*' found in the database."
                        )
                    print(
                        "       Run insert_ecfr_preview_to_db.py first, "
                        "or pass --dataset-version-name."
                    )
                    return 1

                version_id, version_name, version_status = version_row

                # All queries below read only public eCFR chunk text.
                # No user questions and no private data are accessed.
                null_chunks = _fetch_null_embedding_chunks(cur, version_id)
                embedded_count = _fetch_embedded_count(cur, version_id)
                active_count = _fetch_active_count(cur, version_id)
                psal_count = _fetch_psal_count(cur)

    except psycopg.OperationalError:
        # OperationalError message may contain the DSN — print class name only.
        print("ERROR: could not connect to PostgreSQL (psycopg.OperationalError).")
        print(
            "       Check that PostgreSQL is running and DATABASE_URL points to "
            "the correct host/database."
        )
        return 1
    except psycopg.Error as exc:
        print(f"ERROR: database query failed ({type(exc).__name__}): {exc}")
        return 1

    # ---- print human-readable report ----
    _print_report(
        version_id=version_id,
        version_name=version_name,
        version_status=version_status,
        null_chunks=null_chunks,
        embedded_count=embedded_count,
        active_count=active_count,
        psal_count=psal_count,
        limit=args.limit,
    )

    # ---- print compact JSON summary ----
    _print_json_summary(
        version_id=version_id,
        version_name=version_name,
        version_status=version_status,
        null_count=len(null_chunks),
        embedded_count=embedded_count,
        active_count=active_count,
        psal_count=psal_count,
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
