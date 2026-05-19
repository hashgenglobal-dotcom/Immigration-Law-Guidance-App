#!/usr/bin/env python3
"""Hybrid retrieval (vector + keyword) against active public legal_chunks.

Embeds a synthetic test query locally with Ollama nomic-embed-text, runs
both a pgvector cosine-distance search and a PostgreSQL full-text search
against active legal_chunks, then merges the two ranked lists using
Reciprocal Rank Fusion (RRF) to produce a single hybrid ranking.

Privacy
-------
This script handles synthetic test queries against public legal-source data only.
- Only synthetic, public test questions are embedded — never real user facts.
- Query embedding happens locally via Ollama; no text leaves the machine.
- No answer generation happens; only retrieved chunk metadata is printed.
- No question text is stored in any table.
- No public AI API (OpenAI, Anthropic, Cohere, etc.) is called.
- No database writes happen in this script.

WARNING: This script is for synthetic development queries only.
Do not pass real user immigration facts (names, case facts, A-numbers,
addresses, visa history) as the --query argument.

Usage
-----
    # Default query against active chunks (DB URL auto-detected from backend/.env)
    uv run --project backend python scripts/hybrid_retrieve_legal_chunks.py

    # Specify a synthetic query
    uv run --project backend python scripts/hybrid_retrieve_legal_chunks.py \\
        --query "Can asylum applicants get work authorization?" --top-k 5

    # Control candidate pool sizes and Ollama URL
    uv run --project backend python scripts/hybrid_retrieve_legal_chunks.py \\
        --query "What is a Notice to Appear?" \\
        --vector-candidates 10 --keyword-candidates 10 --top-k 5

    # Explicit database URL
    uv run --project backend python scripts/hybrid_retrieve_legal_chunks.py \\
        --database-url "postgresql://user@localhost:5432/immigration_law_dev"

Exit codes
----------
* 0 — hybrid retrieval completed successfully.
* 1 — DB config missing, DB error, Ollama error, embedding dimension mismatch,
      or no active chunks found in the database.
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
# Run with: uv run --project backend python scripts/hybrid_retrieve_legal_chunks.py
try:
    import psycopg
except ImportError:
    print(
        "ERROR: psycopg (v3) is not installed in the current Python environment.\n"
        "       Run this script with:\n"
        "         uv run --project backend python scripts/hybrid_retrieve_legal_chunks.py"
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BACKEND_ENV_PATH = Path("backend/.env")

DEFAULT_QUERY = "What is a Notice to Appear?"
DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "nomic-embed-text"
DEFAULT_TOP_K = 5
DEFAULT_VECTOR_CANDIDATES = 10
DEFAULT_KEYWORD_CANDIDATES = 10

# RRF constant — standard value; controls how steeply early ranks are rewarded.
RRF_K = 60

EXPECTED_DIM = 768    # must match legal_chunks.embedding vector(768)
OLLAMA_TIMEOUT = 60   # seconds
SNIPPET_LEN = 500     # chars shown per chunk
QUERY_LOG_MAX = 180   # chars shown in log lines (full query text is never stored)

_DIVIDER = "-" * 72


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Hybrid retrieval (vector + keyword + RRF) against active public "
            "legal_chunks. Embeds a synthetic test query locally via Ollama, "
            "runs both pgvector cosine-distance search and PostgreSQL full-text "
            "search, then merges results with Reciprocal Rank Fusion. "
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
        "--query",
        default=DEFAULT_QUERY,
        metavar="TEXT",
        help=(
            "Synthetic test query to embed and search. "
            "WARNING: use only synthetic, public test questions — "
            "never real user immigration facts. "
            f"Default: {DEFAULT_QUERY!r}"
        ),
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=DEFAULT_TOP_K,
        metavar="N",
        help=f"Number of final hybrid results to return. Default: {DEFAULT_TOP_K}",
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
    No answer generation happens here — only chunk metadata is returned.
    No question text is written to any table.
    """
    cur.execute(
        """
        SELECT
            lc.id                                   AS chunk_id,
            lc.citation,
            lc.topic,
            lc.subtopic,
            lc.risk_level,
            lc.official_url,
            lc.embedding <-> %s::vector             AS distance,
            LEFT(lc.chunk_text, %s)                 AS snippet
        FROM legal_chunks lc
        WHERE lc.is_active = TRUE
          AND lc.embedding IS NOT NULL
        ORDER BY lc.embedding <-> %s::vector
        LIMIT %s
        """,
        (query_vector_str, SNIPPET_LEN, query_vector_str, n_candidates),
    )
    return [
        {
            "chunk_id": r[0],
            "citation": r[1],
            "topic": r[2],
            "subtopic": r[3],
            "risk_level": r[4],
            "official_url": r[5],
            "distance": float(r[6]) if r[6] is not None else None,
            "snippet": r[7],
        }
        for r in cur.fetchall()
    ]


