#!/usr/bin/env python3
"""Dry-run readiness check for dataset activation.

Inspects a ready dataset and prints exactly what the future activation script
would do — without writing to the database, without changing any status, and
without touching any chunk's is_active flag.

Privacy
-------
This script checks public legal-source data only.
- It does NOT read user questions.
- It does NOT read privacy_safe_answer_logs content — it only verifies the
  row count is 0 as a safety invariant.
- It does NOT generate embeddings.
- It does NOT call Ollama, OpenAI, Anthropic, or any public AI API.
- No database writes happen in this dry-run. No activation happens.

Usage
-----
    # Auto-detect dataset version and DB URL from backend/.env
    uv run --project backend python scripts/dry_run_activate_dataset.py

    # Explicit dataset version
    uv run --project backend python scripts/dry_run_activate_dataset.py \\
        --dataset-version-name ecfr-title8-sample-2026-05-12

    # Explicit database URL
    uv run --project backend python scripts/dry_run_activate_dataset.py \\
        --database-url "postgresql://user@localhost:5432/immigration_law_dev"

Exit codes
----------
* 0 — dry-run completed (including when the dataset is NOT ready; readiness
      issues are shown in the report but do not cause a non-zero exit).
* 1 — database config missing, connection failed, or query failed.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

# psycopg (v3) is the only non-stdlib dependency.
# Run with: uv run --project backend python scripts/dry_run_activate_dataset.py
try:
    import psycopg
except ImportError:
    print(
        "ERROR: psycopg (v3) is not installed in the current Python environment.\n"
        "       Run this script with:\n"
        "         uv run --project backend python scripts/dry_run_activate_dataset.py"
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BACKEND_ENV_PATH = Path("backend/.env")
EXPECTED_DIM = 768  # must match legal_chunks.embedding vector(768)

_DIVIDER = "-" * 72


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Dry-run readiness check for dataset activation. "
            "Read-only: no database writes, no chunk activation."
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


def _gather_facts(
    cur: Any,
    version_name_arg: str | None,
) -> dict[str, Any]:
    """Run all SELECT queries and return a flat facts dict.

    This function reads only public legal-source metadata.
    No user questions are read. No database writes happen.
    No LLM or embedding calls are made.
    """
    facts: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # 1. Resolve target dataset version
    # ------------------------------------------------------------------
    if version_name_arg:
        cur.execute(
            """
            SELECT id, version_name, status, activated_at
            FROM dataset_versions
            WHERE version_name = %s
            """,
            (version_name_arg,),
        )
    else:
        cur.execute(
            """
            SELECT id, version_name, status, activated_at
            FROM dataset_versions
            WHERE version_name LIKE 'ecfr-title8-sample-%'
            ORDER BY started_at DESC
            LIMIT 1
            """,
        )
    row = cur.fetchone()

    if row is None:
        facts["target_found"] = False
        facts["target_id"] = None
        facts["target_name"] = version_name_arg
        facts["target_status"] = None
        facts["target_activated_at"] = None
    else:
        facts["target_found"] = True
        facts["target_id"] = row[0]
        facts["target_name"] = row[1]
        facts["target_status"] = row[2]
        facts["target_activated_at"] = row[3]

    if not facts["target_found"]:
        # Cannot proceed with chunk queries without a valid dataset_version_id.
        facts["target_chunk_count"] = 0
        facts["chunks_with_embeddings"] = 0
        facts["chunks_correct_dim"] = 0
        facts["chunks_missing_embeddings"] = 0
        facts["chunks_wrong_dim"] = 0
        facts["target_active_chunk_count"] = 0
        facts["currently_active_dataset_count"] = 0
        facts["currently_active_dataset_names"] = []
        facts["global_active_chunk_count"] = 0
        facts["privacy_safe_answer_logs_count"] = 0
        return facts

    version_id: int = facts["target_id"]

    # ------------------------------------------------------------------
    # 2. Chunk counts for the target dataset version.
    #
    # vector_dims(embedding) is a pgvector function that returns the
    # number of stored dimensions without pulling the full vector.
    # Only public eCFR chunk metadata is read here.
    # ------------------------------------------------------------------
    cur.execute(
        """
        SELECT
            COUNT(*)                                                    AS total,
            COUNT(*) FILTER (WHERE embedding IS NOT NULL)              AS with_emb,
            COUNT(*) FILTER (
                WHERE embedding IS NOT NULL
                  AND vector_dims(embedding) = %s
            )                                                           AS correct_dim,
            COUNT(*) FILTER (WHERE is_active = TRUE)                   AS active
        FROM legal_chunks
        WHERE dataset_version_id = %s
        """,
        (EXPECTED_DIM, version_id),
    )
    row = cur.fetchone()
    total, with_emb, correct_dim, active = row
    facts["target_chunk_count"] = total
    facts["chunks_with_embeddings"] = with_emb
    facts["chunks_correct_dim"] = correct_dim
    facts["chunks_missing_embeddings"] = total - with_emb
    facts["chunks_wrong_dim"] = with_emb - correct_dim
    facts["target_active_chunk_count"] = active

    # ------------------------------------------------------------------
    # 3. Currently active datasets (other than or including the target)
    # ------------------------------------------------------------------
    cur.execute(
        """
        SELECT id, version_name
        FROM dataset_versions
        WHERE status = 'active'
        ORDER BY activated_at DESC NULLS LAST
        """,
    )
    active_dv_rows = cur.fetchall()
    facts["currently_active_dataset_count"] = len(active_dv_rows)
    facts["currently_active_dataset_names"] = [r[1] for r in active_dv_rows]

    # ------------------------------------------------------------------
    # 4. Global count of active chunks (across all dataset versions)
    # ------------------------------------------------------------------
    cur.execute("SELECT COUNT(*) FROM legal_chunks WHERE is_active = TRUE")
    facts["global_active_chunk_count"] = cur.fetchone()[0]

    # ------------------------------------------------------------------
    # 5. privacy_safe_answer_logs row count (safety invariant only —
    #    no content is read from this table)
    # ------------------------------------------------------------------
    cur.execute("SELECT COUNT(*) FROM privacy_safe_answer_logs")
    facts["privacy_safe_answer_logs_count"] = cur.fetchone()[0]

    return facts


# ---------------------------------------------------------------------------
# Readiness evaluation
# ---------------------------------------------------------------------------


def _evaluate_readiness(facts: dict[str, Any]) -> list[str]:
    """Return a list of readiness issues. Empty list means READY."""
    issues: list[str] = []

    if not facts["target_found"]:
        label = facts["target_name"] or "ecfr-title8-sample-*"
        issues.append(
            f"target dataset {label!r} not found — "
            "run insert_ecfr_preview_to_db.py first"
        )
        return issues  # no further checks possible

    if facts["target_status"] != "ready":
        issues.append(
            f"target dataset status is {facts['target_status']!r}; "
            "must be 'ready' before activation"
        )

    if facts["target_chunk_count"] == 0:
        issues.append(
            "target dataset has no chunks — "
            "run insert_ecfr_preview_to_db.py first"
        )

    if facts["chunks_missing_embeddings"] > 0:
        issues.append(
            f"{facts['chunks_missing_embeddings']} chunk(s) have embedding IS NULL — "
            "run embed_legal_chunks.py first"
        )

    if facts["chunks_wrong_dim"] > 0:
        issues.append(
            f"{facts['chunks_wrong_dim']} chunk(s) have wrong embedding dimension "
            f"(expected {EXPECTED_DIM}) — re-embed with the correct model"
        )

    if facts["target_active_chunk_count"] > 0:
        issues.append(
            f"{facts['target_active_chunk_count']} chunk(s) in the target dataset "
            "are already is_active = TRUE — dataset may already be active"
        )

    if facts["privacy_safe_answer_logs_count"] != 0:
        issues.append(
            f"privacy_safe_answer_logs has {facts['privacy_safe_answer_logs_count']} row(s); "
            "expected 0 at this milestone"
        )

    return issues


# ---------------------------------------------------------------------------
# Report printing
# ---------------------------------------------------------------------------


def _print_report(facts: dict[str, Any], issues: list[str]) -> None:
    is_ready = len(issues) == 0

    print(_DIVIDER)
    print("DRY-RUN: dataset activation readiness check")
    print("(No database writes. No chunk activation. Public legal-source data only.)")
    print(_DIVIDER)

    print(f"\n[Target dataset]")
    print(f"  dataset_version_id     : {facts['target_id']}")
    print(f"  dataset_version_name   : {facts['target_name']}")
    print(f"  current status         : {facts['target_status']}")
    print(f"  activated_at           : {facts['target_activated_at']}")

    print(f"\n[Target chunk state]")
    print(f"  total chunks           : {facts['target_chunk_count']}")
    print(f"  chunks with embeddings : {facts['chunks_with_embeddings']}")
    print(f"  chunks correct dim 768 : {facts['chunks_correct_dim']}")
    print(f"  chunks missing emb     : {facts['chunks_missing_embeddings']}")
    print(f"  chunks wrong dim       : {facts['chunks_wrong_dim']}")
    print(f"  target chunks active   : {facts['target_active_chunk_count']}")

    print(f"\n[Global state]")
    print(f"  active dataset count   : {facts['currently_active_dataset_count']}")
    if facts["currently_active_dataset_names"]:
        for name in facts["currently_active_dataset_names"]:
            print(f"    - {name}")
    print(f"  global active chunks   : {facts['global_active_chunk_count']}")
    print(f"  privacy_safe_answer_logs count : {facts['privacy_safe_answer_logs_count']}")

    # Readiness verdict
    print(f"\n[Readiness]")
    if is_ready:
        print("  READY — all preconditions satisfied")
    else:
        print(f"  NOT READY — {len(issues)} issue(s):")
        for issue in issues:
            print(f"    ! {issue}")

    # What the activation script would do (shown even when not ready, for planning)
    print(f"\n[What activate_dataset.py would do]")
    if facts["target_found"] and facts["currently_active_dataset_names"]:
        for name in facts["currently_active_dataset_names"]:
            if name != facts["target_name"]:
                print(
                    f"  UPDATE dataset_versions SET status = 'archived' "
                    f"WHERE version_name = '{name}'"
                )
    if facts["target_found"]:
        print(
            f"  UPDATE dataset_versions SET status = 'active', activated_at = NOW() "
            f"WHERE version_name = '{facts['target_name']}'"
        )
        print(
            f"  UPDATE legal_chunks SET is_active = TRUE "
            f"WHERE dataset_version_id = {facts['target_id']}"
        )
        print(f"  (affects {facts['target_chunk_count']} chunk(s))")
    print("  -- all in one transaction; rolls back on any failure --")
    print("  privacy_safe_answer_logs : NOT touched")

    print()
    print(_DIVIDER)


def _print_json_summary(facts: dict[str, Any], issues: list[str]) -> None:
    status = "dry_run_ok" if not issues else "dry_run_not_ready"
    summary: dict[str, Any] = {
        "status": status,
        "would_write": False,
        "would_activate_dataset": facts.get("target_name"),
        "target_chunk_count": facts.get("target_chunk_count", 0),
        "chunks_with_embeddings": facts.get("chunks_with_embeddings", 0),
        "chunks_missing_embeddings": facts.get("chunks_missing_embeddings", 0),
        "privacy_safe_answer_logs_count": facts.get("privacy_safe_answer_logs_count", 0),
    }
    if issues:
        summary["readiness_issues"] = issues
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

    # ---- connect and gather facts ----
    try:
        with psycopg.connect(db_url, autocommit=True) as conn:
            with conn.cursor() as cur:
                facts = _gather_facts(cur, args.dataset_version_name)

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

    # ---- evaluate readiness and print ----
    issues = _evaluate_readiness(facts)
    _print_report(facts, issues)
    _print_json_summary(facts, issues)

    # Exit 0 even when not ready — the dry-run itself completed successfully.
    # Only DB config/connection/query failures cause exit 1.
    return 0


if __name__ == "__main__":
    sys.exit(main())
