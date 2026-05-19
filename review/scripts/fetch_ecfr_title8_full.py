#!/usr/bin/env python3
"""Fetch FULL eCFR Title 8 and insert all sections into the database.

This script ingests the COMPLETE Title 8 (Aliens and Nationality) from eCFR,
not just the 5-section sample. It:

1. Fetches the latest Title 8 XML from eCFR API
2. Parses EVERY section (hundreds, not just 5)
3. Inserts into PostgreSQL: dataset_versions, legal_documents, legal_sections, legal_chunks
4. Generates embeddings via local Ollama (nomic-embed-text)
5. Activates the dataset for retrieval

Privacy / Safety
----------------
- ONLY public eCFR legal text (no user data)
- All processing local (Ollama embeddings)
- No external AI APIs called

Usage
-----
    # Full ingestion with embeddings and activation
    uv run --project backend python scripts/fetch_ecfr_title8_full.py --yes

    # Fetch and insert only (no embeddings, no activation)
    uv run --project backend python scripts/fetch_ecfr_title8_full.py --no-embed --no-activate

    # Pin to specific date
    uv run --project backend python scripts/fetch_ecfr_title8_full.py --date 2026-05-11 --yes
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.request
from dataclasses import asdict, dataclass
from datetime import date as date_cls
from pathlib import Path
from typing import Any, Iterable, List, Tuple
from xml.etree import ElementTree as ET

import httpx

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ECFR_TITLES_URL = "https://www.ecfr.gov/api/versioner/v1/titles"
ECFR_VERSIONER_URL = "https://www.ecfr.gov/api/versioner/v1/full/{date}/title-8.xml"
ECFR_SECTION_URL = "https://www.ecfr.gov/current/title-8/section-{section}"
TITLE8_NUMBER = 8

DEFAULT_OUTPUT_DIR = Path("data/ecfr")
TEXT_SNIPPET_CHARS = 1200
HTTP_TIMEOUT_SECONDS = 120  # Title 8 XML is large
USER_AGENT = (
    "Immigration-Law-Guidance-App/1.0 "
    "(development; full Title 8 ingestion; contact: hash@hashgen.global)"
)

# Chunking config
CHUNK_SIZE_CHARS = 1500  # Split large sections into chunks for embeddings
CHUNK_OVERLAP_CHARS = 200

# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class SectionData:
    """One parsed eCFR section."""
    citation: str
    section_number: str
    title: str | None
    official_url: str
    full_text: str
    text_length: int
    source_date: str


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch FULL eCFR Title 8 and ingest into database.",
    )
    parser.add_argument(
        "--date",
        default=None,
        help="eCFR snapshot date YYYY-MM-DD. Default: auto-detect latest.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR}).",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        default=False,
        help="Confirm database insertion (required for writes).",
    )
    parser.add_argument(
        "--no-embed",
        action="store_true",
        default=False,
        help="Skip embedding generation.",
    )
    parser.add_argument(
        "--no-activate",
        action="store_true",
        default=False,
        help="Skip dataset activation.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit to first N sections (for testing).",
    )
    return parser.parse_args(argv)


def _validate_date(value: str) -> str:
    try:
        date_cls.fromisoformat(value)
    except ValueError as exc:
        raise SystemExit(f"ERROR: --date must be YYYY-MM-DD, got {value!r} ({exc})")
    return value


# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------


def fetch_latest_title8_issue_date() -> str:
    """Get latest issue date for Title 8 from eCFR API."""
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    try:
        response = httpx.get(ECFR_TITLES_URL, headers=headers, timeout=HTTP_TIMEOUT_SECONDS)
    except httpx.RequestError as exc:
        raise SystemExit(f"ERROR: network failure fetching {ECFR_TITLES_URL}: {type(exc).__name__}")

    if response.status_code != 200:
        snippet = response.text[:300].replace("\n", " ")
        raise SystemExit(f"ERROR: eCFR titles API returned HTTP {response.status_code}\n       Response: {snippet}")

    try:
        payload = response.json()
    except ValueError as exc:
        raise SystemExit(f"ERROR: eCFR titles API returned non-JSON body ({exc}). Retry with --date YYYY-MM-DD.")

    titles = payload.get("titles") if isinstance(payload, dict) else None
    if not isinstance(titles, list):
        raise SystemExit("ERROR: eCFR titles API JSON did not contain a 'titles' list.")

    title8 = next((t for t in titles if isinstance(t, dict) and t.get("number") == TITLE8_NUMBER), None)
    if title8 is None:
        raise SystemExit("ERROR: eCFR titles API response did not include Title 8.")

    latest_issue_date = title8.get("latest_issue_date")
    if not isinstance(latest_issue_date, str) or not latest_issue_date.strip():
        raise SystemExit("ERROR: eCFR titles API did not return latest_issue_date for Title 8.")

    return _validate_date(latest_issue_date.strip())


def fetch_title8_xml(snapshot_date: str) -> tuple[str, bytes]:
    """Fetch full Title 8 XML."""
    url = ECFR_VERSIONER_URL.format(date=snapshot_date)
    headers = {"User-Agent": USER_AGENT, "Accept": "application/xml"}
    try:
        response = httpx.get(url, headers=headers, timeout=HTTP_TIMEOUT_SECONDS)
    except httpx.RequestError as exc:
        raise SystemExit(f"ERROR: network failure fetching {url}: {type(exc).__name__}")

    if response.status_code != 200:
        snippet = response.text[:300].replace("\n", " ")
        raise SystemExit(f"ERROR: eCFR API returned HTTP {response.status_code} for {url}\n       Response: {snippet}")

    return url, response.content


# ---------------------------------------------------------------------------
# Parse
# ---------------------------------------------------------------------------


_WHITESPACE_RE = re.compile(r"\s+")


def _clean_text(raw: str) -> str:
    """Collapse whitespace and strip."""
    return _WHITESPACE_RE.sub(" ", raw).strip()


def _iter_all_sections(root: ET.Element) -> Iterable[ET.Element]:
    """Yield ALL section elements in the XML tree."""
    for elem in root.iter():
        if elem.get("TYPE") == "SECTION" and elem.get("N"):
            yield elem


def _extract_heading(section_elem: ET.Element) -> str | None:
    """Get HEAD text from section."""
    head = section_elem.find("HEAD")
    if head is None:
        return None
    text = _clean_text("".join(head.itertext()))
    return text or None


def _extract_section_text(section_elem: ET.Element) -> str:
    """Get all text from section."""
    return _clean_text("".join(section_elem.itertext()))


def parse_all_sections(xml_bytes: bytes, source_date: str, limit: int | None = None) -> List[SectionData]:
    """Parse ALL sections from Title 8 XML."""
    root = ET.fromstring(xml_bytes)
    sections = []
    
    for i, elem in enumerate(_iter_all_sections(root)):
        if limit and i >= limit:
            break
            
        section_number = elem.get("N", "").strip()
        if not section_number:
            continue
        
        heading = _extract_heading(elem)
        full_text = _extract_section_text(elem)
        
        if len(full_text) < 50:  # Skip trivial sections
            continue
        
        citation = f"8 CFR § {section_number}"
        official_url = ECFR_SECTION_URL.format(section=section_number)
        
        sections.append(SectionData(
            citation=citation,
            section_number=section_number,
            title=heading,
            official_url=official_url,
            full_text=full_text,
            text_length=len(full_text),
            source_date=source_date,
        ))
    
    return sections


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------


def chunk_section_text(text: str, section_number: str, chunk_size: int = CHUNK_SIZE_CHARS, overlap: int = CHUNK_OVERLAP_CHARS) -> List[Tuple[str, int]]:
    """Split large section text into overlapping chunks."""
    if len(text) <= chunk_size:
        return [(text, 0)]
    
    chunks = []
    start = 0
    chunk_idx = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk_text = text[start:end]
        
        # Try to break at sentence boundary
        if end < len(text):
            last_period = chunk_text.rfind(".")
            if last_period > chunk_size // 2:
                chunk_text = chunk_text[:last_period + 1]
                end = start + last_period + 1
        
        chunks.append((chunk_text.strip(), chunk_idx))
        chunk_idx += 1
        start = end - overlap if end < len(text) else len(text)
    
    return chunks


# ---------------------------------------------------------------------------
# Database insertion
# ---------------------------------------------------------------------------


def insert_full_title8(
    db_url: str,
    sections: List[SectionData],
    source_date: str,
    source_url: str,
    xml_bytes: bytes,
) -> dict[str, Any]:
    """Insert all sections into database."""
    import psycopg
    
    xml_sha256 = hashlib.sha256(xml_bytes).hexdigest()
    version_name = f"ecfr-title8-full-{source_date}"
    xml_text = xml_bytes.decode("utf-8", errors="replace")
    
    counters = {"inserted": 0, "reused": 0, "chunks": 0}
    section_ids = []
    
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            # Get source_registry ID
            cur.execute("SELECT id FROM source_registry WHERE source_name = %s", ("eCFR Title 8",))
            row = cur.fetchone()
            if row is None:
                cur.execute(
                    "INSERT INTO source_registry (source_name, source_type, description) VALUES (%s, %s, %s) RETURNING id",
                    ("eCFR Title 8", "federal_regulation", "Electronic Code of Federal Regulations Title 8"),
                )
                source_id = cur.fetchone()[0]
            else:
                source_id = row[0]
            
            # Create dataset version
            cur.execute("SELECT id FROM dataset_versions WHERE version_name = %s", (version_name,))
            row = cur.fetchone()
            if row:
                dataset_version_id = row[0]
                counters["reused"] += 1
            else:
                cur.execute(
                    """INSERT INTO dataset_versions (version_name, status, notes, created_by)
                       VALUES (%s, 'building', 'Full Title 8 ingestion', 'cli') RETURNING id""",
                    (version_name,),
                )
                dataset_version_id = cur.fetchone()[0]
                counters["inserted"] += 1
            
            # Create raw document
            cur.execute("SELECT id FROM raw_documents WHERE content_hash = %s", (xml_sha256,))
            row = cur.fetchone()
            if row:
                raw_doc_id = row[0]
            else:
                cur.execute(
                    """INSERT INTO raw_documents (source_id, external_id, title, citation, official_url, raw_format, raw_content, content_hash, effective_date, version_date)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                    (source_id, f"title-8-full-{source_date}", "eCFR Title 8 — Aliens and Nationality", "8 CFR Title 8", source_url, "xml", xml_text, xml_sha256, source_date, source_date),
                )
                raw_doc_id = cur.fetchone()[0]
            
            # Create legal document
            cur.execute("SELECT id FROM legal_documents WHERE raw_document_id = %s AND citation = %s", (raw_doc_id, "8 CFR Title 8"))
            row = cur.fetchone()
            if row:
                legal_doc_id = row[0]
            else:
                cur.execute(
                    """INSERT INTO legal_documents (raw_document_id, source_type, title, citation, jurisdiction, publisher, official_url, effective_date, version_date)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                    (raw_doc_id, "regulation", "eCFR Title 8 Full", "8 CFR Title 8", "federal", "eCFR", source_url, source_date, source_date),
                )
                legal_doc_id = cur.fetchone()[0]
            
            # Insert sections and chunks
            for sec in sections:
                # Insert legal_section (uses document_id, not legal_document_id)
                cur.execute(
                    """INSERT INTO legal_sections (document_id, section_number, section_title, citation, official_text, cleaned_text, topic, official_url, effective_date, version_date)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                    (legal_doc_id, sec.section_number, sec.title, sec.citation, sec.full_text, sec.full_text, sec.section_number, sec.official_url, source_date, source_date),
                )
                section_id = cur.fetchone()[0]
                section_ids.append(section_id)
                
                # Create chunks (uses section_id, not legal_section_id)
                chunks = chunk_section_text(sec.full_text, sec.section_number)
                for chunk_text, chunk_idx in chunks:
                    cur.execute(
                        """INSERT INTO legal_chunks (section_id, dataset_version_id, chunk_index, chunk_text, citation, topic, official_url)
                           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                        (section_id, dataset_version_id, chunk_idx, chunk_text, sec.citation, sec.section_number, sec.official_url),
                    )
                    counters["chunks"] += 1
            
            # Update dataset version status
            cur.execute(
                "UPDATE dataset_versions SET status = 'ready', completed_at = NOW() WHERE id = %s",
                (dataset_version_id,),
            )
            
            conn.commit()
    
    return {
        "dataset_version_id": dataset_version_id,
        "legal_doc_id": legal_doc_id,
        "section_count": len(sections),
        "chunk_count": counters["chunks"],
        "version_name": version_name,
    }


# ---------------------------------------------------------------------------
# Embeddings
# ---------------------------------------------------------------------------


def generate_embeddings(db_url: str, dataset_version_id: int, ollama_url: str = "http://localhost:11434", model: str = "nomic-embed-text") -> int:
    """Generate embeddings for all chunks without embeddings."""
    import psycopg
    
    embedded_count = 0
    
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            # Get chunks without embeddings
            cur.execute(
                """SELECT id, chunk_text FROM legal_chunks 
                   WHERE dataset_version_id = %s AND embedding IS NULL""",
                (dataset_version_id,),
            )
            chunks = cur.fetchall()
            
            if not chunks:
                print("  → All chunks already have embeddings")
                return 0
            
            print(f"  → Generating embeddings for {len(chunks)} chunks...")
            
            for chunk_id, chunk_text in chunks:
                # Call Ollama
                req_data = {"model": model, "prompt": chunk_text}
                req = urllib.request.Request(
                    f"{ollama_url}/api/embeddings",
                    data=json.dumps(req_data).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                )
                try:
                    with urllib.request.urlopen(req, timeout=60) as resp:
                        result = json.loads(resp.read().decode("utf-8"))
                        embedding = result.get("embedding")
                except Exception as exc:
                    print(f"  WARNING: Failed to embed chunk {chunk_id}: {exc}")
                    continue
                
                if not embedding or len(embedding) != 768:
                    print(f"  WARNING: Invalid embedding for chunk {chunk_id}")
                    continue
                
                # Update chunk
                cur.execute(
                    "UPDATE legal_chunks SET embedding = %s WHERE id = %s",
                    (embedding, chunk_id),
                )
                embedded_count += 1
                
                if embedded_count % 50 == 0:
                    print(f"    ... {embedded_count}/{len(chunks)} chunks embedded")
            
            conn.commit()
    
    print(f"  → Embedded {embedded_count} chunks")
    return embedded_count


# ---------------------------------------------------------------------------
# Activation
# ---------------------------------------------------------------------------


def activate_dataset(db_url: str, dataset_version_id: int) -> bool:
    """Activate the dataset."""
    import psycopg
    
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            # Deactivate current active dataset (set status back to ready)
            cur.execute("""
                UPDATE dataset_versions 
                SET status = 'ready', activated_at = NULL
                WHERE status = 'active'
            """)
            
            # Activate new dataset
            cur.execute(
                """UPDATE dataset_versions 
                   SET status = 'active', activated_at = NOW()
                   WHERE id = %s""",
                (dataset_version_id,),
            )
            
            conn.commit()
    
    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    
    # Resolve date
    if args.date:
        source_date = _validate_date(args.date)
        print(f"Using pinned date: {source_date}")
    else:
        source_date = fetch_latest_title8_issue_date()
        print(f"Latest Title 8 issue date: {source_date}")
    
    # Fetch XML
    print(f"\nFetching Title 8 XML from eCFR...")
    source_url, xml_bytes = fetch_title8_xml(source_date)
    print(f"  → Downloaded {len(xml_bytes):,} bytes")
    
    # Save raw XML
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = output_dir / f"raw_title8_{source_date}.xml"
    raw_path.write_bytes(xml_bytes)
    print(f"  → Saved to {raw_path}")
    
    # Parse all sections
    print(f"\nParsing all sections...")
    sections = parse_all_sections(xml_bytes, source_date, limit=args.limit)
    print(f"  → Found {len(sections)} sections")
    
    if not sections:
        print("ERROR: No sections parsed. Check XML structure.")
        return 1
    
    # Database insertion
    if not args.yes:
        print("\n--- DRY RUN MODE ---")
        print(f"Would insert {len(sections)} sections")
        print(f"Would create ~{sum(len(chunk_section_text(s.full_text, s.section_number)) for s in sections)} chunks")
        print("\nPass --yes to insert into database.")
        return 0
    
    # Get database URL
    from pathlib import Path as pPath
    env_path = pPath("backend/.env")
    db_url = None
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("DATABASE_URL="):
                db_url = line.split("=", 1)[1].strip().strip('"\'')
                # Strip SQLAlchemy prefix if present
                if db_url.startswith("postgresql+psycopg://"):
                    db_url = db_url.replace("postgresql+psycopg://", "postgresql://", 1)
                break
    if not db_url:
        import os
        db_url = os.environ.get("DATABASE_URL")
        if db_url and db_url.startswith("postgresql+psycopg://"):
            db_url = db_url.replace("postgresql+psycopg://", "postgresql://", 1)
    if not db_url:
        print("ERROR: DATABASE_URL not found. Set in backend/.env or environment.")
        return 1
    
    print(f"\nInserting into database...")
    result = insert_full_title8(db_url, sections, source_date, source_url, xml_bytes)
    print(f"  → Dataset version: {result['version_name']} (ID: {result['dataset_version_id']})")
    print(f"  → Sections: {result['section_count']}")
    print(f"  → Chunks: {result['chunk_count']}")
    
    # Generate embeddings
    if not args.no_embed:
        print(f"\nGenerating embeddings...")
        embedded = generate_embeddings(db_url, result["dataset_version_id"])
        if embedded == 0:
            print("  → Skipping (already embedded or error)")
    
    # Activate dataset
    if not args.no_activate:
        print(f"\nActivating dataset...")
        activate_dataset(db_url, result["dataset_version_id"])
        print(f"  → Dataset activated ✓")
    
    print(f"\n✅ Full Title 8 ingestion complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
