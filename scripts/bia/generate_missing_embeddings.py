#!/usr/bin/env python3
"""
Generate missing embeddings for BIA Precedent Decisions chunks.

What this script does (read + update only legal_chunks.embedding):
1) Resolves DATABASE_URL from env var or backend/.env
2) Finds legal_chunks rows for source_name='BIA Precedent Decisions'
   where embedding IS NULL
3) Calls local Ollama embeddings endpoint in retry-safe mode
4) Updates embeddings in batches
5) Reports progress via tqdm

Usage:
    python3 scripts/bia/generate_missing_embeddings.py
    python3 scripts/bia/generate_missing_embeddings.py --batch-size 100 --max-retries 5
    python3 scripts/bia/generate_missing_embeddings.py --limit 500

Notes:
- Requires local Ollama running at http://localhost:11434
- Uses model nomic-embed-text by default
- Expects 768-dim vectors to match legal_chunks.embedding vector(768)
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Iterable

import httpx
import psycopg

try:
    from tqdm import tqdm
except Exception as exc:  # pragma: no cover - explicit startup failure
    print(
        "ERROR: tqdm is required for progress reporting.\n"
        "Install it in your environment, e.g.:\n"
        "  cd backend && uv pip install tqdm\n",
        file=sys.stderr,
    )
    raise SystemExit(2) from exc


TARGET_SOURCE_NAME = "BIA Precedent Decisions"
EXPECTED_DIM = 768
DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "nomic-embed-text"


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


def resolve_database_url() -> str:
    if os.environ.get("DATABASE_URL"):
        return os.environ["DATABASE_URL"]

    env_path = Path(__file__).resolve().parents[2] / "backend" / ".env"
    dotenv = _read_env_file(env_path)
    db_url = dotenv.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL not found in env or backend/.env")
    return db_url


def normalize_db_url(url: str) -> str:
    for prefix in ("postgresql+psycopg://", "postgres+psycopg://"):
        if url.startswith(prefix):
            scheme = prefix.split("+")[0]
            return scheme + "://" + url[len(prefix) :]
    return url


def vector_literal(values: Iterable[float]) -> str:
    # pgvector input literal: [0.1,0.2,...]
    return "[" + ",".join(f"{float(v):.10g}" for v in values) + "]"


def embed_with_retry(
    client: httpx.Client,
    *,
    ollama_url: str,
    model: str,
    text: str,
    max_retries: int,
    retry_backoff_s: float,
) -> list[float]:
    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = client.post(
                f"{ollama_url.rstrip('/')}/api/embeddings",
                json={"model": model, "prompt": text},
            )
            resp.raise_for_status()
            data = resp.json()
            emb = data.get("embedding")
            if not isinstance(emb, list):
                raise ValueError("Ollama response missing embedding list")
            if len(emb) != EXPECTED_DIM:
                raise ValueError(
                    f"Unexpected embedding dimension: got {len(emb)} expected {EXPECTED_DIM}"
                )
            return [float(x) for x in emb]
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt < max_retries:
                sleep_s = retry_backoff_s * (2 ** (attempt - 1))
                time.sleep(sleep_s)
            else:
                break
    assert last_error is not None
    raise last_error


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate missing BIA embeddings and update legal_chunks."
    )
    parser.add_argument("--batch-size", type=int, default=100, help="Rows per DB batch")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional cap on number of chunks to process",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Ollama embedding model")
    parser.add_argument("--ollama-url", default=DEFAULT_OLLAMA_URL, help="Ollama base URL")
    parser.add_argument("--timeout-s", type=float, default=60.0, help="HTTP timeout seconds")
    parser.add_argument("--max-retries", type=int, default=4, help="Retries per chunk")
    parser.add_argument(
        "--retry-backoff-s",
        type=float,
        default=1.5,
        help="Base retry backoff (exponential)",
    )
    args = parser.parse_args()

    if args.batch_size <= 0:
        raise SystemExit("--batch-size must be > 0")
    if args.max_retries <= 0:
        raise SystemExit("--max-retries must be > 0")

    db_url = normalize_db_url(resolve_database_url())

    count_sql = """
        SELECT COUNT(*)
        FROM legal_chunks lc
        JOIN legal_sections ls ON ls.id = lc.section_id
        JOIN legal_documents ld ON ld.id = ls.document_id
        JOIN raw_documents rd ON rd.id = ld.raw_document_id
        JOIN source_registry sr ON sr.id = rd.source_id
        WHERE sr.source_name = %s
          AND lc.embedding IS NULL
    """

    select_sql = """
        SELECT lc.id, lc.chunk_text
        FROM legal_chunks lc
        JOIN legal_sections ls ON ls.id = lc.section_id
        JOIN legal_documents ld ON ld.id = ls.document_id
        JOIN raw_documents rd ON rd.id = ld.raw_document_id
        JOIN source_registry sr ON sr.id = rd.source_id
        WHERE sr.source_name = %s
          AND lc.embedding IS NULL
          AND lc.id > %s
        ORDER BY lc.id
        LIMIT %s
    """

    update_sql = "UPDATE legal_chunks SET embedding = %s::vector WHERE id = %s"

    total_target = 0
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(count_sql, (TARGET_SOURCE_NAME,))
            total_target = int(cur.fetchone()[0])

    if args.limit is not None:
        total_target = min(total_target, max(args.limit, 0))

    if total_target == 0:
        print("No missing BIA embeddings found. Nothing to do.")
        return 0

    print(
        f"Found {total_target} BIA chunks with embedding IS NULL. "
        f"batch_size={args.batch_size}, model={args.model}"
    )

    processed = 0
    updated = 0
    failed = 0
    last_id = 0

    with httpx.Client(timeout=args.timeout_s) as http_client, psycopg.connect(db_url) as conn:
        pbar = tqdm(total=total_target, desc="Embedding BIA chunks", unit="chunk")
        while processed < total_target:
            fetch_n = min(args.batch_size, total_target - processed)

            with conn.cursor() as cur:
                cur.execute(select_sql, (TARGET_SOURCE_NAME, last_id, fetch_n))
                rows: list[tuple[int, str]] = cur.fetchall()

            if not rows:
                break

            updates: list[tuple[str, int]] = []
            for chunk_id, chunk_text in rows:
                last_id = max(last_id, chunk_id)
                text = (chunk_text or "").strip()
                if not text:
                    failed += 1
                    processed += 1
                    pbar.update(1)
                    continue
                try:
                    emb = embed_with_retry(
                        http_client,
                        ollama_url=args.ollama_url,
                        model=args.model,
                        text=text,
                        max_retries=args.max_retries,
                        retry_backoff_s=args.retry_backoff_s,
                    )
                    updates.append((vector_literal(emb), chunk_id))
                except Exception:
                    failed += 1
                finally:
                    processed += 1
                    pbar.update(1)

            if updates:
                with conn.cursor() as cur:
                    cur.executemany(update_sql, updates)
                conn.commit()
                updated += len(updates)

            pbar.set_postfix(updated=updated, failed=failed)

        pbar.close()

    print("\nDone.")
    print(f"- target:   {total_target}")
    print(f"- updated:  {updated}")
    print(f"- failed:   {failed}")
    print(f"- processed:{processed}")

    # Non-zero exit if there were failures, so operators can decide reruns.
    return 1 if failed > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())

