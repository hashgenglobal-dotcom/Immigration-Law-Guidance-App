#!/usr/bin/env python3
"""Validate MVP corpus state after Supabase handoff.

Read-only: only SELECT queries. Never prints DATABASE_URL or credentials.
Checks dataset versions, chunk counts, BIA exclusion, sample deactivation,
and privacy log state.

Recognises both canonical local MVP names and Supabase alias names:
  Canonical            Supabase alias       Source family
  ecfr-title8-full-*   eCFR-v* / ecfr-v*   eCFR Title 8
  ina-*                ina-v*               INA / U.S. Code Title 8
  uscis-pm-*           uscis-pm-v*          USCIS Policy Manual
  uscis-official-pages-*                    USCIS Official Pages
  bia-*                                     BIA (post-MVP — must be inactive)
  ecfr-title8-sample-* (non-MVP — must be inactive)

Usage
-----
    uv run --project backend python review/scripts/validate_mvp_supabase_handoff.py
    uv run --project backend python review/scripts/validate_mvp_supabase_handoff.py --relaxed
    uv run --project backend python review/scripts/validate_mvp_supabase_handoff.py --allow-bia
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

BACKEND_ENV_PATH = Path("backend/.env")
_DIVIDER = "-" * 72

# MVP target from handoff (11,589 active embedded chunks).
_MVP_MIN_ACTIVE_EMBEDDED = 10_000
_MVP_TARGET_ACTIVE_EMBEDDED = 11_589

try:
    import psycopg
except ImportError:
    print(
        "ERROR: psycopg (v3) is not installed.\n"
        "       Run: uv run --project backend python review/scripts/validate_mvp_supabase_handoff.py"
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# Dataset name classifiers
# ---------------------------------------------------------------------------

def _is_mvp_dataset(name: str) -> bool:
    """True if version_name is a canonical or Supabase-alias MVP source."""
    n = name.lower()
    return (
        n.startswith("ecfr-title8-full")
        or n.startswith("ecfr-v")          # Supabase alias: eCFR-v2026-01
        or n.startswith("ina-")             # covers ina-2026-* and ina-v2026-*
        or n.startswith("uscis-pm-")        # covers uscis-pm-2026-* and uscis-pm-v2026-*
        or n.startswith("uscis-official-pages")
    )


def _is_sample_dataset(name: str) -> bool:
    return name.lower().startswith("ecfr-title8-sample")


def _is_bia_dataset(name: str) -> bool:
    return name.lower().startswith("bia")


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
# Validation (all SELECT — no writes, no user data read)
# ---------------------------------------------------------------------------

def _run_checks(cur: Any, allow_bia: bool) -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    details: dict[str, Any] = {}

    cur.execute(
        "SELECT id, version_name, status FROM dataset_versions ORDER BY version_name"
    )
    all_versions = [
        {"id": r[0], "version_name": r[1], "status": r[2]}
        for r in cur.fetchall()
    ]
    details["all_versions"] = all_versions

    cur.execute(
        """
        SELECT
            dv.version_name,
            dv.status,
            COUNT(lc.id)                                                      AS total,
            COUNT(lc.id) FILTER (WHERE lc.embedding IS NOT NULL)              AS embedded,
            COUNT(lc.id) FILTER (WHERE lc.is_active = TRUE)                   AS active_count,
            COUNT(lc.id) FILTER (WHERE lc.is_active = TRUE
                                   AND lc.embedding IS NOT NULL)              AS active_embedded
        FROM dataset_versions dv
        LEFT JOIN legal_chunks lc ON lc.dataset_version_id = dv.id
        GROUP BY dv.id, dv.version_name, dv.status
        ORDER BY dv.version_name
        """
    )
    per_dataset = [
        {
            "version_name": r[0],
            "status": r[1],
            "total": r[2],
            "embedded": r[3],
            "active": r[4],
            "active_embedded": r[5],
        }
        for r in cur.fetchall()
    ]
    details["per_dataset"] = per_dataset

    mvp_active_embedded = sum(r["active_embedded"] for r in per_dataset if _is_mvp_dataset(r["version_name"]))
    sample_active = sum(r["active"] for r in per_dataset if _is_sample_dataset(r["version_name"]))
    bia_active = sum(r["active"] for r in per_dataset if _is_bia_dataset(r["version_name"]))
    bia_embedded = sum(r["embedded"] for r in per_dataset if _is_bia_dataset(r["version_name"]))

    details["mvp_active_embedded"] = mvp_active_embedded
    details["sample_active"] = sample_active
    details["bia_active"] = bia_active
    details["bia_embedded"] = bia_embedded

    # Count only — no content from privacy logs
    cur.execute("SELECT COUNT(*) FROM privacy_safe_answer_logs")
    privacy_count: int = cur.fetchone()[0]
    details["privacy_log_count"] = privacy_count

    if mvp_active_embedded < _MVP_MIN_ACTIVE_EMBEDDED:
        failures.append(
            f"MVP active embedded chunks: {mvp_active_embedded} "
            f"(target {_MVP_TARGET_ACTIVE_EMBEDDED}, floor {_MVP_MIN_ACTIVE_EMBEDDED}) — "
            "run embed + activate scripts, or check that dataset names are recognised"
        )

    if sample_active > 0:
        failures.append(
            f"eCFR sample active chunks: {sample_active} — must be 0 "
            "(run cleanup_mvp_handoff_state.py --apply)"
        )

    if bia_active > 0 and not allow_bia:
        failures.append(
            f"BIA active chunks: {bia_active} — must be 0 for MVP "
            "(run cleanup_mvp_handoff_state.py --apply, "
            "or pass --allow-bia for post-MVP testing only)"
        )

    if privacy_count > 0:
        failures.append(
            f"privacy_safe_answer_logs: {privacy_count} row(s) — "
            "expected 0 before smoke testing begins"
        )

    return failures, details


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def _print_report(
    details: dict[str, Any],
    failures: list[str],
    allow_bia: bool,
    relaxed: bool,
) -> None:
    print(_DIVIDER)
    print("MVP Supabase handoff validation")
    print("(Read-only. No credentials printed. No user data accessed.)")
    print(_DIVIDER)

    print("\n[Dataset versions]")
    for v in details.get("all_versions", []):
        print(f"  {v['status']:12s}  {v['version_name']}")

    print("\n[Chunks per dataset]")
    header = f"  {'version_name':<42} {'status':12} {'total':>7} {'embedded':>9} {'active':>7} {'act+emb':>8}"
    print(header)
    for row in details.get("per_dataset", []):
        print(
            f"  {row['version_name']:<42} {row['status']:12} "
            f"{row['total']:>7} {row['embedded']:>9} {row['active']:>7} {row['active_embedded']:>8}"
        )

    print(f"\n[MVP summary]")
    print(f"  MVP active embedded chunks : {details.get('mvp_active_embedded')}  (target {_MVP_TARGET_ACTIVE_EMBEDDED})")
    print(f"  eCFR sample active chunks  : {details.get('sample_active')}  (must be 0)")
    print(f"  BIA active chunks          : {details.get('bia_active')}  (must be 0 for MVP)")
    print(f"  BIA embedded chunks        : {details.get('bia_embedded')}")
    print(f"  privacy log rows           : {details.get('privacy_log_count')}  (must be 0)")

    if allow_bia:
        print("\n  NOTE: --allow-bia passed — BIA active check bypassed (post-MVP testing mode)")
    if relaxed:
        print("  NOTE: --relaxed passed — exiting 0 regardless of results")

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
    parser = argparse.ArgumentParser(
        description="Validate MVP corpus state after Supabase handoff (read-only)"
    )
    parser.add_argument("--database-url", default=None, help="Override DATABASE_URL")
    parser.add_argument(
        "--relaxed",
        action="store_true",
        help="Exit 0 even if checks fail (use on sample-only local DB)",
    )
    parser.add_argument(
        "--allow-bia",
        action="store_true",
        help="Allow BIA active chunks (post-MVP testing only; default fails if BIA is active)",
    )
    args = parser.parse_args(argv)

    raw_url = _resolve_db_url(args.database_url)
    if not raw_url:
        print("ERROR: no DATABASE_URL found. Set it in the environment or backend/.env.")
        return 1
    db_url = _normalize_db_url(raw_url)

    try:
        with psycopg.connect(db_url, autocommit=True) as conn:
            with conn.cursor() as cur:
                failures, details = _run_checks(cur, allow_bia=args.allow_bia)
    except psycopg.OperationalError:
        print("ERROR: could not connect to PostgreSQL (psycopg.OperationalError).")
        print("       Check that the database is reachable and DATABASE_URL is correct.")
        return 1
    except psycopg.Error as exc:
        print(f"ERROR: database error ({type(exc).__name__}): {exc}")
        return 1

    _print_report(details, failures, allow_bia=args.allow_bia, relaxed=args.relaxed)

    if args.relaxed:
        return 0
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
