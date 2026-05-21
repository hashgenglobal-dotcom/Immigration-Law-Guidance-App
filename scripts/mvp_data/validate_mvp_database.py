#!/usr/bin/env python3
"""Validate that the local MVP corpus is correctly loaded and activated.

Checks that the three co-active MVP dataset versions are present, active, have
the expected chunk counts, and that the sample eCFR dataset is NOT active.

Read-only. No inserts, updates, or deletes.

Privacy / Safety
----------------
This script reads only public legal-source metadata (dataset_versions,
legal_chunks aggregate counts). It does NOT:
  - read user questions or privacy_safe_answer_logs
  - generate embeddings or call any AI API
  - print DATABASE_URL, passwords, or any credential

Usage
-----
    # DB URL auto-detected from env or backend/.env
    uv run --project backend python scripts/mvp_data/validate_mvp_database.py

    # Explicit DB URL
    uv run --project backend python scripts/mvp_data/validate_mvp_database.py \\
        --database-url "postgresql://user@localhost:5432/immigration_law_dev"

    # Show counts but still exit 0 when MVP datasets are missing (CI warm-up)
    uv run --project backend python scripts/mvp_data/validate_mvp_database.py \\
        --relaxed

Exit codes
----------
* 0 — all checks passed, or --relaxed with only WARN-level findings.
* 1 — one or more FAIL checks, connection error, or missing DATABASE_URL
      (unless --relaxed suppresses the failure).
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
        "       Run with: uv run --project backend python scripts/mvp_data/validate_mvp_database.py"
    )
    sys.exit(1)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BACKEND_ENV_PATH = Path("backend/.env")
EXPECTED_DIM = 768

# MVP corpus: three co-active dataset version name prefixes.
MVP_PREFIXES = ("ecfr-title8-full-", "ina-", "uscis-pm-")
SAMPLE_PREFIX = "ecfr-title8-sample-"

# Minimum chunk counts considered healthy per source.
MIN_CHUNKS: dict[str, int] = {
    "ecfr-title8-full-": 5_000,
    "ina-": 500,
    "uscis-pm-": 200,
}

_DIV = "-" * 72


# ---------------------------------------------------------------------------
# .env parser (stdlib only)
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
    dotenv = _read_env_file(BACKEND_ENV_PATH)
    return dotenv.get("DATABASE_URL")


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
        description="Validate MVP database corpus readiness.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--database-url",
        metavar="DSN",
        help=(
            "PostgreSQL DSN. SQLAlchemy-style postgresql+psycopg:// prefix is stripped. "
            "Defaults to DATABASE_URL env var, then backend/.env."
        ),
    )
    p.add_argument(
        "--relaxed",
        action="store_true",
        help="Exit 0 even if MVP datasets are not yet present (WARN instead of FAIL). "
             "Useful for local dev before data is loaded.",
    )
    return p.parse_args(argv)


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def _prefix_for(version_name: str) -> str | None:
    for prefix in MVP_PREFIXES:
        if version_name.startswith(prefix):
            return prefix
    if version_name.startswith(SAMPLE_PREFIX):
        return SAMPLE_PREFIX
    return None


def run_checks(cur: Any) -> tuple[list[str], list[str], dict[str, Any]]:
    """Return (failures, warnings, details). Read-only; no DB writes."""
    failures: list[str] = []
    warnings: list[str] = []
    details: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # 1. List all dataset_versions
    # ------------------------------------------------------------------
    cur.execute(
        """
        SELECT id, version_name, status, created_at, activated_at
        FROM dataset_versions
        ORDER BY created_at DESC NULLS LAST
        """
    )
    all_rows = cur.fetchall()
    details["all_datasets"] = [
        {
            "id": r[0],
            "version_name": r[1],
            "status": r[2],
            "created_at": str(r[3]) if r[3] else None,
            "activated_at": str(r[4]) if r[4] else None,
        }
        for r in all_rows
    ]

    active_rows = [r for r in all_rows if r[2] == "active"]
    details["active_dataset_count"] = len(active_rows)

    # ------------------------------------------------------------------
    # 2. Sample dataset must NOT be active
    # ------------------------------------------------------------------
    active_sample = [r for r in active_rows if r[1].startswith(SAMPLE_PREFIX)]
    if active_sample:
        failures.append(
            f"FAIL — sample dataset(s) are active and will pollute retrieval: "
            + ", ".join(r[1] for r in active_sample)
            + f". Run set_mvp_active_datasets.py --apply to fix."
        )
    else:
        details["sample_not_active"] = True

    # ------------------------------------------------------------------
    # 3. Each MVP prefix must have at least one active version
    # ------------------------------------------------------------------
    active_names = {r[1] for r in active_rows}
    covered_prefixes: set[str] = set()
    for name in active_names:
        for prefix in MVP_PREFIXES:
            if name.startswith(prefix):
                covered_prefixes.add(prefix)

    missing_prefixes = [p for p in MVP_PREFIXES if p not in covered_prefixes]
    if missing_prefixes:
        msg = (
            "FAIL — active datasets do not cover all MVP sources. "
            "Missing prefixes: " + ", ".join(missing_prefixes)
        )
        if missing_prefixes == list(MVP_PREFIXES):
            failures.append(msg + ". Run set_mvp_active_datasets.py --apply.")
        else:
            failures.append(msg)
    details["covered_prefixes"] = sorted(covered_prefixes)
    details["missing_prefixes"] = missing_prefixes

    # ------------------------------------------------------------------
    # 4. Per-dataset chunk and embedding counts
    # ------------------------------------------------------------------
    cur.execute(
        """
        SELECT
            dv.id,
            dv.version_name,
            dv.status,
            COUNT(lc.id)                                                  AS total_chunks,
            COUNT(lc.id) FILTER (WHERE lc.is_active = TRUE)              AS active_chunks,
            COUNT(lc.id) FILTER (WHERE lc.embedding IS NOT NULL)         AS with_embedding,
            COUNT(lc.id) FILTER (
                WHERE lc.embedding IS NOT NULL
                  AND vector_dims(lc.embedding) = %s
            )                                                             AS correct_dim
        FROM dataset_versions dv
        LEFT JOIN legal_chunks lc ON lc.dataset_version_id = dv.id
        GROUP BY dv.id, dv.version_name, dv.status
        ORDER BY dv.version_name
        """,
        (EXPECTED_DIM,),
    )
    chunk_rows = cur.fetchall()
    dataset_stats: list[dict[str, Any]] = []
    for row in chunk_rows:
        ds_id, ds_name, ds_status, total, active_c, with_emb, correct_d = row
        dataset_stats.append(
            {
                "id": ds_id,
                "version_name": ds_name,
                "status": ds_status,
                "total_chunks": total,
                "active_chunks": active_c,
                "with_embedding": with_emb,
                "correct_dim": correct_d,
                "missing_embedding": total - with_emb,
                "wrong_dim": with_emb - correct_d,
            }
        )
    details["dataset_stats"] = dataset_stats

    # ------------------------------------------------------------------
    # 5. Active MVP datasets must meet minimum chunk thresholds
    # ------------------------------------------------------------------
    for stat in dataset_stats:
        if stat["status"] != "active":
            continue
        name = stat["version_name"]
        for prefix, min_c in MIN_CHUNKS.items():
            if name.startswith(prefix):
                total_c = stat["total_chunks"]
                if total_c < min_c:
                    warnings.append(
                        f"WARN — {name!r} has only {total_c:,} chunks "
                        f"(expected >= {min_c:,} for {prefix!r}). "
                        "Data may be incomplete."
                    )
                elif total_c == 0:
                    failures.append(
                        f"FAIL — active dataset {name!r} has 0 chunks. "
                        "Ingestion has not run."
                    )

    # ------------------------------------------------------------------
    # 6. Embedding completeness for active MVP datasets
    # ------------------------------------------------------------------
    for stat in dataset_stats:
        if stat["status"] != "active":
            continue
        name = stat["version_name"]
        if not any(name.startswith(p) for p in MVP_PREFIXES):
            continue
        missing_emb = stat["missing_embedding"]
        wrong_dim = stat["wrong_dim"]
        if missing_emb > 0:
            warnings.append(
                f"WARN — {name!r}: {missing_emb:,} chunk(s) have embedding IS NULL. "
                "Run embed_legal_chunks.py."
            )
        if wrong_dim > 0:
            failures.append(
                f"FAIL — {name!r}: {wrong_dim:,} chunk(s) have wrong embedding "
                f"dimension (expected {EXPECTED_DIM}). Re-embed with nomic-embed-text."
            )

    return failures, warnings, details


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def _print_report(details: dict[str, Any], failures: list[str], warnings: list[str]) -> None:
    print(_DIV)
    print("MVP DATABASE VALIDATION REPORT")
    print(_DIV)

    print("\n── All dataset_versions ──")
    all_ds = details.get("all_datasets", [])
    if not all_ds:
        print("  (none found)")
    else:
        hdr = f"  {'version_name':<42}  {'status':<10}  {'activated_at'}"
        print(hdr)
        print("  " + "-" * (len(hdr) - 2))
        for d in all_ds:
            activated = d["activated_at"] or "—"
            print(f"  {d['version_name']:<42}  {d['status']:<10}  {activated}")

    print(f"\n── Active datasets ({details.get('active_dataset_count', 0)}) ──")
    for d in all_ds:
        if d["status"] == "active":
            print(f"  {d['version_name']}")

    print("\n── Chunk and embedding counts ──")
    stats = details.get("dataset_stats", [])
    if not stats:
        print("  (no data)")
    else:
        hdr = f"  {'version_name':<42}  {'status':<10}  {'total':>8}  {'active':>8}  {'w/embed':>8}  {'no_embed':>8}"
        print(hdr)
        print("  " + "-" * (len(hdr) - 2))
        for s in stats:
            print(
                f"  {s['version_name']:<42}  {s['status']:<10}"
                f"  {s['total_chunks']:>8,}  {s['active_chunks']:>8,}"
                f"  {s['with_embedding']:>8,}  {s['missing_embedding']:>8,}"
            )

    covered = details.get("covered_prefixes", [])
    missing = details.get("missing_prefixes", [])
    print(f"\n── MVP source coverage ──")
    for prefix in MVP_PREFIXES:
        mark = "PASS" if prefix in covered else "FAIL"
        print(f"  [{mark}]  {prefix!r}")

    sample_ok = details.get("sample_not_active", False)
    print(f"\n── Sample dataset excluded ──")
    print(f"  [{'PASS' if sample_ok else 'FAIL'}]  ecfr-title8-sample-* is not active")

    if warnings:
        print(f"\n── Warnings ({len(warnings)}) ──")
        for w in warnings:
            print(f"  {w}")

    if failures:
        print(f"\n── Failures ({len(failures)}) ──")
        for f in failures:
            print(f"  {f}")

    print(_DIV)
    if failures:
        print("RESULT: FAIL")
    elif warnings:
        print("RESULT: PASS with warnings")
    else:
        print("RESULT: PASS")
    print(_DIV)


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
            "       or add DATABASE_URL to backend/.env.\n"
            "       Do NOT commit backend/.env."
        )
        return 1

    dsn = _normalize_db_url(raw_url)

    try:
        with psycopg.connect(dsn) as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                failures, warnings, details = run_checks(cur)
    except psycopg.OperationalError as exc:
        print(f"ERROR: could not connect to the database.")
        print(f"       Check that PostgreSQL is running and DATABASE_URL is correct.")
        print(f"       ({type(exc).__name__})")
        return 1

    _print_report(details, failures, warnings)

    if failures:
        if args.relaxed:
            print("\n(--relaxed: exiting 0 despite failures)")
            return 0
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
