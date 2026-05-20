#!/usr/bin/env python3
"""Fetch curated USCIS / DHS official pages for common immigration categories.

Reads URL list from data/common-immigration-coverage/source-inventory.json
(entries with ingest=true). Saves raw HTML and a preview JSON manifest.
Does not write to PostgreSQL.

Usage:
    uv run --project backend python review/scripts/fetch_uscis_official_pages.py --inspect
    uv run --project backend python review/scripts/fetch_uscis_official_pages.py --yes
    uv run --project backend python review/scripts/fetch_uscis_official_pages.py --yes --limit 3
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from bs4 import BeautifulSoup

INVENTORY = Path("data/common-immigration-coverage/source-inventory.json")
RAW_DIR = Path("data/uscis-official-pages/raw")
PREVIEW_FILE = Path("data/uscis-official-pages/preview/pages-preview.json")

USER_AGENT = (
    "Immigration-Law-Guidance-App/1.0 "
    "(educational; official USCIS/DHS page ingestion; contact: hash@hashgen.global)"
)
HTTP_TIMEOUT = 60.0
RATE_LIMIT_SEC = 1.0


def _load_urls(limit: int | None) -> list[dict[str, Any]]:
    data = json.loads(INVENTORY.read_text(encoding="utf-8"))
    seen: set[str] = set()
    pages: list[dict[str, Any]] = []
    for cat in data.get("categories", []):
        for entry in cat.get("official_urls", []):
            if not entry.get("ingest"):
                continue
            url = entry["url"]
            if url in seen:
                continue
            seen.add(url)
            pages.append(
                {
                    "url": url,
                    "kind": entry.get("kind", "uscis_guidance"),
                    "category_id": cat["id"],
                    "category_title": cat["title"],
                }
            )
    if limit is not None:
        pages = pages[:limit]
    return pages


def _slug_from_url(url: str) -> str:
    slug = re.sub(r"^https?://", "", url).strip("/")
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "_", slug)
    return slug[:120] or "page"


def _extract_text(html: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    main = soup.find("main") or soup.find("article") or soup.find("div", class_="content")
    root = main if main else soup.body or soup
    title = (soup.title.string or "").strip() if soup.title else ""
    text = root.get_text(separator="\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return title, text


async def _fetch_one(
    client: httpx.AsyncClient,
    page: dict[str, Any],
    semaphore: asyncio.Semaphore,
) -> dict[str, Any]:
    url = page["url"]
    slug = _slug_from_url(url)
    out: dict[str, Any] = {
        **page,
        "slug": slug,
        "success": False,
        "title": None,
        "text_length": 0,
        "html_filename": f"{slug}.html",
        "fetched_at": None,
        "error": None,
    }
    async with semaphore:
        await asyncio.sleep(RATE_LIMIT_SEC)
        try:
            resp = await client.get(url, follow_redirects=True)
            resp.raise_for_status()
            html = resp.text
            title, text = _extract_text(html)
            out["success"] = len(text) >= 200
            out["title"] = title or slug
            out["text_length"] = len(text)
            # Full text stays in raw HTML only — not in preview JSON (privacy/size).
            out["fetched_at"] = datetime.now(timezone.utc).isoformat()
            out["content_hash"] = hashlib.sha256(text.encode()).hexdigest()
            RAW_DIR.mkdir(parents=True, exist_ok=True)
            (RAW_DIR / out["html_filename"]).write_text(html, encoding="utf-8")
        except httpx.HTTPError as exc:
            out["error"] = type(exc).__name__
    return out


async def _run(limit: int | None, write: bool) -> dict[str, Any]:
    pages = _load_urls(limit)
    if not pages:
        raise SystemExit("No ingest=true URLs in source-inventory.json")

    print(f"Pages to fetch: {len(pages)}")
    if not write:
        for p in pages:
            print(f"  [{p['category_id']}] {p['url']}")
        return {"dry_run": True, "count": len(pages)}

    semaphore = asyncio.Semaphore(1)
    async with httpx.AsyncClient(
        headers={"User-Agent": USER_AGENT, "Accept": "text/html"},
        timeout=HTTP_TIMEOUT,
    ) as client:
        results = await asyncio.gather(*[_fetch_one(client, p, semaphore) for p in pages])

    ok = [r for r in results if r.get("success")]
    manifest = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "total": len(results),
        "successful": len(ok),
        "pages": results,
    }
    PREVIEW_FILE.parent.mkdir(parents=True, exist_ok=True)
    PREVIEW_FILE.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    slim_path = PREVIEW_FILE.parent / "pages-manifest-slim.json"
    slim_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote {PREVIEW_FILE} ({len(ok)}/{len(results)} successful)")
    print(f"Wrote {slim_path} (no inline page text)")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch USCIS/DHS official pages")
    parser.add_argument("--inspect", action="store_true", help="List URLs only")
    parser.add_argument("--yes", action="store_true", help="Write raw HTML and preview JSON")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args(argv)
    if not args.inspect and not args.yes:
        print("Use --inspect or --yes")
        return 1
    asyncio.run(_run(args.limit, write=args.yes))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
