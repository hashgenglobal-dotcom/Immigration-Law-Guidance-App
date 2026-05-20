#!/usr/bin/env python3
"""
BIA Pipeline Auto-Trigger

Watches for PDF download completion and triggers text extraction.
Designed to run as a cron job every 5 minutes during active download windows.

Usage:
    python3 scripts/bia/watch_download_complete.py
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List

# Add parent directory to path for config import
sys.path.insert(0, str(Path(__file__).parent))
from config import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOGS_DIR / "watch_download.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def get_download_progress() -> dict:
    """
    Calculate current download progress.
    Returns dict with total, downloaded, percentage, missing_ids
    """
    if not config.DECISION_MANIFEST_JSON.exists():
        return {"error": "Decision manifest not found"}
    
    with open(config.DECISION_MANIFEST_JSON, 'r', encoding='utf-8') as f:
        decisions = json.load(f)
    
    total = len(decisions)
    downloaded = 0
    missing_ids = []
    
    for decision in decisions:
        decision_id = decision['decision_id']
        volume_number = decision['volume_number']
        
        pdf_dir = config.PDFS_DIR / f"volume_{volume_number:02d}"
        pdf_path = pdf_dir / f"ID_{decision_id}.pdf"
        
        if pdf_path.exists():
            downloaded += 1
        else:
            missing_ids.append(decision_id)
    
    percentage = (downloaded / total * 100) if total > 0 else 0
    
    return {
        "total": total,
        "downloaded": downloaded,
        "percentage": percentage,
        "missing_count": len(missing_ids),
        "missing_sample": missing_ids[:10]  # First 10 missing IDs
    }


def check_extraction_needed() -> bool:
    """
    Check if extraction should run.
    Returns True if:
    - Download is 100% complete, OR
    - Download is 95%+ complete AND no active download process
    """
    progress = get_download_progress()
    
    if "error" in progress:
        logger.error(progress["error"])
        return False
    
    # Check if already extracted
    extraction_marker = config.DATA_PROCESSED / ".extraction_complete"
    if extraction_marker.exists():
        logger.info("Extraction already complete (marker file exists)")
        return False
    
    # 100% complete - definitely run extraction
    if progress["percentage"] >= 99.9:
        logger.info(f"✓ Download 100% complete ({progress['downloaded']}/{progress['total']})")
        return True
    
    # 95%+ complete - check if download process is still running
    if progress["percentage"] >= 95:
        import subprocess
        try:
            result = subprocess.run(
                ["pgrep", "-f", "03_download_pdfs.py"],
                capture_output=True,
                text=True
            )
            if result.stdout.strip():
                logger.info(f"Download at {progress['percentage']:.1f}%, process still running - waiting")
                return False
            else:
                logger.warning(f"Download at {progress['percentage']:.1f}%, no active process - triggering extraction")
                return True
        except Exception as e:
            logger.warning(f"Could not check process status: {e}")
            return False
    
    logger.info(f"Download at {progress['percentage']:.1f}% - waiting for completion")
    return False


def run_extraction():
    """Trigger text extraction."""
    logger.info("🚀 Triggering text extraction pipeline...")
    
    import subprocess
    script_path = Path(__file__).parent / "pipeline_orchestrator.py"
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        
        if result.returncode == 0:
            logger.info("✓ Extraction completed successfully")
            # Create marker file
            marker = config.DATA_PROCESSED / ".extraction_complete"
            marker.write_text(f"Extraction completed: {datetime.now().isoformat()}\n")
            return True, result.stdout
        else:
            logger.error(f"✗ Extraction failed with code {result.returncode}")
            logger.error(result.stderr)
            return False, result.stderr
            
    except subprocess.TimeoutExpired:
        logger.error("✗ Extraction timed out after 1 hour")
        return False, "Timeout expired"
    except Exception as e:
        logger.error(f"✗ Extraction failed: {e}")
        return False, str(e)


def main():
    """Main entry point."""
    logger.info("=" * 60)
    logger.info("BIA DOWNLOAD WATCHER")
    logger.info(f"Check time: {datetime.now().isoformat()}")
    logger.info("=" * 60)
    
    # Get progress
    progress = get_download_progress()
    if "error" in progress:
        logger.error(f"Error getting progress: {progress['error']}")
        return 1
    
    logger.info(f"Progress: {progress['downloaded']}/{progress['total']} ({progress['percentage']:.1f}%)")
    logger.info(f"Missing: {progress['missing_count']} PDFs")
    
    # Check if extraction should run
    if check_extraction_needed():
        success, output = run_extraction()
        
        if success:
            logger.info("\n" + "=" * 60)
            logger.info("🎉 PIPELINE COMPLETE - Ready for RAG ingestion")
            logger.info("=" * 60)
            print(output)
            return 0
        else:
            logger.error("Extraction failed - manual intervention may be required")
            return 1
    else:
        logger.info("⏳ Continuing to monitor...")
        return 0


if __name__ == "__main__":
    sys.exit(main())
