#!/usr/bin/env python3
"""Discover all USCIS Policy Manual section URLs from table of contents.

This script:
1. Fetches the USCIS Policy Manual table of contents page
2. Parses all Volume/Part/Chapter links
3. Builds complete URL structure
4. Saves to data/uscis-pm/discovery/urls.json

Usage:
    uv run --project backend python scripts/discover_uscis_pm_urls.py
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TOC_URL = "https://www.uscis.gov/policy-manual/table-of-contents"
BASE_URL = "https://www.uscis.gov"
OUTPUT_DIR = Path("data/uscis-pm/discovery")
OUTPUT_FILE = OUTPUT_DIR / "urls.json"

USER_AGENT = (
    "Immigration-Law-Guidance-App/1.0 "
    "(educational; USCIS Policy Manual ingestion; contact: hash@hashgen.global)"
)
HTTP_TIMEOUT = 60

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Discover USCIS Policy Manual URLs from table of contents.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(OUTPUT_DIR),
        help=f"Output directory (default: {OUTPUT_DIR}).",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        default=False,
        help="Confirm file write (required for writes).",
    )
    return parser.parse_args(argv)


# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------


def fetch_toc_page() -> str:
    """Fetch USCIS Policy Manual table of contents page."""
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html"}
    try:
        response = httpx.get(TOC_URL, headers=headers, timeout=HTTP_TIMEOUT)
        response.raise_for_status()
        return response.text
    except httpx.RequestError as exc:
        raise SystemExit(f"ERROR: network failure fetching TOC: {type(exc).__name__}")


# ---------------------------------------------------------------------------
# Parse
# ---------------------------------------------------------------------------


def extract_volume_part_chapter_urls(html_content: str) -> list[dict]:
    """Parse TOC page and extract all Volume/Part/Chapter URLs."""
    soup = BeautifulSoup(html_content, 'lxml')
    
    urls = []
    
    # Find all links that match the pattern: /policy-manual/volume-X-part-Y-chapter-Z
    pattern = re.compile(r'/policy-manual/volume-\d+-part-[a-z]+-chapter-\d+', re.IGNORECASE)
    
    for link in soup.find_all('a', href=True):
        href = link.get('href', '')
        
        # Check if it's a policy-manual chapter URL
        if pattern.search(href):
            # Extract metadata from URL
            match = re.search(
                r'/policy-manual/volume-(\d+)-part-([a-z]+)-chapter-(\d+)',
                href,
                re.IGNORECASE
            )
            if match:
                volume = int(match.group(1))
                part = match.group(2).upper()
                chapter = int(match.group(3))
                
                # Build full URL if relative
                full_url = href if href.startswith('http') else f"{BASE_URL}{href}"
                
                urls.append({
                    "url": full_url,
                    "volume": volume,
                    "part": part,
                    "chapter": chapter,
                })
    
    # Sort by volume, part, chapter
    urls.sort(key=lambda x: (x["volume"], x["part"], x["chapter"]))
    
    # Remove duplicates
    seen = set()
    unique_urls = []
    for url_data in urls:
        if url_data["url"] not in seen:
            seen.add(url_data["url"])
            unique_urls.append(url_data)
    
    return unique_urls


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    output_dir = Path(args.output_dir)
    
    print(f"🔍 Fetching table of contents from {TOC_URL}...")
    html_content = fetch_toc_page()
    
    print(f"📄 Parsing HTML...")
    urls = extract_volume_part_chapter_urls(html_content)
    
    if not urls:
        raise SystemExit("ERROR: No policy-manual URLs found in table of contents")
    
    # Count by volume
    volume_counts = {}
    for url in urls:
        vol = f"Volume {url['volume']}"
        volume_counts[vol] = volume_counts.get(vol, 0) + 1
    
    print(f"\n✅ Found {len(urls)} unique Policy Manual chapter URLs")
    print("\nBy Volume:")
    for vol, count in sorted(volume_counts.items()):
        print(f"  {vol}: {count} URLs")
    
    # Show sample URLs
    print("\n📋 Sample URLs:")
    for url in urls[:5]:
        print(f"   - Vol {url['volume']}, Part {url['part']}, Ch {url['chapter']}: {url['url']}")
    
    # Write output
    output_file = output_dir / "urls.json"
    
    if not args.yes:
        print(f"\n📁 Would write to {output_file}")
        print(f"   (re-run with --yes to save)")
        return
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_data = {
        "discovered_at": datetime.now().isoformat(),
        "source": TOC_URL,
        "total_urls": len(urls),
        "urls": urls,
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n💾 Saved to {output_file}")
    print(f"   Total: {len(urls)} URLs")


if __name__ == "__main__":
    main()
