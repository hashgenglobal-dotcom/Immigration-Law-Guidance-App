#!/usr/bin/env python3
"""
Fetch INA (Immigration and Nationality Act) from uscode.house.gov.

Source: https://uscode.house.gov/
Format: HTML (official U.S. Code structure)
No API key required.

Output:
  - data/ina/raw/*.txt (raw section text files)
  - data/ina/preview/sections-preview.json (metadata preview)
"""

import httpx
import asyncio
import re
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime

# OLRC (Office of the Law Revision Counsel) URL pattern
BASE_URL = "https://uscode.house.gov"

# Output directories
RAW_DIR = Path("data/ina/raw")
PREVIEW_DIR = Path("data/ina/preview")

# Core INA sections for MVP (Title 8 USC)
INA_SECTIONS = [
    # Chapter 1: General Provisions (Definitions)
    "101", "101a", "101b", "102", "103", "104", "105", "106", "107", "108", "109", "110",
    # Chapter 2: Immigration - General
    "201", "202", "203", "204", "205", "206", "207", "208", "209", "210",
    # Inadmissibility
    "212", "213", "214", "215", "216", "217", "218", "219", "220",
    # Inspection, Apprehension, Examination, Removal
    "231", "232", "233", "234", "235", "236", "237", "238", "239", "240",
    # Adjustment of Status
    "241", "242", "243", "244", "245", "246", "247", "248", "249", "250",
    # Employment
    "274", "274a", "274b", "274c", "274d", "275", "276",
    # Naturalization
    "301", "310", "311", "312", "313", "314", "315", "316", "317", "318", "319", "320", "321", "322",
    # Penalties
    "331", "332", "333", "334", "335", "336", "337", "338", "339", "340",
]


async def fetch_section(session: httpx.AsyncClient, section_id: str) -> dict | None:
    """Fetch a single INA section from uscode.house.gov."""
    # URL pattern: https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title8-section101&num=0&edition=prelim
    url = f"{BASE_URL}/view.xhtml"
    params = {
        "req": f"granuleid:USC-prelim-title8-section{section_id}",
        "num": "0",
        "edition": "prelim",
    }
    
    try:
        response = await session.get(url, params=params, timeout=30)
        if response.status_code == 404:
            print(f"  [{section_id}] Not found (404)")
            return None
        response.raise_for_status()
        
        html_content = response.text
        title, text = parse_ina_section(html_content, section_id)
        
        if not text or len(text.strip()) < 100:
            print(f"  [{section_id}] No meaningful text extracted")
            return None
        
        return {
            "section_id": section_id,
            "citation": f"INA § {section_id}",
            "title": title or f"INA Section {section_id}",
            "text": text,
            "url": f"{url}?req=granuleid:USC-prelim-title8-section{section_id}",
            "fetched_at": datetime.utcnow().isoformat() + "Z",
        }
    except httpx.HTTPError as e:
        print(f"  [{section_id}] HTTP error: {e}")
        return None
    except Exception as e:
        print(f"  [{section_id}] Error: {e}")
        return None


def parse_ina_section(html_content: str, section_id: str) -> tuple[str, str]:
    """Parse INA HTML and extract title and text content."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract title from <title> tag or main heading
    title_elem = soup.find('title')
    title = title_elem.get_text(strip=True) if title_elem else ""
    # Clean up title (remove " - Office of the Law Revision Counsel" suffix)
    title = re.sub(r'\s*-\s*Office of the Law Revision Counsel.*$', '', title)
    
    # Extract main content from the primary container
    # uscode.house.gov uses specific CSS classes for section content
    content_div = soup.find('div', class_='usc-body') or soup.find('div', id='content')
    
    if content_div:
        # Get text from the content div
        text_parts = []
        for elem in content_div.find_all(['p', 'div', 'span'], recursive=True):
            text = elem.get_text(' ', strip=True)
            if text and len(text) > 10:
                text_parts.append(text)
        text = '\n\n'.join(text_parts)
    else:
        # Fallback: get all text and clean it up
        text = soup.get_text(separator=' ', strip=True)
    
    # Clean up whitespace and remove navigation/UI text
    # Remove common boilerplate text
    boilerplate_patterns = [
        r'Office of the Law Revision Counsel',
        r'United States Code',
        r'Navigation',
        r'Search.*Go',
        r'Home.*About.*Contact',
        r'Skip to main content',
        r'View.*Download',
    ]
    for pattern in boilerplate_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Clean up multiple spaces and newlines
    text = re.sub(r'\s+', ' ', text).strip()
    
    return title, text


async def main():
    """Main fetch routine."""
    print("-" * 70)
    print("INA (Title 8 U.S. Code) Fetcher")
    print(f"Source: {BASE_URL}")
    print(f"Target: {RAW_DIR} / {PREVIEW_DIR}")
    print("-" * 70)
    
    # Create directories
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    
    # Fetch all sections
    sections = []
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        print(f"\nFetching {len(INA_SECTIONS)} sections...\n")
        
        for i, section_id in enumerate(INA_SECTIONS, 1):
            print(f"[{i}/{len(INA_SECTIONS)}] Fetching INA § {section_id}...", end=" ")
            result = await fetch_section(client, section_id)
            if result:
                sections.append(result)
                # Save raw text
                txt_path = RAW_DIR / f"sec{section_id}.txt"
                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write(result['text'])
                print(f"✓ Saved ({len(result['text'])} chars)")
            else:
                print("✗ Skipped")
    
    # Save preview JSON
    preview_path = PREVIEW_DIR / 'sections-preview.json'
    import json
    with open(preview_path, 'w', encoding='utf-8') as f:
        json.dump(sections, f, indent=2, ensure_ascii=False)
    
    # Summary
    print("\n" + "=" * 70)
    print("Fetch Complete")
    print("=" * 70)
    print(f"  Sections fetched: {len(sections)}/{len(INA_SECTIONS)}")
    print(f"  Raw text files:   {RAW_DIR} ({len(sections)} files)")
    print(f"  Preview JSON:     {preview_path}")
    print(f"  Total text:       {sum(len(s['text']) for s in sections):,} chars")
    print("=" * 70)
    
    return sections


if __name__ == "__main__":
    asyncio.run(main())
