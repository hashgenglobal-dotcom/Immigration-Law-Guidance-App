#!/usr/bin/env python3
"""
BIA Decisions Database Ingestion

Ingests extracted BIA decisions (JSON files) into the legal RAG database.
Creates legal_documents, legal_sections, and legal_chunks with embeddings.

Usage:
    python3 scripts/bia/ingest_bia_decisions.py [--dataset-version-name bia-2026-05-20]
"""

import sys
import json
import logging
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

try:
    import psycopg
except ImportError:
    print("Installing psycopg...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg[binary]"])
    import psycopg

# Add parent directory to path for config import
sys.path.insert(0, str(Path(__file__).parent))
from config import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOGS_DIR / "ingest_bia_decisions.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def get_database_connection():
    """Get database connection with proper URL format."""
    import os
    db_url = os.environ.get('DATABASE_URL', 'postgresql://hash:hash@localhost:54329/immigration_law_dev')
    # Strip SQLAlchemy prefix if present
    db_url = db_url.replace('postgresql+psycopg://', 'postgresql://', 1)
    return psycopg.connect(db_url)


def ensure_source_registry(conn) -> int:
    """Ensure BIA source exists in source_registry."""
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO source_registry (source_name, source_type, publisher, base_url, access_method, is_official)
            VALUES ('BIA Precedent Decisions', 'bia_decisions', 'Executive Office for Immigration Review', 'https://www.justice.gov/eoir/ag-bia-decisions', 'web_scrape', TRUE)
            ON CONFLICT (source_name) DO UPDATE SET 
                source_type = EXCLUDED.source_type,
                publisher = EXCLUDED.publisher,
                base_url = EXCLUDED.base_url,
                updated_at = NOW()
            RETURNING id
        """)
        source_id = cur.fetchone()[0]
        conn.commit()
        logger.info(f"Source registry ID: {source_id}")
        return source_id


def ensure_dataset_version(conn, version_name: str, notes: str) -> int:
    """Create or get dataset version."""
    with conn.cursor() as cur:
        # Check if exists
        cur.execute("SELECT id, status FROM dataset_versions WHERE version_name = %s", (version_name,))
        row = cur.fetchone()
        
        if row:
            logger.info(f"Dataset version '{version_name}' already exists (ID: {row[0]}, status: {row[1]})")
            return row[0]
        
        # Create new
        cur.execute("""
            INSERT INTO dataset_versions (version_name, status, notes, created_by, started_at)
            VALUES (%s, 'building', %s, 'automated', NOW())
            RETURNING id
        """, (version_name, notes))
        dataset_id = cur.fetchone()[0]
        conn.commit()
        logger.info(f"Created dataset version '{version_name}' (ID: {dataset_id})")
        return dataset_id


def chunk_text(text: str, max_length: int = 1500, overlap: int = 200) -> List[str]:
    """Split text into chunks with overlap at sentence boundaries."""
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + max_length
        
        # If we're at the end, just take the rest
        if end >= len(text):
            chunks.append(text[start:])
            break
        
        # Try to break at sentence boundary
        last_period = text.rfind('. ', start, end)
        last_newline = text.rfind('\n', start, end)
        
        break_point = max(last_period, last_newline)
        
        if break_point > start + 500:  # Only break if we have enough content
            end = break_point + 1  # Include the period/newline
        else:
            # Force break at max_length
            last_word = text.rfind(' ', start, end)
            if last_word > start:
                end = last_word
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end - overlap if end < len(text) else len(text)
    
    return chunks


def generate_content_hash(content: str) -> str:
    """Generate SHA256 hash for deduplication."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def ingest_decisions(dataset_version_id: int, source_id: int, json_dir: Path, batch_size: int = 50) -> Dict:
    """Ingest BIA decisions into database."""
    
    stats = {
        'total_files': 0,
        'ingested': 0,
        'skipped': 0,
        'failed': 0,
        'total_chunks': 0
    }
    
    # Get all JSON files
    json_files = list(json_dir.rglob("*.json"))
    stats['total_files'] = len(json_files)
    logger.info(f"Found {len(json_files)} decision JSON files")
    
    conn = get_database_connection()
    
    try:
        batch = []
        
        for json_path in json_files:
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    decision = json.load(f)
                
                batch.append((decision, json_path))
                
                if len(batch) >= batch_size:
                    ingest_batch(conn, dataset_version_id, source_id, batch, stats)
                    batch = []
                    
            except Exception as e:
                logger.error(f"Error reading {json_path}: {e}")
                stats['failed'] += 1
        
        # Process remaining
        if batch:
            ingest_batch(conn, dataset_version_id, source_id, batch, stats)
        
        conn.commit()
        logger.info(f"Ingestion complete: {stats}")
        
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        raise
    finally:
        conn.close()
    
    return stats


