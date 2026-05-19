#!/usr/bin/env python3
"""Dry-run inspection of active legal_chunks and planned synthetic retrieval queries.

This script is the first step in the retrieval testing milestone (see
``docs/retrieval-milestone-plan.md``). It inspects the *active* public
``legal_chunks`` rows and lists the synthetic test queries that the future
retrieval scripts will run, so a reviewer can confirm the dataset is in
the expected shape before any real retrieval is attempted.

Privacy and safety
------------------
This script handles only public eCFR Title 8 regulatory data.
- It inspects ONLY active, public ``legal_chunks`` (``is_active = TRUE``).
- The five test queries below are SYNTHETIC paraphrases of public
  regulatory topics — they are NOT real user questions and contain no
  case facts, names, or identifying information.
- It does NOT accept user input. It does NOT process real user questions.
- It does NOT store any question text in the database.
- It does NOT write to ANY table — including ``privacy_safe_answer_logs``.
  The row count of ``privacy_safe_answer_logs`` is read only as a safety
  invariant.
- It does NOT call Ollama. It does NOT generate query embeddings.
- It does NOT call OpenAI, Anthropic, Cohere, or any public AI API.
- It does NOT generate legal answers.

Usage
-----
    # Auto-detect DB URL from backend/.env or DATABASE_URL env var
    uv run --project backend python scripts/dry_run_retrieve_legal_chunks.py

    # Explicit database URL
    uv run --project backend python scripts/dry_run_retrieve_legal_chunks.py \\
        --database-url "postgresql://user@localhost:5432/immigration_law_dev"

Exit codes
----------
* 0 — dry-run completed (including when readiness checks fail; readiness
      issues are shown in the report but do not by themselves cause a
      non-zero exit, matching the dry-run convention used elsewhere in
      this project).
* 1 — missing DB config, DB connection failure, or query failure.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

# psycopg (v3) is the only non-stdlib dependency.
# Run with: uv run --project backend python scripts/dry_run_retrieve_legal_chunks.py
try:
    import psycopg
except ImportError:
    print(
        "ERROR: psycopg (v3) is not installed in the current Python environment.\n"
        "       Run this script with:\n"
        "         uv run --project backend python scripts/dry_run_retrieve_legal_chunks.py"
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BACKEND_ENV_PATH = Path("backend/.env")
EXPECTED_DIM = 768          # must match legal_chunks.embedding vector(768)
EXPECTED_ACTIVE_CHUNKS = 5  # milestone: exactly 5 eCFR Title 8 sample chunks
SNIPPET_CHARS = 180         # how many characters of chunk_text to preview

# Synthetic test queries planned for the retrieval milestone.
# These are paraphrases of public regulatory topics — NOT real user
# questions, NOT case facts, NOT personal data. They will eventually be
# embedded locally with Ollama nomic-embed-text and used to test pgvector
# retrieval against the active public legal_chunks.
SYNTHETIC_TEST_QUERIES: tuple[tuple[str, str], ...] = (
    ("Can asylum applicants get work authorization?",     "8 CFR § 208.7"),
    ("When can someone file for asylum?",                 "8 CFR § 208.4"),
    ("Who is eligible for adjustment of status?",         "8 CFR § 245.1"),
    ("What categories are authorized for employment?",    "8 CFR § 274a.12"),
    ("What is a Notice to Appear?",                       "8 CFR § 239.1"),
)

_DIVIDER = "-" * 72


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Dry-run inspection of active legal_chunks and planned synthetic "
            "retrieval test queries. Read-only: no DB writes, no Ollama calls, "
            "no embedding generation, no answer generation."
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
# Database queries (all read-only SELECT queries — no INSERT/UPDATE/DELETE)
# ---------------------------------------------------------------------------


def _gather_facts(cur: Any) -> dict[str, Any]:
    """Run all SELECT queries and return a flat facts dict.

    Reads ONLY public eCFR legal-source metadata plus a row count from
    privacy_safe_answer_logs. No user questions are read. No content
    from privacy_safe_answer_logs is read. No database writes happen.
    No LLM or embedding calls are made.
    """
    facts: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # 1. Active dataset(s). We expect exactly one row with status='active'.
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
    facts["active_dataset_count"] = len(active_rows)

    if not active_rows:
        # No active dataset — readiness will fail; remaining queries are
        # skipped because they are scoped to an active dataset_version_id.
        facts["active_dataset_id"] = None
        facts["active_dataset_name"] = None
        facts["active_dataset_status"] = None
        facts["active_dataset_activated_at"] = None
        facts["active_chunk_count"] = 0
        facts["active_chunks"] = []
        cur.execute("SELECT COUNT(*) FROM privacy_safe_answer_logs")
        facts["privacy_safe_answer_logs_count"] = cur.fetchone()[0]
        return facts

    # Use the most recently activated row as the target.
    active_id, active_name, active_status, active_activated_at = active_rows[0]
    facts["active_dataset_id"] = active_id
    facts["active_dataset_name"] = active_name
    facts["active_dataset_status"] = active_status
    facts["active_dataset_activated_at"] = (
        str(active_activated_at) if active_activated_at else None
    )

    # ------------------------------------------------------------------
    # 2. Active chunks belonging to that dataset version.
    #
    # vector_dims(embedding) is a pgvector function that returns the
    # number of stored dimensions without pulling the full vector to the
    # client. Only public eCFR chunk metadata is read.
    # ------------------------------------------------------------------
    cur.execute(
        """
        SELECT
            id,
            citation,
            topic,
            subtopic,
            risk_level,
            official_url,
            CASE
                WHEN embedding IS NOT NULL THEN vector_dims(embedding)
                ELSE NULL
            END                                            AS embedding_dim,
            LEFT(COALESCE(chunk_text, ''), %s)             AS snippet
        FROM legal_chunks
        WHERE is_active = TRUE
          AND dataset_version_id = %s
        ORDER BY citation, chunk_index
        """,
        (SNIPPET_CHARS, active_id),
    )
    chunk_rows = cur.fetchall()
    chunks: list[dict[str, Any]] = []
    for r in chunk_rows:
        chunks.append(
            {
                "id": r[0],
                "citation": r[1],
                "topic": r[2],
                "subtopic": r[3],
                "risk_level": r[4],
                "official_url": r[5],
                "embedding_dim": r[6],
                "snippet": r[7],
            }
        )
    facts["active_chunks"] = chunks
    facts["active_chunk_count"] = len(chunks)

    # ------------------------------------------------------------------
    # 3. privacy_safe_answer_logs row count (safety invariant only —
    #    no content is read from this table).
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

    active_count = facts.get("active_dataset_count", 0)
    if active_count == 0:
        issues.append(
            "dataset_versions: no row has status = 'active' — "
            "run activate_dataset.py --yes first"
        )
        # Still check privacy_safe_answer_logs invariant below.
    elif active_count != 1:
        issues.append(
            f"dataset_versions: {active_count} rows have status = 'active'; "
            "expected exactly 1"
        )

    active_chunk_count = facts.get("active_chunk_count", 0)
    if active_chunk_count != EXPECTED_ACTIVE_CHUNKS:
        issues.append(
            f"legal_chunks: active chunk count is {active_chunk_count}; "
            f"expected exactly {EXPECTED_ACTIVE_CHUNKS} at this milestone"
        )

    # Per-chunk embedding dimension check.
    bad_dim = [
        c for c in facts.get("active_chunks", [])
        if c["embedding_dim"] != EXPECTED_DIM
    ]
    if bad_dim:
        offenders = ", ".join(
            f"{c['citation']} (dim={c['embedding_dim']})" for c in bad_dim
        )
        issues.append(
            f"legal_chunks: {len(bad_dim)} active chunk(s) do not have "
            f"embedding dimension {EXPECTED_DIM}: {offenders}"
        )

    # Each expected synthetic-query target citation must be present
    # among the active chunks. Without this, retrieval cannot succeed
    # because the target chunk does not exist in the active set.
    present_citations = {c["citation"] for c in facts.get("active_chunks", [])}
    expected_citations = [exp for _, exp in SYNTHETIC_TEST_QUERIES]
    missing_citations = [c for c in expected_citations if c not in present_citations]
    if missing_citations:
        issues.append(
            "legal_chunks: missing expected target citation(s): "
            + ", ".join(missing_citations)
        )

    psal_count = facts.get("privacy_safe_answer_logs_count", 0)
    if psal_count != 0:
        issues.append(
            f"privacy_safe_answer_logs: expected 0 rows at this milestone, "
            f"found {psal_count}"
        )

    return issues


# ---------------------------------------------------------------------------
# Report printing
# ---------------------------------------------------------------------------


def _print_report(facts: dict[str, Any], issues: list[str]) -> None:
    is_ready = len(issues) == 0

    print(_DIVIDER)
    print("DRY-RUN: retrieval readiness inspection")
    print("(Read-only. Public legal-source data only. No Ollama, no embeddings,")
    print(" no answer generation, no database writes.)")
    print(_DIVIDER)

    print("\n[Active dataset]")
    print(f"  active_dataset_count   : {facts.get('active_dataset_count')}")
    print(f"  dataset_version_id     : {facts.get('active_dataset_id')}")
    print(f"  version_name           : {facts.get('active_dataset_name')}")
    print(f"  status                 : {facts.get('active_dataset_status')}")
    print(f"  activated_at           : {facts.get('active_dataset_activated_at')}")
    print(f"  active chunk count     : {facts.get('active_chunk_count')}")

    chunks = facts.get("active_chunks", [])
    print(f"\n[Active chunks ({len(chunks)})]")
    if not chunks:
        print("  (none)")
    for c in chunks:
        print(f"  - id            : {c['id']}")
        print(f"    citation      : {c['citation']}")
        print(f"    topic         : {c['topic']}")
        print(f"    subtopic      : {c['subtopic']}")
        print(f"    risk_level    : {c['risk_level']}")
        print(f"    official_url  : {c['official_url']}")
        print(f"    embedding_dim : {c['embedding_dim']}")
        snippet = (c["snippet"] or "").replace("\n", " ").strip()
        print(f"    snippet[:{SNIPPET_CHARS}] : {snippet}")

    print(f"\n[Planned synthetic test queries ({len(SYNTHETIC_TEST_QUERIES)})]")
    print("  (synthetic paraphrases of public regulatory topics —")
    print("   NOT real user questions, NOT stored, NOT embedded in this dry-run)")
    for query, expected in SYNTHETIC_TEST_QUERIES:
        print(f"    Query             : {query}")
        print(f"    Expected citation : {expected}")
        print()

    print(f"[Safety invariants]")
    print(f"  privacy_safe_answer_logs count : {facts.get('privacy_safe_answer_logs_count')}")

    print(f"\n[Readiness]")
    if is_ready:
        print("  READY — active chunks and expected target citations are in place")
    else:
        print(f"  NOT READY — {len(issues)} issue(s):")
        for issue in issues:
            print(f"    ! {issue}")

    print(f"\n[What this dry-run did NOT do]")
    print("  - Did NOT call Ollama")
    print("  - Did NOT generate any query embeddings")
    print("  - Did NOT call OpenAI, Anthropic, or any public AI API")
    print("  - Did NOT generate any legal answers")
    print("  - Did NOT process any real user question")
    print("  - Did NOT store any question text")
    print("  - Did NOT write to privacy_safe_answer_logs")
    print("  - Did NOT write to any database table")

    print()
    print(_DIVIDER)


def _print_json_summary(facts: dict[str, Any], issues: list[str]) -> None:
    status = "dry_run_ok" if not issues else "dry_run_not_ready"
    summary: dict[str, Any] = {
        "status": status,
        "would_write": False,
        "would_call_ollama": False,
        "would_generate_answers": False,
        "active_dataset": facts.get("active_dataset_name"),
        "active_chunk_count": facts.get("active_chunk_count", 0),
        "synthetic_query_count": len(SYNTHETIC_TEST_QUERIES),
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

    raw_url = _resolve_database_url(args.database_url)
    if not raw_url:
        print("ERROR: no DATABASE_URL found.")
        print(
            "       Set DATABASE_URL in the environment, pass --database-url, "
            "or add DATABASE_URL to backend/.env."
        )
        return 1
    db_url = _normalize_db_url(raw_url)

    try:
        with psycopg.connect(db_url, autocommit=True) as conn:
            with conn.cursor() as cur:
                facts = _gather_facts(cur)

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

    issues = _evaluate_readiness(facts)
    _print_report(facts, issues)
    _print_json_summary(facts, issues)

    # Exit 0 even when not ready — the dry-run itself completed successfully.
    # Only DB config / connection / query failures cause exit 1, matching
    # the convention used by dry_run_activate_dataset.py.
    return 0


if __name__ == "__main__":
    sys.exit(main())
