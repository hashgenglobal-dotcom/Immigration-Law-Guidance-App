#!/usr/bin/env python3
"""Activate a ready public eCFR dataset for retrieval.

Sets a reviewed, embedded dataset from 'ready' to 'active', flips
legal_chunks.is_active = TRUE for its chunks, and archives any previously
active dataset — all in one transaction.

Requires --yes to prevent accidental activation. Without --yes the script
prints the activation plan and exits 1 with instructions.

Privacy / Safety
----------------
This script activates ONLY reviewed public eCFR legal-source data.
- No user questions are processed.
- No answer logs are written (privacy_safe_answer_logs is never touched).
- No embeddings are generated or modified.
- No Ollama, OpenAI, Anthropic, or other AI APIs are called.
- No LLM calls happen during activation.
- Only dataset_versions and legal_chunks are written.

Usage
-----
    # Preview the activation plan without writing (exits 1 with instructions)
    uv run --project backend python scripts/activate_dataset.py

    # Activate (requires --yes)
    uv run --project backend python scripts/activate_dataset.py --yes

    # Activate a specific dataset version
    uv run --project backend python scripts/activate_dataset.py \\
        --dataset-version-name ecfr-title8-sample-2026-05-12 \\
        --yes

Exit codes
----------
* 0 — activation committed successfully (only when --yes is provided).
* 1 — --yes not provided (plan printed, no writes); pre-check failed;
      connection error; or transaction rolled back on any write failure.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

# psycopg (v3) is the only non-stdlib dependency.
# Run with: uv run --project backend python scripts/activate_dataset.py
try:
    import psycopg
except ImportError:
    print(
        "ERROR: psycopg (v3) is not installed in the current Python environment.\n"
        "       Run this script with:\n"
        "         uv run --project backend python scripts/activate_dataset.py"
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
            "Activate a ready public eCFR dataset for retrieval. "
            "Requires --yes to write. Without --yes, prints the plan and exits 1."
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
            "dataset_versions.version_name to activate. "
            "Default: newest ecfr-title8-sample-* row in the database."
        ),
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        default=False,
        help=(
            "Confirm activation and write to the database. "
            "Without this flag the script prints the plan and exits 1."
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
# Pre-activation checks (SELECT queries — used in both plan and write paths)
# ---------------------------------------------------------------------------


def _gather_facts(cur: Any, version_name_arg: str | None) -> dict[str, Any]:
    """Collect all facts needed for pre-checks and the activation plan.

    Reads only public legal-source metadata.
    No user questions are read. No database writes happen here.
    """
    facts: dict[str, Any] = {}

    # Resolve target dataset version
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
        facts["target_chunk_count"] = 0
        facts["chunks_with_embeddings"] = 0
        facts["chunks_correct_dim"] = 0
        facts["chunks_missing_embeddings"] = 0
        facts["chunks_wrong_dim"] = 0
        facts["target_active_chunk_count"] = 0
        facts["currently_active_datasets"] = []
        facts["privacy_safe_answer_logs_count"] = 0
        return facts

    facts["target_found"] = True
    facts["target_id"] = row[0]
    facts["target_name"] = row[1]
    facts["target_status"] = row[2]
    facts["target_activated_at"] = row[3]
    version_id: int = row[0]

    # Chunk counts for target dataset.
    # vector_dims() reads only the stored dimension — no vector data is pulled.
    # Only public eCFR chunk metadata is accessed.
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

    # Currently active datasets (will be archived on activation)
    cur.execute(
        "SELECT id, version_name FROM dataset_versions WHERE status = 'active' ORDER BY activated_at DESC NULLS LAST",
    )
    facts["currently_active_datasets"] = [
        {"id": r[0], "version_name": r[1]} for r in cur.fetchall()
    ]

    # privacy_safe_answer_logs row count — safety invariant only;
    # no content is read from this table.
    cur.execute("SELECT COUNT(*) FROM privacy_safe_answer_logs")
    facts["privacy_safe_answer_logs_count"] = cur.fetchone()[0]

    return facts


def _run_prechecks(facts: dict[str, Any]) -> list[str]:
    """Return a list of pre-check failures. Empty list means all checks pass."""
    failures: list[str] = []

    if not facts["target_found"]:
        label = facts["target_name"] or "ecfr-title8-sample-*"
        failures.append(
            f"target dataset {label!r} not found — "
            "run insert_ecfr_preview_to_db.py first"
        )
        return failures

    if facts["target_status"] != "ready":
        failures.append(
            f"target status is {facts['target_status']!r}; must be 'ready'"
        )

    if facts["target_chunk_count"] == 0:
        failures.append(
            "target dataset has no chunks — run insert_ecfr_preview_to_db.py first"
        )

    if facts["chunks_missing_embeddings"] > 0:
        failures.append(
            f"{facts['chunks_missing_embeddings']} chunk(s) have embedding IS NULL — "
            "run embed_legal_chunks.py first"
        )

    if facts["chunks_wrong_dim"] > 0:
        failures.append(
            f"{facts['chunks_wrong_dim']} chunk(s) have wrong embedding dimension "
            f"(expected {EXPECTED_DIM}) — re-embed with the correct model"
        )

    if facts["target_active_chunk_count"] > 0:
        failures.append(
            f"{facts['target_active_chunk_count']} chunk(s) in the target dataset "
            "are already is_active = TRUE — dataset may already be active"
        )

    if facts["privacy_safe_answer_logs_count"] != 0:
        failures.append(
            f"privacy_safe_answer_logs has {facts['privacy_safe_answer_logs_count']} row(s); "
            "expected 0 at this milestone"
        )

    return failures


# ---------------------------------------------------------------------------
# Activation writes (one transaction)
# ---------------------------------------------------------------------------


def _run_activation_writes(
    cur: Any,
    target_id: int,
    target_name: str,
) -> dict[str, Any]:
    """Execute all activation UPDATEs inside the caller's open transaction.

    Activation makes reviewed public chunks available for retrieval.
    No user questions are processed. No answer logs are written.
    No LLM calls happen. Only dataset_versions and legal_chunks are modified.

    Returns a dict with counts for the summary report.
    """
    # Step 1: Collect IDs of currently active datasets before modifying anything.
    cur.execute(
        "SELECT id, version_name FROM dataset_versions WHERE status = 'active'",
    )
    previously_active = cur.fetchall()
    previously_active_ids = [r[0] for r in previously_active]

    # Step 2: Deactivate chunks belonging to previously active datasets.
    deactivated_chunk_count = 0
    if previously_active_ids:
        cur.execute(
            "UPDATE legal_chunks SET is_active = FALSE WHERE dataset_version_id = ANY(%s)",
            (previously_active_ids,),
        )
        deactivated_chunk_count = cur.rowcount

    # Step 3: Archive previously active dataset versions.
    archived_dataset_count = 0
    if previously_active_ids:
        cur.execute(
            "UPDATE dataset_versions SET status = 'archived' WHERE id = ANY(%s)",
            (previously_active_ids,),
        )
        archived_dataset_count = cur.rowcount

    # Step 4: Promote target dataset to active.
    cur.execute(
        """
        UPDATE dataset_versions
        SET status = 'active', activated_at = NOW()
        WHERE id = %s
        """,
        (target_id,),
    )

    # Step 5: Activate all chunks belonging to the target dataset.
    cur.execute(
        "UPDATE legal_chunks SET is_active = TRUE WHERE dataset_version_id = %s",
        (target_id,),
    )
    activated_chunk_count = cur.rowcount

    return {
        "archived_dataset_count": archived_dataset_count,
        "archived_dataset_names": [r[1] for r in previously_active],
        "deactivated_chunk_count": deactivated_chunk_count,
        "activated_chunk_count": activated_chunk_count,
    }


# ---------------------------------------------------------------------------
# Report printing
# ---------------------------------------------------------------------------


def _print_plan(facts: dict[str, Any], failures: list[str]) -> None:
    """Print the activation plan (used in both no-confirm and pre-check-fail paths)."""
    print(_DIVIDER)
    print("activate_dataset.py — activation plan (no writes yet)")
    print("(Public legal-source data only. No user data. No LLM calls.)")
    print(_DIVIDER)

    print(f"\n[Target dataset]")
    print(f"  dataset_version_id   : {facts['target_id']}")
    print(f"  dataset_version_name : {facts['target_name']}")
    print(f"  current status       : {facts['target_status']}")
    print(f"  activated_at         : {facts['target_activated_at']}")

    print(f"\n[Target chunks]")
    print(f"  total chunks         : {facts['target_chunk_count']}")
    print(f"  with embeddings      : {facts['chunks_with_embeddings']}")
    print(f"  correct dim ({EXPECTED_DIM})   : {facts['chunks_correct_dim']}")
    print(f"  missing embeddings   : {facts['chunks_missing_embeddings']}")
    print(f"  wrong dimension      : {facts['chunks_wrong_dim']}")
    print(f"  currently active     : {facts['target_active_chunk_count']}")

    print(f"\n[Currently active datasets — would be archived]")
    if facts["currently_active_datasets"]:
        for ds in facts["currently_active_datasets"]:
            print(f"  {ds['version_name']} (id={ds['id']})")
    else:
        print("  (none)")

    print(f"\n[privacy_safe_answer_logs count] : {facts['privacy_safe_answer_logs_count']}")

    print(f"\n[Writes that would be committed with --yes]")
    if facts["currently_active_datasets"]:
        for ds in facts["currently_active_datasets"]:
            print(
                f"  UPDATE dataset_versions SET status = 'archived'"
                f" WHERE id = {ds['id']}  -- {ds['version_name']}"
            )
        print(
            f"  UPDATE legal_chunks SET is_active = FALSE"
            f" WHERE dataset_version_id = ANY({[ds['id'] for ds in facts['currently_active_datasets']]})"
        )
    if facts["target_id"] is not None:
        print(
            f"  UPDATE dataset_versions SET status = 'active', activated_at = NOW()"
            f" WHERE id = {facts['target_id']}"
        )
        print(
            f"  UPDATE legal_chunks SET is_active = TRUE"
            f" WHERE dataset_version_id = {facts['target_id']}"
            f"  -- {facts['target_chunk_count']} chunk(s)"
        )
    print("  -- all in one transaction; rolls back on any failure --")
    print("  privacy_safe_answer_logs : NOT written")

    if failures:
        print(f"\n[Pre-check failures — {len(failures)}]")
        for f in failures:
            print(f"  ! {f}")

    print()
    print(_DIVIDER)


def _print_summary(
    facts: dict[str, Any],
    result: dict[str, Any],
) -> None:
    print(_DIVIDER)
    print("Activation complete")
    print(_DIVIDER)
    print(f"\n  activated dataset_version_id   : {facts['target_id']}")
    print(f"  activated dataset_version_name : {facts['target_name']}")
    print(f"  chunks activated               : {result['activated_chunk_count']}")
    print(f"  datasets archived              : {result['archived_dataset_count']}")
    if result["archived_dataset_names"]:
        for name in result["archived_dataset_names"]:
            print(f"    - {name}")
    print(f"  chunks deactivated (archived)  : {result['deactivated_chunk_count']}")
    print()
    print("  Only public eCFR legal-source data was activated.")
    print("  legal_chunks.is_active = TRUE on target dataset only.")
    print("  privacy_safe_answer_logs       : not read or written")
    print()
    print("  Next: run validate_active_dataset.py to confirm.")
    print(_DIVIDER)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    # ---- resolve and normalize database URL ----
    raw_url = _resolve_database_url(args.database_url)
    if not raw_url:
        print("ERROR: no DATABASE_URL found.")
        print(
            "       Set DATABASE_URL in the environment, pass --database-url, "
            "or add DATABASE_URL to backend/.env."
        )
        return 1
    db_url = _normalize_db_url(raw_url)

    # ---- no-confirm path: gather facts, print plan, exit 1 ----
    if not args.yes:
        try:
            with psycopg.connect(db_url, autocommit=True) as conn:
                with conn.cursor() as cur:
                    facts = _gather_facts(cur, args.dataset_version_name)
        except psycopg.OperationalError:
            print("ERROR: could not connect to PostgreSQL (psycopg.OperationalError).")
            print("       Check that PostgreSQL is running and DATABASE_URL is correct.")
            return 1
        except psycopg.Error as exc:
            print(f"ERROR: database query failed ({type(exc).__name__}): {exc}")
            return 1

        failures = _run_prechecks(facts)
        _print_plan(facts, failures)
        print(
            "Dry-run complete. No changes were made.\n"
            "Re-run with --yes to activate:\n"
            "  uv run --project backend python scripts/activate_dataset.py --yes"
        )
        return 1

    # ---- activation path: one transaction with pre-checks inside ----
    facts: dict[str, Any] = {}
    result: dict[str, Any] = {}

    try:
        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:

                # Gather facts inside the transaction so the pre-checks and
                # writes see a consistent snapshot of the database.
                facts = _gather_facts(cur, args.dataset_version_name)
                failures = _run_prechecks(facts)

                if failures:
                    _print_plan(facts, failures)
                    print(
                        f"ERROR: {len(failures)} pre-check(s) failed — "
                        "activation aborted."
                    )
                    # Raising here triggers psycopg3's rollback on __exit__.
                    raise _PreCheckError("pre-checks failed")

                # All checks passed — execute activation writes.
                result = _run_activation_writes(
                    cur,
                    target_id=facts["target_id"],
                    target_name=facts["target_name"],
                )

                # Transaction commits here on clean exit of the with block.

    except _PreCheckError:
        # Already printed the failure details above.
        print("Transaction rolled back. No changes were made.")
        return 1

    except psycopg.OperationalError:
        # OperationalError messages may contain the DSN — print class name only.
        print("\nERROR: could not connect to PostgreSQL (psycopg.OperationalError).")
        print("       Check that PostgreSQL is running and DATABASE_URL is correct.")
        return 1

    except psycopg.Error as exc:
        print(f"\nERROR: database write failed ({type(exc).__name__}): {exc}")
        print("Transaction rolled back. No changes were made.")
        return 1

    _print_summary(facts, result)
    return 0


# ---------------------------------------------------------------------------
# Internal exception
# ---------------------------------------------------------------------------


class _PreCheckError(Exception):
    """Raised inside the transaction when pre-checks fail, to trigger rollback."""


if __name__ == "__main__":
    sys.exit(main())
