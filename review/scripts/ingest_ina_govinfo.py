#!/usr/bin/env python3
"""Fetch and ingest Immigration and Nationality Act (INA) from GovInfo API.

The INA is codified in Title 8 of the U.S. Code (8 U.S.C.). This script:
1. Fetches INA sections from GovInfo bulk XML API
2. Parses XML structure to extract sections
3. Inserts into database (raw_documents → legal_documents → legal_sections → legal_chunks)
4. Creates dataset version

GovInfo API: https://www.govinfo.gov/link/uscode/8/

Usage:
    uv run --project backend python scripts/ingest_ina_govinfo.py --yes
"""

import argparse
import hashlib
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Optional

import psycopg
from psycopg.types.json import Json


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GOVINFO_BASE_URL = "https://www.govinfo.gov/bulkdata/USCODE/title-08"
NAMESPACE = {
    'uscode': 'http://namespaces.govinfo.gov/2002/uscode',
    'atom': 'http://www.w3.org/2005/Atom'
}


def get_db_connection():
    """Get database connection from DATABASE_URL env var or backend/.env."""
    import os

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        env_path = Path("backend/.env")
        if env_path.exists():
            for raw_line in env_path.read_text().splitlines():
                stripped = raw_line.strip()
                if stripped.startswith("DATABASE_URL="):
                    db_url = stripped.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not db_url:
        raise RuntimeError(
            "DATABASE_URL not set. "
            "Set it in the environment or add DATABASE_URL to backend/.env."
        )
    # Strip SQLAlchemy driver suffix if present
    db_url = db_url.replace("postgresql+psycopg://", "postgresql://")
    return psycopg.connect(db_url)


def fetch_ina_xml(year: str = "2024") -> str:
    """Fetch INA XML from GovInfo.
    
    GovInfo provides annual editions of U.S. Code in XML format.
    We fetch the most recent complete edition.
    """
    # Try to get the XML package URL
    # Format: https://www.govinfo.gov/bulkdata/USCODE/title-08/USCODE_title-08-2024.xml
    xml_url = f"{GOVINFO_BASE_URL}/USCODE_title-08-{year}.xml"
    
    print(f"📥 Fetching INA from: {xml_url}")
    
    try:
        req = urllib.request.Request(
            xml_url,
            headers={'User-Agent': 'Immigration-Law-App/1.0'}
        )
        with urllib.request.urlopen(req, timeout=120) as response:
            return response.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"❌ Year {year} not found. Trying previous year...")
            return fetch_ina_xml(str(int(year) - 1))
        raise
    except urllib.error.URLError as e:
        print(f"❌ Network error: {e}")
        sys.exit(1)


def parse_ina_sections(xml_content: str) -> list[dict]:
    """Parse INA XML and extract sections.
    
    Returns list of dicts with:
    - section_number: e.g., "101", "201", "212"
    - title: Section title
    - text: Full section text
    - subsections: List of subsection texts (a), (b), (c), etc.
    """
    sections = []
    
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        print(f"❌ XML parse error: {e}")
        sys.exit(1)
    
    # Find all SECTION elements
    # Structure: CHAPTER > SECTION > subsections
    section_elements = root.findall('.//uscode:SECTION', NAMESPACE)
    
    print(f"📋 Found {len(section_elements)} INA sections")
    
    for idx, section_elem in enumerate(section_elements):
        try:
            # Extract section number from NUM element
            num_elem = section_elem.find('uscode:NUM', NAMESPACE)
            section_number = num_elem.text.strip() if num_elem is not None and num_elem.text else f"Unknown-{idx}"
            
            # Clean section number (remove "§" prefix if present)
            section_number = re.sub(r'^§\s*', '', section_number)
            
            # Extract heading/title
            heading_elem = section_elem.find('uscode:HEADING', NAMESPACE)
            title = heading_elem.text.strip() if heading_elem is not None and heading_elem.text else "Untitled"
            
            # Extract full text (all paragraphs)
            text_parts = []
            for para in section_elem.findall('.//uscode:PARA', NAMESPACE):
                if para.text:
                    text_parts.append(para.text.strip())
            
            full_text = '\n\n'.join(text_parts) if text_parts else ""
            
            # Extract subsections if present
            subsections = []
            for sub in section_elem.findall('.//uscode:SUBSECTION', NAMESPACE):
                sub_text = sub.text.strip() if sub.text else ""
                if sub_text:
                    subsections.append(sub_text)
            
            # If no subsections found, try PARAS within SECTION
            if not subsections:
                for para in section_elem.findall('uscode:PARA', NAMESPACE):
                    if para.text:
                        subsections.append(para.text.strip())
            
            sections.append({
                'section_number': section_number,
                'title': title,
                'text': full_text,
                'subsections': subsections,
            })
            
            if (idx + 1) % 50 == 0:
                print(f"  Parsed {idx + 1}/{len(section_elements)} sections...")
                
        except Exception as e:
            print(f"⚠️  Error parsing section {idx}: {e}")
            continue
    
    return sections


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


