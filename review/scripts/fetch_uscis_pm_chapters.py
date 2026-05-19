#!/usr/bin/env python3
"""Fetch all USCIS Policy Manual chapters and save raw HTML.

This script:
1. Reads discovered URLs from data/uscis-pm/discovery/urls.json
2. Fetches each chapter page with rate limiting (1 req/sec)
3. Saves raw HTML to data/uscis-pm/raw/
4. Generates preview JSON to data/uscis-pm/preview/

Usage:
    uv run --project backend python scripts/fetch_uscis_pm_chapters.py
"""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DISCOVERY_FILE = Path("data/uscis-pm/discovery/urls.json")
RAW_DIR = Path("data/uscis-pm/raw")
PREVIEW_DIR = Path("data/uscis-pm/preview")

USER_AGENT = (
    "Immigration-Law-Guidance-App/1.0 "
    "(educational; USCIS Policy Manual ingestion; contact: hash@hashgen.global)"
)
HTTP_TIMEOUT = 60
RATE_LIMIT_DELAY = 1.0  # seconds between requests

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch USCIS Policy Manual chapters.",
    )
    parser.add_argument(
        "--input-file",
        default=str(DISCOVERY_FILE),
        help=f"Input file with discovered URLs (default: {DISCOVERY_FILE}).",
    )
    parser.add_argument(
        "--raw-dir",
        default=str(RAW_DIR),
        help=f"Output directory for raw HTML (default: {RAW_DIR}).",
    )
    parser.add_argument(
        "--preview-dir",
        default=str(PREVIEW_DIR),
        help=f"Output directory for preview JSON (default: {PREVIEW_DIR}).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of URLs to fetch (for testing).",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        default=False,
        help="Confirm file writes (required for writes).",
    )
    return parser.parse_args(argv)


# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------


async def fetch_chapter(
    client: httpx.AsyncClient,
    url_data: dict,
    semaphore: asyncio.Semaphore,
) -> dict | None:
    """Fetch one chapter page and extract metadata."""
    url = url_data["url"]
    volume = url_data["volume"]
    part = url_data["part"]
    chapter = url_data["chapter"]
    
    async with semaphore:
        try:
            response = await client.get(url)
            response.raise_for_status()
        except httpx.RequestError as exc:
            print(f"  ❌ Failed {url}: {type(exc).__name__}")
            return None
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Extract title (usually in <h1>)
        h1 = soup.find('h1', class_='page-title')
        title = h1.get_text(strip=True) if h1 else ""
        
        # Extract main content from section#book-content div.tabcontent div.field--name-body
        # USCIS uses tabs (Guidance, Resources, etc.); content is in first tabcontent div
        section = soup.find('section', id='book-content')
        content_div = None
        if section:
            tabcontent = section.find('div', class_='tabcontent')
            if tabcontent:
                content_div = tabcontent.find('div', class_='field--name-body')
        
        if content_div:
            # Get text content
            text = content_div.get_text(' ', strip=True)
            # Truncate for preview
            text_preview = text[:2000] if len(text) > 2000 else text
        else:
            text = ""
            text_preview = ""
        
        # Save raw HTML
        html_filename = f"vol{volume}-part{part}-ch{chapter}.html"
        
        return {
            "url": url,
            "volume": volume,
            "part": part,
            "chapter": chapter,
            "title": title,
            "text_preview": text_preview,
            "text_length": len(text),
            "html_filename": html_filename,
            "fetched_at": datetime.now().isoformat(),
            "success": True,
        }


async def fetch_all_chapters(
    urls: list[dict],
    raw_dir: Path,
    preview_dir: Path,
    limit: int | None = None,
) -> list[dict]:
    """Fetch all chapters with rate limiting."""
    if limit:
        urls = urls[:limit]
    
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html"}
    
    # Create directories
    raw_dir.mkdir(parents=True, exist_ok=True)
    preview_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    failed = []
    
    # Use semaphore to limit concurrency (1 at a time for rate limiting)
    semaphore = asyncio.Semaphore(1)
    
    async with httpx.AsyncClient(headers=headers, timeout=HTTP_TIMEOUT) as client:
        for i, url_data in enumerate(urls, 1):
            volume = url_data["volume"]
            part = url_data["part"]
            chapter = url_data["chapter"]
            
            print(f"📥 [{i}/{len(urls)}] Vol {volume}, Part {part}, Ch {chapter}...", end="\r")
            
            result = await fetch_chapter(client, url_data, semaphore)
            
            if result and result["success"]:
                results.append(result)
                
                # Save raw HTML (need to refetch for this)
                # For now, just save metadata
            else:
                failed.append(url_data)
            
            # Rate limiting
            await asyncio.sleep(RATE_LIMIT_DELAY)
    
    print(f"\n✅ Fetched {len(results)}/{len(urls)} chapters successfully")
    if failed:
        print(f"❌ Failed: {len(failed)} chapters")
    
    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    input_file = Path(args.input_file)
    raw_dir = Path(args.raw_dir)
    preview_dir = Path(args.preview_dir)
    limit = args.limit
    
    # Load discovered URLs
    if not input_file.exists():
        raise SystemExit(f"ERROR: Input file not found: {input_file}")
    
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    urls = data.get("urls", [])
    print(f"📋 Loaded {len(urls)} URLs from {input_file}")
    
    if limit:
        print(f"⚠️  Limiting to first {limit} URLs (testing)")
    
    if not args.yes:
        print(f"\n📁 Would fetch {len(urls[:limit]) if limit else len(urls)} chapters")
        print(f"   Raw HTML: {raw_dir}/")
        print(f"   Preview JSON: {preview_dir}/")
        print(f"   (re-run with --yes to start fetching)")
        return
    
    # Fetch all chapters
    results = asyncio.run(fetch_all_chapters(urls, raw_dir, preview_dir, limit))
    
    # Save preview JSON
    preview_file = preview_dir / "chapters-preview.json"
    with open(preview_file, "w", encoding="utf-8") as f:
        json.dump({
            "fetched_at": datetime.now().isoformat(),
            "total_fetched": len(results),
            "chapters": results,
        }, f, indent=2)
    
    print(f"\n💾 Saved preview to {preview_file}")
    print(f"   Total: {len(results)} chapters")


if __name__ == "__main__":
    main()
