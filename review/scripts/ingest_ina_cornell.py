#!/usr/bin/env python3
"""Fetch and ingest INA from Cornell LII using direct section URLs.

Instead of crawling chapter pages (which have nested navigation), this script
fetches INA sections directly using their known section numbers.

INA Core Sections (Chapter 12):
- 1101-1107: Definitions and General Provisions
- 1151-1161: Visa Quotas and Selection System
- 1181-1189: Admission Qualifications (Inadmissibility)
- 1201-1205: Visa Issuance
- 1221-1232: Inspection, Apprehension, Removal
- 1251-1260: Adjustment of Status
- 1281-1288: Alien Crewmen
- 1301-1306: Alien Registration
- 1321-1330: Penalties
- 1351-1382: Miscellaneous
- 1401-1504: Nationality and Naturalization
- 1521-1525: Refugee Assistance
- 1531-1537: Alien Terrorist Removal

Usage:
    uv run --project backend python scripts/ingest_ina_cornell.py --yes
"""

import argparse
import hashlib
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx
from bs4 import BeautifulSoup


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LII_BASE_URL = "https://www.law.cornell.edu/uscode/text/8"

# Core INA section ranges to scrape
SECTION_RANGES = [
    # (start, end, topic, subtopic)
    (1, 18, "General Provisions", "Early Immigration Law"),  # Chapter 1
    (100, 241, "Immigration", "Early Immigration Provisions"),  # Chapter 6
    (501, 1001, "Nationality", "Citizenship and Nationality"),  # Chapter 11
    (1101, 1107, "Definitions", "General Definitions"),  # Ch 12, Subch I
    (1151, 1161, "Visa Quotas", "Selection System"),  # Ch 12, Subch II, Part I
    (1181, 1189, "Admissibility", "Entry Requirements"),  # Ch 12, Subch II, Part II
    (1201, 1205, "Visa Issuance", "Documentation"),  # Ch 12, Subch II, Part III
    (1221, 1232, "Inspection and Removal", "Enforcement"),  # Ch 12, Subch II, Part IV
    (1251, 1260, "Adjustment of Status", "Status Changes"),  # Ch 12, Subch II, Part V
    (1281, 1288, "Alien Crewmen", "Crew Regulations"),  # Ch 12, Subch II, Part VI
    (1301, 1306, "Alien Registration", "Registration Requirements"),  # Ch 12, Subch II, Part VII
    (1321, 1330, "Penalties", "Criminal and Civil Penalties"),  # Ch 12, Subch II, Part VIII
    (1351, 1382, "Miscellaneous", "General Provisions"),  # Ch 12, Subch II, Part IX
    (1401, 1504, "Naturalization", "Citizenship Process"),  # Ch 12, Subch III
    (1521, 1525, "Refugee Assistance", "Refugee Programs"),  # Ch 12, Subch IV
    (1531, 1537, "Terrorist Removal", "Removal Procedures"),  # Ch 12, Subch V
    (1551, 1574, "INS Administration", "Immigration Service"),  # Chapter 13
    (1601, 1646, "Public Benefits", "Welfare Restrictions"),  # Chapter 14
    (1701, 1778, "Border Security", "Visa Entry Reform"),  # Chapter 15
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}


def get_db_connection():
    """Get database connection from environment."""
    import psycopg
    conn = psycopg.connect(
        host="localhost",
        port=54329,
        user="hash",
        password="hash",
        dbname="immigration_law_dev",
    )
    return conn


def fetch_section_page(section_num: int) -> tuple[str, str]:
    """Fetch a section page from Cornell LII.
    
    Returns: (html, url)
    """
    url = f"{LII_BASE_URL}/{section_num}"
    
    try:
        with httpx.Client(headers=HEADERS, timeout=30.0) as client:
            response = client.get(url)
            if response.status_code == 404:
                return ("", url)
            response.raise_for_status()
            return (response.text, url)
    except httpx.RequestError as e:
        print(f"  ⚠️  Error fetching §{section_num}: {e}")
        return ("", url)


