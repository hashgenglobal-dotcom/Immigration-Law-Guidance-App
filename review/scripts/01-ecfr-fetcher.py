#!/usr/bin/env python3
"""
CFR Title 8 Fetcher - Cornell Law LII

Fetches immigration-related CFR sections from Cornell Law School's Legal Information Institute.
LII provides clean, accessible HTML for CFR regulations.

Sources:
- Cornell LII CFR: https://www.law.cornell.edu/cfr/text/8
- LII API: https://www.law.cornell.edu/cfr/text/8/208.7

MVP Priority Sections (from docs/01-mvp-questions-source-mapping.md):
- 8 CFR § 208.7 - Asylum work authorization
- 8 CFR § 208.4 - Asylum application procedures
- 8 CFR § 245.1-245.2 - Adjustment of status
- 8 CFR § 214.2 - F-1 student status (H-1B, etc.)
- 8 CFR § 235 - Inspection by immigration officers
- 8 CFR § 274a - Control of employment of aliens
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Cornell LII CFR URL pattern
LII_BASE_URL = "https://www.law.cornell.edu/cfr/text/8/{section}"

# MVP Priority Sections
MVP_SECTIONS = [
    # Asylum (Part 208)
    {"section": "208.4", "topic": "Asylum application procedures"},
    {"section": "208.7", "topic": "Employment authorization (asylum pending)"},
    {"section": "208.13", "topic": "Establishing asylum eligibility"},
    {"section": "208.20", "topic": "Frivolous asylum applications"},
    
    # Documentary requirements (Part 212)
    {"section": "212.1", "topic": "Documents required for entry"},
    {"section": "212.7", "topic": "Waivers of inadmissibility"},
    
    # Nonimmigrant classification (Part 214)
    {"section": "214.1", "topic": "General nonimmigrant requirements"},
    {"section": "214.2", "topic": "Special requirements (F-1, H-1B, etc.)"},
    
    # Inspection (Part 235)
    {"section": "235.1", "topic": "Inspection procedures"},
    {"section": "235.3", "topic": "Expedited removal"},
    
    # Adjustment of status (Part 245)
    {"section": "245.1", "topic": "Adjustment of status eligibility"},
    {"section": "245.2", "topic": "Adjustment of status procedures"},
    
    # Employment control (Part 274a)
    {"section": "274a.1", "topic": "Employment authorization definitions"},
    {"section": "274a.12", "topic": "Classes of aliens authorized to work"},
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def fetch_section_html(section: str) -> Optional[str]:
    """Fetch HTML for a specific CFR section from Cornell LII"""
    url = LII_BASE_URL.format(section=section)
    print(f"  📥 {section}...")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"  ❌ {section}: {e}")
        return None


def parse_section_html(html: str, section_num: str) -> Optional[Dict]:
    """Parse CFR section HTML from Cornell LII"""
    soup = BeautifulSoup(html, "html.parser")
    
    # Remove scripts, styles, nav, footer
    for elem in soup(["script", "style", "noscript", "nav", "footer", "header", ".ad"]):
        elem.decompose()
    
    # Find main content - LII uses <div class="contextual-message"> or <div class="field-content">
    main_content = soup.find("div", class_=re.compile(r"field-content|content|body", re.I))
    if not main_content:
        main_content = soup.find("main")
    if not main_content:
        main_content = soup.body
    
    if not main_content:
        return None
    
    # Extract section heading - LII uses <h1> or <h2>
    heading = None
    for tag in ["h1", "h2", "h3"]:
        elem = main_content.find(tag)
        if elem:
            text = elem.get_text(" ", strip=True)
            if text and len(text) > 5:
                heading = text
                break
    
    # Extract regulation text from paragraphs
    paragraphs = []
    for p in main_content.find_all("p"):
        text = p.get_text(" ", strip=True)
        if text and len(text) > 20:
            # Filter boilerplate
            if not any(x in text.lower() for x in ["cookie", "privacy", "advertisement", "copyright"]):
                paragraphs.append(text)
    
    # Also extract from <div class="section-content"> or similar
    for div in main_content.find_all("div", class_=re.compile(r"section|provision|subsection|paragraph", re.I)):
        text = div.get_text(" ", strip=True)
        if text and len(text) > 20 and text not in paragraphs:
            paragraphs.append(text)
    
    # Extract from <pre> tags (sometimes used for regulation text)
    for pre in main_content.find_all("pre"):
        text = pre.get_text(" ", strip=True)
        if text and len(text) > 20 and text not in paragraphs:
            paragraphs.append(text)
    
    if not paragraphs:
        return None
    
    section_content = "\n\n".join(paragraphs)
    
    # Clean up multiple newlines
    section_content = re.sub(r"\n{3,}", "\n\n", section_content)
    
    return {
        "source": "Cornell LII",
        "title": "Title 8 - Aliens and Nationality",
        "section_number": section_num,
        "section_title": heading or f"Section {section_num}",
        "content": section_content,
        "url": LII_BASE_URL.format(section=section_num),
        "effective_date": datetime.now().strftime("%Y-%m-%d"),
        "retrieved_at": datetime.now().isoformat(),
    }


def fetch_all_mvp_sections(output_path: Path) -> List[Dict]:
    """Fetch all MVP priority sections"""
    print("📥 Fetching MVP priority CFR sections from Cornell Law LII...")
    
    sections_data = []
    
    for sec_info in MVP_SECTIONS:
        section = sec_info["section"]
        html = fetch_section_html(section)
        if html:
            parsed = parse_section_html(html, section)
            if parsed:
                parsed["topic"] = sec_info["topic"]
                sections_data.append(parsed)
                content_preview = parsed['content'][:80].replace("\n", " ")
                print(f"    ✓ {section} ({sec_info['topic'][:25]}...): {len(parsed['content'])} chars - '{content_preview}...'")
            else:
                print(f"    ⚠ {section}: No content parsed")
        else:
            print(f"    ❌ {section}: Failed to fetch")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(sections_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Fetched {len(sections_data)}/{len(MVP_SECTIONS)} sections → {output_path}")
    return sections_data


def chunk_text(text: str, max_tokens: int = 800, overlap: int = 100) -> List[str]:
    """Split text into overlapping chunks for RAG retrieval"""
    max_chars = max_tokens * 4
    overlap_chars = overlap * 4
    
    chunks = []
    paragraphs = text.split("\n\n")
    
    current_chunk = ""
    for para in paragraphs:
        if len(current_chunk) + len(para) + 2 <= max_chars:
            current_chunk += para + "\n\n" if para else ""
        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            
            if len(para) > max_chars:
                for i in range(0, len(para), max_chars - overlap_chars):
                    chunk = para[i:i + max_chars]
                    chunks.append(chunk.strip())
            else:
                current_chunk = para + "\n\n"
    
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks


def test_chunking(sections_path: Path, output_path: Path):
    """Test chunking strategy on parsed sections"""
    print(f"\n🔪 Testing chunking strategy...")
    
    with open(sections_path, "r", encoding="utf-8") as f:
        sections = json.load(f)
    
    all_chunks = []
    
    for section in sections:
        section_text = f"§ {section['section_number']} - {section['section_title']}\n\n{section['content']}"
        chunks = chunk_text(section_text, max_tokens=800, overlap=100)
        
        for i, chunk in enumerate(chunks):
            chunk_data = {
                "source": "Cornell LII",
                "section_number": section["section_number"],
                "section_title": section["section_title"],
                "topic": section.get("topic", ""),
                "chunk_index": i,
                "total_chunks": len(chunks),
                "chunk_text": chunk,
                "char_count": len(chunk),
                "url": section["url"],
            }
            all_chunks.append(chunk_data)
        
        print(f"  {section['section_number']}: {len(chunks)} chunks ({len(section_text)} chars)")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Created {len(all_chunks)} chunks → {output_path}")
    return all_chunks


def main():
    """Main pipeline: fetch → parse → chunk"""
    print("=" * 60)
    print("CFR Title 8 Fetcher (Cornell Law LII)")
    print("=" * 60)
    
    base_dir = Path(__file__).parent.parent / "data" / "ecfr"
    sections_path = base_dir / "mvp-sections.json"
    chunks_path = base_dir / "mvp-chunks.json"
    
    print("\n[Step 1/2] Fetching MVP priority sections...")
    sections = fetch_all_mvp_sections(sections_path)
    
    if not sections:
        print("\n❌ No sections fetched. Check network or LII availability.")
        return
    
    print("\n[Step 2/2] Testing chunking strategy...")
    chunks = test_chunking(sections_path, chunks_path)
    
    print("\n" + "=" * 60)
    print("📊 Summary")
    print("=" * 60)
    print(f"Parsed sections: {sections_path} ({len(sections)} sections)")
    print(f"Chunks:          {chunks_path} ({len(chunks)} chunks)")
    print(f"\n✅ Pipeline complete!")
    
    if chunks:
        print("\n📝 Sample chunk (first 600 chars):")
        print("-" * 60)
        print(chunks[0]["chunk_text"][:600])
        print("-" * 60)


if __name__ == "__main__":
    main()