def ingest_batch(conn, dataset_version_id: int, source_id: int, batch: List, stats: Dict):
    """Ingest a batch of decisions."""
    
    for decision, json_path in batch:
        try:
            decision_id = decision.get('decision_id', '')
            
            if not decision_id:
                logger.warning(f"Skipping {json_path} - no decision_id")
                stats['skipped'] += 1
                continue
            
            # Check if already ingested (by decision_id in raw_documents)
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT rd.id FROM raw_documents rd
                    JOIN legal_documents ld ON rd.id = ld.raw_document_id
                    WHERE rd.source_id = %s AND rd.external_id = %s
                """, (source_id, decision_id))
                
                if cur.fetchone():
                    logger.debug(f"Skipping {decision_id} - already ingested")
                    stats['skipped'] += 1
                    continue
            
            # Insert raw_document first (required by legal_documents FK)
            with conn.cursor() as cur:
                # Sanitize text - remove NUL bytes (PostgreSQL doesn't allow them)
                full_text = decision.get('full_text', '').replace('\x00', '')
                case_name = decision.get('case_name', f'BIA Decision {decision_id}').replace('\x00', '')
                citation = decision.get('citation', '').replace('\x00', '')
                
                cur.execute("""
                    INSERT INTO raw_documents (
                        source_id, external_id, title, citation,
                        raw_content, content_hash, fetched_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, NOW())
                    RETURNING id
                """, (
                    source_id,
                    decision_id,
                    case_name,
                    citation,
                    full_text,
                    decision.get('sha256', generate_content_hash(full_text))
                ))
                
                raw_doc_id = cur.fetchone()[0]
            
            # Store metadata in legal_documents instead (via publisher field or we can use a separate tracking)
            # For now, metadata goes into legal_documents via effective_date/version_date
            
            # Insert legal_document
            with conn.cursor() as cur:
                year = decision.get('year')
                effective_date = f"{year}-01-01" if year and str(year) != 'None' else None
                version_date = f"{year}-01-01" if year and str(year) != 'None' else None
                
                cur.execute("""
                    INSERT INTO legal_documents (
                        raw_document_id, source_type, title, citation,
                        publisher, effective_date, version_date
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    raw_doc_id,
                    'bia_decisions',
                    decision.get('case_name', f'BIA Decision {decision_id}'),
                    decision.get('citation', ''),
                    'Executive Office for Immigration Review',
                    effective_date,
                    version_date
                ))
                
                doc_id = cur.fetchone()[0]
            
            # Insert legal_section (one section per decision for BIA)
            with conn.cursor() as cur:
                # Sanitize text fields
                section_title = decision.get('case_name', '').replace('\x00', '')
                full_text_sanitized = decision.get('full_text', '').replace('\x00', '')
                citation_text = f"{decision.get('citation', '')} (BIA {decision.get('year', '')})".replace('\x00', '')
                
                cur.execute("""
                    INSERT INTO legal_sections (
                        document_id, section_number, section_title,
                        official_text, cleaned_text, citation
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    doc_id,
                    f"Vol {decision.get('volume', '')} I&N Dec. {decision.get('page', '')}",
                    section_title,
                    full_text_sanitized,
                    full_text_sanitized,
                    citation_text
                ))
                
                section_id = cur.fetchone()[0]
            
            # Create chunks
            full_text = decision.get('full_text', '').replace('\x00', '')
            chunks = chunk_text(full_text)
            
            for chunk_idx, chunk_text_content in enumerate(chunks):
                # Sanitize chunk text
                chunk_text_sanitized = chunk_text_content.replace('\x00', '')
                content_hash = generate_content_hash(chunk_text_sanitized)
                
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO legal_chunks (
                            section_id, chunk_index, chunk_text,
                            citation, topic, subtopic, dataset_version_id,
                            is_active
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
                    """, (
                        section_id,
                        chunk_idx,
                        chunk_text_sanitized,
                        f"{decision.get('citation', '')} (BIA {decision.get('year', '')}) [Chunk {chunk_idx + 1}/{len(chunks)}]".replace('\x00', ''),
                        'BIA Precedent',
                        (decision.get('headnotes', ['Immigration'])[0] if decision.get('headnotes') else 'Immigration')[:100].replace('\x00', ''),
                        dataset_version_id
                    ))
            
            stats['ingested'] += 1
            stats['total_chunks'] += len(chunks)
            
            if stats['ingested'] % 100 == 0:
                logger.info(f"  Progress: {stats['ingested']}/{stats['total_files']} decisions, {stats['total_chunks']} chunks")
            
        except Exception as e:
            logger.error(f"Error ingesting {json_path}: {e}")
            stats['failed'] += 1


