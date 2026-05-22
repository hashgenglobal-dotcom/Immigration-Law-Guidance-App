#!/usr/bin/env python3
"""Seed demo Official Updates rows for mobile/API testing without network."""

from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import get_settings  # noqa: E402
from app.services.official_updates_feeds import content_hash  # noqa: E402
from app.services.official_updates_service import upsert_feed_item  # noqa: E402


DEMO_ITEMS = [
    {
        "publisher": "uscis",
        "external_id": "demo-uscis-opt-2026",
        "title": "USCIS reminder: F-1 students must maintain status when applying for OPT",
        "official_url": "https://www.uscis.gov/",
        "raw_excerpt": "Optional Practical Training (OPT) for F-1 students requires maintaining lawful status and timely filing.",
        "summary_bullets": [
            "USCIS reminded F-1 students about rules for Optional Practical Training (OPT).",
            "Students must keep lawful F-1 status when they apply for OPT.",
            "See the official USCIS release for filing steps and deadlines.",
        ],
        "topic_tags": ["f1_j1", "ead_work"],
    },
    {
        "publisher": "dhs",
        "external_id": "demo-dhs-humanitarian-2026",
        "title": "DHS announces humanitarian parole process update for designated countries",
        "official_url": "https://www.dhs.gov/",
        "raw_excerpt": "Temporary humanitarian parole may be available for nationals of certain countries under announced processes.",
        "summary_bullets": [
            "DHS posted an update about humanitarian parole for some country nationals.",
            "Eligibility and steps depend on the official DHS notice.",
            "Check the official DHS page for country lists and how to apply.",
        ],
        "topic_tags": ["tps", "general"],
    },
    {
        "publisher": "federal_register",
        "external_id": "demo-fr-fee-2026",
        "title": "Federal Register: USCIS filing fee adjustment for selected forms",
        "official_url": "https://www.federalregister.gov/",
        "raw_excerpt": "A rule may change filing fees for certain USCIS forms; effective dates appear in the notice.",
        "summary_bullets": [
            "A Federal Register notice discusses USCIS filing fee changes.",
            "Fees may apply only to certain form types listed in the notice.",
            "Read the official Federal Register document for amounts and effective dates.",
        ],
        "topic_tags": ["fees_forms", "general"],
    },
]


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


async def _run() -> int:
    _load_database_url_hint()
    settings = get_settings()
    now = datetime.now(timezone.utc)
    for row in DEMO_ITEMS:
        digest = content_hash(row["title"], row["official_url"], row["raw_excerpt"])
        await upsert_feed_item(
            settings,
            publisher=row["publisher"],
            external_id=row["external_id"],
            title=row["title"],
            official_url=row["official_url"],
            published_at=now,
            raw_excerpt=row["raw_excerpt"],
            summary_bullets=row["summary_bullets"],
            topic_tags=row["topic_tags"],
            content_hash=digest,
            summary_model="demo-seed",
        )
        print(f"Seeded: {row['publisher']} — {row['title'][:60]}…")
    print(f"Seeded {len(DEMO_ITEMS)} demo update(s).")
    return 0


def main() -> None:
    raise SystemExit(asyncio.run(_run()))


if __name__ == "__main__":
    main()
