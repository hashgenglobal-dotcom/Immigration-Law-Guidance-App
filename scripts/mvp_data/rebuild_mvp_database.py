#!/usr/bin/env python3
"""Orchestrate a local MVP corpus rebuild.

Walks through all pipeline stages needed to bring a fresh local PostgreSQL
database to a fully-loaded, embedded, and activated MVP state. Stages are
intentionally independent so you can skip completed stages with flags.

Stages
------
  1. fetch    — Download full eCFR Title 8 XML, INA, and USCIS PM source data
                into data/ (git-ignored). Not yet fully automated — see notes.
  2. insert   — Parse and insert legal_chunks rows into PostgreSQL.
  3. embed    — Generate 768-dim embeddings via Ollama nomic-embed-text.
  4. activate — Set MVP dataset versions to 'active', sample to 'ready'.
  5. validate — Run validate_mvp_database.py and confirm PASS.

Privacy / Safety
----------------
This script calls other scripts in scripts/ and scripts/mvp_data/. It does NOT:
  - read or write user questions or privacy_safe_answer_logs
  - delete any database rows unless --reset is passed
  - commit any raw PDFs, screenshots, or large data artifacts
  - print DATABASE_URL, passwords, or any credential

Usage
-----
    # Show what would run — no changes
    uv run --project backend python scripts/mvp_data/rebuild_mvp_database.py --dry-run

    # Full rebuild (interactive — asks for confirmation before destructive steps)
    uv run --project backend python scripts/mvp_data/rebuild_mvp_database.py

    # Skip fetch (data already in data/)
    uv run --project backend python scripts/mvp_data/rebuild_mvp_database.py --skip-fetch

    # Skip embedding (already embedded)
    uv run --project backend python scripts/mvp_data/rebuild_mvp_database.py --skip-embed

    # Reset DB state before rebuild (requires explicit flag)
    uv run --project backend python scripts/mvp_data/rebuild_mvp_database.py --reset

Exit codes
----------
* 0 — pipeline completed (or dry-run finished).
* 1 — a stage failed, or --dry-run printed the plan.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCRIPTS_DIR = Path("scripts")
MVP_DATA_DIR = Path("scripts/mvp_data")
BACKEND_DIR = Path("backend")

_DIV = "-" * 72

# Map of stage names to (script_path, description, automation_status).
# automation_status: "automated" | "partial" | "manual"
STAGES: list[tuple[str, Path | None, str, str]] = [
    (
        "fetch",
        None,
        "Download full eCFR Title 8, INA, and USCIS PM source data into data/",
        "partial",
    ),
    (
        "insert",
        None,
        "Parse source data and insert legal_chunks rows into PostgreSQL",
        "partial",
    ),
    (
        "embed",
        SCRIPTS_DIR / "embed_legal_chunks.py",
        "Generate 768-dim embeddings via local Ollama nomic-embed-text",
        "automated",
    ),
    (
        "activate",
        MVP_DATA_DIR / "set_mvp_active_datasets.py",
        "Set MVP dataset versions active; demote sample to ready",
        "automated",
    ),
    (
        "validate",
        MVP_DATA_DIR / "validate_mvp_database.py",
        "Confirm all MVP datasets are active, embedded, and retrieval-ready",
        "automated",
    ),
]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Orchestrate a local MVP corpus rebuild.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry-run — print the plan without executing
  uv run --project backend python scripts/mvp_data/rebuild_mvp_database.py --dry-run

  # Full pipeline (fetch + insert + embed + activate + validate)
  uv run --project backend python scripts/mvp_data/rebuild_mvp_database.py

  # Already have data in data/ — skip fetch
  uv run --project backend python scripts/mvp_data/rebuild_mvp_database.py --skip-fetch

  # Already embedded — skip embed
  uv run --project backend python scripts/mvp_data/rebuild_mvp_database.py --skip-embed

  # Activation + validation only
  uv run --project backend python scripts/mvp_data/rebuild_mvp_database.py \\
      --skip-fetch --skip-insert --skip-embed
""",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the pipeline plan without executing any stage.",
    )
    p.add_argument(
        "--skip-fetch",
        action="store_true",
        help="Skip stage 1 (fetch). Use when source data is already in data/.",
    )
    p.add_argument(
        "--skip-insert",
        action="store_true",
        help="Skip stage 2 (insert). Use when legal_chunks rows already exist.",
    )
    p.add_argument(
        "--skip-embed",
        action="store_true",
        help="Skip stage 3 (embed). Use when embeddings already exist.",
    )
    p.add_argument(
        "--reset",
        action="store_true",
        help=(
            "Truncate legal_chunks and reset dataset_versions before rebuild. "
            "DESTRUCTIVE. Requires explicit --reset flag. "
            "You will be asked to confirm before any rows are deleted."
        ),
    )
    p.add_argument(
        "--database-url",
        metavar="DSN",
        help="PostgreSQL DSN. Defaults to DATABASE_URL env var, then backend/.env.",
    )
    return p.parse_args(argv)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run(cmd: list[str], label: str) -> int:
    """Run a subprocess command. Returns exit code."""
    print(f"\n  $ {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"  ✗ {label} exited {result.returncode}")
    else:
        print(f"  ✓ {label} succeeded")
    return result.returncode


def _uv_run(script: Path, extra_args: list[str] | None = None) -> list[str]:
    """Build a uv run command for a Python script."""
    cmd = ["uv", "run", "--project", str(BACKEND_DIR), "python", str(script)]
    if extra_args:
        cmd.extend(extra_args)
    return cmd


def _print_pipeline_plan(args: argparse.Namespace) -> None:
    skip_map = {
        "fetch": args.skip_fetch,
        "insert": args.skip_insert,
        "embed": args.skip_embed,
    }
    print(_DIV)
    print("MVP REBUILD PIPELINE PLAN")
    print(_DIV)
    for i, (name, script, desc, automation) in enumerate(STAGES, 1):
        skipped = skip_map.get(name, False)
        status = "SKIP" if skipped else "RUN "
        auto_tag = f"[{automation}]"
        print(f"  {i}. [{status}]  {name:<10}  {auto_tag:<12}  {desc}")
        if automation in ("partial", "manual") and not skipped:
            _print_manual_note(name)
    if args.reset:
        print("\n  [RESET]  Will truncate legal_chunks and reset dataset_versions first.")
        print("           You will be asked to confirm before any rows are deleted.")
    print()


def _print_manual_note(stage: str) -> None:
    notes = {
        "fetch": (
            "           MANUAL STEP REQUIRED — full-corpus fetch is not yet automated.\n"
            "           See scripts/mvp_data/README.md §3 for fetch commands.\n"
            "           eCFR sample fetch: scripts/fetch_ecfr_title8_sample.py\n"
            "           Full eCFR / INA / USCIS PM: bulk download instructions in README."
        ),
        "insert": (
            "           MANUAL STEP REQUIRED — full-corpus insert is not yet automated.\n"
            "           See scripts/mvp_data/README.md §4 for insert commands.\n"
            "           Sample insert: scripts/insert_ecfr_preview_to_db.py\n"
            "           Full corpus insert: see ingestion scripts when available."
        ),
    }
    note = notes.get(stage)
    if note:
        print(note)


# ---------------------------------------------------------------------------
# Reset (destructive)
# ---------------------------------------------------------------------------


def _do_reset(dsn: str) -> int:
    """Truncate legal_chunks and reset dataset_versions. Requires psycopg."""
    print(_DIV)
    print("RESET: This will TRUNCATE legal_chunks and DELETE all dataset_versions rows.")
    print("       This cannot be undone. Type 'yes' to confirm:")
    try:
        answer = input("  > ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\nReset cancelled.")
        return 1
    if answer != "yes":
        print("Reset cancelled (did not type 'yes').")
        return 1

    try:
        import psycopg  # type: ignore[import]
    except ImportError:
        print("ERROR: psycopg not available. Run with uv run --project backend.")
        return 1

    try:
        with psycopg.connect(dsn) as conn:
            with conn.transaction():
                cur = conn.cursor()
                cur.execute("TRUNCATE TABLE legal_chunks RESTART IDENTITY CASCADE")
                cur.execute("DELETE FROM dataset_versions")
        print("Reset complete: legal_chunks truncated, dataset_versions cleared.")
    except psycopg.Error as exc:
        print(f"ERROR: reset failed. ({type(exc).__name__}: {exc})")
        return 1
    return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    _print_pipeline_plan(args)

    if args.dry_run:
        print(_DIV)
        print("DRY-RUN complete. No changes made.")
        print("Remove --dry-run to execute the pipeline.")
        print(_DIV)
        return 1

    # Optional reset
    if args.reset:
        from scripts.mvp_data import validate_mvp_database as _vmv  # noqa: F401
        raw_url = _resolve_url(args.database_url)
        if not raw_url:
            print("ERROR: DATABASE_URL not found. Cannot reset.")
            return 1
        dsn = _vmv._normalize_db_url(raw_url)
        rc = _do_reset(dsn)
        if rc != 0:
            return rc

    # Build extra args for sub-scripts
    db_extra: list[str] = []
    if args.database_url:
        db_extra = ["--database-url", args.database_url]

    skip_map = {
        "fetch": args.skip_fetch,
        "insert": args.skip_insert,
        "embed": args.skip_embed,
    }

    for name, script, desc, automation in STAGES:
        if skip_map.get(name, False):
            print(f"\n[SKIP] Stage: {name}")
            continue

        print(f"\n{_DIV}")
        print(f"Stage: {name.upper()} — {desc}")
        print(_DIV)

        if automation in ("partial", "manual"):
            _print_manual_note(name)
            print()
            print(f"  Stage '{name}' requires manual steps. See README.md for instructions.")
            print(f"  After completing '{name}' manually, re-run with --skip-{name}.")
            return 1

        if script is None:
            print(f"  No script defined for stage '{name}'. Skipping.")
            continue

        if not script.exists():
            print(f"  ERROR: script not found: {script}")
            return 1

        extra = list(db_extra)
        if name == "activate":
            extra.append("--apply")

        rc = _run(_uv_run(script, extra), desc)
        if rc != 0:
            print(f"\nPipeline stopped at stage '{name}' (exit code {rc}).")
            print("Fix the error above and re-run with appropriate --skip-* flags.")
            return rc

    print(f"\n{_DIV}")
    print("MVP rebuild pipeline complete.")
    print("Run validate_mvp_database.py to confirm final state:")
    print("  uv run --project backend python scripts/mvp_data/validate_mvp_database.py")
    print(_DIV)
    return 0


def _resolve_url(arg_url: str | None) -> str | None:
    if arg_url:
        return arg_url
    env_val = os.environ.get("DATABASE_URL")
    if env_val:
        return env_val
    env_path = Path("backend/.env")
    result: dict[str, str] = {}
    try:
        text = env_path.read_text(encoding="utf-8")
    except OSError:
        return None
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, raw_val = line.partition("=")
        result[key.strip()] = raw_val.strip().strip('"').strip("'")
    return result.get("DATABASE_URL")


if __name__ == "__main__":
    sys.exit(main())
