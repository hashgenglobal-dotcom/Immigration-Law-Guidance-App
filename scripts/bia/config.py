"""
BIA Precedent Decisions Acquisition Pipeline - Configuration
"""
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

@dataclass
class BIAConfig:
    # Source URLs
    BASE_URL: str = "https://www.justice.gov"
    AGENCY_DECISIONS_URL: str = "https://www.justice.gov/eoir/ag-bia-decisions"
    
    # Request settings
    USER_AGENT: str = "BIA-RAG-Bot/1.0 (Immigration Legal Research Project; Contact: hash@hashgen.global)"
    REQUEST_TIMEOUT: int = 30
    REQUEST_DELAY: float = 2.0  # seconds between requests
    PDF_DOWNLOAD_DELAY: float = 2.5  # seconds between PDF downloads
    MAX_RETRIES: int = 3
    RETRY_BACKOFF: float = 2.0  # exponential backoff multiplier
    
    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    DATA_RAW: Path = BASE_DIR / "data" / "raw" / "bia"
    DATA_PROCESSED: Path = BASE_DIR / "data" / "processed" / "bia"
    DATA_FINAL: Path = BASE_DIR / "data" / "final"
    REPORTS_DIR: Path = BASE_DIR / "reports"
    LOGS_DIR: Path = BASE_DIR / "logs"
    
    # Output files
    VOLUME_MANIFEST_CSV: Path = DATA_RAW / "volume_manifest.csv"
    VOLUME_MANIFEST_JSON: Path = DATA_RAW / "volume_manifest.json"
    DECISION_MANIFEST_CSV: Path = DATA_RAW / "bia_decision_manifest.csv"
    DECISION_MANIFEST_JSON: Path = DATA_RAW / "bia_decision_manifest.json"
    PDFS_DIR: Path = DATA_RAW / "bia" / "pdfs"
    TEXT_DIR: Path = DATA_PROCESSED / "text"
    JSON_DIR: Path = DATA_PROCESSED / "json"
    CHUNKS_DIR: Path = DATA_PROCESSED / "chunks"
    FINAL_JSONL: Path = DATA_FINAL / "bia_precedent_decisions.jsonl"
    FINAL_CHUNKS_JSONL: Path = DATA_FINAL / "bia_precedent_chunks.jsonl"
    FINAL_MANIFEST_CSV: Path = DATA_FINAL / "bia_precedent_manifest.csv"
    VALIDATION_REPORT: Path = REPORTS_DIR / "bia_acquisition_report.md"
    
    # Chunking settings
    CHUNK_SIZE: int = 1000  # tokens (approx 4000 chars)
    CHUNK_OVERLAP: int = 125  # tokens (approx 500 chars)
    
    # Test mode
    TEST_MODE: bool = False
    TEST_VOLUMES: Optional[list] = None  # e.g., ["29"] for test mode, None means no filtering
    
    @classmethod
    def from_env(cls) -> "BIAConfig":
        """Load config from environment variables or use defaults."""
        import os
        
        config = cls()
        
        # Override from environment
        if os.getenv("BIA_TEST_MODE"):
            config.TEST_MODE = os.getenv("BIA_TEST_MODE").lower() == "true"
        if os.getenv("BIA_TEST_VOLUMES"):
            config.TEST_VOLUMES = os.getenv("BIA_TEST_VOLUMES").split(",")
        if os.getenv("BIA_REQUEST_DELAY"):
            config.REQUEST_DELAY = float(os.getenv("BIA_REQUEST_DELAY"))
        if os.getenv("BIA_PDF_DOWNLOAD_DELAY"):
            config.PDF_DOWNLOAD_DELAY = float(os.getenv("BIA_PDF_DOWNLOAD_DELAY"))
        
        # Ensure directories exist
        for path in [
            config.DATA_RAW, config.DATA_PROCESSED, config.DATA_FINAL,
            config.REPORTS_DIR, config.LOGS_DIR, config.PDFS_DIR,
            config.TEXT_DIR, config.JSON_DIR, config.CHUNKS_DIR
        ]:
            path.mkdir(parents=True, exist_ok=True)
        
        return config


# Global config instance
config = BIAConfig.from_env()
