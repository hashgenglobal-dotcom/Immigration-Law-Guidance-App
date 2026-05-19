#!/usr/bin/env python3
"""Validate that exactly one dataset is active and its public legal_chunks are retrieval-ready.

This script is read-only. It issues only SELECT queries and never inserts,
updates, or deletes anything. Run it after activate_dataset.py to confirm
the activation phase completed correctly before proceeding to retrieval testing.

Privacy
-------
This script validates public legal-source retrieval readiness only.
- It does NOT read or store user questions.
- It does NOT read privacy_safe_answer_logs content — it only verifies the
  row count is 0, confirming that no Q&A activity has occurred.
- It does NOT generate embeddings.
- It does NOT call Ollama, OpenAI, Anthropic, or any public AI API.
- No database writes happen in this script.

Usage
-----
    # Auto-detect DB URL from backend/.env
    uv run --project backend python scripts/validate_active_dataset.py

    # Explicit database URL
    uv run --project backend python scripts/validate_active_dataset.py \\
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
# Run with: uv run --project backend python scripts/validate_active_dataset.py
try:
    import psycopg
except ImportError:
    print(
        "ERROR: psycopg (v3) is not installed in the current Python environment.\n"
        "       Run this script with:\n"
        "         uv run --project backend python scripts/validate_active_dataset.py"
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BACKEND_ENV_PATH = Path("backend/.env")

# Expected citations in the active dataset at this milestone.
# These must all exist as legal_chunks with is_active = TRUE after activation.
EXPECTED_CITATIONS: tuple[str, ...] = (
    "8 CFR § 208.7",
    "8 CFR § 208.4",
    "8 CFR § 245.1",
    "8 CFR § 274a.12",
    "8 CFR § 239.1",
)

EXPECTED_CHUNK_COUNT = 5  # milestone: exactly 5 eCFR Title 8 sample chunks
EXPECTED_DIM = 768        # must match legal_chunks.embedding vector(768)

_DIVIDER = "-" * 72


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only validation of the active dataset's retrieval readiness. "
            "Confirms exactly one dataset is active, all its public legal chunks "
            "are marked is_active = TRUE with 768-dim embeddings, and expected "
            "citations are present. Never reads user data."
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


def _run_checks(cur: Any) -> tuple[list[str], dict[str, Any]]:
    """Run all validation SELECT queries. Returns (failures, details).

    This function validates public legal-source retrieval readiness only.
    No user questions are read. No database writes happen.
    No LLM or embedding calls are made.
    """
    failures: list[str] = []
    details: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # 1. Exactly one dataset_versions row must have status = 'active'.
    #
    # The one-active-at-a-time rule is enforced by activate_dataset.py
    # via transaction ordering, but this check catches any drift.
    # ------------------------------------------------------------------
    cur.execute(
        """
        SELECT id, version_name, status, activated_at
        FROM dataset_versions
        WHERE status = 'active'
        ORDER BY activated_at DESC NULLS LAST
        """,
    )
    active_rows = cur.fetchall()
    active_count = len(active_rows)
    details["active_dataset_count"] = active_count

    if active_count == 0:
        failures.append(
            "dataset_versions: no row has status = 'active' — "
            "run activate_dataset.py --yes first"
        )
        # Cannot proceed with chunk checks without an active dataset.
        details["active_dataset_id"] = None
        details["active_dataset_name"] = None
        details["active_dataset_status"] = None
        details["active_dataset_activated_at"] = None
        details["total_chunks"] = None
        details["active_chunks"] = None
        details["chunks_with_embedding"] = None
        details["chunks_correct_dim"] = None
        details["missing_citations"] = list(EXPECTED_CITATIONS)
        details["chunks_not_active"] = []
        details["chunks_missing_embedding"] = []
        details["chunks_wrong_dimension"] = []
        details["leaked_active_chunks"] = None
        details["privacy_safe_answer_logs_count"] = None
        details["chunk_detail"] = []
        return failures, details

    if active_count > 1:
        extra_names = ", ".join(r[1] for r in active_rows)
        failures.append(
            f"dataset_versions: {active_count} rows have status = 'active'; "
            f"expected exactly 1 — found: {extra_names}"
        )

    # Use the most recently activated dataset for all subsequent checks.
    active_id, active_name, active_status, active_activated_at = active_rows[0]
    details["active_dataset_id"] = active_id
    details["active_dataset_name"] = active_name
    details["active_dataset_status"] = active_status
    details["active_dataset_activated_at"] = str(active_activated_at) if active_activated_at else None

    # ------------------------------------------------------------------
    # 2. activated_at must be non-NULL on the active dataset.
    # ------------------------------------------------------------------
    if active_activated_at is None:
        failures.append(
            f"dataset_versions: activated_at IS NULL on active dataset "
            f"{active_name!r} — activation may not have completed"
        )

    # ------------------------------------------------------------------
    # 3–7. Aggregate chunk counts for the active dataset.
    #
    # vector_dims(embedding) is a pgvector function that returns the number
    # of dimensions stored without pulling the full vector to the client.
    # Only public eCFR chunk metadata is read — no user questions,
    # no privacy_safe_answer_logs content.
    # ------------------------------------------------------------------
    cur.execute(
        """
        SELECT
            COUNT(*)                                                     AS total,
            COUNT(*) FILTER (WHERE is_active = TRUE)                    AS active_count,
            COUNT(*) FILTER (WHERE embedding IS NOT NULL)               AS with_emb,
            COUNT(*) FILTER (
                WHERE embedding IS NOT NULL
                  AND vector_dims(embedding) = %s
            )                                                            AS correct_dim
        FROM legal_chunks
        WHERE dataset_version_id = %s
        """,
        (EXPECTED_DIM, active_id),
    )
    row = cur.fetchone()
    total, active_chunk_count, with_emb, correct_dim = row
    details["total_chunks"] = total
    details["active_chunks"] = active_chunk_count
    details["chunks_with_embedding"] = with_emb
    details["chunks_correct_dim"] = correct_dim

    # 3. Active dataset must have at least 1 chunk.
    if total == 0:
        failures.append(
            f"legal_chunks: active dataset {active_name!r} has no chunks — "
            "run insert_ecfr_preview_to_db.py first"
        )

    # 4. Active dataset must have exactly EXPECTED_CHUNK_COUNT chunks at this milestone.
    if total != EXPECTED_CHUNK_COUNT:
        failures.append(
            f"legal_chunks: active dataset has {total} chunk(s); "
            f"expected exactly {EXPECTED_CHUNK_COUNT} at this milestone"
        )

    # 5. All chunks in the active dataset must have is_active = TRUE.
    inactive_count = total - active_chunk_count
    if inactive_count > 0:
        failures.append(
            f"legal_chunks: {inactive_count} chunk(s) in the active dataset "
            "still have is_active = FALSE — activation may not have completed"
        )

    # 6. All chunks must have embedding IS NOT NULL.
    missing_emb_count = total - with_emb
    if missing_emb_count > 0:
        failures.append(
            f"legal_chunks: {missing_emb_count} chunk(s) have embedding IS NULL — "
            "run embed_legal_chunks.py before activating"
        )

    # 7. All embeddings must be 768-dimensional.
    wrong_dim_count = with_emb - correct_dim
    if wrong_dim_count > 0:
        failures.append(
            f"legal_chunks: {wrong_dim_count} chunk(s) have wrong embedding "
            f"dimension (expected {EXPECTED_DIM}) — re-embed with the correct model"
        )

    # ------------------------------------------------------------------
    # 8. Expected citations must all be present and correctly activated.
    #
    # Per-citation check: each expected citation must exist as a chunk with
    # is_active = TRUE, embedding IS NOT NULL, and vector_dims = 768.
    # ------------------------------------------------------------------
    cur.execute(
        """
        SELECT
            citation,
            is_active,
            embedding IS NOT NULL                                    AS has_embedding,
            CASE
                WHEN embedding IS NOT NULL THEN vector_dims(embedding)
                ELSE NULL
            END                                                      AS embedding_dim
        FROM legal_chunks
        WHERE dataset_version_id = %s
          AND citation = ANY(%s)
        ORDER BY citation
        """,
        (active_id, list(EXPECTED_CITATIONS)),
    )
    citation_rows = cur.fetchall()

    found: dict[str, dict[str, Any]] = {
        r[0]: {"is_active": r[1], "has_embedding": r[2], "embedding_dim": r[3]}
        for r in citation_rows
    }

    missing_citations = [c for c in EXPECTED_CITATIONS if c not in found]
    chunks_not_active = [
        c for c in EXPECTED_CITATIONS if c in found and not found[c]["is_active"]
    ]
    chunks_missing_embedding = [
        c for c in EXPECTED_CITATIONS if c in found and not found[c]["has_embedding"]
    ]
    chunks_wrong_dimension = [
        c for c in EXPECTED_CITATIONS
        if c in found
        and found[c]["has_embedding"]
        and found[c]["embedding_dim"] != EXPECTED_DIM
    ]

    details["missing_citations"] = missing_citations
    details["chunks_not_active"] = chunks_not_active
    details["chunks_missing_embedding"] = chunks_missing_embedding
    details["chunks_wrong_dimension"] = chunks_wrong_dimension
    details["chunk_detail"] = [
        {
            "citation": c,
            "is_active": found[c]["is_active"] if c in found else None,
            "has_embedding": found[c]["has_embedding"] if c in found else None,
            "embedding_dim": found[c]["embedding_dim"] if c in found else None,
        }
        for c in EXPECTED_CITATIONS
    ]

    if missing_citations:
        failures.append(
            "legal_chunks: missing expected citations: "
            + ", ".join(missing_citations)
        )

    if chunks_not_active:
        failures.append(
            "legal_chunks: is_active = FALSE on expected chunk(s): "
            + ", ".join(chunks_not_active)
        )

    if chunks_missing_embedding:
        failures.append(
            "legal_chunks: embedding IS NULL on expected chunk(s): "
            + ", ".join(chunks_missing_embedding)
        )

    if chunks_wrong_dimension:
        bad = ", ".join(
            f"{c} (dim={found[c]['embedding_dim']})" for c in chunks_wrong_dimension
        )
        failures.append(
            f"legal_chunks: wrong embedding dimension on chunk(s) — "
            f"expected {EXPECTED_DIM}: {bad}"
        )

    # ------------------------------------------------------------------
    # 9. No chunks from other dataset versions should have is_active = TRUE.
    #
    # Activation archives the old active dataset, which should also have
    # set its chunks to is_active = FALSE. Any leakage here means the
    # deactivation step in activate_dataset.py did not complete.
    # ------------------------------------------------------------------
    cur.execute(
        """
        SELECT COUNT(*)
        FROM legal_chunks
        WHERE is_active = TRUE
          AND dataset_version_id != %s
        """,
        (active_id,),
    )
    leaked: int = cur.fetchone()[0]
    details["leaked_active_chunks"] = leaked

    if leaked > 0:
        failures.append(
            f"legal_chunks: {leaked} chunk(s) from other dataset versions "
            "still have is_active = TRUE — deactivation of old datasets may "
            "not have completed"
        )

    # ------------------------------------------------------------------
    # 10. privacy_safe_answer_logs must have 0 rows at this milestone.
    #     Only the row count is read — no content is accessed.
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


def _print_report(failures: list[str], details: dict[str, Any]) -> None:
    print(_DIVIDER)
    print("active dataset validation")
    print("(Read-only. Public legal-source data only. No user data accessed.)")
    print(_DIVIDER)

    print(f"\n[Active dataset]")
    print(f"  active_dataset_count   : {details.get('active_dataset_count')}")
    print(f"  active_dataset_id      : {details.get('active_dataset_id')}")
    print(f"  active_dataset_name    : {details.get('active_dataset_name')}")
    print(f"  status                 : {details.get('active_dataset_status')}")
    print(f"  activated_at           : {details.get('active_dataset_activated_at')}")

    print(f"\n[Chunk counts — active dataset]")
    print(f"  total chunks           : {details.get('total_chunks')}")
    print(f"  chunks is_active=TRUE  : {details.get('active_chunks')}")
    print(f"  chunks with embedding  : {details.get('chunks_with_embedding')}")
    print(f"  chunks dim={EXPECTED_DIM}        : {details.get('chunks_correct_dim')}")

    chunk_detail = details.get("chunk_detail", [])
    if chunk_detail:
        print(f"\n[Per-citation result]")
        for cd in chunk_detail:
            citation = cd["citation"]
            is_active = cd["is_active"]
            has_emb = cd["has_embedding"]
            dim = cd["embedding_dim"]

            if is_active is None:
                tag = "MISSING"
            elif not has_emb:
                tag = "NO EMB"
            elif dim != EXPECTED_DIM:
                tag = f"BAD DIM ({dim})"
            elif not is_active:
                tag = "NOT ACTIVE"
            else:
                tag = f"OK  dim={dim}  active={is_active}"

            print(f"    [{tag:<26}] {citation}")

    print(f"\n[Global state]")
    print(f"  leaked active chunks   : {details.get('leaked_active_chunks')}")
    print(f"  privacy_safe_answer_logs count : {details.get('privacy_safe_answer_logs_count')}")

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
                failures, details = _run_checks(cur)

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
