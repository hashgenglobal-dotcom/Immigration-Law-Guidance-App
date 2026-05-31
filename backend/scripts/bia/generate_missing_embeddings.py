#!/usr/bin/env python3
"""
Generate missing embeddings for BIA Precedent Decisions legal_chunks.

Targets a single dataset version (default: bia-2026-05-21). Selects only
legal_chunks rows where embedding IS NULL for that version. Calls local
Ollama /api/embed, validates 768 dimensions, and writes to the DB in
commit-per-batch mode so any interrupted run can be safely resumed.

Safety guarantees:
  * Never touches dataset_versions.status
  * Never modifies legal_chunks.is_active
  * Filters strictly to the one named dataset version
  * Commits per batch — safe to interrupt and rerun
  * Never prints chunk text, database URLs, or credentials

Usage:
    # Inspect only — no Ollama calls, no DB writes
    uv run --project backend python backend/scripts/bia/generate_missing_embeddings.py --dry-run

    # Smoke test: embed first 3 chunks
    uv run --project backend python backend/scripts/bia/generate_missing_embeddings.py --limit 3

    # Full run (all 25 k chunks; takes ~35-60 min on local Ollama)
    uv run --project backend python backend/scripts/bia/generate_missing_embeddings.py

    # Explicit dataset version or Ollama URL
    uv run --project backend python backend/scripts/bia/generate_missing_embeddings.py \\
        --dataset-version-name bia-2026-05-21 \\
        --ollama-base-url http://localhost:11434

Exit codes:
    0 — completed (or dry-run OK)
    1 — config error, dataset not found, Ollama failure, or DB error
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

try:
    import psycopg
except ImportError:
    print(
        "ERROR: psycopg (v3) not found.\n"
        "Run with: uv run --project backend python backend/scripts/bia/generate_missing_embeddings.py",
        file=sys.stderr,
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_DATASET_VERSION = "bia-2026-05-21"
DEFAULT_BATCH_SIZE = 50
DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "nomic-embed-text"
EXPECTED_DIM = 768
BACKEND_ENV_PATH = Path("backend/.env")
_DIVIDER = "-" * 72


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate missing embeddings for BIA legal_chunks. "
            "Targets one dataset version only. Never activates the dataset."
        ),
    )
    parser.add_argument(
        "--dataset-version-name",
        default=DEFAULT_DATASET_VERSION,
        metavar="VERSION",
        help=f"dataset_versions.version_name to target. Default: {DEFAULT_DATASET_VERSION}",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print chunk count and previews only. No Ollama calls, no DB writes.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Embed at most N chunks this run. Remaining stay NULL (resumable).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        metavar="N",
        help=f"Chunks per commit batch. Default: {DEFAULT_BATCH_SIZE}",
    )
    parser.add_argument(
        "--ollama-base-url",
        default=None,
        help=(
            f"Ollama base URL. Overrides OLLAMA_BASE_URL env var. "
            f"Default: {DEFAULT_OLLAMA_URL}"
        ),
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Ollama embedding model. Default: {DEFAULT_MODEL}",
    )
    parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=0.0,
        metavar="S",
        help="Sleep between chunk embeddings (seconds). Throttles Ollama. Default: 0.0",
    )
    parser.add_argument(
        "--database-url",
        default=None,
        help="PostgreSQL connection URL. Overrides DATABASE_URL env var and backend/.env.",
    )
    return parser.parse_args(argv)


# ---------------------------------------------------------------------------
# Config resolution  (stdlib only — no dotenv dependency)
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
    """Strip SQLAlchemy driver prefix so psycopg3 accepts the URL."""
    for prefix in ("postgresql+psycopg://", "postgres+psycopg://"):
        if url.startswith(prefix):
            return prefix.split("+")[0] + "://" + url[len(prefix):]
    return url


def _resolve_ollama_url(arg_url: str | None) -> str:
    if arg_url:
        return arg_url
    env_val = os.environ.get("OLLAMA_BASE_URL")
    if env_val:
        return env_val
    dotenv = _read_env_file(BACKEND_ENV_PATH)
    return dotenv.get("OLLAMA_BASE_URL") or DEFAULT_OLLAMA_URL


# ---------------------------------------------------------------------------
# DB queries  (all read-only unless noted; never touch status or is_active)
# ---------------------------------------------------------------------------


def _fetch_dataset_version(cur: Any, version_name: str) -> tuple[int, str] | None:
    """Return (id, status) for the dataset version row, or None."""
    cur.execute(
        "SELECT id, status FROM dataset_versions WHERE version_name = %s",
        (version_name,),
    )
    row = cur.fetchone()
    return (row[0], row[1]) if row else None


def _count_null_embeddings(cur: Any, dataset_version_id: int) -> int:
    """Count legal_chunks where embedding IS NULL for the given dataset version."""
    cur.execute(
        """
        SELECT COUNT(*)
        FROM legal_chunks
        WHERE dataset_version_id = %s
          AND embedding IS NULL
        """,
        (dataset_version_id,),
    )
    return int(cur.fetchone()[0])


def _fetch_dry_run_preview(
    cur: Any,
    dataset_version_id: int,
    n: int = 5,
) -> list[tuple[int, str, str]]:
    """Return (chunk_id, citation, text_preview[:120]) for the first n NULL-embedding chunks."""
    cur.execute(
        """
        SELECT id, citation, LEFT(chunk_text, 120)
        FROM legal_chunks
        WHERE dataset_version_id = %s
          AND embedding IS NULL
        ORDER BY id
        LIMIT %s
        """,
        (dataset_version_id, n),
    )
    return [(r[0], r[1] or "", r[2] or "") for r in cur.fetchall()]


def _fetch_batch(
    cur: Any,
    dataset_version_id: int,
    last_id: int,
    n: int,
) -> list[tuple[int, str, str]]:
    """Cursor-paginated fetch: (chunk_id, citation, chunk_text) where id > last_id."""
    cur.execute(
        """
        SELECT id, citation, chunk_text
        FROM legal_chunks
        WHERE dataset_version_id = %s
          AND embedding IS NULL
          AND id > %s
        ORDER BY id
        LIMIT %s
        """,
        (dataset_version_id, last_id, n),
    )
    return [(r[0], r[1] or "", r[2] or "") for r in cur.fetchall()]


# ---------------------------------------------------------------------------
# Ollama embedding  — new /api/embed endpoint only
# ---------------------------------------------------------------------------


class _EmbeddingError(Exception):
    """Ollama call failed. Message is privacy-safe (no request text or body)."""


class _DimError(Exception):
    """Embedding returned wrong number of dimensions."""


def _embed(
    ollama_url: str,
    model: str,
    text: str,
    timeout_s: float = 60.0,
) -> list[float]:
    """POST to /api/embed and return embeddings[0].

    Uses the current Ollama API format:
        POST /api/embed  {"model": ..., "input": ...}
        response: {"embeddings": [[...768 floats...]]}

    Error messages never include input text, the URL, or HTTP response bodies.
    """
    payload = json.dumps({"model": model, "input": text}).encode("utf-8")
    req = urllib.request.Request(
        f"{ollama_url.rstrip('/')}/api/embed",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise _EmbeddingError(
            f"Ollama returned HTTP {exc.code} from /api/embed"
        ) from exc
    except urllib.error.URLError as exc:
        raise _EmbeddingError(
            f"Ollama not reachable ({exc.reason}). "
            "Is Ollama running? Try: ollama serve"
        ) from exc
    except json.JSONDecodeError:
        raise _EmbeddingError("Ollama returned non-JSON response")

    embeddings = data.get("embeddings")
    if not isinstance(embeddings, list) or not embeddings:
        raise _EmbeddingError("Ollama response missing 'embeddings' list")
    first = embeddings[0]
    if not isinstance(first, list):
        raise _EmbeddingError(
            f"Ollama 'embeddings[0]' expected list, got {type(first).__name__}"
        )
    return [float(v) for v in first]


def _validate_dim(embedding: list[float], chunk_id: int) -> None:
    got = len(embedding)
    if got != EXPECTED_DIM:
        raise _DimError(
            f"chunk {chunk_id}: got {got} dimensions, expected {EXPECTED_DIM}. "
            "Verify the correct Ollama model is loaded: ollama pull nomic-embed-text"
        )


def _fmt_vector(embedding: list[float]) -> str:
    """Format as pgvector literal: [x1,x2,...,x768]"""
    return "[" + ",".join(f"{v:.10g}" for v in embedding) + "]"


# ---------------------------------------------------------------------------
# Dry-run report
# ---------------------------------------------------------------------------


def _do_dry_run(
    conn: Any,
    dataset_version_id: int,
    version_name: str,
    version_status: str,
    limit: int | None,
    model: str,
    ollama_url: str,
) -> None:
    with conn.cursor() as cur:
        total_null = _count_null_embeddings(cur, dataset_version_id)
        preview = _fetch_dry_run_preview(cur, dataset_version_id)

    to_embed = total_null if limit is None else min(total_null, limit)

    print(_DIVIDER)
    print("DRY-RUN — BIA embedding inspection")
    print("No Ollama calls. No DB writes.")
    print(_DIVIDER)
    print(f"  dataset_version_name  : {version_name}")
    print(f"  dataset_version_id    : {dataset_version_id}")
    print(f"  dataset status        : {version_status}")
    print(f"  ollama_url            : {ollama_url}")
    print(f"  model                 : {model}")
    print(f"  expected_dim          : {EXPECTED_DIM}")
    print(f"  chunks with NULL emb  : {total_null}")
    print(f"  would embed this run  : {to_embed}")
    if limit is not None and limit < total_null:
        print(f"  skipped (--limit)     : {total_null - limit}")
    print()
    if preview:
        print(f"  First {len(preview)} chunk(s) that would be embedded:")
        for chunk_id, citation, text_preview in preview:
            safe = text_preview.replace("\n", " ")[:100]
            print(f"    [{chunk_id}] {citation!r}")
            print(f"           text[0:100]: {safe!r}")
    print()
    print("  dataset_versions.status : NOT changed by this script")
    print("  legal_chunks.is_active  : NOT changed by this script")
    print("  legal_chunks.embedding  : NOT changed (dry-run)")
    print(_DIVIDER)


# ---------------------------------------------------------------------------
# Embedding loop
# ---------------------------------------------------------------------------


def _do_embed(
    conn: Any,
    dataset_version_id: int,
    version_name: str,
    limit: int | None,
    batch_size: int,
    ollama_url: str,
    model: str,
    sleep_seconds: float,
) -> int:
    """Run the embedding loop. Returns exit code 0 (success) or 1 (failure)."""
    with conn.cursor() as cur:
        total_null = _count_null_embeddings(cur, dataset_version_id)

    target = total_null if limit is None else min(total_null, limit)

    if target == 0:
        print("No chunks need embedding for this dataset version. Nothing to do.")
        return 0

    print(_DIVIDER)
    print(f"BIA embedding run — {version_name}")
    print(
        f"  chunks to embed  : {target}"
        + (f"  (of {total_null} with NULL embedding)" if limit else "")
    )
    print(f"  batch_size       : {batch_size}")
    print(f"  model            : {model}")
    print(f"  sleep/chunk      : {sleep_seconds}s")
    print(_DIVIDER)

    processed = 0
    updated = 0
    last_id = 0

    while processed < target:
        fetch_n = min(batch_size, target - processed)

        with conn.cursor() as cur:
            batch = _fetch_batch(cur, dataset_version_id, last_id, fetch_n)

        if not batch:
            break

        batch_updates: list[tuple[str, int]] = []

        for chunk_id, citation, chunk_text in batch:
            text = chunk_text.strip()
            last_id = max(last_id, chunk_id)
            processed += 1

            if not text:
                print(f"  SKIP [{chunk_id}] — empty chunk_text")
                continue

            try:
                embedding = _embed(ollama_url, model, text)
                _validate_dim(embedding, chunk_id)
            except _DimError as exc:
                print(f"\nERROR (dimension mismatch): {exc}", file=sys.stderr)
                print("Aborting — current batch not written.", file=sys.stderr)
                return 1
            except _EmbeddingError as exc:
                print(f"\nERROR (Ollama): {exc}", file=sys.stderr)
                print("Aborting — current batch not written.", file=sys.stderr)
                return 1

            batch_updates.append((_fmt_vector(embedding), chunk_id))

            if sleep_seconds > 0:
                time.sleep(sleep_seconds)

        if not batch_updates:
            continue

        # Write batch atomically; roll back only this batch on failure.
        try:
            with conn.cursor() as cur:
                for vec_str, cid in batch_updates:
                    cur.execute(
                        "UPDATE legal_chunks SET embedding = %s::vector WHERE id = %s",
                        (vec_str, cid),
                    )
            conn.commit()
            updated += len(batch_updates)
        except psycopg.Error as exc:
            conn.rollback()
            print(
                f"\nERROR: DB commit failed ({type(exc).__name__}). Batch rolled back.",
                file=sys.stderr,
            )
            return 1

        print(
            f"  batch done — processed: {processed}/{target}  "
            f"updated: {updated}  last_id: {last_id}"
        )

    remaining = total_null - processed
    print()
    print(_DIVIDER)
    print(f"Complete — {version_name}")
    print(f"  updated    : {updated}")
    print(f"  skipped    : {processed - updated}  (empty chunk_text)")
    print(f"  remaining  : {remaining}  (embedding IS NULL; rerun to continue)")
    print()
    print("  dataset_versions.status : NOT changed")
    print("  legal_chunks.is_active  : NOT changed")
    print(_DIVIDER)
    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    raw_url = _resolve_database_url(args.database_url)
    if not raw_url:
        print(
            "ERROR: DATABASE_URL not found in environment or backend/.env",
            file=sys.stderr,
        )
        return 1
    db_url = _normalize_db_url(raw_url)
    ollama_url = _resolve_ollama_url(args.ollama_base_url)

    try:
        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:
                version_row = _fetch_dataset_version(cur, args.dataset_version_name)

            if version_row is None:
                print(
                    f"ERROR: dataset_versions row {args.dataset_version_name!r} not found.",
                    file=sys.stderr,
                )
                return 1

            dataset_version_id, version_status = version_row

            if args.dry_run:
                _do_dry_run(
                    conn=conn,
                    dataset_version_id=dataset_version_id,
                    version_name=args.dataset_version_name,
                    version_status=version_status,
                    limit=args.limit,
                    model=args.model,
                    ollama_url=ollama_url,
                )
                return 0

            return _do_embed(
                conn=conn,
                dataset_version_id=dataset_version_id,
                version_name=args.dataset_version_name,
                limit=args.limit,
                batch_size=args.batch_size,
                ollama_url=ollama_url,
                model=args.model,
                sleep_seconds=args.sleep_seconds,
            )

    except psycopg.OperationalError:
        print(
            "ERROR: PostgreSQL connection failed (psycopg.OperationalError).\n"
            "Check that DATABASE_URL is set and the host is reachable.",
            file=sys.stderr,
        )
        return 1
    except psycopg.Error as exc:
        print(
            f"ERROR: database error ({type(exc).__name__}): {exc}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
