#!/usr/bin/env python3
"""Generate local vector embeddings for public eCFR legal_chunks using Ollama.

Finds every legal_chunks row with embedding IS NULL for the target dataset
version, calls local Ollama nomic-embed-text to generate a 768-dimensional
vector for each chunk's chunk_text, verifies the dimension, and writes the
result to legal_chunks.embedding — all in one transaction.

Privacy / Safety
----------------
This script embeds ONLY public eCFR regulatory text that already exists in
legal_chunks. It does NOT:
  - process or embed user questions
  - read or write privacy_safe_answer_logs
  - write to admin_users
  - set is_active = TRUE on any chunk
  - change dataset_versions.status
  - call OpenAI, Anthropic, Cohere, or any public AI API

Ollama must be running locally (default http://localhost:11434). The script
never opens a network connection to any external AI service.

Usage
-----
    # Auto-detect dataset version; DB URL from backend/.env
    uv run --project backend python scripts/embed_legal_chunks.py

    # Explicit args
    uv run --project backend python scripts/embed_legal_chunks.py \\
        --database-url "postgresql://user@localhost:5432/immigration_law_dev" \\
        --dataset-version-name ecfr-title8-sample-2026-05-12 \\
        --ollama-url http://localhost:11434 \\
        --model nomic-embed-text

    # Embed only the first N chunks (rest stay NULL, run again later)
    uv run --project backend python scripts/embed_legal_chunks.py --limit 3

Exit codes
----------
* 0 — all targeted chunks embedded and committed successfully.
* 1 — connection error, dataset not found, Ollama unreachable, dimension
      mismatch, or database write failure. Transaction is rolled back on any
      error — no partial writes.
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
# Run with: uv run --project backend python scripts/embed_legal_chunks.py
try:
    import psycopg
except ImportError:
    print(
        "ERROR: psycopg (v3) is not installed in the current Python environment.\n"
        "       Run this script with:\n"
        "         uv run --project backend python scripts/embed_legal_chunks.py"
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BACKEND_ENV_PATH = Path("backend/.env")
DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "nomic-embed-text"
EXPECTED_DIM = 768  # must match legal_chunks.embedding vector(768)

_DIVIDER = "-" * 72


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------


class _EmbeddingError(Exception):
    """Raised when the Ollama HTTP call fails or returns an unexpected response."""


class _DimMismatchError(Exception):
    """Raised when the embedding returned by Ollama has the wrong dimension."""


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate local embeddings for public eCFR legal_chunks using Ollama. "
            "Writes only to legal_chunks.embedding. "
            "No public AI APIs. No user data. No chunk activation."
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
        "--dataset-version-name",
        default=None,
        metavar="ecfr-title8-sample-YYYY-MM-DD",
        help=(
            "dataset_versions.version_name to process. "
            "Default: newest ecfr-title8-sample-* row in the database."
        ),
    )
    parser.add_argument(
        "--ollama-url",
        default=DEFAULT_OLLAMA_URL,
        help=f"Base URL for the local Ollama server. Default: {DEFAULT_OLLAMA_URL}",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Ollama embedding model name. Default: {DEFAULT_MODEL}",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help=(
            "Embed at most N chunks in this run; the rest keep embedding=NULL "
            "and can be embedded in a subsequent run. Default: all NULL chunks."
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
# Database queries
# ---------------------------------------------------------------------------


def _resolve_dataset_version(
    cur: Any,
    version_name_arg: str | None,
) -> tuple[int, str, str] | None:
    """Return (id, version_name, status) for the target dataset version, or None."""
    if version_name_arg:
        cur.execute(
            "SELECT id, version_name, status FROM dataset_versions WHERE version_name = %s",
            (version_name_arg,),
        )
    else:
        cur.execute(
            """
            SELECT id, version_name, status
            FROM dataset_versions
            WHERE version_name LIKE 'ecfr-title8-sample-%'
            ORDER BY started_at DESC
            LIMIT 1
            """,
        )
    row = cur.fetchone()
    return (row[0], row[1], row[2]) if row else None


def _fetch_null_embedding_chunks(
    cur: Any,
    dataset_version_id: int,
) -> list[dict[str, Any]]:
    """Fetch legal_chunks where embedding IS NULL for the given dataset version.

    Only public eCFR regulatory text from legal_chunks is read here.
    No user questions and no private data are accessed.
    """
    cur.execute(
        """
        SELECT id, citation, topic, subtopic, risk_level, chunk_text
        FROM legal_chunks
        WHERE dataset_version_id = %s
          AND embedding IS NULL
        ORDER BY id
        """,
        (dataset_version_id,),
    )
    rows = cur.fetchall()
    return [
        {
            "id": r[0],
            "citation": r[1],
            "topic": r[2],
            "subtopic": r[3],
            "risk_level": r[4],
            "chunk_text": r[5] or "",
            "text_length": len(r[5] or ""),
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Ollama embedding (local only — no public AI APIs)
# ---------------------------------------------------------------------------


def _call_ollama_embed(ollama_url: str, model: str, text: str) -> list[float]:
    """POST chunk_text to local Ollama /api/embed; return embeddings[0].

    IMPORTANT:
    - Only public eCFR regulatory text is sent here.
    - No user questions and no private data are passed to Ollama.
    - Ollama must be running locally (e.g. http://localhost:11434).
    - No public AI APIs (OpenAI, Anthropic, Cohere, etc.) are used.
    """
    payload = json.dumps({"model": model, "input": text}).encode("utf-8")
    req = urllib.request.Request(
        f"{ollama_url.rstrip('/')}/api/embed",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise _EmbeddingError(
            f"Ollama not reachable at {ollama_url} "
            f"(URLError: {exc.reason}). "
            "Is Ollama running? Try: ollama serve"
        ) from exc
    except json.JSONDecodeError as exc:
        raise _EmbeddingError(f"Ollama returned invalid JSON: {exc}") from exc

    embeddings = data.get("embeddings")
    if not isinstance(embeddings, list) or not embeddings:
        raise _EmbeddingError(
            "Ollama response is missing 'embeddings' key or the list is empty. "
            f"Keys in response: {sorted(data.keys())}"
        )
    first = embeddings[0]
    if not isinstance(first, list):
        raise _EmbeddingError(
            f"Ollama 'embeddings[0]' is not a list (got {type(first).__name__})"
        )
    return first


def _verify_dimension(
    embedding: list[float],
    chunk_id: int,
    citation: str,
    expected: int,
) -> None:
    """Raise _DimMismatchError if the returned vector has the wrong dimension.

    Storing a malformed vector is worse than failing loudly — this check
    ensures the pgvector column always receives exactly vector(768) data.
    """
    got = len(embedding)
    if got != expected:
        raise _DimMismatchError(
            f"chunk {chunk_id} ({citation}): "
            f"expected {expected} dimensions, got {got}. "
            "Is the correct Ollama model loaded? "
            f"Try: ollama pull {DEFAULT_MODEL}"
        )


def _format_vector(embedding: list[float]) -> str:
    """Format a Python float list as a pgvector-compatible literal: '[x,y,z,...]'."""
    return "[" + ",".join(str(x) for x in embedding) + "]"


# ---------------------------------------------------------------------------
# Report printing
# ---------------------------------------------------------------------------


def _print_prerun(
    version_id: int,
    version_name: str,
    version_status: str,
    chunks: list[dict[str, Any]],
    all_null_count: int,
    model: str,
    ollama_url: str,
) -> None:
    print(_DIVIDER)
    print("embed_legal_chunks.py — local Ollama embedding for public eCFR chunks")
    print("(Public legal text only. No user questions. No public AI APIs.)")
    print(_DIVIDER)
    print(f"\n  dataset_version_id       : {version_id}")
    print(f"  dataset_version_name     : {version_name}")
    print(f"  dataset status           : {version_status}")
    print(f"  model                    : {model}")
    print(f"  ollama_url               : {ollama_url}")
    print(f"  expected dimension       : {EXPECTED_DIM}")
    print(f"  chunks with NULL emb     : {all_null_count}")
    print(f"  chunks to embed this run : {len(chunks)}")
    if all_null_count > len(chunks):
        print(
            f"  chunks skipped (--limit) : {all_null_count - len(chunks)} "
            "(embedding IS NULL — will be embedded in a future run)"
        )
    print()
    if chunks:
        print("  Chunk plan:")
        for chunk in chunks:
            print(
                f"    [{chunk['id']}] {chunk['citation']!r}"
                f"  topic={chunk['topic'] or '<null>'}"
                f"  text={chunk['text_length']} chars"
            )
    print()


def _print_summary(
    updated: list[dict[str, Any]],
    skipped_by_limit: int,
    version_name: str,
) -> None:
    print()
    print(_DIVIDER)
    print("Embedding run complete")
    print(_DIVIDER)
    print(f"\n  updated  : {len(updated)}")
    print(f"  skipped  : {skipped_by_limit}  (--limit applied; embedding still NULL)")
    print(f"  failed   : 0  (any failure rolls back all updates)")
    if updated:
        print(f"\n  Updated chunks:")
        for rec in updated:
            print(f"    [{rec['id']}] {rec['citation']!r}")
    print()
    print("  legal_chunks.is_active        : unchanged (FALSE on all rows)")
    print("  dataset_versions.status       : unchanged (not activated)")
    print("  privacy_safe_answer_logs      : not read or written")
    print()
    print("  Next: run validate_legal_chunk_embeddings.py to confirm.")
    print(_DIVIDER)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    # ---- resolve and normalize database URL ----
    raw_url = _resolve_database_url(args.database_url)
    if not raw_url:
        print("ERROR: no DATABASE_URL found.")
        print(
            "       Set DATABASE_URL in the environment, pass --database-url, "
            "or add DATABASE_URL to backend/.env."
        )
        return 1
    db_url = _normalize_db_url(raw_url)

    # Accumulators used after the try block for the summary report.
    updated_records: list[dict[str, Any]] = []
    skipped_by_limit = 0

    try:
        # One transaction: SELECT chunks → call Ollama per chunk → UPDATE each
        # → commit on clean exit, rollback on any exception.
        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:

                # Resolve target dataset version
                version_row = _resolve_dataset_version(cur, args.dataset_version_name)
                if version_row is None:
                    if args.dataset_version_name:
                        print(
                            f"ERROR: dataset_versions row "
                            f"{args.dataset_version_name!r} not found."
                        )
                    else:
                        print(
                            "ERROR: no dataset_versions row matching "
                            "'ecfr-title8-sample-*' found in the database."
                        )
                    print(
                        "       Run insert_ecfr_preview_to_db.py first, "
                        "or pass --dataset-version-name."
                    )
                    return 1

                version_id, version_name, version_status = version_row

                # Fetch all chunks with NULL embedding.
                # Only public eCFR regulatory text is read here — no user questions.
                all_null_chunks = _fetch_null_embedding_chunks(cur, version_id)

                # Apply --limit: remaining chunks stay NULL and are embedded later.
                chunks_to_embed = (
                    all_null_chunks[: args.limit]
                    if args.limit is not None
                    else all_null_chunks
                )
                skipped_by_limit = len(all_null_chunks) - len(chunks_to_embed)

                # Print pre-run report before any Ollama calls.
                _print_prerun(
                    version_id=version_id,
                    version_name=version_name,
                    version_status=version_status,
                    chunks=chunks_to_embed,
                    all_null_count=len(all_null_chunks),
                    model=args.model,
                    ollama_url=args.ollama_url,
                )

                if not chunks_to_embed:
                    print("No chunks need embedding for this dataset version. Exiting.")
                    return 0

                # --- embedding loop ---
                # For each chunk: call local Ollama, verify dimension, UPDATE.
                # All UPDATEs share this open transaction — any failure rolls back
                # everything so no partial embeddings are left in the database.
                for chunk in chunks_to_embed:
                    chunk_id: int = chunk["id"]
                    citation: str = chunk["citation"]
                    chunk_text: str = chunk["chunk_text"]

                    print(
                        f"  embedding chunk {chunk_id} ({citation}) ...",
                        end=" ",
                        flush=True,
                    )

                    # Call local Ollama — only public eCFR text, never user questions.
                    # Raises _EmbeddingError on HTTP failure or unexpected response.
                    embedding = _call_ollama_embed(args.ollama_url, args.model, chunk_text)

                    # Reject wrong-dimension vectors before writing — a malformed
                    # vector in pgvector is harder to recover from than a failed run.
                    _verify_dimension(embedding, chunk_id, citation, EXPECTED_DIM)

                    # Write only legal_chunks.embedding.
                    # is_active, dataset_version_id, and all other columns are untouched.
                    vector_str = _format_vector(embedding)
                    cur.execute(
                        "UPDATE legal_chunks SET embedding = %s::vector WHERE id = %s",
                        (vector_str, chunk_id),
                    )

                    updated_records.append({"id": chunk_id, "citation": citation})
                    print(f"OK ({len(embedding)} dims)")

                # Transaction commits here on clean exit of the with block.

    except psycopg.OperationalError:
        # OperationalError messages may contain the DSN — print class name only.
        print("\nERROR: could not connect to PostgreSQL (psycopg.OperationalError).")
        print(
            "       Check that PostgreSQL is running and DATABASE_URL is correct."
        )
        return 1

    except _EmbeddingError as exc:
        print(f"\nERROR (Ollama): {exc}")
        print("Transaction rolled back. No embeddings were stored.")
        return 1

    except _DimMismatchError as exc:
        print(f"\nERROR (dimension mismatch): {exc}")
        print("Transaction rolled back. No embeddings were stored.")
        return 1

    except psycopg.Error as exc:
        print(f"\nERROR: database update failed ({type(exc).__name__}): {exc}")
        print("Transaction rolled back. No embeddings were stored.")
        return 1

    _print_summary(
        updated=updated_records,
        skipped_by_limit=skipped_by_limit,
        version_name=version_name,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