def activate_dataset(conn, dataset_version_id: int):
    """Activate the dataset after ingestion."""
    with conn.cursor() as cur:
        # First ensure chunks are active
        cur.execute("""
            UPDATE legal_chunks 
            SET is_active = TRUE 
            WHERE dataset_version_id = %s AND is_active IS NOT TRUE
        """, (dataset_version_id,))
        
        # Then activate dataset version
        cur.execute("""
            UPDATE dataset_versions 
            SET status = 'active', activated_at = NOW()
            WHERE id = %s
        """, (dataset_version_id,))
    
    conn.commit()
    logger.info(f"Dataset version {dataset_version_id} activated")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest BIA decisions into legal RAG database")
    parser.add_argument(
        "--dataset-version-name",
        default=f"bia-{datetime.now().strftime('%Y-%m-%d')}",
        help="Dataset version name (default: bia-YYYY-MM-DD)"
    )
    parser.add_argument(
        "--json-dir",
        type=Path,
        default=config.JSON_DIR,
        help="Directory containing BIA decision JSON files"
    )
    parser.add_argument(
        "--no-activate",
        action="store_true",
        help="Don't activate dataset after ingestion (for testing)"
    )
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("BIA DECISIONS DATABASE INGESTION")
    logger.info(f"Dataset version: {args.dataset_version_name}")
    logger.info(f"JSON directory: {args.json_dir}")
    logger.info("=" * 60)
    
    if not args.json_dir.exists():
        logger.error(f"JSON directory not found: {args.json_dir}")
        return 1
    
    conn = get_database_connection()
    
    try:
        # 1. Ensure source registry
        source_id = ensure_source_registry(conn)
        
        # 2. Create/get dataset version
        notes = f"BIA Precedent Decisions: Volumes 8-29, {datetime.now().strftime('%Y-%m-%d')}"
        dataset_id = ensure_dataset_version(conn, args.dataset_version_name, notes)
        
        # 3. Ingest decisions
        stats = ingest_decisions(dataset_id, source_id, args.json_dir)
        
        # 4. Activate dataset
        if not args.no_activate:
            activate_dataset(conn, dataset_id)
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("INGESTION COMPLETE")
        logger.info("=" * 60)
        logger.info(f"  Total files: {stats['total_files']}")
        logger.info(f"  Ingested: {stats['ingested']} decisions")
        logger.info(f"  Skipped: {stats['skipped']} (already exists)")
        logger.info(f"  Failed: {stats['failed']}")
        logger.info(f"  Total chunks: {stats['total_chunks']}")
        logger.info(f"  Dataset version: {args.dataset_version_name} (ID: {dataset_id})")
        logger.info("=" * 60)
        
        return 0
        
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
