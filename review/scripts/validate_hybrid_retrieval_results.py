#!/usr/bin/env python3
"""Hybrid retrieval validation against active public legal_chunks.

Runs all five synthetic test queries through hybrid retrieval (vector + keyword + RRF)
and verifies that each expected CFR citation appears in the top-k hybrid results and
ranks first for every test case where expected_rank_1 is True.

Privacy
-------
This script handles synthetic test queries against public legal-source data only.
- Only synthetic, public test questions are embedded — never real user facts.
- Query embedding happens locally via Ollama; no text leaves the machine.
- No answer generation happens; only retrieved chunk metadata is used for validation.
- No question text is stored in any table.
- No public AI API (OpenAI, Anthropic, Cohere, etc.) is called.
- No database writes happen in this script.

WARNING: This script is for synthetic development queries only.
Do not pass real user immigration facts (names, case facts, A-numbers,
addresses, visa history) into this script.

Usage
-----
    # Run all five synthetic validation queries (DB URL auto-detected from backend/.env)
    uv run --project backend python scripts/validate_hybrid_retrieval_results.py

    # Specify top-k and candidate pool sizes
    uv run --project backend python scripts/validate_hybrid_retrieval_results.py \\
        --top-k 5 --vector-candidates 10 --keyword-candidates 10

    # Explicit database URL
    uv run --project backend python scripts/validate_hybrid_retrieval_results.py \\
        --database-url "postgresql://user@localhost:5432/immigration_law_dev"

Exit codes
----------
* 0 — all expected citations appear in top-k, all expected_rank_1 checks pass,
      and privacy_safe_answer_logs count is 0.
* 1 — any citation missing from top-k, any rank_1 check fails, psal_count != 0,
      DB config missing, DB error, Ollama error, or embedding dimension mismatch.
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
# Run with: uv run --project backend python scripts/validate_hybrid_retrieval_results.py
try:
    import psycopg
except ImportError:
    print(
        "ERROR: psycopg (v3) is not installed in the current Python environment.\n"
        "       Run this script with:\n"
        "         uv run --project backend python scripts/validate_hybrid_retrieval_results.py"
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BACKEND_ENV_PATH = Path("backend/.env")

DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "nomic-embed-text"
DEFAULT_TOP_K = 5
DEFAULT_VECTOR_CANDIDATES = 10
DEFAULT_KEYWORD_CANDIDATES = 10

# RRF constant — standard value; controls how steeply early ranks are rewarded.
# Must match hybrid_retrieve_legal_chunks.py so validation uses the same fusion.
RRF_K = 60

EXPECTED_DIM = 768    # must match legal_chunks.embedding vector(768)
OLLAMA_TIMEOUT = 60   # seconds
QUERY_LOG_MAX = 180   # chars shown in log display (full query text is never stored)

_DIVIDER = "-" * 72

# ---------------------------------------------------------------------------
# Synthetic test cases (public regulatory topics only — no user facts)
# ---------------------------------------------------------------------------

# All five queries are paraphrases of public eCFR Title 8 regulatory topics.
# They contain no names, A-numbers, dates of birth, addresses, case facts, or
# other identifying information. expected_rank_1 = True means the expected
# citation must be the top hybrid result, not merely somewhere in top-k.
TEST_CASES: tuple[dict[str, Any], ...] = (
    {
        "query": "Can asylum applicants get work authorization?",
        "expected_citation": "8 CFR § 208.7",
        "expected_rank_1": True,
    },
    {
        "query": "When can someone file for asylum?",
        "expected_citation": "8 CFR § 208.4",
        "expected_rank_1": True,
    },
    {
        "query": "Who is eligible for adjustment of status?",
        "expected_citation": "8 CFR § 245.1",
        "expected_rank_1": True,
    },
    {
        "query": "What categories are authorized for employment?",
        "expected_citation": "8 CFR § 274a.12",
        "expected_rank_1": True,
    },
    {
        "query": "What is a Notice to Appear?",
        "expected_citation": "8 CFR § 239.1",
        "expected_rank_1": True,
    },
)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Hybrid retrieval validation (vector + keyword + RRF) against active "
            "public legal_chunks. Embeds all five synthetic test queries locally "
            "via Ollama, runs hybrid retrieval for each, and checks that each "
            "expected CFR citation appears in top-k at rank 1. "
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
        help=f"Number of final hybrid results to check. Default: {DEFAULT_TOP_K}",
    )
    parser.add_argument(
        "--vector-candidates",
        type=int,
        default=DEFAULT_VECTOR_CANDIDATES,
        metavar="N",
        help=(
            f"Number of candidates to fetch from vector retrieval before fusion. "
            f"Default: {DEFAULT_VECTOR_CANDIDATES}"
        ),
    )
    parser.add_argument(
        "--keyword-candidates",
        type=int,
        default=DEFAULT_KEYWORD_CANDIDATES,
        metavar="N",
        help=(
            f"Number of candidates to fetch from keyword retrieval before fusion. "
            f"Default: {DEFAULT_KEYWORD_CANDIDATES}"
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
    n_candidates: int,
) -> list[dict[str, Any]]:
    """Fetch vector candidates from active public legal_chunks ordered by cosine distance.

    Filters to is_active = TRUE so only the published dataset is searched.
    Returns only chunk_id, citation, and distance — enough for RRF fusion and
    citation-presence validation. No answer generation. No question text written.
    """
    cur.execute(
        """
        SELECT
            lc.id                                   AS chunk_id,
            lc.citation,
            lc.embedding <-> %s::vector             AS distance
        FROM legal_chunks lc
        WHERE lc.is_active = TRUE
          AND lc.embedding IS NOT NULL
        ORDER BY lc.embedding <-> %s::vector
        LIMIT %s
        """,
        (query_vector_str, query_vector_str, n_candidates),
    )
    return [
        {
            "chunk_id": r[0],
            "citation": r[1],
            "distance": float(r[2]) if r[2] is not None else None,
        }
        for r in cur.fetchall()
    ]


def _run_keyword_search(
    cur: Any,
    query: str,
    n_candidates: int,
) -> list[dict[str, Any]]:
    """Fetch keyword candidates from active public legal_chunks via full-text search.

    Uses PostgreSQL plainto_tsquery against legal_chunks.search_vector.
    Filters to is_active = TRUE. Returns only chunk_id, citation, and kw_score
    — enough for RRF fusion and citation-presence validation.
    No answer generation. No question text written.
    """
    cur.execute(
        """
        SELECT
            lc.id                                                           AS chunk_id,
            lc.citation,
            ts_rank_cd(lc.search_vector, plainto_tsquery('english', %s))   AS kw_score
        FROM legal_chunks lc
        WHERE lc.is_active = TRUE
          AND lc.search_vector IS NOT NULL
          AND lc.search_vector @@ plainto_tsquery('english', %s)
        ORDER BY ts_rank_cd(lc.search_vector, plainto_tsquery('english', %s)) DESC
        LIMIT %s
        """,
        (query, query, query, n_candidates),
    )
    return [
        {
            "chunk_id": r[0],
            "citation": r[1],
            "kw_score": float(r[2]) if r[2] is not None else None,
        }
        for r in cur.fetchall()
    ]


# ---------------------------------------------------------------------------
# Reciprocal Rank Fusion
# ---------------------------------------------------------------------------


def _fuse_results(
    vector_results: list[dict[str, Any]],
    keyword_results: list[dict[str, Any]],
    top_k: int,
) -> list[dict[str, Any]]:
    """Merge vector and keyword candidates using Reciprocal Rank Fusion.

    RRF score = 1/(RRF_K + vector_rank) + 1/(RRF_K + keyword_rank)
    Chunks in both lists accumulate both scores; chunks in only one list
    still receive that signal's contribution. Sorted by hybrid_score DESC.
    Logic is identical to hybrid_retrieve_legal_chunks.py for consistency.
    """
    combined: dict[int, dict[str, Any]] = {}

    for rank, row in enumerate(vector_results, start=1):
        chunk_id = row["chunk_id"]
        rrf_vector = 1.0 / (RRF_K + rank)
        combined[chunk_id] = {
            "chunk_id": chunk_id,
            "citation": row["citation"],
            "vector_rank": rank,
            "vector_distance": row["distance"],
            "keyword_rank": None,
            "rrf_vector": rrf_vector,
            "rrf_keyword": 0.0,
            "hybrid_score": rrf_vector,
        }

    for rank, row in enumerate(keyword_results, start=1):
        chunk_id = row["chunk_id"]
        rrf_keyword = 1.0 / (RRF_K + rank)
        if chunk_id in combined:
            combined[chunk_id]["keyword_rank"] = rank
            combined[chunk_id]["rrf_keyword"] = rrf_keyword
            combined[chunk_id]["hybrid_score"] += rrf_keyword
        else:
            combined[chunk_id] = {
                "chunk_id": chunk_id,
                "citation": row["citation"],
                "vector_rank": None,
                "vector_distance": None,
                "keyword_rank": rank,
                "rrf_vector": 0.0,
                "rrf_keyword": rrf_keyword,
                "hybrid_score": rrf_keyword,
            }

    ranked = sorted(combined.values(), key=lambda x: x["hybrid_score"], reverse=True)
    return ranked[:top_k]


# ---------------------------------------------------------------------------
# Per-query test runner
# ---------------------------------------------------------------------------


def _run_one_test(
    cur: Any,
    ollama_url: str,
    model: str,
    query: str,
    expected_citation: str,
    expected_rank_1: bool,
    top_k: int,
    vector_candidates: int,
    keyword_candidates: int,
) -> dict[str, Any]:
    """Embed one synthetic query and run hybrid retrieval validation.

    Only synthetic test questions are embedded — never real user facts.
    All embedding work happens locally via Ollama; no text leaves the machine.
    No answer generation happens. No question text is stored in any table.
    No public AI API is called.
    Returns a dict describing the test outcome; does not raise on soft failures.
    """
    # Embed the synthetic query locally — no answer generation, no question storage.
    try:
        embedding = _embed_query(ollama_url, model, query)
    except RuntimeError as exc:
        return {
            "query": query,
            "expected_citation": expected_citation,
            "expected_rank_1": expected_rank_1,
            "error": str(exc),
            "query_dim": None,
            "hybrid_results": [],
            "expected_rank": None,
            "top_citation": None,
            "in_top_k": False,
            "rank_1_passed": False,
            "passed": False,
        }

    query_dim = len(embedding)
    if query_dim != EXPECTED_DIM:
        return {
            "query": query,
            "expected_citation": expected_citation,
            "expected_rank_1": expected_rank_1,
            "error": (
                f"query embedding dimension {query_dim} != {EXPECTED_DIM}; "
                f"check that the model is {model}"
            ),
            "query_dim": query_dim,
            "hybrid_results": [],
            "expected_rank": None,
            "top_citation": None,
            "in_top_k": False,
            "rank_1_passed": False,
            "passed": False,
        }

    query_vector_str = _format_vector(embedding)

    # Run both retrieval signals over active public chunks — read-only, no writes.
    vector_results = _run_vector_search(cur, query_vector_str, vector_candidates)
    keyword_results = _run_keyword_search(cur, query, keyword_candidates)

    # Fuse signals with Reciprocal Rank Fusion (identical logic to hybrid_retrieve_legal_chunks.py).
    hybrid_results = _fuse_results(vector_results, keyword_results, top_k)

    # Check whether expected citation appears in the hybrid top-k.
    citations = [r["citation"] for r in hybrid_results]
    expected_rank: int | None = None
    for i, citation in enumerate(citations, start=1):
        if citation == expected_citation:
            expected_rank = i
            break

    in_top_k = expected_rank is not None
    # rank_1_passed: True if expected_rank_1 is False (no rank constraint), or if rank == 1.
    rank_1_passed = (expected_rank == 1) if expected_rank_1 else True
    passed = in_top_k and rank_1_passed

    return {
        "query": query,
        "expected_citation": expected_citation,
        "expected_rank_1": expected_rank_1,
        "error": None,
        "query_dim": query_dim,
        "hybrid_results": hybrid_results,
        "expected_rank": expected_rank,
        "top_citation": citations[0] if citations else None,
        "in_top_k": in_top_k,
        "rank_1_passed": rank_1_passed,
        "passed": passed,
    }


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
    vector_candidates: int,
    keyword_candidates: int,
    active_dataset_name: str | None,
    active_chunk_count: int,
    psal_count: int,
    test_results: list[dict[str, Any]],
) -> None:
    print(_DIVIDER)
    print("hybrid retrieval validation — active public legal_chunks")
    print("(Read-only. Synthetic queries only. No answer generation. No question stored.)")
    print(_DIVIDER)

    print(f"\n[Configuration]")
    print(f"  model              : {model}")
    print(f"  top_k              : {top_k}")
    print(f"  vector_candidates  : {vector_candidates}")
    print(f"  keyword_candidates : {keyword_candidates}")
    print(f"  RRF_K              : {RRF_K}")

    print(f"\n[Dataset state]")
    print(f"  active dataset         : {active_dataset_name or '(none)'}")
    print(f"  active embedded chunks : {active_chunk_count}")
    print(f"  privacy_safe_answer_logs count : {psal_count}")

    print(f"\n[Test results]")
    for i, result in enumerate(test_results, start=1):
        print()
        print(f"  Test {i}")
        print(f"    query (truncated)    : {_truncate_query(result['query'])}")
        print(f"    expected citation    : {result['expected_citation']}")

        if result["error"]:
            print(f"    error               : {result['error']}")
            print(f"    result              : FAIL")
            continue

        top_citation = result["top_citation"] or "(none)"
        print(f"    top hybrid result   : {top_citation}")

        if result["expected_rank"] is not None:
            rank_str = str(result["expected_rank"])
        else:
            rank_str = f"not found in top {top_k}"
        print(f"    expected rank       : {rank_str}")

        if result["expected_rank_1"]:
            rank1_label = "PASS" if result["rank_1_passed"] else "FAIL"
            print(f"    rank_1_check        : {rank1_label}")

        if result["passed"]:
            print(f"    result              : PASS")
        else:
            print(f"    result              : FAIL")
            if not result["in_top_k"]:
                retrieved_citations = [r["citation"] for r in result["hybrid_results"]]
                print(f"    retrieved citations : {retrieved_citations}")

    # ---- summary ----
    total = len(test_results)
    passed_count = sum(1 for r in test_results if r["passed"])
    failed_count = total - passed_count
    rank_1_passed_count = sum(
        1 for r in test_results
        if r["expected_rank_1"] and r["rank_1_passed"] and not r["error"]
    )
    rank_1_total = sum(1 for r in test_results if r["expected_rank_1"])
    rank_1_failed_count = rank_1_total - rank_1_passed_count

    all_passed = passed_count == total and psal_count == 0
    final_status = "PASS" if all_passed else "FAIL"

    print()
    print(_DIVIDER)
    print(f"\n[Summary]")
    print(f"  total tests              : {total}")
    print(f"  passed                   : {passed_count}")
    print(f"  failed                   : {failed_count}")
    print(f"  rank_1_passed            : {rank_1_passed_count} / {rank_1_total}")
    print(f"  rank_1_failed            : {rank_1_failed_count}")
    print(f"  privacy_safe_answer_logs : {psal_count}")
    print(f"  final status             : {final_status}")
    print()
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

    # ---- connect to PostgreSQL and run validation ----
    # All queries are read-only. No answer generation. No question text stored.
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

                # Run all five test cases. Each embeds locally via Ollama, runs hybrid
                # retrieval, and checks citation presence and rank. Continues even if
                # one test fails so all results are visible in a single report.
                test_results: list[dict[str, Any]] = []
                for case in TEST_CASES:
                    print(
                        f"Testing [{len(test_results) + 1}/{len(TEST_CASES)}]: "
                        f"{_truncate_query(case['query'])} …"
                    )
                    result = _run_one_test(
                        cur=cur,
                        ollama_url=args.ollama_url,
                        model=args.model,
                        query=case["query"],
                        expected_citation=case["expected_citation"],
                        expected_rank_1=case["expected_rank_1"],
                        top_k=args.top_k,
                        vector_candidates=args.vector_candidates,
                        keyword_candidates=args.keyword_candidates,
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

    _print_report(
        model=args.model,
        top_k=args.top_k,
        vector_candidates=args.vector_candidates,
        keyword_candidates=args.keyword_candidates,
        active_dataset_name=active_dataset_name,
        active_chunk_count=active_chunk_count,
        psal_count=psal_count,
        test_results=test_results,
    )

    all_passed = all(r["passed"] for r in test_results) and psal_count == 0
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
