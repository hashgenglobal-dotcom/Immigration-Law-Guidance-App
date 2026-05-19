#!/usr/bin/env python3
"""Vector retrieval against active public legal_chunks using a local Ollama embedding.

This script is retrieval-only. It embeds a synthetic test query locally with
Ollama nomic-embed-text, then searches the active legal_chunks using pgvector
cosine distance. It does not generate answers, does not store questions, and
does not write to any database table.

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
    uv run --project backend python scripts/retrieve_legal_chunks.py

    # Specify a synthetic query
    uv run --project backend python scripts/retrieve_legal_chunks.py \\
        --query "When can someone file for asylum?"

    # Specify top-k and Ollama URL
    uv run --project backend python scripts/retrieve_legal_chunks.py \\
        --query "Who is eligible for adjustment of status?" \\
        --top-k 5 \\
        --ollama-url http://localhost:11434

    # Explicit database URL
    uv run --project backend python scripts/retrieve_legal_chunks.py \\
        --database-url "postgresql://user@localhost:5432/immigration_law_dev"

Exit codes
----------
* 0 — retrieval completed successfully.
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
# Run with: uv run --project backend python scripts/retrieve_legal_chunks.py
try:
    import psycopg
except ImportError:
    print(
        "ERROR: psycopg (v3) is not installed in the current Python environment.\n"
        "       Run this script with:\n"
        "         uv run --project backend python scripts/retrieve_legal_chunks.py"
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BACKEND_ENV_PATH = Path("backend/.env")

DEFAULT_QUERY = "Can asylum applicants get work authorization?"
DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "nomic-embed-text"
DEFAULT_TOP_K = 3

EXPECTED_DIM = 768      # must match legal_chunks.embedding vector(768)
OLLAMA_TIMEOUT = 60     # seconds
SNIPPET_LEN = 500       # chars shown per chunk
QUERY_LOG_MAX = 180     # chars shown in log lines (never store full query)

_DIVIDER = "-" * 72


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Embed a synthetic test query locally with Ollama nomic-embed-text "
            "and run pgvector search against active public legal_chunks. "
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
        help=f"Number of top results to return. Default: {DEFAULT_TOP_K}",
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
    """Run pgvector cosine-distance search over active public legal_chunks.

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
        (query_vector_str, SNIPPET_LEN, query_vector_str, top_k),
    )
    rows = cur.fetchall()
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
        for r in rows
    ]


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
    active_dataset_name: str | None,
    active_chunk_count: int,
    psal_count: int,
    results: list[dict[str, Any]],
) -> None:
    print(_DIVIDER)
    print("vector retrieval — active public legal_chunks")
    print("(Read-only. Synthetic query only. No answer generation. No question stored.)")
    print(_DIVIDER)

    print(f"\n[Query]")
    print(f"  text (truncated)       : {_truncate_query(query)}")
    print(f"  embedding model        : {model}")
    print(f"  embedding dimension    : {query_dim}")
    print(f"  top_k                  : {top_k}")

    print(f"\n[Dataset state]")
    print(f"  active dataset         : {active_dataset_name or '(none)'}")
    print(f"  active embedded chunks : {active_chunk_count}")
    print(f"  privacy_safe_answer_logs count : {psal_count}")

    print(f"\n[Results — top {len(results)} of {top_k} requested]")
    if not results:
        print("  (no results returned)")
    else:
        for i, r in enumerate(results, start=1):
            print(f"\n  Rank {i}")
            print(f"    chunk_id   : {r['chunk_id']}")
            print(f"    citation   : {r['citation']}")
            print(f"    topic      : {r['topic']}")
            print(f"    subtopic   : {r['subtopic']}")
            print(f"    risk_level : {r['risk_level']}")
            print(f"    distance   : {r['distance']:.6f}" if r["distance"] is not None else "    distance   : n/a")
            print(f"    url        : {r['official_url']}")
            snippet = (r["snippet"] or "").strip().replace("\n", " ")
            print(f"    snippet    : {snippet[:SNIPPET_LEN]}")

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

                results = _run_vector_search(cur, query_vector_str, args.top_k)

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
        query=args.query,
        model=args.model,
        query_dim=query_dim,
        top_k=args.top_k,
        active_dataset_name=active_dataset_name,
        active_chunk_count=active_chunk_count,
        psal_count=psal_count,
        results=results,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
