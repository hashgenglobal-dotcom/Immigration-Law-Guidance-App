#!/usr/bin/env python3
"""Clear dev/test rows from privacy_safe_answer_logs before MVP demo.

Privacy
-------
- Never SELECTs or prints question/answer text columns (schema has none).
- Only reports row counts, column names, hash presence, and timestamps.
- TRUNCATE removes all rows; does not drop the table.

Usage
-----
    # Inspect schema and row count (no writes)
    uv run --project backend python review/scripts/clear_privacy_safe_answer_logs.py --inspect

    # Show what would be deleted
    uv run --project backend python review/scripts/clear_privacy_safe_answer_logs.py --dry-run

    # Delete all rows (MVP demo prep)
    uv run --project backend python review/scripts/clear_privacy_safe_answer_logs.py --execute

Exit codes
----------
* 0 — completed successfully
* 1 — database error or unexpected raw-text columns detected
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Any

try:
    import psycopg
except ImportError:
    print(
        "ERROR: psycopg (v3) required.\n"
        "  uv run --project backend python review/scripts/clear_privacy_safe_answer_logs.py --inspect"
    )
    sys.exit(1)

BACKEND_ENV_PATH = Path("backend/.env")
TABLE = "privacy_safe_answer_logs"

# Columns that must not exist (legacy full-text logging).
_FORBIDDEN_COLUMNS = frozenset({
    "question_text",
    "answer_text",
    "raw_question",
    "raw_answer",
    "user_message",
    "assistant_message",
    "prompt_text",
    "response_text",
})


def _normalize_database_url(database_url: str) -> str:
    """postgresql+psycopg://... → postgresql://... for libpq."""
    return re.sub(r"^postgresql\+[a-zA-Z0-9_]+://", "postgresql://", database_url)


def _load_database_url(explicit: str | None) -> str:
    if explicit:
        return _normalize_database_url(explicit)
    if BACKEND_ENV_PATH.is_file():
        for line in BACKEND_ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("DATABASE_URL=") and not line.startswith("#"):
                return _normalize_database_url(
                    line.split("=", 1)[1].strip().strip('"').strip("'")
                )
    url = os.environ.get("DATABASE_URL")
    if url:
        return _normalize_database_url(url)
    print("ERROR: DATABASE_URL not set and backend/.env not found.")
    sys.exit(1)


def _connect(dsn: str) -> psycopg.Connection[Any]:
    return psycopg.connect(dsn)


def _fetch_schema(cur: psycopg.Cursor[Any]) -> list[tuple[str, str]]:
    cur.execute(
        """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s
        ORDER BY ordinal_position
        """,
        (TABLE,),
    )
    return list(cur.fetchall())


def _inspect(cur: psycopg.Cursor[Any]) -> dict[str, Any]:
    cols = _fetch_schema(cur)
    col_names = [c[0] for c in cols]
    forbidden = [c for c in col_names if c in _FORBIDDEN_COLUMNS]
    if forbidden:
        raise RuntimeError(
            f"{TABLE} has forbidden raw-text columns: {forbidden}. "
            "Do not run cleanup until logging code is fixed."
        )

    cur.execute(f"SELECT COUNT(*) FROM {TABLE}")
    count = cur.fetchone()[0]

    hash_info: dict[str, Any] = {}
    for name in ("question_hash", "answer_hash"):
        if name in col_names:
            cur.execute(
                f"""
                SELECT COUNT(*) FILTER (WHERE {name} IS NOT NULL),
                       MIN(length({name}::text)),
                       MAX(length({name}::text))
                FROM {TABLE}
                """
            )
            populated, min_len, max_len = cur.fetchone()
            hash_info[name] = {
                "populated": populated,
                "len_min": min_len,
                "len_max": max_len,
            }

    ts_range = None
    if "created_at" in col_names:
        cur.execute(f"SELECT MIN(created_at), MAX(created_at) FROM {TABLE}")
        ts_range = cur.fetchone()

    return {
        "columns": cols,
        "row_count": count,
        "hash_info": hash_info,
        "created_at_range": ts_range,
        "has_raw_text_columns": False,
    }


def _print_inspect(facts: dict[str, Any]) -> None:
    print(f"\n[{TABLE}] schema (no row content printed)")
    for name, dtype in facts["columns"]:
        print(f"  {name}: {dtype}")
    print(f"\n  row_count            : {facts['row_count']}")
    print(f"  raw_text_columns     : none (forbidden set absent)")
    for hname, info in facts.get("hash_info", {}).items():
        print(
            f"  {hname}              : populated={info['populated']} "
            f"len={info['len_min']}..{info['len_max']}"
        )
    if facts.get("created_at_range"):
        print(f"  created_at range     : {facts['created_at_range'][0]} .. {facts['created_at_range'][1]}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=f"Inspect or clear {TABLE}")
    parser.add_argument("--database-url", default=None)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--inspect", action="store_true", help="Schema + counts only")
    mode.add_argument("--dry-run", action="store_true", help="Report rows that would be removed")
    mode.add_argument("--execute", action="store_true", help="TRUNCATE all rows")
    args = parser.parse_args(argv)

    dsn = _load_database_url(args.database_url)

    with _connect(dsn) as conn:
        with conn.cursor() as cur:
            facts = _inspect(cur)
            _print_inspect(facts)

            if args.inspect:
                return 0

            count = facts["row_count"]
            if count == 0:
                print("\n  Nothing to clear — table already empty.")
                return 0

            if args.dry_run:
                print(f"\n  DRY-RUN: would TRUNCATE {count} row(s) from {TABLE}.")
                print("  Run with --execute to apply.")
                return 0

            # --execute
            cur.execute(f"TRUNCATE TABLE {TABLE} RESTART IDENTITY CASCADE")
            conn.commit()
            cur.execute(f"SELECT COUNT(*) FROM {TABLE}")
            after = cur.fetchone()[0]
            print(f"\n  EXECUTE: truncated {count} row(s). remaining={after}")
            if after != 0:
                print("  ERROR: table not empty after TRUNCATE.")
                return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
