#!/usr/bin/env python3
"""Ingest Official Updates from whitelisted government feeds.

Privacy
-------
- Fetches public RSS/API only; does not log full user questions.
- Summaries generated once at ingest via local Ollama (or fallback bullets).
- Does not insert into legal_chunks.

Usage
-----
    uv run --project backend python review/scripts/ingest_official_updates.py --dry-run
    uv run --project backend python review/scripts/ingest_official_updates.py --limit 5
    uv run --project backend python review/scripts/ingest_official_updates.py --skip-llm

Requires migration database/migrations/003-official-updates.sql applied.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import get_settings  # noqa: E402
from app.services.official_updates_feeds import (  # noqa: E402
    content_hash,
    fetch_all_whitelisted,
)
from app.services.official_updates_service import upsert_feed_item  # noqa: E402
from app.services.official_updates_summary import generate_summary_bullets  # noqa: E402
from app.services.official_updates_topics import tag_topics  # noqa: E402


def _load_database_url_hint() -> None:
    env_path = Path("backend/.env")
    if env_path.is_file():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("DATABASE_URL=") and not line.startswith("#"):
                os.environ.setdefault(
                    "DATABASE_URL",
                    line.split("=", 1)[1].strip().strip('"').strip("'"),
                )
                break


async def _run(*, dry_run: bool, limit: int | None, skip_llm: bool) -> int:
    _load_database_url_hint()
    settings = get_settings()
    items = await fetch_all_whitelisted()
    if limit is not None:
        items = items[: max(0, limit)]

    print(f"Fetched {len(items)} feed item(s) from whitelisted sources.")
    inserted = 0
    updated = 0
    skipped = 0

    for item in items:
        digest = content_hash(item.title, item.official_url, item.raw_excerpt)
        tags = tag_topics(item.title, item.raw_excerpt)

        if dry_run:
            print(f"  [dry-run] {item.publisher}: {item.title[:72]}… tags={tags}")
            continue

        if skip_llm:
            bullets, model = (
                [
                    f"{item.publisher.replace('_', ' ').title()} posted an official announcement.",
                    item.title[:200],
                    "Open the official release link for complete details.",
                ],
                None,
            )
        else:
            bullets, model = await generate_summary_bullets(
                settings=settings,
                title=item.title,
                publisher=item.publisher,
                raw_excerpt=item.raw_excerpt,
            )

        was_new = await upsert_feed_item(
            settings,
            publisher=item.publisher,
            external_id=item.external_id,
            title=item.title,
            official_url=item.official_url,
            published_at=item.published_at,
            raw_excerpt=item.raw_excerpt,
            summary_bullets=bullets,
            topic_tags=tags,
            content_hash=digest,
            summary_model=model,
        )
        if was_new:
            inserted += 1
        else:
            updated += 1

    if not dry_run:
        print(f"Done. inserted={inserted} updated={updated} skipped={skipped}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest Official Updates feeds")
    parser.add_argument("--dry-run", action="store_true", help="List items only; no DB writes")
    parser.add_argument("--limit", type=int, default=None, help="Max items to process")
    parser.add_argument(
        "--skip-llm",
        action="store_true",
        help="Use template bullets (no Ollama) for faster local testing",
    )
    args = parser.parse_args()
    if args.dry_run and args.limit is None:
        args.limit = 10
    raise SystemExit(asyncio.run(_run(dry_run=args.dry_run, limit=args.limit, skip_llm=args.skip_llm)))


if __name__ == "__main__":
    main()