def parse_section_page(html: str, section_num: int, url: str) -> Optional[dict]:
    """Parse section page to extract section number, title, and text."""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Check if this is a 404 or error page
    if soup.find('h1') and '404' in soup.find('h1').get_text():
        return None
    
    # Extract title from h1
    title_elem = soup.find('h1')
    if not title_elem:
        return None
    
    full_title = title_elem.get_text(strip=True)
    
    # Clean title (remove "8 U.S. Code § 1101 — " prefix)
    title = re.sub(r'^\d+\s+U\.?\s*S?\.?\s*Code\s+§+\s*[\d–-]+\s*—\s*', '', full_title)
    title = title.strip()
    
    if not title:
        title = f"Section {section_num}"
    
    # Extract section text
    text_parts = []
    
    # Look for the main content area
    main_elem = soup.find('main')
    if not main_elem:
        main_elem = soup.find('div', id='content')
    
    if main_elem:
        # Get all paragraphs
        for para in main_elem.find_all('p', recursive=True):
            text = para.get_text(strip=True)
            if text and len(text) > 20:
                text_parts.append(text)
        
        # Also get list items (subsections often in lists)
        for li in main_elem.find_all('li', recursive=True):
            text = li.get_text(strip=True)
            if text and len(text) > 20:
                text_parts.append(text)
        
        # Get preformatted text (sometimes used for statutory text)
        for pre in main_elem.find_all('pre', recursive=True):
            text = pre.get_text(strip=True)
            if text and len(text) > 20:
                text_parts.append(text)
    
    # Fallback: get all paragraphs from body
    if not text_parts:
        for para in soup.find_all('p'):
            text = para.get_text(strip=True)
            if text and len(text) > 20:
                text_parts.append(text)
    
    full_text = '\n\n'.join(text_parts) if text_parts else ""
    
    # Skip if too short (likely empty or error page)
    if len(full_text) < 100:
        return None
    
    return {
        'section_number': str(section_num),
        'title': title,
        'text': full_text,
        'url': url,
    }


def chunk_text(text: str, max_length: int = 1500, overlap: int = 200) -> list[str]:
    """Split text into overlapping chunks for retrieval."""
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + max_length
        
        # Try to break at a sentence boundary
        if end < len(text):
            search_region = text[start:end]
            last_period = search_region.rfind('. ')
            last_newline = search_region.rfind('\n')
            
            if last_period > max_length - 300:
                end = start + last_period + 1
            elif last_newline > max_length - 300:
                end = start + last_newline + 1
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end - overlap
        if start >= len(text):
            break
    
    return chunks


def get_topic_for_section(section_num: int) -> tuple[str, str]:
    """Get topic and subtopic for a section number."""
    for start, end, topic, subtopic in SECTION_RANGES:
        if start <= section_num <= end:
            return (topic, subtopic)
    return ("General", "General")


def register_source(conn) -> int:
    """Register INA as a source."""
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO source_registry (source_name, source_type, publisher, base_url, access_method)
            VALUES (
                'Immigration and Nationality Act',
                'statute',
                'U.S. Congress (via Cornell LII)',
                'https://www.law.cornell.edu/uscode/text/8',
                'web_scrape'
            )
            ON CONFLICT (source_name) DO UPDATE SET
                publisher = EXCLUDED.publisher,
                base_url = EXCLUDED.base_url,
                updated_at = NOW()
            RETURNING id;
        """)
        source_id = cur.fetchone()[0]
        conn.commit()
        print(f"✅ Source registered: INA (ID: {source_id})")
        return source_id


def insert_sections(conn, source_id: int, sections: list[dict]) -> tuple[int, int, int]:
    """Insert all INA sections into database."""
    documents_inserted = 0
    sections_inserted = 0
    chunks_inserted = 0
    
    with conn.cursor() as cur:
        for section in sections:
            section_number = section['section_number']
            title = section['title']
            text = section['text']
            
            if not text or len(text.strip()) < 50:
                continue
            
            topic, subtopic = get_topic_for_section(int(section_number))
            citation = f"8 U.S.C. § {section_number}"
            
            # Insert into raw_documents
            cur.execute("""
                INSERT INTO raw_documents (
                    source_id, external_id, title, citation, official_url,
                    raw_format, raw_content, content_hash
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    'html', %s, %s
                )
                RETURNING id;
            """, (
                source_id,
                f"ina-{section_number}",
                title,
                citation,
                section['url'],
                text,
                hashlib.sha256(text.encode()).hexdigest(),
            ))
            raw_doc_id = cur.fetchone()[0]
            
            # Insert into legal_documents
            cur.execute("""
                INSERT INTO legal_documents (
                    raw_document_id, source_type, title, citation,
                    publisher, official_url
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s
                )
                RETURNING id;
            """, (
                raw_doc_id,
                'ina_section',
                title,
                citation,
                'U.S. Congress (Cornell LII)',
                section['url'],
            ))
            doc_id = cur.fetchone()[0]
            documents_inserted += 1
            
            # Insert into legal_sections
            cur.execute("""
                INSERT INTO legal_sections (
                    document_id, section_number, section_title,
                    citation, official_text, topic, subtopic
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s
                )
                RETURNING id;
            """, (
                doc_id,
                f"§ {section_number}",
                title,
                citation,
                text,
                topic,
                subtopic,
            ))
            section_id = cur.fetchone()[0]
            sections_inserted += 1
            
            # Create chunks for retrieval
            chunks = chunk_text(text)
            for i, chunk_text_item in enumerate(chunks):
                cur.execute("""
                    INSERT INTO legal_chunks (
                        section_id, chunk_index, chunk_text,
                        citation, topic, subtopic, is_active
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, TRUE
                    );
                """, (
                    section_id,
                    i,
                    chunk_text_item,
                    citation,
                    topic,
                    subtopic,
                ))
                chunks_inserted += 1
            
            if documents_inserted % 50 == 0:
                conn.commit()
                print(f"  📦 Inserted {documents_inserted}/{len(sections)} sections...")
        
        conn.commit()
    
    return documents_inserted, sections_inserted, chunks_inserted


def create_dataset_version(conn, source_id: int, chunk_count: int) -> int:
    """Create and activate a new dataset version."""
    version_name = f"ina-{datetime.now().strftime('%Y-%m-%d')}"
    
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO dataset_versions (
                version_name, status, notes, created_by, activated_at
            ) VALUES (
                %s, 'active', %s, %s, NOW()
            )
            RETURNING id;
        """, (
            version_name,
            f"INA ingestion: {chunk_count} chunks from U.S. Code Title 8 (Cornell LII)",
            'automated_ingestion',
        ))
        dataset_id = cur.fetchone()[0]
        
        conn.commit()
        
        print(f"✅ Dataset version created: {version_name} (ID: {dataset_id})")
        return dataset_id


