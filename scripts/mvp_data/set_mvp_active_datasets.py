#!/usr/bin/env python3
"""Set MVP dataset versions to 'active' and demote sample datasets to 'ready'.

Finds dataset_versions rows matching the three MVP prefixes:
  - ecfr-title8-full-*  → set status = 'active', is_active = TRUE on chunks
  - ina-*               → set status = 'active', is_active = TRUE on chunks
  - uscis-pm-*          → set status = 'active', is_active = TRUE on chunks

Also sets any ecfr-title8-sample-* row to status = 'ready' and flips
is_active = FALSE on its chunks.

Does NOT delete any rows. Does NOT touch any other dataset versions.
Requires --apply; otherwise prints the plan and exits 1.

Privacy / Safety
----------------
This script writes ONLY to dataset_versions.status and legal_chunks.is_active.
It does NOT:
  - read or write user questions or privacy_safe_answer_logs
  - delete any data
  - generate embeddings or call any AI API
  - print DATABASE_URL, passwords, or any credential

Usage
-----
    # Dry-run — show what would change without writing
    uv run --project backend python scripts/mvp_data/set_mvp_active_datasets.py

    # Apply changes
    uv run --project backend python scripts/mvp_data/set_mvp_active_datasets.py --apply

    # Explicit DB URL
    uv run --project backend python scripts/mvp_data/set_mvp_active_datasets.py \\
        --database-url "postgresql://user@localhost:5432/immigration_law_dev" \\
        --apply

Exit codes
----------
* 0 — --apply: changes committed successfully.
      dry-run: plan printed, no writes.
* 1 — connection error, no DATABASE_URL, or no matching datasets found.
      --apply not provided (plan printed, instructions given).
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

try:
    import psycopg
except ImportError:
    print(
        "ERROR: psycopg (v3) is not installed.\n"
        "       Run with: uv run --project backend python scripts/mvp_data/set_mvp_active_datasets.py"
    )
    sys.exit(1)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BACKEND_ENV_PATH = Path("backend/.env")

MVP_ACTIVATE_PREFIXES = ("ecfr-title8-full-", "ina-", "uscis-pm-")
SAMPLE_DEMOTE_PREFIX = "ecfr-title8-sample-"

_DIV = "-" * 72


# ---------------------------------------------------------------------------
# .env / URL helpers
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


def _resolve_database_url(arg_url: str | None) -> str | None:
    if arg_url:
        return arg_url
    env_val = os.environ.get("DATABASE_URL")
    if env_val:
        return env_val
    return _read_env_file(BACKEND_ENV_PATH).get("DATABASE_URL")


def _normalize_db_url(url: str) -> str:
    for prefix in ("postgresql+psycopg://", "postgres+psycopg://"):
        if url.startswith(prefix):
            scheme = prefix.split("+")[0]
            return scheme + "://" + url[len(prefix):]
    return url


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Set MVP dataset versions active and demote sample datasets.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--database-url",
        metavar="DSN",
        help="PostgreSQL DSN. Defaults to DATABASE_URL env var, then backend/.env.",
    )
    p.add_argument(
        "--apply",
        action="store_true",
        help="Write changes to the database. Without this flag, only a dry-run plan is shown.",
    )
    return p.parse_args(argv)


# ---------------------------------------------------------------------------
# Plan builder (read-only)
# ---------------------------------------------------------------------------


def _build_plan(cur: Any) -> dict[str, Any]:
    """Query current state and return the proposed change plan."""
    cur.execute(
        """
        SELECT id, version_name, status
        FROM dataset_versions
        ORDER BY version_name
        """
    )
    rows = cur.fetchall()

    to_activate: list[dict[str, Any]] = []
    to_demote: list[dict[str, Any]] = []
    already_active: list[dict[str, Any]] = []
    already_demoted: list[dict[str, Any]] = []

    for ds_id, name, status in rows:
        entry = {"id": ds_id, "version_name": name, "current_status": status}
        if any(name.startswith(p) for p in MVP_ACTIVATE_PREFIXES):
            if status == "active":
                already_active.append(entry)
            else:
                to_activate.append(entry)
        elif name.startswith(SAMPLE_DEMOTE_PREFIX):
            if status == "ready":
                already_demoted.append(entry)
            else:
                to_demote.append(entry)

    return {
        "to_activate": to_activate,
        "to_demote": to_demote,
        "already_active": already_active,
        "already_demoted": already_demoted,
    }


def _print_plan(plan: dict[str, Any], apply: bool) -> None:
    mode = "APPLY MODE" if apply else "DRY-RUN (no writes)"
    print(_DIV)
    print(f"MVP DATASET ACTIVATION PLAN  —  {mode}")
    print(_DIV)

    if plan["to_activate"]:
        print(f"\nWill SET TO ACTIVE ({len(plan['to_activate'])} dataset(s)):")
        for d in plan["to_activate"]:
            print(f"  {d['version_name']!r:<50}  {d['current_status']} → active")
    else:
        print("\nNo datasets need activation.")

    if plan["to_demote"]:
        print(f"\nWill DEMOTE TO READY ({len(plan['to_demote'])} dataset(s)):")
        for d in plan["to_demote"]:
            print(f"  {d['version_name']!r:<50}  {d['current_status']} → ready")
    else:
        print("\nNo sample datasets need demotion.")

    if plan["already_active"]:
        print(f"\nAlready active (no change):")
        for d in plan["already_active"]:
            print(f"  {d['version_name']!r}")

    if plan["already_demoted"]:
        print(f"\nAlready ready/demoted (no change):")
        for d in plan["already_demoted"]:
            print(f"  {d['version_name']!r}")

    print()


# ---------------------------------------------------------------------------
# Apply
# ---------------------------------------------------------------------------


def _apply_plan(conn: Any, plan: dict[str, Any]) -> dict[str, int]:
    """Execute the plan in a single transaction. Returns change counts."""
    counts = {"activated": 0, "chunks_activated": 0, "demoted": 0, "chunks_demoted": 0}

    with conn.transaction():
        cur = conn.cursor()

        for entry in plan["to_activate"]:
            ds_id = entry["id"]
            name = entry["version_name"]

            cur.execute(
                "UPDATE dataset_versions SET status = 'active', activated_at = NOW() WHERE id = %s",
                (ds_id,),
            )
            cur.execute(
                "UPDATE legal_chunks SET is_active = TRUE WHERE dataset_version_id = %s",
                (ds_id,),
            )
            affected = cur.rowcount
            counts["activated"] += 1
            counts["chunks_activated"] += affected
            print(f"  Activated {name!r} — {affected:,} chunk(s) set is_active = TRUE")

        for entry in plan["to_demote"]:
            ds_id = entry["id"]
            name = entry["version_name"]

            cur.execute(
                "UPDATE dataset_versions SET status = 'ready' WHERE id = %s",
                (ds_id,),
            )
            cur.execute(
                "UPDATE legal_chunks SET is_active = FALSE WHERE dataset_version_id = %s",
                (ds_id,),
            )
            affected = cur.rowcount
            counts["demoted"] += 1
            counts["chunks_demoted"] += affected
            print(f"  Demoted {name!r} to ready — {affected:,} chunk(s) set is_active = FALSE")

    return counts


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    raw_url = _resolve_database_url(args.database_url)
    if not raw_url:
        print("ERROR: no DATABASE_URL found.")
        print(
            "       Set DATABASE_URL in your environment, pass --database-url,\n"
            "       or add DATABASE_URL to backend/.env. Do NOT commit backend/.env."
        )
        return 1

    dsn = _normalize_db_url(raw_url)

    try:
        with psycopg.connect(dsn) as conn:
            with conn.cursor() as cur:
                plan = _build_plan(cur)
    except psycopg.OperationalError as exc:
        print(f"ERROR: could not connect to the database. ({type(exc).__name__})")
        print("       Check PostgreSQL is running and DATABASE_URL is correct.")
        return 1

    _print_plan(plan, apply=args.apply)

    no_work = not plan["to_activate"] and not plan["to_demote"]
    if no_work:
        print("Nothing to do — all MVP datasets already in correct state.")
        print("Run validate_mvp_database.py to confirm.")
        return 0

    if not args.apply:
        print(_DIV)
        print("DRY-RUN complete. No changes written.")
        print("Re-run with --apply to commit the changes above.")
        print(_DIV)
        return 1

    # Apply
    print(f"Applying changes...")
    try:
        with psycopg.connect(dsn) as conn:
            counts = _apply_plan(conn, plan)
    except psycopg.Error as exc:
        print(f"\nERROR: transaction failed and was rolled back. ({type(exc).__name__}: {exc})")
        return 1

    print(_DIV)
    print("Changes committed:")
    print(f"  Datasets activated : {counts['activated']}")
    print(f"  Chunks activated   : {counts['chunks_activated']:,}")
    print(f"  Datasets demoted   : {counts['demoted']}")
    print(f"  Chunks demoted     : {counts['chunks_demoted']:,}")
    print(_DIV)
    print("Run validate_mvp_database.py to confirm the result.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
