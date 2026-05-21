#!/usr/bin/env python3
"""Fast ingest for fetched USCIS HTML (one chunk per page, single transaction).

Use when ingest_uscis_official_pages.py is too slow for local triggers.
Requires pages-manifest-slim.json + raw HTML from fetch_uscis_official_pages.py.

Usage:
    uv run --project backend python review/scripts/ingest_uscis_official_pages_fast.py --yes
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from html import unescape
from pathlib import Path

import psycopg

MANIFEST = Path("data/uscis-official-pages/preview/pages-manifest-slim.json")
RAW_DIR = Path("data/uscis-official-pages/raw")
DATASET = "uscis-official-pages-2026-05-20"
SOURCE_NAME = "USCIS Official Pages"
MAX_TEXT = 8000


def _db_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url and Path("backend/.env").exists():
        for line in Path("backend/.env").read_text().splitlines():
            if line.strip().startswith("DATABASE_URL="):
                url = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not url:
        sys.exit("DATABASE_URL required")
    return re.sub(r"^postgresql\+[a-zA-Z0-9_]+://", "postgresql://", url)


def _strip_html(html: str) -> str:
    html = re.sub(r"(?is)<(script|style|nav|footer|header)[^>]*>.*?</\1>", " ", html)
    text = re.sub(r"<[^>]+>", " ", html)
    text = unescape(re.sub(r"\s+", " ", text)).strip()
    return text[:MAX_TEXT]


def _citation(url: str) -> str:
    m = re.search(r"/(i-\d+[a-z]?|n-\d+)", url, re.I)
    return f"USCIS Form {m.group(1).upper()}" if m else "USCIS Official Page"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--yes", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not args.yes and not args.dry_run:
        print("Use --yes or --dry-run")
        return 1
    if not MANIFEST.exists():
        print(f"Missing {MANIFEST}")
        return 1

    pages = [p for p in json.loads(MANIFEST.read_text())["pages"] if p.get("success")]
    print(f"Pages: {len(pages)}")

    with psycopg.connect(_db_url()) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO source_registry (source_name, source_type, publisher, base_url, access_method)
                VALUES (%s, 'form', 'USCIS', 'https://www.uscis.gov', 'html_fetch')
                ON CONFLICT (source_name) DO UPDATE SET updated_at = NOW()
                RETURNING id
                """,
                (SOURCE_NAME,),
            )
            source_id = cur.fetchone()[0]

            cur.execute(
                "SELECT id FROM dataset_versions WHERE version_name = %s",
                (DATASET,),
            )
            row = cur.fetchone()
            if row:
                dataset_id = row[0]
            else:
                cur.execute(
                    """
                    INSERT INTO dataset_versions (version_name, status, notes, created_by)
                    VALUES (%s, 'ready', 'USCIS official pages (fast ingest)', 'fast_ingest')
                    RETURNING id
                    """,
                    (DATASET,),
                )
                dataset_id = cur.fetchone()[0]

            inserted = 0
            for page in pages:
                html_path = RAW_DIR / page["html_filename"]
                if not html_path.is_file():
                    continue
                text = _strip_html(html_path.read_text(encoding="utf-8", errors="replace"))
                if len(text) < 200:
                    continue
                url = page["url"]
                cite = _citation(url)
                slug = page.get("slug", "page")
                chash = hashlib.sha256(text.encode()).hexdigest()

                cur.execute(
                    """
                    INSERT INTO raw_documents (
                        source_id, external_id, title, citation, official_url,
                        raw_format, raw_content, content_hash
                    ) VALUES (%s, %s, %s, %s, %s, 'html', %s, %s)
                    RETURNING id
                    """,
                    (source_id, slug, page.get("title") or cite, cite, url, text[:3000], chash),
                )
                raw_id = cur.fetchone()[0]
                cur.execute(
                    """
                    INSERT INTO legal_documents (
                        raw_document_id, source_type, title, citation, publisher, official_url
                    ) VALUES (%s, 'uscis_page', %s, %s, 'USCIS', %s)
                    RETURNING id
                    """,
                    (raw_id, page.get("title") or cite, cite, url),
                )
                doc_id = cur.fetchone()[0]
                cur.execute(
                    """
                    INSERT INTO legal_sections (
                        document_id, section_number, section_title, citation,
                        official_text, topic, subtopic, official_url
                    ) VALUES (%s, '1', %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        doc_id,
                        page.get("title") or cite,
                        cite,
                        text[:3000],
                        page.get("category_title", "USCIS"),
                        page.get("kind", "guidance"),
                        url,
                    ),
                )
                sec_id = cur.fetchone()[0]
                cur.execute(
                    """
                    INSERT INTO legal_chunks (
                        section_id, dataset_version_id, chunk_index, chunk_text,
                        citation, topic, subtopic, official_url, is_active
                    ) VALUES (%s, %s, 0, %s, %s, %s, %s, %s, FALSE)
                    """,
                    (
                        sec_id,
                        dataset_id,
                        text,
                        cite,
                        page.get("category_title", "USCIS"),
                        page.get("kind", "guidance"),
                        url,
                    ),
                )
                inserted += 1
                print(f"  ok {cite}", flush=True)

        if args.yes:
            conn.commit()
            print(f"Committed {inserted} pages ({inserted} chunks)")
        else:
            conn.rollback()
            print(f"DRY-RUN: would insert {inserted} pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
