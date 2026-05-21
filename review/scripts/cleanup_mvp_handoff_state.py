#!/usr/bin/env python3
"""Deactivate eCFR sample and BIA datasets after Supabase handoff.

Dry-run by default. Pass --apply to commit changes.

Safety constraints:
  - Never deletes rows.
  - Never truncates tables.
  - Never touches user data or privacy logs.
  - Never prints DATABASE_URL or credentials.
  - All writes execute in a single transaction; rolled back on any error.

Changes applied with --apply:
  - legal_chunks.is_active = FALSE for ecfr-title8-sample% datasets
  - legal_chunks.is_active = FALSE for bia% datasets
  - dataset_versions.status  = 'archived' for bia% datasets

Usage
-----
    uv run --project backend python review/scripts/cleanup_mvp_handoff_state.py
    uv run --project backend python review/scripts/cleanup_mvp_handoff_state.py --apply
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

BACKEND_ENV_PATH = Path("backend/.env")
_DIVIDER = "-" * 72

try:
    import psycopg
except ImportError:
    print(
        "ERROR: psycopg (v3) is not installed.\n"
        "       Run: uv run --project backend python review/scripts/cleanup_mvp_handoff_state.py"
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# DB URL helpers (never print the URL)
# ---------------------------------------------------------------------------

def _read_env_file(path: Path) -> dict[str, str]:
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


def _resolve_db_url(arg_url: str | None) -> str | None:
    if arg_url:
        return arg_url
    val = os.environ.get("DATABASE_URL")
    if val:
        return val
    return _read_env_file(BACKEND_ENV_PATH).get("DATABASE_URL")


def _normalize_db_url(url: str) -> str:
    for prefix in ("postgresql+psycopg://", "postgres+psycopg://"):
        if url.startswith(prefix):
            scheme = prefix.split("+")[0]
            return scheme + "://" + url[len(prefix):]
    return url


# ---------------------------------------------------------------------------
# Count helpers (read-only SELECT)
# ---------------------------------------------------------------------------

def _count_sample_active(cur: Any) -> int:
    cur.execute(
        """
        SELECT COUNT(*)
        FROM legal_chunks lc
        JOIN dataset_versions dv ON dv.id = lc.dataset_version_id
        WHERE dv.version_name LIKE %s
          AND lc.is_active = TRUE
        """,
        ("ecfr-title8-sample%",),
    )
    return cur.fetchone()[0]


def _count_bia_active(cur: Any) -> int:
    cur.execute(
        """
        SELECT COUNT(*)
        FROM legal_chunks lc
        JOIN dataset_versions dv ON dv.id = lc.dataset_version_id
        WHERE dv.version_name ILIKE %s
          AND lc.is_active = TRUE
        """,
        ("bia%",),
    )
    return cur.fetchone()[0]


def _count_bia_datasets_not_archived(cur: Any) -> int:
    cur.execute(
        "SELECT COUNT(*) FROM dataset_versions WHERE version_name ILIKE %s AND status != 'archived'",
        ("bia%",),
    )
    return cur.fetchone()[0]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Deactivate eCFR sample and BIA datasets (dry-run by default)"
    )
    parser.add_argument("--database-url", default=None, help="Override DATABASE_URL")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Commit changes (default: dry-run, no writes)",
    )
    args = parser.parse_args(argv)

    raw_url = _resolve_db_url(args.database_url)
    if not raw_url:
        print("ERROR: no DATABASE_URL found. Set it in the environment or backend/.env.")
        return 1
    db_url = _normalize_db_url(raw_url)

    mode = "[APPLY]" if args.apply else "[DRY-RUN]"
    print(_DIVIDER)
    print(f"MVP handoff cleanup {mode}")
    print("(Never deletes rows. Never truncates. Never touches user data.)")
    print(_DIVIDER)

    try:
        with psycopg.connect(db_url, autocommit=True) as read_conn:
            with read_conn.cursor() as cur:
                sample_before = _count_sample_active(cur)
                bia_active_before = _count_bia_active(cur)
                bia_not_archived = _count_bia_datasets_not_archived(cur)
    except psycopg.OperationalError:
        print("ERROR: could not connect to PostgreSQL (psycopg.OperationalError).")
        print("       Check that the database is reachable and DATABASE_URL is correct.")
        return 1
    except psycopg.Error as exc:
        print(f"ERROR: database error ({type(exc).__name__}): {exc}")
        return 1

    print(f"\n[Before]")
    print(f"  eCFR sample active chunks        : {sample_before}")
    print(f"  BIA active chunks                : {bia_active_before}")
    print(f"  BIA dataset versions (not archived): {bia_not_archived}")

    if not args.apply:
        print(f"\n[Planned actions — dry-run]")
        if sample_before > 0:
            print(f"  would set is_active=FALSE on {sample_before} eCFR sample chunk(s)")
        else:
            print("  eCFR sample chunks already inactive — no action needed")
        if bia_active_before > 0:
            print(f"  would set is_active=FALSE on {bia_active_before} BIA chunk(s)")
        else:
            print("  BIA chunks already inactive — no action needed")
        if bia_not_archived > 0:
            print(f"  would set status='archived' on {bia_not_archived} BIA dataset version(s)")
        else:
            print("  BIA dataset versions already archived — no action needed")
        print("\nRun with --apply to commit these changes.")
        print(_DIVIDER)
        return 0

    # Apply all changes in a single transaction; roll back on any error.
    try:
        with psycopg.connect(db_url, autocommit=False) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE legal_chunks
                    SET is_active = FALSE
                    WHERE dataset_version_id IN (
                        SELECT id FROM dataset_versions
                        WHERE version_name LIKE %s
                    )
                      AND is_active = TRUE
                    """,
                    ("ecfr-title8-sample%",),
                )
                sample_deactivated = cur.rowcount

                cur.execute(
                    """
                    UPDATE legal_chunks
                    SET is_active = FALSE
                    WHERE dataset_version_id IN (
                        SELECT id FROM dataset_versions
                        WHERE version_name ILIKE %s
                    )
                      AND is_active = TRUE
                    """,
                    ("bia%",),
                )
                bia_chunks_deactivated = cur.rowcount

                cur.execute(
                    """
                    UPDATE dataset_versions
                    SET status = 'archived'
                    WHERE version_name ILIKE %s
                      AND status != 'archived'
                    """,
                    ("bia%",),
                )
                bia_versions_archived = cur.rowcount

            conn.commit()

    except psycopg.OperationalError:
        print("ERROR: could not connect to PostgreSQL (psycopg.OperationalError).")
        return 1
    except Exception as exc:
        print(f"\nERROR: transaction rolled back — {type(exc).__name__}: {exc}")
        return 1

    print(f"\n[Applied]")
    print(f"  eCFR sample chunks deactivated   : {sample_deactivated}")
    print(f"  BIA chunks deactivated           : {bia_chunks_deactivated}")
    print(f"  BIA dataset versions archived    : {bia_versions_archived}")

    # After counts (fresh read connection)
    try:
        with psycopg.connect(db_url, autocommit=True) as read_conn:
            with read_conn.cursor() as cur:
                sample_after = _count_sample_active(cur)
                bia_after = _count_bia_active(cur)
    except psycopg.Error as exc:
        print(f"WARN: could not read after-counts ({type(exc).__name__}): {exc}")
        print(_DIVIDER)
        return 0

    print(f"\n[After]")
    print(f"  eCFR sample active chunks : {sample_after}")
    print(f"  BIA active chunks         : {bia_after}")

    if sample_after > 0 or bia_after > 0:
        print("\nWARN: some chunks still active after cleanup — investigate manually")
        print(_DIVIDER)
        return 1

    print(_DIVIDER)
    return 0


if __name__ == "__main__":
    sys.exit(main())
