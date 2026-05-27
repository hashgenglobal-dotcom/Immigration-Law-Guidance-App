#!/usr/bin/env python3
"""
Step 1: Discover BIA Precedent Decision Volumes

Scrapes the EOIR Agency Decisions page and extracts all volume links
under the "AG/BIA Precedent Decisions" section.

Output:
- data/raw/bia/volume_manifest.csv
- data/raw/bia/volume_manifest.json
"""

import sys
import json
import logging
import re
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Optional

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
        logging.FileHandler(config.LOGS_DIR / "01_discover_volumes.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class VolumeInfo:
    """Represents a BIA precedent decision volume."""
    volume_number: int
    decision_id_range: str  # e.g., "4085 - " or "3985 - 4084"
    volume_page_url: str
    resolved_url: Optional[str] = None
    redirect_chain: List[str] = None
    fetch_status: str = "pending"
    fetch_timestamp: Optional[str] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.redirect_chain is None:
            self.redirect_chain = []


def extract_volume_number(text: str) -> Optional[int]:
    """Extract volume number from text like 'Volume 29 (4085 - )'."""
    match = re.search(r'Volume\s+(\d+)', text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def extract_decision_range(text: str) -> str:
    """Extract decision ID range from text like 'Volume 29 (4085 - )'."""
    match = re.search(r'\(([\d\s\-]+)\)', text)
    if match:
        return match.group(1).strip()
    return ""


def fetch_with_redirect_handling(url: str, session: requests.Session) -> tuple:
    """
    Fetch URL and track redirect chain.
    Returns: (final_url, redirect_chain, status_code, error_message)
    """
    redirect_chain = [url]
    
    try:
        response = session.get(
            url,
            headers={"User-Agent": config.USER_AGENT},
            timeout=config.REQUEST_TIMEOUT,
            allow_redirects=True
        )
        
        # Build redirect chain from response history
        redirect_chain = [resp.url for resp in response.history] + [response.url]
        
        return response.url, redirect_chain, response.status_code, None
        
    except requests.exceptions.RequestException as e:
        logger.warning(f"Error fetching {url}: {e}")
        return url, redirect_chain, 0, str(e)


def parse_ag_bia_section(soup: BeautifulSoup) -> List[dict]:
    """
    Parse the AG/BIA Precedent Decisions section from the main page.
    Returns list of volume data dicts.
    """
    volumes = []
    
    # Find the "AG/BIA Precedent Decisions" heading (h2)
    # Try multiple strategies
    heading = None
    
    # Strategy 1: Find h2 with exact text
    for h2 in soup.find_all('h2'):
        text = h2.get_text(strip=True)
        if 'AG/BIA Precedent Decisions' in text:
            heading = h2
            break
    
    # Strategy 2: Find by heading level and text content
    if not heading:
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        for h in headings:
            text = h.get_text(strip=True)
            if 'AG/BIA Precedent Decisions' in text:
                heading = h
                break
    
    if not heading:
        logger.error("Could not find 'AG/BIA Precedent Decisions' heading")
        logger.debug("Available headings:")
        for h in soup.find_all(['h1', 'h2', 'h3'])[:10]:
            logger.debug(f"  - {h.get_text(strip=True)[:50]}")
        return volumes
    
    logger.info(f"Found heading: {heading.get_text(strip=True)[:50]}")
    
    # Find the table following the heading
    table = heading.find_next('table')
    if not table:
        logger.error("Could not find volume table after heading")
        # Try to find any table on the page
        tables = soup.find_all('table')
        logger.debug(f"Found {len(tables)} tables on page")
        return volumes
    
    # Extract all links from the table
    for link in table.find_all('a', href=True):
        text = link.get_text(strip=True)
        if not text:
            continue
            
        volume_num = extract_volume_number(text)
        if volume_num is None:
            continue
        
        decision_range = extract_decision_range(text)
        volume_url = config.BASE_URL + link['href'] if link['href'].startswith('/') else link['href']
        
        volumes.append({
            'volume_number': volume_num,
            'decision_id_range': decision_range,
            'volume_page_url': volume_url
        })
    
    logger.info(f"Found {len(volumes)} volumes in AG/BIA Precedent Decisions section")
    return volumes


def discover_volumes(test_mode: bool = False, test_volumes: List[str] = None) -> List[VolumeInfo]:
    """
    Main discovery function.
    Fetches the main page, parses volumes, and resolves redirects.
    """
    logger.info("Starting BIA volume discovery...")
    logger.info(f"Source URL: {config.AGENCY_DECISIONS_URL}")
    
    # Create session with custom headers
    session = requests.Session()
    session.headers.update({
        "User-Agent": config.USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive"
    })
    
    # Fetch main page
    logger.info("Fetching Agency Decisions page...")
    try:
        response = session.get(
            config.AGENCY_DECISIONS_URL,
            timeout=config.REQUEST_TIMEOUT
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch main page: {e}")
        raise
    
    # Parse HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    volume_data = parse_ag_bia_section(soup)
    
    if not volume_data:
        logger.error("No volumes found - page structure may have changed")
        raise ValueError("No volumes discovered")
    
    # Filter for test mode if enabled
    if test_mode and test_volumes:
        original_count = len(volume_data)
        volume_data = [v for v in volume_data if str(v['volume_number']) in test_volumes]
        logger.info(f"Test mode: filtered from {original_count} to {len(volume_data)} volumes")
    
    # Resolve redirects for each volume
    logger.info(f"Resolving redirects for {len(volume_data)} volumes...")
    volumes = []
    
    for vol in tqdm(volume_data, desc="Resolving URLs"):
        volume_info = VolumeInfo(
            volume_number=vol['volume_number'],
            decision_id_range=vol['decision_id_range'],
            volume_page_url=vol['volume_page_url']
        )
        
        # Fetch with redirect tracking
        final_url, redirect_chain, status_code, error = fetch_with_redirect_handling(
            volume_info.volume_page_url,
            session
        )
        
        volume_info.resolved_url = final_url
        volume_info.redirect_chain = redirect_chain
        volume_info.fetch_status = "success" if status_code == 200 else f"http_{status_code}"
        volume_info.fetch_timestamp = datetime.utcnow().isoformat()
        volume_info.error_message = error
        
        volumes.append(volume_info)
        
        # Rate limiting
        import time
        time.sleep(config.REQUEST_DELAY)
    
    logger.info(f"Discovery complete: {len(volumes)} volumes")
    return volumes


def save_manifests(volumes: List[VolumeInfo]):
    """Save volume manifests to CSV and JSON."""
    
    # Convert to dicts
    volume_dicts = [asdict(v) for v in volumes]
    
    # Save CSV
    df = pd.DataFrame(volume_dicts)
    df.to_csv(config.VOLUME_MANIFEST_CSV, index=False)
    logger.info(f"Saved CSV: {config.VOLUME_MANIFEST_CSV}")
    
    # Save JSON
    with open(config.VOLUME_MANIFEST_JSON, 'w', encoding='utf-8') as f:
        json.dump(volume_dicts, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved JSON: {config.VOLUME_MANIFEST_JSON}")
    
    # Print summary
    print("\n" + "="*60)
    print("VOLUME DISCOVERY SUMMARY")
    print("="*60)
    print(f"Total volumes discovered: {len(volumes)}")
    print(f"Volume range: {min(v.volume_number for v in volumes)} - {max(v.volume_number for v in volumes)}")
    print(f"Successful URL resolutions: {sum(1 for v in volumes if v.fetch_status == 'success')}")
    print(f"Failed URL resolutions: {sum(1 for v in volumes if v.fetch_status != 'success')}")
    print(f"\nOutput files:")
    print(f"  - {config.VOLUME_MANIFEST_CSV}")
    print(f"  - {config.VOLUME_MANIFEST_JSON}")
    print("="*60)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Discover BIA precedent decision volumes")
    parser.add_argument("--test", action="store_true", help="Enable test mode")
    parser.add_argument("--volumes", type=str, help="Comma-separated volume numbers for test mode (e.g., '29,28')")
    args = parser.parse_args()
    
    test_mode = args.test or config.TEST_MODE
    test_volumes = args.volumes.split(',') if args.volumes else config.TEST_VOLUMES
    
    try:
        volumes = discover_volumes(test_mode=test_mode, test_volumes=test_volumes)
        save_manifests(volumes)
        return 0
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
