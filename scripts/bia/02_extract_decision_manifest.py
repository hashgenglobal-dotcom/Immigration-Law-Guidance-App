#!/usr/bin/env python3
"""
Step 2: Extract Decision Manifest from Volume Pages

For each volume page, extract all precedent decisions with metadata.

Output:
- data/raw/bia/bia_decision_manifest.csv
- data/raw/bia/bia_decision_manifest.json
"""

import sys
import json
import logging
import re
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import pandas as pd

# Add parent directory to path for config import
sys.path.insert(0, str(Path(__file__).parent))
from config import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOGS_DIR / "02_extract_decisions.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class DecisionInfo:
    """Represents a single BIA precedent decision."""
    volume_number: int
    decision_id: str  # e.g., "4193"
    case_name: str  # e.g., "I-B-M-S-"
    full_citation: str  # e.g., "29 I&N Dec. 628 (BIA 2026)"
    iandn_volume: int  # e.g., 29
    iandn_page: int  # e.g., 628
    tribunal: str  # "BIA" or "AG"
    year: int
    pdf_url: str
    source_volume_url: str
    headnotes: List[str] = field(default_factory=list)
    extraction_status: str = "pending"
    extraction_timestamp: Optional[str] = None
    error_message: Optional[str] = None


def parse_citation(citation_text: str) -> Dict:
    """
    Parse citation like "29 I&N Dec. 628 (BIA 2026)".
    Returns dict with volume, page, tribunal, year.
    """
    result = {
        'iandn_volume': None,
        'iandn_page': None,
        'tribunal': None,
        'year': None
    }
    
    # Pattern: "29 I&N Dec. 628 (BIA 2026)"
    match = re.search(r'(\d+)\s+I&N\s+Dec\.\s+(\d+)\s+\((\w+)\s+(\d{4})\)', citation_text)
    if match:
        result['iandn_volume'] = int(match.group(1))
        result['iandn_page'] = int(match.group(2))
        result['tribunal'] = match.group(3)
        result['year'] = int(match.group(4))
    
    return result


def extract_case_name(citation_text: str) -> str:
    """Extract case name from text like "MATTER OF I-B-M-S-, 29 I&N Dec. 628 (BIA 2026)"."""
    # Pattern: "MATTER OF X-Y-Z-" or just "X-Y-Z-"
    match = re.search(r'(?:MATTER\s+OF\s+)?([A-Z][A-Z0-9\-]+),\s+\d+\s+I&N', citation_text)
    if match:
        return match.group(1)
    
    # Fallback: first part before comma
    if ',' in citation_text:
        return citation_text.split(',')[0].strip()
    
    return citation_text


def parse_decision_block(block_element, volume_number: int, source_url: str) -> Optional[DecisionInfo]:
    """
    Parse a single decision block from the volume page.
    
    Expected structure (from DOJ Volume 29 page):
    - Table with two cells: case citation and PDF link
    - Followed by paragraph(s) with headnotes
    - Then a separator
    
    Example:
    <table>
      <tr>
        <td><strong>I-B-M-S-</strong>, 29 I&N Dec. 628 (BIA 2026)</td>
        <td><a href="...">ID 4193</a> (PDF)</td>
      </tr>
    </table>
    <paragraph>(1) The closer in time...</paragraph>
    <paragraph>(2) Off-the-record...</paragraph>
    <separator/>
    """
    # Find the PDF link (ID ####)
    pdf_link = block_element.find('a', href=True, string=re.compile(r'ID\s+\d+', re.IGNORECASE))
    if not pdf_link:
        return None
    
    # Extract decision ID from link text
    id_match = re.search(r'ID\s+(\d+)', pdf_link.get_text(strip=True), re.IGNORECASE)
    if not id_match:
        return None
    
    decision_id = id_match.group(1)
    pdf_url = config.BASE_URL + pdf_link['href'] if pdf_link['href'].startswith('/') else pdf_link['href']
    
    # Find the case citation from the table cell
    table = pdf_link.find_parent('table')
    if not table:
        return None
    
    # Find all text in the first cell (case name and citation)
    cells = table.find_all('td')
    if not cells:
        return None
    
    citation_text = cells[0].get_text(strip=True) if len(cells) > 0 else ""
    
    # Clean up citation text (remove extra whitespace)
    citation_text = re.sub(r'\s+', ' ', citation_text).strip()
    
    # Parse citation
    citation_data = parse_citation(citation_text)
    case_name = extract_case_name(citation_text)
    
    # Extract headnotes (paragraphs between table and separator)
    headnotes = []
    current = table
    while current and current.next_sibling:
        current = current.next_sibling
        
        # Stop at separator
        if hasattr(current, 'name') and current.name == 'hr':
            break
        
        # Collect headnote paragraphs
        if hasattr(current, 'name') and current.name == 'p':
            text = current.get_text(strip=True)
            if text and not text.startswith('Updated') and len(text) > 20:
                # Clean up whitespace
                text = re.sub(r'\s+', ' ', text)
                headnotes.append(text)
    
    # Build decision info
    decision = DecisionInfo(
        volume_number=volume_number,
        decision_id=decision_id,
        case_name=case_name,
        full_citation=citation_text,
        iandn_volume=citation_data.get('iandn_volume', volume_number),
        iandn_page=citation_data.get('iandn_page', 0),
        tribunal=citation_data.get('tribunal', 'BIA'),
        year=citation_data.get('year', datetime.now().year),
        pdf_url=pdf_url,
        source_volume_url=source_url,
        headnotes=headnotes,
        extraction_status="success",
        extraction_timestamp=datetime.utcnow().isoformat()
    )
    
    return decision


