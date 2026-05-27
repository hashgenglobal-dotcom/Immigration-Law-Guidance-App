#!/usr/bin/env python3
"""
Read-only Supabase DB audit (tables, pgvector, row counts, source coverage).

Loads DATABASE_URL from backend/.env (or env var), connects via psycopg3, and
prints a minimal, high-signal audit. No writes, no migrations, no updates.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Iterable


EXPECTED_CORE_TABLES = (
    "source_registry",
    "raw_documents",
    "legal_documents",
    "legal_sections",
    "legal_chunks",
    "scenario_guides",
    "dataset_versions",
    "ingestion_jobs",
    "privacy_safe_answer_logs",
    "admin_users",
)


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


def _resolve_database_url() -> str:
    env_val = os.environ.get("DATABASE_URL")
    if env_val:
        return env_val
    dotenv = _read_env_file(Path(__file__).resolve().parents[1] / ".env")
    url = dotenv.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL not set (env var or backend/.env).")
    return url


def _normalize_db_url(url: str) -> str:
    # Accept SQLAlchemy-style prefixes used elsewhere in repo.
    for prefix in ("postgresql+psycopg://", "postgres+psycopg://"):
        if url.startswith(prefix):
            scheme = prefix.split("+")[0]
            return scheme + "://" + url[len(prefix) :]
    return url


def _print_list(title: str, items: Iterable[str]) -> None:
    print(f"\n{title}")
    print("-" * len(title))
    for item in items:
        print(item)


def main() -> int:
    try:
        import psycopg  # type: ignore
    except Exception:
        print(
            "ERROR: psycopg (v3) is not installed in this Python environment.\n"
            "Try: cd backend && uv run python scripts/supabase_audit.py\n",
            file=sys.stderr,
        )
        return 2

    db_url = _normalize_db_url(_resolve_database_url())

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            # 1) Table inventory (public schema)
            cur.execute(
                """
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY tablename
                """
            )
            tables = [r[0] for r in cur.fetchall()]
            _print_list("1) Table Inventory (public schema)", (f"- {t}" for t in tables))

            missing = [t for t in EXPECTED_CORE_TABLES if t not in set(tables)]
            present = [t for t in EXPECTED_CORE_TABLES if t in set(tables)]
            print("\nExpected core tables (from 001-initial-schema.sql)")
            print("------------------------------------------------")
            print(f"- present: {len(present)}/{len(EXPECTED_CORE_TABLES)}")
            if missing:
                print(f"- missing: {', '.join(missing)}")
            else:
                print("- missing: (none)")

            # 2) pgvector extension check
            cur.execute(
                "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"
            )
            row = cur.fetchone()
            print("\n2) Vector Check (pgvector)")
            print("-------------------------")
            if row:
                print(f"- vector extension: installed (version={row[1]})")
            else:
                print("- vector extension: NOT FOUND")

            # 3) Total counts
            def _count(table: str) -> int:
                cur.execute(f"SELECT COUNT(*) FROM {table};")
                return int(cur.fetchone()[0])

            src_count = _count("source_registry") if "source_registry" in tables else -1
            doc_count = _count("legal_documents") if "legal_documents" in tables else -1
            chunk_count = _count("legal_chunks") if "legal_chunks" in tables else -1

            print("\n3) Total Data Counts")
            print("-------------------")
            print(f"- source_registry: {src_count}")
            print(f"- legal_documents: {doc_count}")
            print(f"- legal_chunks: {chunk_count}")

            # 4) Source verification (legal_chunks grouped by source_name)
            print("\n4) Source Verification (legal_chunks by source_name)")
            print("---------------------------------------------------")
            if all(t in set(tables) for t in ("legal_chunks", "legal_sections", "legal_documents", "raw_documents", "source_registry")):
                cur.execute(
                    """
                    SELECT
                      sr.source_name,
                      COUNT(lc.id) AS chunks,
                      COUNT(*) FILTER (WHERE lc.embedding IS NOT NULL) AS embedded
                    FROM legal_chunks lc
                    JOIN legal_sections ls ON ls.id = lc.section_id
                    JOIN legal_documents ld ON ld.id = ls.document_id
                    JOIN raw_documents rd ON rd.id = ld.raw_document_id
                    JOIN source_registry sr ON sr.id = rd.source_id
                    GROUP BY sr.source_name
                    ORDER BY chunks DESC, sr.source_name ASC;
                    """
                )
                rows = cur.fetchall()
                if not rows:
                    print("- (no rows)")
                else:
                    for name, chunks, embedded in rows:
                        print(f"- {name}: chunks={chunks} embedded={embedded}")
            else:
                print("- Required join tables missing; cannot compute.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