def _run_keyword_search(
    cur: Any,
    query: str,
    n_candidates: int,
) -> list[dict[str, Any]]:
    """Fetch keyword candidates from active public legal_chunks via full-text search.

    Uses PostgreSQL plainto_tsquery against legal_chunks.search_vector, which
    the schema trigger keeps populated from chunk_text. Filters to is_active = TRUE.
    No answer generation happens here — only chunk metadata is returned.
    No question text is written to any table.
    """
    cur.execute(
        """
        SELECT
            lc.id                                                       AS chunk_id,
            lc.citation,
            lc.topic,
            lc.subtopic,
            lc.risk_level,
            lc.official_url,
            ts_rank_cd(lc.search_vector, plainto_tsquery('english', %s)) AS kw_score,
            LEFT(lc.chunk_text, %s)                                     AS snippet
        FROM legal_chunks lc
        WHERE lc.is_active = TRUE
          AND lc.search_vector IS NOT NULL
          AND lc.search_vector @@ plainto_tsquery('english', %s)
        ORDER BY ts_rank_cd(lc.search_vector, plainto_tsquery('english', %s)) DESC
        LIMIT %s
        """,
        (query, SNIPPET_LEN, query, query, n_candidates),
    )
    return [
        {
            "chunk_id": r[0],
            "citation": r[1],
            "topic": r[2],
            "subtopic": r[3],
            "risk_level": r[4],
            "official_url": r[5],
            "kw_score": float(r[6]) if r[6] is not None else None,
            "snippet": r[7],
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
    Chunks that appear in both lists accumulate both scores; chunks that
    appear in only one list still receive that signal's contribution.
    Results are sorted by hybrid_score DESC and truncated to top_k.
    """
    combined: dict[int, dict[str, Any]] = {}

    for rank, row in enumerate(vector_results, start=1):
        chunk_id = row["chunk_id"]
        rrf_vector = 1.0 / (RRF_K + rank)
        combined[chunk_id] = {
            "chunk_id": chunk_id,
            "citation": row["citation"],
            "topic": row["topic"],
            "subtopic": row["subtopic"],
            "risk_level": row["risk_level"],
            "official_url": row["official_url"],
            "snippet": row["snippet"],
            "vector_rank": rank,
            "vector_distance": row["distance"],
            "keyword_rank": None,
            "kw_score": None,
            "rrf_vector": rrf_vector,
            "rrf_keyword": 0.0,
            "hybrid_score": rrf_vector,
        }

    for rank, row in enumerate(keyword_results, start=1):
        chunk_id = row["chunk_id"]
        rrf_keyword = 1.0 / (RRF_K + rank)
        if chunk_id in combined:
            combined[chunk_id]["keyword_rank"] = rank
            combined[chunk_id]["kw_score"] = row["kw_score"]
            combined[chunk_id]["rrf_keyword"] = rrf_keyword
            combined[chunk_id]["hybrid_score"] += rrf_keyword
        else:
            combined[chunk_id] = {
                "chunk_id": chunk_id,
                "citation": row["citation"],
                "topic": row["topic"],
                "subtopic": row["subtopic"],
                "risk_level": row["risk_level"],
                "official_url": row["official_url"],
                "snippet": row["snippet"],
                "vector_rank": None,
                "vector_distance": None,
                "keyword_rank": rank,
                "kw_score": row["kw_score"],
                "rrf_vector": 0.0,
                "rrf_keyword": rrf_keyword,
                "hybrid_score": rrf_keyword,
            }

    ranked = sorted(combined.values(), key=lambda x: x["hybrid_score"], reverse=True)
    return ranked[:top_k]


# ---------------------------------------------------------------------------
# Report printing
# ---------------------------------------------------------------------------


def _truncate_query(query: str) -> str:
    """Truncate query for log display — full text is never stored."""
    if len(query) <= QUERY_LOG_MAX:
        return query
    return query[:QUERY_LOG_MAX] + "…"


def _print_report(
    query: str,
    model: str,
    query_dim: int,
    top_k: int,
    vector_candidates: int,
    keyword_candidates: int,
    active_dataset_name: str | None,
    active_chunk_count: int,
    psal_count: int,
    vector_results: list[dict[str, Any]],
    keyword_results: list[dict[str, Any]],
    hybrid_results: list[dict[str, Any]],
) -> None:
    print(_DIVIDER)
    print("hybrid retrieval — active public legal_chunks (vector + keyword + RRF)")
    print("(Read-only. Synthetic query only. No answer generation. No question stored.)")
    print(_DIVIDER)

    print(f"\n[Query]")
    print(f"  text (truncated)       : {_truncate_query(query)}")
    print(f"  embedding model        : {model}")
    print(f"  embedding dimension    : {query_dim}")
    print(f"  top_k                  : {top_k}")
    print(f"  vector_candidates      : {vector_candidates}")
    print(f"  keyword_candidates     : {keyword_candidates}")
    print(f"  RRF_K constant         : {RRF_K}")

    print(f"\n[Dataset state]")
    print(f"  active dataset         : {active_dataset_name or '(none)'}")
    print(f"  active embedded chunks : {active_chunk_count}")
    print(f"  privacy_safe_answer_logs count : {psal_count}")

    # ---- vector signal summary ----
    print(f"\n[Vector candidates ({len(vector_results)} retrieved)]")
    if not vector_results:
        print("  (none)")
    else:
        for i, r in enumerate(vector_results, start=1):
            dist_str = f"{r['distance']:.6f}" if r["distance"] is not None else "n/a"
            print(f"  {i:>2}. [{dist_str}] {r['citation']}")

    # ---- keyword signal summary ----
    print(f"\n[Keyword candidates ({len(keyword_results)} retrieved)]")
    if not keyword_results:
        print("  (none — no full-text matches for this query)")
    else:
        for i, r in enumerate(keyword_results, start=1):
            kw_str = f"{r['kw_score']:.6f}" if r["kw_score"] is not None else "n/a"
            print(f"  {i:>2}. [ts_rank={kw_str}] {r['citation']}")

    # ---- hybrid results ----
    print(f"\n[Hybrid results — top {len(hybrid_results)} of {top_k} requested]")
    if not hybrid_results:
        print("  (no results)")
    else:
        for i, r in enumerate(hybrid_results, start=1):
            signals: list[str] = []
            if r["vector_rank"] is not None:
                signals.append(f"vector#{r['vector_rank']}")
            if r["keyword_rank"] is not None:
                signals.append(f"kw#{r['keyword_rank']}")
            signal_str = "+".join(signals) if signals else "unknown"

            print(f"\n  Rank {i}  [{signal_str}]  hybrid_score={r['hybrid_score']:.6f}")
            print(f"    chunk_id       : {r['chunk_id']}")
            print(f"    citation       : {r['citation']}")
            print(f"    topic          : {r['topic']}")
            print(f"    subtopic       : {r['subtopic']}")
            print(f"    risk_level     : {r['risk_level']}")
            print(f"    url            : {r['official_url']}")

            if r["vector_rank"] is not None:
                dist_str = f"{r['vector_distance']:.6f}" if r["vector_distance"] is not None else "n/a"
                rrf_v = f"{r['rrf_vector']:.6f}"
                print(f"    vector_rank    : {r['vector_rank']}  distance={dist_str}  rrf={rrf_v}")
            else:
                print(f"    vector_rank    : not in vector candidates")

            if r["keyword_rank"] is not None:
                kw_str = f"{r['kw_score']:.6f}" if r["kw_score"] is not None else "n/a"
                rrf_k = f"{r['rrf_keyword']:.6f}"
                print(f"    keyword_rank   : {r['keyword_rank']}  ts_rank={kw_str}  rrf={rrf_k}")
            else:
                print(f"    keyword_rank   : not in keyword candidates")

            snippet = (r["snippet"] or "").strip().replace("\n", " ")
            print(f"    snippet        : {snippet[:SNIPPET_LEN]}")

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

    # ---- embed query locally via Ollama ----
    # Only synthetic test questions reach this point — never real user facts.
    # All embedding work happens on-device; no text leaves the machine.
    print(f"Embedding query via local Ollama ({args.model}) …")
    try:
        embedding = _embed_query(args.ollama_url, args.model, args.query)
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        print(
            "       Ensure Ollama is running locally and the model is available:\n"
            f"         ollama pull {args.model}\n"
            f"         ollama serve"
        )
        return 1

    # ---- verify embedding dimension ----
    query_dim = len(embedding)
    if query_dim != EXPECTED_DIM:
        print(
            f"ERROR: query embedding has dimension {query_dim}; "
            f"expected {EXPECTED_DIM}. "
            f"Check that the model is {DEFAULT_MODEL}."
        )
        return 1

    query_vector_str = _format_vector(embedding)

    # ---- connect to PostgreSQL and run retrieval ----
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

                # Vector retrieval — pgvector cosine distance over active chunks.
                # No answer generation. No question text stored.
                vector_results = _run_vector_search(
                    cur, query_vector_str, args.vector_candidates
                )

                # Keyword retrieval — PostgreSQL full-text over active chunks.
                # No answer generation. No question text stored.
                keyword_results = _run_keyword_search(
                    cur, args.query, args.keyword_candidates
                )

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

    # ---- fuse results with RRF ----
    hybrid_results = _fuse_results(vector_results, keyword_results, args.top_k)

    _print_report(
        query=args.query,
        model=args.model,
        query_dim=query_dim,
        top_k=args.top_k,
        vector_candidates=args.vector_candidates,
        keyword_candidates=args.keyword_candidates,
        active_dataset_name=active_dataset_name,
        active_chunk_count=active_chunk_count,
        psal_count=psal_count,
        vector_results=vector_results,
        keyword_results=keyword_results,
        hybrid_results=hybrid_results,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
