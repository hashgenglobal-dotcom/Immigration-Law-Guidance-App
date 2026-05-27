#!/usr/bin/env python3
"""
Step 4: Extract Text from BIA PDFs

Uses PyMuPDF to extract text from downloaded PDFs.
Creates both plain text and structured JSON outputs.

Output:
- data/processed/bia/text/volume_{volume}/ID_{decision_id}.txt
- data/processed/bia/json/volume_{volume}/ID_{decision_id}.json
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict

import pandas as pd

try:
    import pymupdf  # PyMuPDF
except ImportError:
    print("PyMuPDF not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pymupdf"])
    import pymupdf

# Add parent directory to path for config import
sys.path.insert(0, str(Path(__file__).parent))
from config import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOGS_DIR / "04_extract_text.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class ExtractedDecision:
    """Structured extracted decision data."""
    source_type: str = "BIA_PRECEDENT_DECISION"
    agency: str = "EOIR"
    court_or_body: str = "Board of Immigration Appeals"
    decision_id: str = ""
    case_name: str = ""
    citation: str = ""
    volume: str = ""
    page: str = ""
    year: str = ""
    issuer: str = ""
    headnotes: List[str] = None
    pdf_url: str = ""
    source_volume_url: str = ""
    local_pdf_path: str = ""
    sha256: str = ""
    full_text: str = ""
    extraction_status: str = "pending"
    created_at: str = ""
    
    def __post_init__(self):
        if self.headnotes is None:
            self.headnotes = []
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()


def extract_text_from_pdf(pdf_path: Path) -> tuple:
    """
    Extract text from PDF using PyMuPDF.
    Returns: (full_text, page_count, success, error_message)
    """
    try:
        doc = pymupdf.open(pdf_path)
        pages = []
        
        for page in doc:
            text = page.get_text("text")
            pages.append(text)
        
        full_text = "\n\n".join(pages)
        page_count = len(doc)
        doc.close()
        
        return full_text, page_count, True, None
        
    except Exception as e:
        logger.error(f"Error extracting text from {pdf_path}: {e}")
        return "", 0, False, str(e)


def process_decision(decision: Dict) -> ExtractedDecision:
    """Process a single decision and extract text."""
    
    decision_id = decision['decision_id']
    volume_number = decision['volume_number']
    
    # Find PDF file
    pdf_dir = config.PDFS_DIR / f"volume_{volume_number:02d}"
    pdf_path = pdf_dir / f"ID_{decision_id}.pdf"
    
    if not pdf_path.exists():
        logger.warning(f"PDF not found: {pdf_path}")
        return ExtractedDecision(
            decision_id=decision_id,
            extraction_status="failed",
            error_message="PDF not found"
        )
    
    # Extract text
    full_text, page_count, success, error = extract_text_from_pdf(pdf_path)
    
    if not success:
        return ExtractedDecision(
            decision_id=decision_id,
            extraction_status="failed",
            error_message=error
        )
    
    # Build extracted decision
    extracted = ExtractedDecision(
        decision_id=decision_id,
        case_name=decision.get('case_name', ''),
        citation=decision.get('full_citation', ''),
        volume=str(decision.get('iandn_volume', volume_number)),
        page=str(decision.get('iandn_page', '')),
        year=str(decision.get('year', '')),
        issuer=decision.get('tribunal', 'BIA'),
        headnotes=decision.get('headnotes', []) if isinstance(decision.get('headnotes'), list) else [],
        pdf_url=decision.get('pdf_url', ''),
        source_volume_url=decision.get('source_volume_url', ''),
        local_pdf_path=str(pdf_path),
        sha256=decision.get('download_sha256', ''),
        full_text=full_text,
        extraction_status="success"
    )
    
    return extracted


def save_outputs(extracted: ExtractedDecision, volume_number: int):
    """Save extracted text and JSON."""
    
    decision_id = extracted.decision_id
    
    # Create directories
    text_dir = config.TEXT_DIR / f"volume_{volume_number:02d}"
    json_dir = config.JSON_DIR / f"volume_{volume_number:02d}"
    text_dir.mkdir(parents=True, exist_ok=True)
    json_dir.mkdir(parents=True, exist_ok=True)
    
    # Save plain text
    text_path = text_dir / f"ID_{decision_id}.txt"
    with open(text_path, 'w', encoding='utf-8') as f:
        f.write(extracted.full_text)
    
    # Save structured JSON
    json_path = json_dir / f"ID_{decision_id}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(asdict(extracted), f, indent=2, ensure_ascii=False)
    
    return text_path, json_path


def extract_all_text(test_mode: bool = False) -> List[ExtractedDecision]:
    """
    Extract text from all downloaded PDFs.
    """
    logger.info("Starting text extraction...")
    
    # Load decision manifest
    if not config.DECISION_MANIFEST_JSON.exists():
        logger.error("Decision manifest not found.")
        raise FileNotFoundError(f"Decision manifest not found: {config.DECISION_MANIFEST_JSON}")
    
    with open(config.DECISION_MANIFEST_JSON, 'r', encoding='utf-8') as f:
        decisions = json.load(f)
    
    # Filter for decisions with successful downloads
    decisions = [d for d in decisions if d.get('download_status') == 'success']
    logger.info(f"Processing {len(decisions)} successfully downloaded PDFs")
    
    # Filter for test mode
    if test_mode:
        original_count = len(decisions)
        decisions = [d for d in decisions if str(d['volume_number']) in config.TEST_VOLUMES or config.TEST_VOLUMES is None]
        logger.info(f"Test mode: processing {len(decisions)} of {original_count} decisions")
    
    extracted_decisions = []
    
    for decision in decisions:
        decision_id = decision['decision_id']
        volume_number = decision['volume_number']
        
        logger.debug(f"Extracting text from {decision_id} (Volume {volume_number})")
        
        extracted = process_decision(decision)
        extracted_decisions.append(extracted)
        
        if extracted.extraction_status == "success":
            save_outputs(extracted, volume_number)
    
    logger.info(f"Text extraction complete: {len(extracted_decisions)} decisions processed")
    return extracted_decisions


def print_summary(extracted: List[ExtractedDecision]):
    """Print extraction summary."""
    total = len(extracted)
    success = sum(1 for e in extracted if e.extraction_status == "success")
    failed = sum(1 for e in extracted if e.extraction_status == "failed")
    
    total_chars = sum(len(e.full_text) for e in extracted if e.extraction_status == "success")
    
    print("\n" + "="*60)
    print("TEXT EXTRACTION SUMMARY")
    print("="*60)
    print(f"Total PDFs processed: {total}")
    print(f"  - Successful: {success}")
    print(f"  - Failed: {failed}")
    print(f"\nTotal text extracted: {total_chars:,} characters ({total_chars / 1024 / 1024:.2f} MB)")
    print(f"\nOutput directories:")
    print(f"  - Text: {config.TEXT_DIR}")
    print(f"  - JSON: {config.JSON_DIR}")
    print("="*60)
    
    # Log failures
    if failed > 0:
        logger.warning("Failed extractions:")
        for e in extracted:
            if e.extraction_status == "failed":
                logger.warning(f"  - {e.decision_id}: {getattr(e, 'error_message', 'Unknown error')}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract text from BIA PDFs")
    parser.add_argument("--test", action="store_true", help="Enable test mode")
    args = parser.parse_args()
    
    test_mode = args.test or config.TEST_MODE
    
    try:
        extracted = extract_all_text(test_mode=test_mode)
        print_summary(extracted)
        return 0
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
