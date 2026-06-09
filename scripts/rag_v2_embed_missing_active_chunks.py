#!/usr/bin/env python3
"""RAG v2: resumably embed active legal_chunks missing 1024-dim embeddings."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

try:
    import psycopg
except ImportError:
    print("ERROR: psycopg is not available. Run with uv run --project backend python ...")
    sys.exit(1)


EXPECTED_DIM = 1024
DEFAULT_MODEL = "mxbai-embed-large"
DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
BACKEND_ENV_PATH = Path("backend/.env")


def normalize_db_url(url: str) -> str:
    if url.startswith("postgresql+psycopg://"):
        return url.replace("postgresql+psycopg://", "postgresql://", 1)
    return url


def read_database_url() -> str:
    value = os.environ.get("DATABASE_URL", "").strip()
    if value:
        return normalize_db_url(value)

    if BACKEND_ENV_PATH.exists():
        for line in BACKEND_ENV_PATH.read_text(errors="ignore").splitlines():
            s = line.strip()
            if not s or s.startswith("#") or "=" not in s:
                continue
            key, val = s.split("=", 1)
            if key.strip() == "DATABASE_URL":
                return normalize_db_url(val.strip().strip('"').strip("'"))

    raise SystemExit("ERROR: DATABASE_URL not found")


def format_vector(vector: list[float]) -> str:
    return "[" + ",".join(str(float(v)) for v in vector) + "]"


def clean_text(text: str) -> str:
    return " ".join((text or "").split())


def embed_candidate(text: str, *, model: str, ollama_url: str, timeout: int) -> list[float]:
    req = urllib.request.Request(
        f"{ollama_url.rstrip('/')}/api/embeddings",
        data=json.dumps({"model": model, "prompt": text}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    emb = data.get("embedding")
    if not isinstance(emb, list):
        raise RuntimeError("missing embedding")
    if len(emb) != EXPECTED_DIM:
        raise RuntimeError(f"expected {EXPECTED_DIM}, got {len(emb)}")
    return [float(v) for v in emb]


def embed_with_fallback(text: str, citation: str, *, model: str, ollama_url: str, timeout: int) -> list[float]:
    cleaned = clean_text(text)
    candidates = [
        cleaned,
        cleaned[:10000],
        cleaned[:8000],
        cleaned[:6000],
        cleaned[:4000],
        cleaned[:2500],
        cleaned[:1500],
        cleaned[:800],
        f"{citation}. {cleaned[:500]}",
        f"Legal source chunk: {citation}",
    ]

    last_error: Exception | None = None
    seen: set[str] = set()

    for candidate in candidates:
        candidate = candidate.strip()
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)

        try:
            return embed_candidate(candidate, model=model, ollama_url=ollama_url, timeout=timeout)
        except Exception as exc:
            last_error = exc
            time.sleep(0.5)

    raise RuntimeError(f"all embedding fallbacks failed: {last_error}")


def fetch_batch(db_url: str, batch_size: int) -> list[tuple[int, str, int, str]]:
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, citation, dataset_version_id, chunk_text
                FROM legal_chunks
                WHERE is_active = TRUE
                  AND embedding IS NULL
                ORDER BY dataset_version_id, id
                LIMIT %s
                """,
                (batch_size,),
            )
            return cur.fetchall()


def save_batch(db_url: str, updates: list[tuple[int, list[float]]]) -> None:
    for attempt in range(1, 6):
        try:
            with psycopg.connect(db_url) as conn:
                with conn.cursor() as cur:
                    for chunk_id, vector in updates:
                        cur.execute(
                            "UPDATE legal_chunks SET embedding=%s::vector WHERE id=%s",
                            (format_vector(vector), chunk_id),
                        )
                conn.commit()
            return
        except Exception as exc:
            print(f"DB save failed attempt={attempt}: {exc}", flush=True)
            time.sleep(5 * attempt)

    raise RuntimeError("DB save failed after retries")


def count_progress(db_url: str) -> tuple[int, int]:
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                  COUNT(*) FILTER (WHERE is_active = TRUE AND embedding IS NOT NULL) AS active_embedded,
                  COUNT(*) FILTER (WHERE is_active = TRUE AND embedding IS NULL) AS active_missing
                FROM legal_chunks
                """
            )
            return cur.fetchone()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Resumably embed active legal_chunks missing 1024-dim embeddings.")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--ollama-url", default=DEFAULT_OLLAMA_URL)
    parser.add_argument("--batch-size", type=int, default=25)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--sleep", type=float, default=0.10)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    db_url = read_database_url()

    print(f"Starting active missing embedding job model={args.model} batch_size={args.batch_size}", flush=True)

    no_progress_rounds = 0
    previous_missing: int | None = None

    while True:
        active_embedded, active_missing = count_progress(db_url)
        print(f"progress: active_embedded={active_embedded}, active_missing={active_missing}", flush=True)

        if active_missing == 0:
            print("done", flush=True)
            return

        if previous_missing == active_missing:
            no_progress_rounds += 1
        else:
            no_progress_rounds = 0
        previous_missing = active_missing

        if no_progress_rounds >= 10:
            raise SystemExit("No progress for 10 rounds; stopping to avoid infinite loop.")

        rows = fetch_batch(db_url, args.batch_size)
        updates: list[tuple[int, list[float]]] = []

        for chunk_id, citation, dataset_version_id, chunk_text in rows:
            try:
                vector = embed_with_fallback(
                    chunk_text or "",
                    citation or f"chunk {chunk_id}",
                    model=args.model,
                    ollama_url=args.ollama_url,
                    timeout=args.timeout,
                )
                updates.append((chunk_id, vector))
            except Exception as exc:
                print(f"FAILED chunk_id={chunk_id} dataset={dataset_version_id} citation={citation}: {exc}", flush=True)

            if args.sleep:
                time.sleep(args.sleep)

        if updates:
            save_batch(db_url, updates)


if __name__ == "__main__":
    main()