def fetch_volume_page(url: str, session: requests.Session) -> Optional[BeautifulSoup]:
    """Fetch and parse a volume page."""
    try:
        response = session.get(
            url,
            headers={"User-Agent": config.USER_AGENT},
            timeout=config.REQUEST_TIMEOUT
        )
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return None


def extract_decisions_from_volume(soup: BeautifulSoup, volume_number: int, source_url: str) -> List[DecisionInfo]:
    """Extract all decisions from a volume page."""
    decisions = []
    
    # Find all tables that contain ID links
    for table in soup.find_all('table'):
        # Check if this table has an ID link
        id_link = table.find('a', href=True, string=re.compile(r'ID\s+\d+', re.IGNORECASE))
        if not id_link:
            continue
        
        # Parse this decision block (pass the table, not the link)
        decision = parse_decision_block(table, volume_number, source_url)
        if decision:
            decisions.append(decision)
    
    logger.info(f"Extracted {len(decisions)} decisions from Volume {volume_number}")
    return decisions


def process_volumes(test_mode: bool = False) -> List[DecisionInfo]:
    """
    Process all volumes from the manifest and extract decisions.
    """
    logger.info("Starting decision extraction...")
    
    # Load volume manifest
    if not config.VOLUME_MANIFEST_JSON.exists():
        logger.error("Volume manifest not found. Run 01_discover_volumes.py first.")
        raise FileNotFoundError(f"Volume manifest not found: {config.VOLUME_MANIFEST_JSON}")
    
    with open(config.VOLUME_MANIFEST_JSON, 'r', encoding='utf-8') as f:
        volumes = json.load(f)
    
    # Filter for test mode
    if test_mode:
        original_count = len(volumes)
        test_vols = config.TEST_VOLUMES or []
        if test_vols:  # Only filter if test volumes specified
            volumes = [v for v in volumes if str(v['volume_number']) in test_vols]
        logger.info(f"Test mode: processing {len(volumes)} of {original_count} volumes")
    
    # Create session
    session = requests.Session()
    session.headers.update({
        "User-Agent": config.USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive"
    })
    
    all_decisions = []
    
    for vol in tqdm(volumes, desc="Extracting decisions"):
        volume_number = vol['volume_number']
        volume_url = vol.get('resolved_url') or vol['volume_page_url']
        
        logger.info(f"Processing Volume {volume_number}: {volume_url}")
        
        # Fetch volume page
        soup = fetch_volume_page(volume_url, session)
        if not soup:
            logger.warning(f"Skipping Volume {volume_number} - failed to fetch")
            continue
        
        # Extract decisions
        decisions = extract_decisions_from_volume(soup, volume_number, volume_url)
        all_decisions.extend(decisions)
        
        # Rate limiting
        import time
        time.sleep(config.REQUEST_DELAY)
    
    logger.info(f"Extraction complete: {len(all_decisions)} total decisions")
    return all_decisions


def save_manifests(decisions: List[DecisionInfo]):
    """Save decision manifests to CSV and JSON."""
    
    # Handle empty decisions
    if not decisions:
        logger.warning("No decisions to save")
        pd.DataFrame(columns=DECISION_COLUMNS).to_csv(config.DECISION_MANIFEST_CSV, index=False)
        with open(config.DECISION_MANIFEST_JSON, 'w') as f:
            json.dump([], f, indent=2)
        print("\n" + "="*60)
        print("DECISION EXTRACTION SUMMARY")
        print("="*60)
        print("Total decisions extracted: 0")
        print(f"\nOutput files:")
        print(f"  - {config.DECISION_MANIFEST_CSV}")
        print(f"  - {config.DECISION_MANIFEST_JSON}")
        print("="*60)
        return
    
    # Convert to dicts
    decision_dicts = [asdict(d) for d in decisions]
    
    # Save CSV (flatten headnotes list)
    csv_rows = []
    for d in decision_dicts:
        row = d.copy()
        row['headnotes'] = ' ||| '.join(row['headnotes'])  # Join with delimiter
        csv_rows.append(row)
    
    df = pd.DataFrame(csv_rows)
    df.to_csv(config.DECISION_MANIFEST_CSV, index=False)
    logger.info(f"Saved CSV: {config.DECISION_MANIFEST_CSV}")
    
    # Save JSON
    with open(config.DECISION_MANIFEST_JSON, 'w', encoding='utf-8') as f:
        json.dump(decision_dicts, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved JSON: {config.DECISION_MANIFEST_JSON}")
    
    # Print summary
    print("\n" + "="*60)
    print("DECISION EXTRACTION SUMMARY")
    print("="*60)
    print(f"Total decisions extracted: {len(decisions)}")
    print(f"Volume range: {min(d.volume_number for d in decisions)} - {max(d.volume_number for d in decisions)}")
    print(f"Decision ID range: {min(d.decision_id for d in decisions)} - {max(d.decision_id for d in decisions)}")
    print(f"Decisions with headnotes: {sum(1 for d in decisions if d.headnotes)}")
    print(f"\nOutput files:")
    print(f"  - {config.DECISION_MANIFEST_CSV}")
    print(f"  - {config.DECISION_MANIFEST_JSON}")
    print("="*60)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract BIA decisions from volume pages")
    parser.add_argument("--test", action="store_true", help="Enable test mode (only test volumes)")
    args = parser.parse_args()
    
    test_mode = args.test or config.TEST_MODE
    
    try:
        decisions = process_volumes(test_mode=test_mode)
        save_manifests(decisions)
        return 0
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
