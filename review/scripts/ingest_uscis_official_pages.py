#!/usr/bin/env python3
"""Ingest fetched USCIS/DHS official pages into legal_chunks (metadata + official_url).

Requires: review/scripts/fetch_uscis_official_pages.py --yes first.

Privacy: ingests only public government pages. No user data.

Usage:
    uv run --project backend python review/scripts/ingest_uscis_official_pages.py --dry-run
    uv run --project backend python review/scripts/ingest_uscis_official_pages.py --yes
    uv run --project backend python scripts/embed_legal_chunks.py \\
        --dataset-version-name uscis-official-pages-2026-05-20 --yes
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import psycopg
    from bs4 import BeautifulSoup
except ImportError:
    print("Run with: uv run --project backend python review/scripts/ingest_uscis_official_pages.py")
    sys.exit(1)

PREVIEW_FILE = Path("data/uscis-official-pages/preview/pages-manifest-slim.json")
FALLBACK_PREVIEW = Path("data/uscis-official-pages/preview/pages-preview.json")
RAW_DIR = Path("data/uscis-official-pages/raw")
SOURCE_NAME = "USCIS Official Pages"
CHUNK_MAX = 1200
CHUNK_OVERLAP = 150
MAX_PAGE_TEXT = 12000
MAX_CHUNKS_PER_PAGE = 4


def _db_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        env = Path("backend/.env")
        if env.exists():
            for line in env.read_text().splitlines():
                s = line.strip()
                if s.startswith("DATABASE_URL="):
                    url = s.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not url:
        sys.exit("DATABASE_URL required")
    return re.sub(r"^postgresql\+[a-zA-Z0-9_]+://", "postgresql://", url)


def _extract_text_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    main = soup.find("main") or soup.find("article") or soup.body or soup
    text = main.get_text(separator="\n", strip=True)
    return re.sub(r"\n{3,}", "\n\n", text)


def _chunk_text(text: str) -> list[str]:
    if len(text) <= CHUNK_MAX:
        return [text] if text.strip() else []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + CHUNK_MAX, len(text))
        if end < len(text):
            region = text[start:end]
            period = region.rfind(". ")
            if period > CHUNK_MAX - 300:
                end = start + period + 1
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        start = end - CHUNK_OVERLAP
        if start >= len(text):
            break
    return chunks


def _form_citation(page: dict[str, Any]) -> str:
    url = page["url"]
    m = re.search(r"/(i-\d+[a-z]?|n-\d+)", url, re.I)
    if m:
        return f"USCIS Form {m.group(1).upper()}"
    if "studyinthestates" in url:
        return "DHS Study in the States"
    return page.get("title") or page.get("slug", "USCIS guidance")


def register_source(conn: psycopg.Connection[Any]) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO source_registry (source_name, source_type, publisher, base_url, access_method)
            VALUES (%s, 'form', 'U.S. Citizenship and Immigration Services', %s, 'html_fetch')
            ON CONFLICT (source_name) DO UPDATE SET
                base_url = EXCLUDED.base_url,
                access_method = EXCLUDED.access_method,
                updated_at = NOW()
            RETURNING id
            """,
            (SOURCE_NAME, "https://www.uscis.gov"),
        )
        sid = cur.fetchone()[0]
    conn.commit()
    return sid


def create_dataset(conn: psycopg.Connection[Any], chunk_count: int) -> tuple[int, str]:
    version_name = f"uscis-official-pages-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM dataset_versions WHERE version_name = %s",
            (version_name,),
        )
        row = cur.fetchone()
        if row:
            did = row[0]
            cur.execute(
                """
                UPDATE dataset_versions
                SET notes = %s
                WHERE id = %s
                """,
                (f"USCIS/DHS official pages: {chunk_count} chunks pending embed", did),
            )
        else:
            cur.execute(
                """
                INSERT INTO dataset_versions (version_name, status, notes, created_by)
                VALUES (%s, 'ready', %s, 'ingest_uscis_official_pages')
                RETURNING id
                """,
                (version_name, f"USCIS/DHS official pages: {chunk_count} chunks pending embed"),
            )
            did = cur.fetchone()[0]
    conn.commit()
    return did, version_name


def _load_manifest() -> list[dict[str, Any]]:
    """Load manifest; prefer slim file (no inline page text)."""
    path = PREVIEW_FILE if PREVIEW_FILE.exists() else FALLBACK_PREVIEW
    data = json.loads(path.read_text(encoding="utf-8"))
    pages: list[dict[str, Any]] = []
    for page in data.get("pages", []):
        pages.append({k: v for k, v in page.items() if k != "text"})
    return pages


