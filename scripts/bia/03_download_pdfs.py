#!/usr/bin/env python3
"""
Step 3: Download BIA Precedent Decision PDFs

Downloads all PDFs from the decision manifest with rate limiting,
retries, and checkpointing.

Output:
- data/raw/bia/pdfs/volume_{volume}/ID_{decision_id}.pdf
- Updates decision manifest with download metadata
"""

import sys
import json
import logging
import hashlib
import time
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict

import requests
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
        logging.FileHandler(config.LOGS_DIR / "03_download_pdfs.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class DownloadResult:
    """Result of a PDF download attempt."""
    decision_id: str
    volume_number: int
    local_path: str
    http_status: int
    content_type: str
    file_size_bytes: int
    sha256: str
    downloaded_at: str
    download_status: str  # "success", "failed", "skipped", "invalid"
    error_message: Optional[str] = None


def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def validate_pdf(file_path: Path) -> bool:
    """Validate that file starts with %PDF header."""
    try:
        with open(file_path, 'rb') as f:
            header = f.read(8)
            return header.startswith(b'%PDF')
    except Exception:
        return False


def download_pdf(decision: Dict, session: requests.Session) -> DownloadResult:
    """
    Download a single PDF with retries and validation.
    """
    decision_id = decision['decision_id']
    volume_number = decision['volume_number']
    pdf_url = decision['pdf_url']
    
    # Create volume directory
    volume_dir = config.PDFS_DIR / f"volume_{volume_number:02d}"
    volume_dir.mkdir(parents=True, exist_ok=True)
    
    # Local path
    local_path = volume_dir / f"ID_{decision_id}.pdf"
    
    # Check if already downloaded
    if local_path.exists():
        logger.info(f"Skipping {decision_id} - already exists")
        # Validate existing file
        if validate_pdf(local_path):
            return DownloadResult(
                decision_id=decision_id,
                volume_number=volume_number,
                local_path=str(local_path),
                http_status=200,
                content_type="application/pdf",
                file_size_bytes=local_path.stat().st_size,
                sha256=compute_sha256(local_path),
                downloaded_at=datetime.utcnow().isoformat(),
                download_status="skipped",
                error_message="Already exists"
            )
        else:
            logger.warning(f"Existing file {local_path} is invalid - re-downloading")
            local_path.unlink()
    
    # Download with retries
    for attempt in range(config.MAX_RETRIES):
        try:
            logger.debug(f"Downloading {decision_id} (attempt {attempt + 1}/{config.MAX_RETRIES})")
            
            response = session.get(
                pdf_url,
                headers={"User-Agent": config.USER_AGENT},
                timeout=config.REQUEST_TIMEOUT,
                stream=True
            )
            
            # Check for access control issues
            if response.status_code in [401, 403]:
                logger.error(f"Access denied for {pdf_url} - stopping")
                return DownloadResult(
                    decision_id=decision_id,
                    volume_number=volume_number,
                    local_path="",
                    http_status=response.status_code,
                    content_type=response.headers.get('Content-Type', ''),
                    file_size_bytes=0,
                    sha256="",
                    downloaded_at=datetime.utcnow().isoformat(),
                    download_status="failed",
                    error_message=f"Access denied: {response.status_code}"
                )
            
            if response.status_code != 200:
                logger.warning(f"HTTP {response.status_code} for {decision_id}")
                if attempt < config.MAX_RETRIES - 1:
                    wait_time = config.RETRY_BACKOFF ** attempt
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
            
            # Write file
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Validate PDF
            if not validate_pdf(local_path):
                logger.error(f"Invalid PDF for {decision_id} - does not start with %PDF")
                local_path.unlink()
                return DownloadResult(
                    decision_id=decision_id,
                    volume_number=volume_number,
                    local_path="",
                    http_status=response.status_code,
                    content_type=response.headers.get('Content-Type', ''),
                    file_size_bytes=0,
                    sha256="",
                    downloaded_at=datetime.utcnow().isoformat(),
                    download_status="invalid",
                    error_message="Invalid PDF header"
                )
            
            # Success
            return DownloadResult(
                decision_id=decision_id,
                volume_number=volume_number,
                local_path=str(local_path),
                http_status=response.status_code,
                content_type=response.headers.get('Content-Type', 'application/pdf'),
                file_size_bytes=local_path.stat().st_size,
                sha256=compute_sha256(local_path),
                downloaded_at=datetime.utcnow().isoformat(),
                download_status="success"
            )
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Download error for {decision_id}: {e}")
            if attempt < config.MAX_RETRIES - 1:
                wait_time = config.RETRY_BACKOFF ** attempt
                logger.info(f"Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                return DownloadResult(
                    decision_id=decision_id,
                    volume_number=volume_number,
                    local_path="",
                    http_status=0,
                    content_type="",
                    file_size_bytes=0,
                    sha256="",
                    downloaded_at=datetime.utcnow().isoformat(),
                    download_status="failed",
                    error_message=str(e)
                )
    
    # Should not reach here, but just in case
    return DownloadResult(
        decision_id=decision_id,
        volume_number=volume_number,
        local_path="",
        http_status=0,
        content_type="",
        file_size_bytes=0,
        sha256="",
        downloaded_at=datetime.utcnow().isoformat(),
        download_status="failed",
        error_message="Max retries exceeded"
    )


def download_all_pdfs(test_mode: bool = False) -> List[DownloadResult]:
    """
    Download all PDFs from the decision manifest.
    """
    logger.info("Starting PDF download...")
    
    # Load decision manifest
    if not config.DECISION_MANIFEST_JSON.exists():
        logger.error("Decision manifest not found. Run 02_extract_decision_manifest.py first.")
        raise FileNotFoundError(f"Decision manifest not found: {config.DECISION_MANIFEST_JSON}")
    
    with open(config.DECISION_MANIFEST_JSON, 'r', encoding='utf-8') as f:
        decisions = json.load(f)
    
    # Filter for test mode
    if test_mode:
        original_count = len(decisions)
        test_vols = config.TEST_VOLUMES or []
        if test_vols:  # Only filter if test volumes specified
            decisions = [d for d in decisions if str(d['volume_number']) in test_vols]
        logger.info(f"Test mode: downloading {len(decisions)} of {original_count} decisions")
    
    # Create session
    session = requests.Session()
    session.headers.update({
        "User-Agent": config.USER_AGENT,
        "Accept": "application/pdf,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive"
    })
    
    results = []
    
    for decision in tqdm(decisions, desc="Downloading PDFs"):
        result = download_pdf(decision, session)
        results.append(result)
        
        # Rate limiting
        time.sleep(config.PDF_DOWNLOAD_DELAY)
    
    logger.info(f"Download complete: {len(results)} PDFs processed")
    return results


def update_manifest(results: List[DownloadResult]):
    """Update decision manifest with download metadata."""
    
    # Load existing manifest
    with open(config.DECISION_MANIFEST_JSON, 'r', encoding='utf-8') as f:
        decisions = json.load(f)
    
    # Create lookup
    results_lookup = {r.decision_id: r for r in results}
    
    # Update decisions
    for decision in decisions:
        result = results_lookup.get(decision['decision_id'])
        if result:
            decision['local_pdf_path'] = result.local_path
            decision['download_http_status'] = result.http_status
            decision['download_content_type'] = result.content_type
            decision['download_file_size_bytes'] = result.file_size_bytes
            decision['download_sha256'] = result.sha256
            decision['downloaded_at'] = result.downloaded_at
            decision['download_status'] = result.download_status
            decision['download_error'] = result.error_message
    
    # Save updated manifest
    with open(config.DECISION_MANIFEST_JSON, 'w', encoding='utf-8') as f:
        json.dump(decisions, f, indent=2, ensure_ascii=False)
    
    # Also save CSV
    df = pd.DataFrame(decisions)
    df['headnotes'] = df['headnotes'].apply(lambda x: ' ||| '.join(x) if isinstance(x, list) else x)
    df.to_csv(config.DECISION_MANIFEST_CSV, index=False)
    
    logger.info("Updated decision manifest with download metadata")


def print_summary(results: List[DownloadResult]):
    """Print download summary."""
    total = len(results)
    success = sum(1 for r in results if r.download_status == "success")
    skipped = sum(1 for r in results if r.download_status == "skipped")
    failed = sum(1 for r in results if r.download_status == "failed")
    invalid = sum(1 for r in results if r.download_status == "invalid")
    
    total_size = sum(r.file_size_bytes for r in results if r.download_status in ["success", "skipped"])
    
    print("\n" + "="*60)
    print("PDF DOWNLOAD SUMMARY")
    print("="*60)
    print(f"Total PDFs: {total}")
    print(f"  - Downloaded successfully: {success}")
    print(f"  - Skipped (already exists): {skipped}")
    print(f"  - Failed: {failed}")
    print(f"  - Invalid: {invalid}")
    print(f"\nTotal size: {total_size / 1024 / 1024:.2f} MB")
    print(f"Download location: {config.PDFS_DIR}")
    print("="*60)
    
    # Log failures
    if failed > 0 or invalid > 0:
        logger.warning("Failed/Invalid downloads:")
        for r in results:
            if r.download_status in ["failed", "invalid"]:
                logger.warning(f"  - {r.decision_id}: {r.error_message}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Download BIA precedent decision PDFs")
    parser.add_argument("--test", action="store_true", help="Enable test mode")
    parser.add_argument("--no-update", action="store_true", help="Don't update manifest")
    args = parser.parse_args()
    
    test_mode = args.test or config.TEST_MODE
    
    try:
        results = download_all_pdfs(test_mode=test_mode)
        
        if not args.no_update:
            update_manifest(results)
        
        print_summary(results)
        return 0
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
