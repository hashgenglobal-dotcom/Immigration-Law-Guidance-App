#!/usr/bin/env python3
"""
BIA Pipeline Orchestrator

Automates the full BIA acquisition pipeline:
1. Download PDFs (if not complete)
2. Extract text from PDFs
3. Validate outputs

Usage:
    python3 scripts/bia/pipeline_orchestrator.py [--force-extract]
"""

import sys
import json
import logging
import subprocess
from pathlib import Path
from datetime import datetime

# Add parent directory to path for config import
sys.path.insert(0, str(Path(__file__).parent))
from config import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOGS_DIR / "pipeline_orchestrator.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def check_download_complete() -> tuple:
    """
    Check if PDF download is complete.
    Returns: (is_complete, total_decisions, downloaded_count, missing_ids)
    """
    # Load decision manifest
    if not config.DECISION_MANIFEST_JSON.exists():
        logger.error("Decision manifest not found. Run 02_extract_decision_manifest.py first.")
        return False, 0, 0, []
    
    with open(config.DECISION_MANIFEST_JSON, 'r', encoding='utf-8') as f:
        decisions = json.load(f)
    
    total = len(decisions)
    downloaded = 0
    missing_ids = []
    
    for decision in decisions:
        decision_id = decision['decision_id']
        volume_number = decision['volume_number']
        
        # Check if PDF exists
        pdf_dir = config.PDFS_DIR / f"volume_{volume_number:02d}"
        pdf_path = pdf_dir / f"ID_{decision_id}.pdf"
        
        if pdf_path.exists():
            downloaded += 1
        else:
            missing_ids.append(decision_id)
    
    is_complete = (downloaded == total)
    return is_complete, total, downloaded, missing_ids


def run_download():
    """Run PDF download script."""
    logger.info("Starting PDF download (03_download_pdfs.py)...")
    script_path = Path(__file__).parent / "03_download_pdfs.py"
    
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=False,
        text=True
    )
    
    if result.returncode != 0:
        logger.error(f"Download failed with exit code {result.returncode}")
        return False
    
    logger.info("PDF download completed successfully")
    return True


def run_extraction():
    """Run text extraction script."""
    logger.info("Starting text extraction (04_extract_pdf_text.py)...")
    script_path = Path(__file__).parent / "04_extract_pdf_text.py"
    
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=False,
        text=True
    )
    
    if result.returncode != 0:
        logger.error(f"Extraction failed with exit code {result.returncode}")
        return False
    
    logger.info("Text extraction completed successfully")
    return True


def run_chunking():
    """Run RAG chunking script."""
    logger.info("Starting RAG chunking (05_create_rag_chunks.py)...")
    script_path = Path(__file__).parent / "05_create_rag_chunks.py"
    
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=False,
        text=True
    )
    
    if result.returncode != 0:
        logger.error(f"Chunking failed with exit code {result.returncode}")
        return False
    
    logger.info("RAG chunking completed successfully")
    return True


def run_ingestion():
    """Run database ingestion script."""
    logger.info("Starting database ingestion (ingest_bia_decisions.py)...")
    script_path = Path(__file__).parent / "ingest_bia_decisions.py"
    
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=False,
        text=True
    )
    
    if result.returncode != 0:
        logger.error(f"Ingestion failed with exit code {result.returncode}")
        return False
    
    logger.info("Database ingestion completed successfully")
    return True


def run_validation():
    """Run dataset validation."""
    logger.info("Running validation (06_validate_bia_dataset.py)...")
    script_path = Path(__file__).parent / "06_validate_bia_dataset.py"
    
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=False,
        text=True
    )
    
    if result.returncode != 0:
        logger.warning(f"Validation completed with warnings (exit code {result.returncode})")
        return False
    
    logger.info("Validation completed successfully")
    return True


def validate_outputs() -> dict:
    """Validate extraction outputs."""
    results = {
        "text_files": 0,
        "json_files": 0,
        "total_text_size_mb": 0,
        "total_json_size_mb": 0
    }
    
    # Count text files
    if config.TEXT_DIR.exists():
        text_files = list(config.TEXT_DIR.rglob("*.txt"))
        results["text_files"] = len(text_files)
        results["total_text_size_mb"] = sum(f.stat().st_size for f in text_files) / 1024 / 1024
    
    # Count JSON files
    if config.JSON_DIR.exists():
        json_files = list(config.JSON_DIR.rglob("*.json"))
        results["json_files"] = len(json_files)
        results["total_json_size_mb"] = sum(f.stat().st_size for f in json_files) / 1024 / 1024
    
    return results


def run_pipeline(force_extract: bool = False):
    """
    Run the full BIA acquisition pipeline.
    
    Args:
        force_extract: If True, run extraction even if download is incomplete
    """
    logger.info("=" * 60)
    logger.info("BIA PIPELINE ORCHESTRATOR")
    logger.info(f"Started: {datetime.now().isoformat()}")
    logger.info("=" * 60)
    
    # Step 1: Check download status
    logger.info("\n[STEP 1/4] Checking PDF download status...")
    is_complete, total, downloaded, missing_ids = check_download_complete()
    
    logger.info(f"  Total decisions: {total}")
    logger.info(f"  Downloaded: {downloaded} ({downloaded/total*100:.1f}%)")
    
    if not is_complete:
        if force_extract:
            logger.warning("  ⚠️  Download incomplete, but --force-extract specified")
            logger.warning(f"  Missing {len(missing_ids)} PDFs - extraction will skip these")
        else:
            logger.info("  Starting PDF download...")
            if not run_download():
                logger.error("Pipeline failed at download stage")
                return 1
            
            # Re-check after download
            is_complete, total, downloaded, missing_ids = check_download_complete()
    
    if downloaded == 0:
        logger.error("No PDFs found to process. Pipeline aborted.")
        return 1
    
    # Step 2: Run text extraction
    logger.info("\n[STEP 2/4] Extracting text from PDFs...")
    if not run_extraction():
        logger.error("Pipeline failed at extraction stage")
        return 1
    
    # Step 3: Create RAG chunks
    logger.info("\n[STEP 3/4] Creating RAG chunks...")
    if not run_chunking():
        logger.error("Pipeline failed at chunking stage")
        return 1
    
    # Step 4: Ingest into database
    logger.info("\n[STEP 4/4] Ingesting into database...")
    if not run_ingestion():
        logger.error("Pipeline failed at ingestion stage")
        return 1
    
    # Final validation
    logger.info("\n[VALIDATION] Running dataset validation...")
    if not run_validation():
        logger.warning("Validation completed with warnings")
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("PIPELINE COMPLETE")
    logger.info("=" * 60)
    logger.info(f"  Decisions processed: {downloaded}")
    logger.info(f"  Output location: {config.DATA_PROCESSED}")
    logger.info(f"  Database: immigration_law_dev (legal_chunks table)")
    logger.info(f"  Finished: {datetime.now().isoformat()}")
    logger.info("=" * 60)
    
    return 0


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="BIA Pipeline Orchestrator")
    parser.add_argument(
        "--force-extract",
        action="store_true",
        help="Run extraction even if PDF download is incomplete"
    )
    args = parser.parse_args()
    
    try:
        return run_pipeline(force_extract=args.force_extract)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