def ingest_pages(
    conn: psycopg.Connection[Any],
    source_id: int,
    dataset_id: int,
    pages: list[dict[str, Any]],
    *,
    commit: bool,
) -> dict[str, int]:
    stats = {"documents": 0, "sections": 0, "chunks": 0, "skipped": 0}
    with conn.cursor() as cur:
        for page in pages:
            if not page.get("success"):
                stats["skipped"] += 1
                continue
            html_path = RAW_DIR / page.get("html_filename", "")
            if not html_path.is_file():
                stats["skipped"] += 1
                continue
            text = _extract_text_from_html(html_path.read_text(encoding="utf-8", errors="replace"))
            text = text[:MAX_PAGE_TEXT]
            if len(text) < 200:
                stats["skipped"] += 1
                continue
            url = page["url"]
            citation = _form_citation(page)
            topic = page.get("category_title", "USCIS Guidance")
            subtopic = page.get("kind", "guidance")
            external_id = page.get("slug", "page")

            cur.execute(
                """
                INSERT INTO raw_documents (
                    source_id, external_id, title, citation, official_url,
                    raw_format, raw_content, content_hash
                ) VALUES (%s, %s, %s, %s, %s, 'html', %s, %s)
                RETURNING id
                """,
                (
                    source_id,
                    external_id,
                    page.get("title") or citation,
                    citation,
                    url,
                    text[:8000],
                    page.get("content_hash") or "hash-pending",
                ),
            )
            raw_id = cur.fetchone()[0]

            cur.execute(
                """
                INSERT INTO legal_documents (
                    raw_document_id, source_type, title, citation, publisher, official_url
                ) VALUES (%s, 'uscis_page', %s, %s, 'USCIS', %s)
                RETURNING id
                """,
                (raw_id, page.get("title") or citation, citation, url),
            )
            doc_id = cur.fetchone()[0]
            stats["documents"] += 1

            cur.execute(
                """
                INSERT INTO legal_sections (
                    document_id, section_number, section_title, citation,
                    official_text, topic, subtopic, official_url
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (doc_id, "1", page.get("title") or citation, citation, text, topic, subtopic, url),
            )
            section_id = cur.fetchone()[0]
            stats["sections"] += 1

            print(f"  ingest: {citation} ({len(text)} chars)", flush=True)
            for idx, chunk in enumerate(_chunk_text(text)[:MAX_CHUNKS_PER_PAGE]):
                cur.execute(
                    """
                    INSERT INTO legal_chunks (
                        section_id, dataset_version_id, chunk_index, chunk_text,
                        citation, topic, subtopic, official_url, is_active
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, FALSE)
                    """,
                    (section_id, dataset_id, idx, chunk, citation, topic, subtopic, url),
                )
                stats["chunks"] += 1

            if commit:
                conn.commit()

    if not commit:
        conn.rollback()
    return stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--yes", action="store_true")
    parser.add_argument("--limit", type=int, default=None, help="Max pages to ingest")
    args = parser.parse_args(argv)
    if not args.dry_run and not args.yes:
        print("Use --dry-run or --yes")
        return 1
    if not PREVIEW_FILE.exists() and not FALLBACK_PREVIEW.exists():
        print("Missing manifest. Run fetch_uscis_official_pages.py --yes first.")
        return 1

    pages = _load_manifest()
    ok_pages = [p for p in pages if p.get("success")]
    if args.limit is not None:
        ok_pages = ok_pages[: args.limit]
    print(f"Manifest: {len(ok_pages)}/{len(pages)} successful pages to process")

    with psycopg.connect(_db_url()) as conn:
        source_id = register_source(conn)
        dataset_id, version_name = create_dataset(conn, len(ok_pages) * 3)
        stats = ingest_pages(conn, source_id, dataset_id, ok_pages, commit=args.yes)
        print(f"Dataset: {version_name} (id={dataset_id})")
        print(f"Stats: {stats}")
        if args.dry_run:
            print("DRY-RUN: rolled back")
        else:
            print(
                "Next: embed and activate:\n"
                f"  uv run --project backend python scripts/embed_legal_chunks.py "
                f"--dataset-version-name {version_name}\n"
                "  uv run --project backend python review/scripts/activate_uscis_official_pages.py --yes"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