def main():
    parser = argparse.ArgumentParser(description='Ingest INA from Cornell LII')
    parser.add_argument('--yes', action='store_true', help='Skip confirmation prompt')
    parser.add_argument('--section', type=int, nargs='*', default=None, 
                        help='Specific sections to scrape (default: all INA ranges)')
    args = parser.parse_args()
    
    print("📋 INA Ingestion Pipeline (Cornell LII - Direct Section Fetch)")
    print("=" * 60)
    
    # Build list of sections to scrape
    sections_to_scrape = []
    for start, end, topic, subtopic in SECTION_RANGES:
        for num in range(start, end + 1):
            sections_to_scrape.append((num, topic, subtopic))
    
    # If specific sections requested, filter
    if args.section:
        sections_to_scrape = [(num, t, s) for num, t, s in sections_to_scrape if num in args.section]
    
    print(f"\n📚 Scraping {len(sections_to_scrape)} INA sections...")
    print(f"   Ranges: {SECTION_RANGES[0][0]}-{SECTION_RANGES[-1][1]}")
    
    all_sections = []
    
    # Fetch sections
    for i, (section_num, topic, subtopic) in enumerate(sections_to_scrape):
        # Progress indicator
        if (i + 1) % 50 == 0:
            print(f"  📈 Progress: {i + 1}/{len(sections_to_scrape)} sections...")
        
        # Fetch page
        html, url = fetch_section_page(section_num)
        if not html:
            continue
        
        # Parse
        section_data = parse_section_page(html, section_num, url)
        if section_data:
            section_data['topic'] = topic
            section_data['subtopic'] = subtopic
            all_sections.append(section_data)
            print(f"  ✅ §{section_num}: {section_data['title'][:50]}...")
        else:
            print(f"  ⚠️  §{section_num}: No content found")
        
        # Rate limiting: 1 request per 1.5 seconds
        time.sleep(1.5)
    
    print(f"\n{'='*60}")
    print(f"✅ Scraping complete: {len(all_sections)} sections collected")
    print(f"{'='*60}")
    
    if not all_sections:
        print("❌ No sections scraped. Exiting.")
        sys.exit(1)
    
    # Save preview
    raw_dir = Path("data/ina/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    preview_dir = Path("data/ina/preview")
    preview_dir.mkdir(parents=True, exist_ok=True)
    
    import json
    preview_data = {
        'total_sections': len(all_sections),
        'ingestion_date': datetime.now().isoformat(),
        'section_ranges': [(s, e) for s, e, _, _ in SECTION_RANGES],
        'sections': [{
            'section_number': s['section_number'],
            'title': s['title'],
            'text_length': len(s['text']),
            'url': s['url'],
            'topic': s.get('topic', 'General'),
        } for s in all_sections]
    }
    preview_path = preview_dir / "sections-preview.json"
    preview_path.write_text(json.dumps(preview_data, indent=2), encoding='utf-8')
    print(f"💾 Saved preview to: {preview_path}")
    
    if not args.yes:
        confirm = input(f"\nProceed with inserting {len(all_sections)} sections? [y/N] ")
        if confirm.lower() != 'y':
            print("Aborted")
            sys.exit(0)
    
    # Connect to database
    conn = get_db_connection()
    
    try:
        # Register source
        source_id = register_source(conn)
        
        # Insert sections
        print("\n📦 Inserting sections into database...")
        docs, secs, chunks = insert_sections(conn, source_id, all_sections)
        
        print(f"\n✅ Insertion complete:")
        print(f"   Documents: {docs}")
        print(f"   Sections: {secs}")
        print(f"   Chunks: {chunks}")
        
        # Create dataset version
        dataset_id = create_dataset_version(conn, source_id, chunks)
        
        print(f"\n🎉 INA ingestion complete!")
        print(f"   Dataset: ina-{datetime.now().strftime('%Y-%m-%d')}")
        print(f"   Next: Run embed_legal_chunks.py to generate embeddings")
        
    finally:
        conn.close()


if __name__ == '__main__':
    main()
