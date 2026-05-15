#!/usr/bin/env python3
"""Validate that public eCFR legal_chunks have correct 768-dimensional embeddings.

This script is read-only. It issues only SELECT queries and never inserts,
updates, or deletes anything. Run it after embed_legal_chunks.py to confirm
the embedding phase completed correctly before proceeding to activation or
retrieval testing.

Privacy
-------
This script validates public legal-source embeddings only.
- It does NOT read or store user questions.
- It does NOT read privacy_safe_answer_logs content — it only verifies the
  row count is 0, confirming that no Q&A activity has occurred.
- It does NOT generate embeddings.
- It does NOT call Ollama, OpenAI, Anthropic, or any public AI API.
- No database writes happen in this script.

Usage
-----
    # Auto-detect dataset version and DB URL from backend/.env
    uv run --project backend python scripts/validate_legal_chunk_embeddings.py

    # Explicit dataset version
    uv run --project backend python scripts/validate_legal_chunk_embeddings.py \\
        --dataset-version-name ecfr-title8-sample-2026-05-12

    # Explicit database URL
    uv run --project backend python scripts/validate_legal_chunk_embeddings.py \\
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
# Run with: uv run --project backend python scripts/validate_legal_chunk_embeddings.py
try:
    import psycopg
except ImportError:
    print(
        "ERROR: psycopg (v3) is not installed in the current Python environment.\n"
        "       Run this script with:\n"
        "         uv run --project backend python scripts/validate_legal_chunk_embeddings.py"
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BACKEND_ENV_PATH = Path("backend/.env")

# Full citations expected in legal_chunks after the embedding milestone.
EXPECTED_CITATIONS: tuple[str, ...] = (
    "8 CFR § 208.7",
    "8 CFR § 208.4",
    "8 CFR § 245.1",
    "8 CFR § 274a.12",
    "8 CFR § 239.1",
)

EXPECTED_DIM = 768  # must match legal_chunks.embedding vector(768)

_DIVIDER = "-" * 72


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only validation of legal_chunks embeddings. "
            "Checks that public eCFR chunks have correct 768-dim embeddings "
            "and remain inactive. Never reads user data."
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
            "dataset_versions.version_name to validate. "
            "Default: newest ecfr-title8-sample-* row in the database."
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
    version_name_arg: str | None,
) -> tuple[list[str], dict[str, Any]]:
    """Run all validation SELECT queries. Returns (failures, details).

    This function validates public legal-source embeddings only.
    No user questions are read. No database writes happen.
    No LLM or embedding calls are made.
    """
    failures: list[str] = []
    details: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # 1. Resolve dataset version — find the target row
    # ------------------------------------------------------------------
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
        label = version_name_arg or "ecfr-title8-sample-*"
        failures.append(
            f"dataset_versions: no row matching {label!r} — "
            "run insert_ecfr_preview_to_db.py first"
        )
        details["dataset_version_id"] = None
        details["dataset_version_name"] = version_name_arg
        details["dataset_version_status"] = None
        # Cannot proceed without a valid dataset_version_id
        return failures, details

    version_id, version_name, version_status = row
    details["dataset_version_id"] = version_id
    details["dataset_version_name"] = version_name
    details["dataset_version_status"] = version_status

    # ------------------------------------------------------------------
    # 2. Dataset status must be 'ready' or 'active'
    # ------------------------------------------------------------------
    if version_status not in ("ready", "active"):
        failures.append(
            f"dataset_versions: status is {version_status!r}; "
            "expected 'ready' or 'active'"
        )

    # ------------------------------------------------------------------
    # 3–7. Query legal_chunks for expected citations in this dataset version.
    #
    # vector_dims(embedding) is a pgvector function that returns the number
    # of dimensions stored in the vector column. We use it here rather than
    # pulling the full vector to the client, keeping the query lightweight.
    #
    # Only public eCFR chunk metadata is read — no user questions, no
    # privacy_safe_answer_logs content.
    # ------------------------------------------------------------------
    cur.execute(
        """
        SELECT
            citation,
            is_active,
            embedding IS NOT NULL                                  AS has_embedding,
            CASE
                WHEN embedding IS NOT NULL THEN vector_dims(embedding)
                ELSE NULL
            END                                                    AS embedding_dim
        FROM legal_chunks
        WHERE dataset_version_id = %s
          AND citation = ANY(%s)
        ORDER BY citation
        """,
        (version_id, list(EXPECTED_CITATIONS)),
    )
    chunk_rows = cur.fetchall()

    # Index by citation for easy lookup
    found: dict[str, dict[str, Any]] = {
        r[0]: {"is_active": r[1], "has_embedding": r[2], "embedding_dim": r[3]}
        for r in chunk_rows
    }

    details["expected_chunk_count"] = len(EXPECTED_CITATIONS)
    details["found_chunk_count"] = len(found)

    missing_citations = [c for c in EXPECTED_CITATIONS if c not in found]
    no_embedding = [c for c in EXPECTED_CITATIONS if c in found and not found[c]["has_embedding"]]
    wrong_dim = [
        c for c in EXPECTED_CITATIONS
        if c in found and found[c]["has_embedding"] and found[c]["embedding_dim"] != EXPECTED_DIM
    ]
    active_chunks = [c for c in EXPECTED_CITATIONS if c in found and found[c]["is_active"]]

    details["missing_citations"] = missing_citations
    details["chunks_missing_embedding"] = no_embedding
    details["chunks_wrong_dimension"] = wrong_dim
    details["chunks_active"] = active_chunks
    details["chunk_detail"] = [
        {
            "citation": c,
            "has_embedding": found[c]["has_embedding"] if c in found else None,
            "embedding_dim": found[c]["embedding_dim"] if c in found else None,
            "is_active": found[c]["is_active"] if c in found else None,
        }
        for c in EXPECTED_CITATIONS
    ]

    # 3. All expected citations must exist as chunks
    if missing_citations:
        failures.append(
            f"legal_chunks: missing expected citations: "
            + ", ".join(missing_citations)
        )

    # 4. Every expected chunk must have a non-NULL embedding
    if no_embedding:
        failures.append(
            "legal_chunks: embedding IS NULL on chunk(s) — "
            "run embed_legal_chunks.py first: "
            + ", ".join(no_embedding)
        )

    # 5. Every embedding must be exactly 768 dimensions
    if wrong_dim:
        bad_dims = ", ".join(
            f"{c} (dim={found[c]['embedding_dim']})" for c in wrong_dim
        )
        failures.append(
            f"legal_chunks: wrong embedding dimension on chunk(s) — "
            f"expected {EXPECTED_DIM}: {bad_dims}"
        )

    # 6. No chunk should be active at this milestone (activation is a separate step)
    if active_chunks:
        failures.append(
            "legal_chunks: is_active = TRUE on chunk(s) that should remain FALSE "
            "at the embedding milestone: "
            + ", ".join(active_chunks)
        )

    # ------------------------------------------------------------------
    # 7. privacy_safe_answer_logs must have 0 rows at this milestone
    #    (only the row count is read — no content is accessed)
    # ------------------------------------------------------------------
    cur.execute("SELECT COUNT(*) FROM privacy_safe_answer_logs")
    psal_count: int = cur.fetchone()[0]
    details["privacy_safe_answer_logs_count"] = psal_count
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
) -> None:
    print(_DIVIDER)
    print("legal_chunks embedding validation")
    print("(Read-only. Public legal-source data only. No user data accessed.)")
    print(_DIVIDER)

    print(f"\n  dataset_version_id     : {details.get('dataset_version_id')}")
    print(f"  dataset_version_name   : {details.get('dataset_version_name')}")
    print(f"  dataset status         : {details.get('dataset_version_status')}")
    print(f"  expected chunk count   : {details.get('expected_chunk_count', len(EXPECTED_CITATIONS))}")
    print(f"  chunks found           : {details.get('found_chunk_count', 0)}")

    chunk_detail = details.get("chunk_detail", [])
    if chunk_detail:
        print(f"\n  Per-chunk result:")
        for cd in chunk_detail:
            citation = cd["citation"]
            has_emb = cd["has_embedding"]
            dim = cd["embedding_dim"]
            active = cd["is_active"]

            if has_emb is None:
                status_tag = "MISSING"
            elif not has_emb:
                status_tag = "NO EMB"
            elif dim != EXPECTED_DIM:
                status_tag = f"BAD DIM ({dim})"
            elif active:
                status_tag = "ACTIVE (unexpected)"
            else:
                status_tag = f"OK  dim={dim}  active={active}"

            print(f"    [{status_tag:<24}] {citation}")

    missing = details.get("missing_citations", [])
    if missing:
        print(f"\n  Missing citations     : {', '.join(missing)}")

    no_emb = details.get("chunks_missing_embedding", [])
    if no_emb:
        print(f"  Embedding IS NULL    : {', '.join(no_emb)}")

    wrong = details.get("chunks_wrong_dimension", [])
    if wrong:
        print(f"  Wrong dimension      : {', '.join(wrong)}")

    active = details.get("chunks_active", [])
    if active:
        print(f"  Unexpectedly active  : {', '.join(active)}")

    print(f"\n  privacy_safe_answer_logs count : {details.get('privacy_safe_answer_logs_count', 'n/a')}")

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

    # ---- connect and run checks ----
    try:
        with psycopg.connect(db_url, autocommit=True) as conn:
            with conn.cursor() as cur:
                failures, details = _run_checks(cur, args.dataset_version_name)

    except psycopg.OperationalError:
        # OperationalError messages may contain the DSN — print class name only.
        print("ERROR: could not connect to PostgreSQL (psycopg.OperationalError).")
        print(
            "       Check that PostgreSQL is running and DATABASE_URL is correct."
        )
        return 1
    except psycopg.Error as exc:
        print(f"ERROR: database query failed ({type(exc).__name__}): {exc}")
        return 1

    _print_report(failures, details)
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
