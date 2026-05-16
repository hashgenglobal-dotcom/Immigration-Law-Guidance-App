#!/usr/bin/env python3
"""Validate vector retrieval quality against the active public legal_chunks.

Runs five synthetic test queries through local Ollama embedding and pgvector
search, then checks whether each expected CFR citation appears in the top-k
results. Exits 0 (PASS) only when all five queries retrieve their expected
citation and privacy_safe_answer_logs is still 0.

Privacy
-------
This script uses only synthetic, public test questions — never real user facts.
- Only synthetic test queries are embedded; real user immigration facts must
  never be passed here.
- Query embedding happens locally via Ollama; no text leaves the machine.
- No answer generation happens; only citation and distance metadata is read.
- No question text is stored in any database table.
- No public AI API (OpenAI, Anthropic, Cohere, etc.) is called.
- No database writes happen in this script.

Usage
-----
    # Auto-detect DB URL from backend/.env (uses default top-k = 5)
    uv run --project backend python scripts/validate_retrieval_results.py

    # Explicit top-k
    uv run --project backend python scripts/validate_retrieval_results.py --top-k 3

    # Explicit Ollama URL and database URL
    uv run --project backend python scripts/validate_retrieval_results.py \\
        --ollama-url http://localhost:11434 \\
        --database-url "postgresql://user@localhost:5432/immigration_law_dev"

Exit codes
----------
* 0 — all expected citations found in top-k and privacy_safe_answer_logs = 0 (PASS).
* 1 — one or more citations not found, privacy_safe_answer_logs != 0, DB/Ollama
      error, dimension mismatch, or no active chunks (FAIL).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

# psycopg (v3) is the only non-stdlib dependency.
# Run with: uv run --project backend python scripts/validate_retrieval_results.py
try:
    import psycopg
except ImportError:
    print(
        "ERROR: psycopg (v3) is not installed in the current Python environment.\n"
        "       Run this script with:\n"
        "         uv run --project backend python scripts/validate_retrieval_results.py"
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BACKEND_ENV_PATH = Path("backend/.env")

DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "nomic-embed-text"
DEFAULT_TOP_K = 5

EXPECTED_DIM = 768    # must match legal_chunks.embedding vector(768)
OLLAMA_TIMEOUT = 60   # seconds
QUERY_LOG_MAX = 180   # chars shown in log lines — query text is never stored

# Synthetic test cases from docs/retrieval-milestone-plan.md §5.
# These are paraphrases of public regulatory topics — no names, A-numbers,
# case facts, or other identifying information.
TEST_CASES: tuple[dict[str, str], ...] = (
    {
        "query": "Can asylum applicants get work authorization?",
        "expected_citation": "8 CFR § 208.7",
    },
    {
        "query": "When can someone file for asylum?",
        "expected_citation": "8 CFR § 208.4",
    },
    {
        "query": "Who is eligible for adjustment of status?",
        "expected_citation": "8 CFR § 245.1",
    },
    {
        "query": "What categories are authorized for employment?",
        "expected_citation": "8 CFR § 274a.12",
    },
    {
        "query": "What is a Notice to Appear?",
        "expected_citation": "8 CFR § 239.1",
    },
)

_DIVIDER = "-" * 72


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate vector retrieval quality against the active public legal_chunks. "
            "Embeds five synthetic test queries locally via Ollama and checks that each "
            "expected CFR citation appears in the top-k pgvector results. "
            "No answer generation. No question storage. No public AI APIs."
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
        "--ollama-url",
        default=DEFAULT_OLLAMA_URL,
        metavar="URL",
        help=f"Local Ollama base URL. Default: {DEFAULT_OLLAMA_URL}",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        metavar="MODEL",
        help=f"Ollama embedding model. Default: {DEFAULT_MODEL}",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=DEFAULT_TOP_K,
        metavar="N",
        help=(
            f"Number of top chunks to retrieve per query. "
            f"A query PASSES if its expected citation appears anywhere in the top-k. "
            f"Default: {DEFAULT_TOP_K}"
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
# Ollama embedding (local only — no public AI API)
# ---------------------------------------------------------------------------


def _embed_query(ollama_url: str, model: str, query: str) -> list[float]:
    """Embed query text via the local Ollama /api/embed endpoint.

    Only synthetic test questions are embedded here — never real user facts.
    All embedding work happens locally; no text leaves the machine.
    """
    url = ollama_url.rstrip("/") + "/api/embed"
    payload = json.dumps({"model": model, "input": query}).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT) as resp:
            body = json.loads(resp.read())
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Ollama request failed ({type(exc).__name__}): {exc.reason}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Ollama returned invalid JSON: {exc}") from exc

    embeddings = body.get("embeddings")
    if not embeddings or not isinstance(embeddings, list) or not embeddings[0]:
        raise RuntimeError(
            "Ollama response did not contain an 'embeddings' list. "
            f"Keys returned: {list(body.keys())}"
        )
    return embeddings[0]


def _format_vector(embedding: list[float]) -> str:
    """Format a float list as a pgvector-compatible string: [x,y,z,...]"""
    return "[" + ",".join(str(x) for x in embedding) + "]"


# ---------------------------------------------------------------------------
# Database queries (all read-only SELECT queries)
# ---------------------------------------------------------------------------


def _fetch_active_dataset_name(cur: Any) -> str | None:
    """Return the version_name of the currently active dataset, or None."""
    cur.execute(
        "SELECT version_name FROM dataset_versions WHERE status = 'active' LIMIT 1"
    )
    row = cur.fetchone()
    return row[0] if row else None


def _count_active_chunks(cur: Any) -> int:
    """Return the total number of active, embedded chunks available for retrieval."""
    cur.execute(
        "SELECT COUNT(*) FROM legal_chunks WHERE is_active = TRUE AND embedding IS NOT NULL"
    )
    return cur.fetchone()[0]


def _fetch_psal_count(cur: Any) -> int:
    """Return privacy_safe_answer_logs row count (safety invariant only — no content read)."""
    cur.execute("SELECT COUNT(*) FROM privacy_safe_answer_logs")
    return cur.fetchone()[0]


def _run_vector_search(
    cur: Any,
    query_vector_str: str,
    top_k: int,
) -> list[dict[str, Any]]:
    """Search active public legal_chunks by pgvector cosine distance.

    Filters to is_active = TRUE so only the published dataset is searched.
    No answer generation happens here — only citation and distance are returned.
    No question text is written to any table.
    """
    cur.execute(
        """
        SELECT
            lc.citation,
            lc.embedding <-> %s::vector AS distance
        FROM legal_chunks lc
        WHERE lc.is_active = TRUE
          AND lc.embedding IS NOT NULL
        ORDER BY lc.embedding <-> %s::vector
        LIMIT %s
        """,
        (query_vector_str, query_vector_str, top_k),
    )
    return [
        {"citation": r[0], "distance": float(r[1]) if r[1] is not None else None}
        for r in cur.fetchall()
    ]


# ---------------------------------------------------------------------------
# Per-query test runner
# ---------------------------------------------------------------------------


def _run_one_test(
    cur: Any,
    ollama_url: str,
    model: str,
    query: str,
    expected_citation: str,
    top_k: int,
) -> dict[str, Any]:
    """Embed one synthetic query, search, and return a result dict.

    The result contains: query, expected_citation, error (if any), query_dim,
    results (list of {citation, distance}), expected_rank (1-based or None),
    top_citation, distance_of_expected, passed.
    """
    result: dict[str, Any] = {
        "query": query,
        "expected_citation": expected_citation,
        "error": None,
        "query_dim": None,
        "results": [],
        "expected_rank": None,
        "top_citation": None,
        "distance_of_expected": None,
        "passed": False,
    }

    # Embed query locally via Ollama — no public AI API used.
    try:
        embedding = _embed_query(ollama_url, model, query)
    except RuntimeError as exc:
        result["error"] = str(exc)
        return result

    dim = len(embedding)
    result["query_dim"] = dim
    if dim != EXPECTED_DIM:
        result["error"] = (
            f"embedding dimension {dim} != expected {EXPECTED_DIM}; "
            f"check that model is {DEFAULT_MODEL}"
        )
        return result

    query_vector_str = _format_vector(embedding)

    # Run vector search against active chunks.
    search_results = _run_vector_search(cur, query_vector_str, top_k)
    result["results"] = search_results

    if search_results:
        result["top_citation"] = search_results[0]["citation"]

    # Locate the expected citation in the ranked results.
    for rank, r in enumerate(search_results, start=1):
        if r["citation"] == expected_citation:
            result["expected_rank"] = rank
            result["distance_of_expected"] = r["distance"]
            result["passed"] = True
            break

    return result


# ---------------------------------------------------------------------------
# Report printing
# ---------------------------------------------------------------------------


def _truncate_query(query: str) -> str:
    """Truncate query for log display — full text is never stored."""
    if len(query) <= QUERY_LOG_MAX:
        return query
    return query[:QUERY_LOG_MAX] + "…"


def _print_report(
    model: str,
    top_k: int,
    active_dataset_name: str | None,
    active_chunk_count: int,
    psal_count: int,
    test_results: list[dict[str, Any]],
) -> None:
    total = len(test_results)
    passed = sum(1 for r in test_results if r["passed"])
    failed = total - passed
    psal_ok = psal_count == 0
    all_passed = (failed == 0) and psal_ok

    print(_DIVIDER)
    print("retrieval validation — active public legal_chunks")
    print("(Read-only. Synthetic queries only. No answer generation. No question stored.)")
    print(_DIVIDER)

    print(f"\n[Configuration]")
    print(f"  model                  : {model}")
    print(f"  top_k                  : {top_k}")
    print(f"  active dataset         : {active_dataset_name or '(none)'}")
    print(f"  active embedded chunks : {active_chunk_count}")

    print(f"\n[Per-query results]")
    for i, r in enumerate(test_results, start=1):
        verdict = "PASS" if r["passed"] else "FAIL"
        print(f"\n  [{i}/{total}] {verdict}")
        print(f"    query (truncated)    : {_truncate_query(r['query'])}")
        print(f"    expected citation    : {r['expected_citation']}")

        if r["error"]:
            print(f"    error               : {r['error']}")
        else:
            top = r["top_citation"] or "(no results)"
            print(f"    top result citation : {top}")

            if r["expected_rank"] is not None:
                dist = r["distance_of_expected"]
                dist_str = f"{dist:.6f}" if dist is not None else "n/a"
                print(f"    expected rank       : {r['expected_rank']} of {top_k}  (distance={dist_str})")
            else:
                print(f"    expected rank       : not found in top {top_k}")
                if r["results"]:
                    retrieved = ", ".join(x["citation"] for x in r["results"])
                    print(f"    retrieved           : {retrieved}")

    print(f"\n[Summary]")
    print(f"  total tests            : {total}")
    print(f"  passed                 : {passed}")
    print(f"  failed                 : {failed}")
    print(f"  privacy_safe_answer_logs count : {psal_count}")

    print()
    if all_passed:
        print("  status : PASS")
    else:
        print("  status : FAIL")
        if failed > 0:
            print(f"    ! {failed} query/queries did not retrieve the expected citation in top {top_k}")
        if not psal_ok:
            print(f"    ! privacy_safe_answer_logs has {psal_count} row(s); expected 0")

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

    # ---- connect to PostgreSQL and run all test cases ----
    try:
        with psycopg.connect(db_url, autocommit=True) as conn:
            with conn.cursor() as cur:
                active_dataset_name = _fetch_active_dataset_name(cur)
                active_chunk_count = _count_active_chunks(cur)
                psal_count = _fetch_psal_count(cur)

                if active_chunk_count == 0:
                    print(
                        "ERROR: no active, embedded chunks found in legal_chunks. "
                        "Run activate_dataset.py --yes first."
                    )
                    return 1

                print(
                    f"Running {len(TEST_CASES)} retrieval tests "
                    f"(top_k={args.top_k}, model={args.model}) …"
                )

                # Run each synthetic test case.
                # Only synthetic test questions are embedded here —
                # embeddings happen locally via Ollama; no answer generation occurs.
                test_results: list[dict[str, Any]] = []
                for tc in TEST_CASES:
                    print(f"  [{len(test_results) + 1}/{len(TEST_CASES)}] {_truncate_query(tc['query'])}")
                    result = _run_one_test(
                        cur=cur,
                        ollama_url=args.ollama_url,
                        model=args.model,
                        query=tc["query"],
                        expected_citation=tc["expected_citation"],
                        top_k=args.top_k,
                    )
                    test_results.append(result)

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

    print()
    _print_report(
        model=args.model,
        top_k=args.top_k,
        active_dataset_name=active_dataset_name,
        active_chunk_count=active_chunk_count,
        psal_count=psal_count,
        test_results=test_results,
    )

    passed = sum(1 for r in test_results if r["passed"])
    all_passed = (passed == len(TEST_CASES)) and (psal_count == 0)
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
