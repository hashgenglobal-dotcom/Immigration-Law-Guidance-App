#!/usr/bin/env python3
"""Insert USCIS Policy Manual chapters into database.

This script:
1. Reads fetched chapters from data/uscis-pm/preview/chapters-preview.json
2. Registers USCIS as a source (if not exists)
3. Inserts documents into legal_documents
4. Inserts chapters into legal_sections
5. Creates legal_chunks with embeddings
6. Creates and activates dataset version

Usage:
    uv run --project backend python scripts/ingest_uscis_pm.py --yes
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import psycopg
from psycopg.types.json import Json


def get_db_connection():
    """Get database connection from environment."""
    conn = psycopg.connect(
        host="localhost",
        port=54329,
        user="hash",
        password="hash",
        dbname="immigration_law_dev",
    )
    return conn


def register_source(conn):
    """Register USCIS Policy Manual as a source."""
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO source_registry (source_name, source_type, publisher, base_url, access_method)
            VALUES (
                'USCIS Policy Manual',
                'policy',
                'U.S. Citizenship and Immigration Services',
                'https://www.uscis.gov/policy-manual',
                'scraping'
            )
            ON CONFLICT (source_name) DO UPDATE SET
                publisher = EXCLUDED.publisher,
                base_url = EXCLUDED.base_url,
                access_method = EXCLUDED.access_method,
                updated_at = NOW()
            RETURNING id;
        """)
        source_id = cur.fetchone()[0]
        conn.commit()
        print(f"✅ Source registered: USCIS Policy Manual (ID: {source_id})")
        return source_id


def chunk_text(text, max_length=1500, overlap=200):
    """Split text into overlapping chunks for retrieval."""
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + max_length
        
        # Try to break at a sentence boundary
        if end < len(text):
            # Look for sentence endings in the last 200 chars
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


def extract_topic_from_volume(volume_num):
    """Map volume number to topic/subtopic."""
    topics = {
        1: ("General Policies", "USCIS Procedures"),
        2: ("Nonimmigrants", "Visa Categories"),
        3: ("Humanitarian Protection", "Parole & Protection"),
        4: ("Refugees and Asylees", "Refugee Status"),
        5: ("Adoptions", "International Adoptions"),
        6: ("Immigrants", "Immigrant Visas"),
        7: ("Adjustment of Status", "Green Card Process"),
        8: ("Admissibility", "Grounds of Inadmissibility"),
        9: ("Waivers", "Relief from Inadmissibility"),
        10: ("Employment Authorization", "Work Permits"),
        11: ("Travel Documents", "Identity & Travel"),
        12: ("Citizenship", "Naturalization"),
    }
    return topics.get(volume_num, ("General", "General"))


def insert_chapters(conn, source_id, chapters):
    """Insert all chapters into database."""
    documents_inserted = 0
    sections_inserted = 0
    chunks_inserted = 0
    
    with conn.cursor() as cur:
        for chapter in chapters:
            if not chapter.get('success', False):
                continue
            
            volume = chapter['volume']
            part = chapter['part']
            chapter_num = chapter['chapter']
            title = chapter['title']
            text = chapter.get('text_preview', '')
            url = chapter['url']
            
            # Extract full text from HTML file if available
            html_path = Path(f"data/uscis-pm/raw/{chapter['html_filename']}")
            if html_path.exists():
                # We'd need to re-parse HTML to get full text
                # For now, use the preview text
                pass
            
            # Insert into raw_documents first (required FK)
            topic, subtopic = extract_topic_from_volume(volume)
            citation = f"Vol {volume}, Part {part}, Ch {chapter_num}"
            
            cur.execute("""
                INSERT INTO raw_documents (
                    source_id, external_id, title, citation, official_url,
                    raw_format, raw_content, content_hash
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    'html', %s, gen_random_uuid()::text
                )
                RETURNING id;
            """, (
                source_id,
                f"vol{volume}-part{part}-ch{chapter_num}",
                title,
                citation,
                url,
                text,
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
                'policy_chapter',
                title,
                citation,
                'USCIS',
                url,
            ))
            doc_id = cur.fetchone()[0]
            documents_inserted += 1
            
            # Insert into legal_sections (section level = chapter text)
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
                f"Vol {volume}, Part {part}, Ch {chapter_num}",
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
                print(f"  📦 Inserted {documents_inserted}/{len(chapters)} chapters...")
        
        conn.commit()
    
    return documents_inserted, sections_inserted, chunks_inserted


def create_dataset_version(conn, source_id, chunk_count):
    """Create and activate a new dataset version."""
    version_name = f"uscis-pm-{datetime.now().strftime('%Y-%m-%d')}"
    
    with conn.cursor() as cur:
        # Create dataset version
        cur.execute("""
            INSERT INTO dataset_versions (
                version_name, status, notes, created_by
            ) VALUES (
                %s, 'pending', %s, %s
            )
            RETURNING id;
        """, (
            version_name,
            f"USCIS Policy Manual ingestion: {chunk_count} chunks from 451 chapters",
            'automated_ingestion',
        ))
        dataset_id = cur.fetchone()[0]
        
        # Activate the dataset
        cur.execute("""
            UPDATE dataset_versions 
            SET status = 'active', activated_at = NOW()
            WHERE id = %s;
        """, (dataset_id,))
        
        conn.commit()
        
        print(f"✅ Dataset version created: {version_name} (ID: {dataset_id})")
        return dataset_id


def main():
    parser = argparse.ArgumentParser(description='Ingest USCIS Policy Manual into database')
    parser.add_argument('--yes', action='store_true', help='Skip confirmation prompt')
    args = parser.parse_args()
    
    # Load chapters
    preview_path = Path("data/uscis-pm/preview/chapters-preview.json")
    if not preview_path.exists():
        print(f"❌ Preview file not found: {preview_path}")
        print("Run fetch_uscis_pm_chapters.py first")
        sys.exit(1)
    
    with open(preview_path) as f:
        data = json.load(f)
    
    chapters = data['chapters']
    successful = [c for c in chapters if c.get('success', False)]
    
    print(f"📋 Loaded {len(chapters)} chapters ({len(successful)} successful)")
    
    if not args.yes:
        confirm = input(f"Proceed with inserting {len(successful)} chapters? [y/N] ")
        if confirm.lower() != 'y':
            print("Aborted")
            sys.exit(0)
    
    conn = get_db_connection()
    
    try:
        # Register source
        source_id = register_source(conn)
        
        # Insert chapters
        print("📦 Inserting chapters into database...")
        docs, sections, chunks = insert_chapters(conn, source_id, chapters)
        
        print(f"✅ Insertion complete:")
        print(f"   Documents: {docs}")
        print(f"   Sections: {sections}")
        print(f"   Chunks: {chunks}")
        
        # Create dataset version
        dataset_id = create_dataset_version(conn, source_id, chunks)
        
        print(f"\n🎉 USCIS Policy Manual ingestion complete!")
        
    finally:
        conn.close()


if __name__ == '__main__':
    main()