def extract_topic_from_section(section_number: str) -> tuple[str, str]:
    """Map INA section number to topic/subtopic.
    
    INA structure:
    - 101-103: Definitions
    - 201-222: Immigration (visas, admission)
    - 231-242: Removal proceedings
    - 301-339: Nationality and naturalization
    """
    try:
        num = int(section_number)
    except ValueError:
        return ("General", "General")
    
    if 101 <= num <= 103:
        return ("Definitions", "Statutory Definitions")
    elif 201 <= num <= 222:
        return ("Immigration", "Visas and Admission")
    elif 231 <= num <= 242:
        return ("Removal", "Deportation Proceedings")
    elif 301 <= num <= 339:
        return ("Nationality", "Naturalization")
    else:
        return ("General", "General")


def register_source(conn) -> int:
    """Register INA as a source."""
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO source_registry (source_name, source_type, publisher, base_url, access_method)
            VALUES (
                'Immigration and Nationality Act',
                'statute',
                'U.S. Congress',
                'https://www.govinfo.gov/app/collection/uscode',
                'bulk_xml'
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
                continue  # Skip empty or very short sections
            
            topic, subtopic = extract_topic_from_section(section_number)
            citation = f"8 U.S.C. § {section_number}"
            
            # Insert into raw_documents
            cur.execute("""
                INSERT INTO raw_documents (
                    source_id, external_id, title, citation, official_url,
                    raw_format, raw_content, content_hash
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    'xml', %s, %s
                )
                RETURNING id;
            """, (
                source_id,
                f"ina-{section_number}",
                title,
                citation,
                f"https://www.govinfo.gov/link/uscode/8/{section_number}",
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
                'U.S. Congress',
                f"https://www.govinfo.gov/link/uscode/8/{section_number}",
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
        # Create dataset version
        cur.execute("""
            INSERT INTO dataset_versions (
                version_name, status, notes, created_by, activated_at
            ) VALUES (
                %s, 'active', %s, %s, NOW()
            )
            RETURNING id;
        """, (
            version_name,
            f"INA ingestion: {chunk_count} chunks from U.S. Code Title 8",
            'automated_ingestion',
        ))
        dataset_id = cur.fetchone()[0]
        
        conn.commit()
        
        print(f"✅ Dataset version created: {version_name} (ID: {dataset_id})")
        return dataset_id


def main():
    parser = argparse.ArgumentParser(description='Ingest INA from GovInfo')
    parser.add_argument('--yes', action='store_true', help='Skip confirmation prompt')
    parser.add_argument('--year', type=str, default='2024', help='Year of US Code edition')
    args = parser.parse_args()
    
    print("📋 INA Ingestion Pipeline")
    print("=" * 60)
    
    # Fetch XML
    xml_content = fetch_ina_xml(args.year)
    print(f"✅ Fetched {len(xml_content):,} bytes of XML")
    
    # Save raw XML for audit
    raw_dir = Path("data/ina/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    xml_path = raw_dir / f"ina-title8-{args.year}.xml"
    xml_path.write_text(xml_content, encoding='utf-8')
    print(f"💾 Saved raw XML to: {xml_path}")
    
    # Parse sections
    print("\n📋 Parsing INA sections...")
    sections = parse_ina_sections(xml_content)
    print(f"✅ Parsed {len(sections)} sections")
    
    # Save preview
    preview_dir = Path("data/ina/preview")
    preview_dir.mkdir(parents=True, exist_ok=True)
    preview_path = preview_dir / "sections-preview.json"
    
    import json
    preview_data = {
        'total_sections': len(sections),
        'ingestion_date': datetime.now().isoformat(),
        'sections': [{
            'section_number': s['section_number'],
            'title': s['title'],
            'text_length': len(s['text']),
            'subsection_count': len(s['subsections']),
        } for s in sections]
    }
    preview_path.write_text(json.dumps(preview_data, indent=2), encoding='utf-8')
    print(f"💾 Saved preview to: {preview_path}")
    
    if not args.yes:
        confirm = input(f"\nProceed with inserting {len(sections)} sections? [y/N] ")
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
        docs, secs, chunks = insert_sections(conn, source_id, sections)
        
        print(f"\n✅ Insertion complete:")
        print(f"   Documents: {docs}")
        print(f"   Sections: {secs}")
        print(f"   Chunks: {chunks}")
        
        # Create dataset version
        dataset_id = create_dataset_version(conn, source_id, chunks)
        
        print(f"\n🎉 INA ingestion complete!")
        print(f"   Next: Run embed_legal_chunks.py to generate embeddings")
        
    finally:
        conn.close()


if __name__ == '__main__':
    main()
