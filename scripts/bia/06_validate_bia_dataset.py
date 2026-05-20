#!/usr/bin/env python3
"""
Step 6: Validate BIA Dataset

Comprehensive validation of the entire acquisition pipeline.
Generates a detailed report.

Output:
- reports/bia_acquisition_report.md
"""

import sys
import json
import logging
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple
from collections import defaultdict

import pandas as pd

# Add parent directory to path for config import
sys.path.insert(0, str(Path(__file__).parent))
from config import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOGS_DIR / "06_validate.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ValidationReport:
    """Collects and formats validation results."""
    
    def __init__(self):
        self.volumes_discovered = 0
        self.decisions_discovered = 0
        self.pdfs_downloaded = 0
        self.pdfs_failed = 0
        self.text_extractions_failed = 0
        self.duplicate_decision_ids = []
        self.missing_citations = []
        self.missing_pdf_urls = []
        self.invalid_pdfs = []
        self.total_chunks = 0
        self.failures = []
        self.warnings = []
        
    def add_failure(self, category: str, item: str, reason: str):
        self.failures.append({
            'category': category,
            'item': item,
            'reason': reason
        })
    
    def add_warning(self, category: str, item: str, reason: str):
        self.warnings.append({
            'category': category,
            'item': item,
            'reason': reason
        })
    
    def generate_markdown(self) -> str:
        """Generate markdown report."""
        now = datetime.utcnow().isoformat()
        
        md = f"""# BIA Precedent Decisions Acquisition Report

**Generated:** {now}  
**Source:** {config.AGENCY_DECISIONS_URL}

---

## Summary

| Metric | Count |
|--------|-------|
| Volumes Discovered | {self.volumes_discovered} |
| Decisions Discovered | {self.decisions_discovered} |
| PDFs Downloaded | {self.pdfs_downloaded} |
| PDFs Failed | {self.pdfs_failed} |
| Text Extraction Failures | {self.text_extractions_failed} |
| Duplicate Decision IDs | {len(self.duplicate_decision_ids)} |
| Missing Citations | {len(self.missing_citations)} |
| Missing PDF URLs | {len(self.missing_pdf_urls)} |
| Invalid PDFs | {len(self.invalid_pdfs)} |
| Total Chunks Created | {self.total_chunks} |

---

## Pipeline Status

### ✅ Volume Discovery
- **Status:** Complete
- **Volumes:** {self.volumes_discovered}
- **Manifest:** `{config.VOLUME_MANIFEST_JSON}`

### ✅ Decision Extraction
- **Status:** Complete
- **Decisions:** {self.decisions_discovered}
- **Manifest:** `{config.DECISION_MANIFEST_JSON}`

### ✅ PDF Download
- **Status:** Complete
- **Downloaded:** {self.pdfs_downloaded}
- **Failed:** {self.pdfs_failed}
- **Location:** `{config.PDFS_DIR}`

### ✅ Text Extraction
- **Status:** Complete
- **Failures:** {self.text_extractions_failed}
- **Output:** `{config.JSON_DIR}`

### ✅ RAG Chunking
- **Status:** Complete
- **Total Chunks:** {self.total_chunks}
- **Output:** `{config.DATA_FINAL / 'bia_precedent_chunks.jsonl'}`

---

## Validation Issues

"""
        
        # Failures
        if self.failures:
            md += "### ❌ Failures\n\n"
            by_category = defaultdict(list)
            for f in self.failures:
                by_category[f['category']].append(f)
            
            for category, items in by_category.items():
                md += f"#### {category}\n\n"
                for item in items[:10]:  # Limit to first 10 per category
                    md += f"- **{item['item']}**: {item['reason']}\n"
                if len(items) > 10:
                    md += f"- ... and {len(items) - 10} more\n"
                md += "\n"
        else:
            md += "### ✅ No Failures\n\n"
        
        # Warnings
        if self.warnings:
            md += "### ⚠️ Warnings\n\n"
            by_category = defaultdict(list)
            for w in self.warnings:
                by_category[w['category']].append(w)
            
            for category, items in by_category.items():
                md += f"#### {category}\n\n"
                for item in items[:10]:
                    md += f"- **{item['item']}**: {item['reason']}\n"
                if len(items) > 10:
                    md += f"- ... and {len(items) - 10} more\n"
                md += "\n"
        
        # Next steps
        md += """---

## Next Steps

1. **Review failures** - Address any critical issues in the Failures section
2. **Load into database** - Use the JSONL files to populate your RAG database
3. **Generate embeddings** - Run embedding generation on chunks
4. **Test retrieval** - Verify search quality with sample queries
5. **Schedule updates** - Set up periodic re-scraping for new decisions

### File Locations

| File | Path |
|------|------|
| Volume Manifest | `{config.VOLUME_MANIFEST_JSON}` |
| Decision Manifest | `{config.DECISION_MANIFEST_JSON}` |
| PDFs | `{config.PDFS_DIR}` |
| Extracted Text (JSON) | `{config.JSON_DIR}` |
| Extracted Text (TXT) | `{config.TEXT_DIR}` |
| RAG Chunks | `{config.DATA_FINAL / 'bia_precedent_chunks.jsonl'}` |
| Final Manifest | `{config.DATA_FINAL / 'bia_precedent_manifest.csv'}` |

---

*Report generated by BIA Acquisition Pipeline v1.0*
"""
        
        return md


def validate_volumes(report: ValidationReport) -> Dict:
    """Validate volume manifest."""
    logger.info("Validating volume manifest...")
    
    if not config.VOLUME_MANIFEST_JSON.exists():
        report.add_failure("Volume Manifest", "File", "Volume manifest not found")
        return {}
    
    with open(config.VOLUME_MANIFEST_JSON, 'r') as f:
        volumes = json.load(f)
    
    report.volumes_discovered = len(volumes)
    
    # Check for issues
    for vol in volumes:
        if not vol.get('resolved_url'):
            report.add_warning("Volume URL", f"Volume {vol['volume_number']}", "No resolved URL")
        if vol.get('fetch_status') != 'success':
            report.add_failure("Volume Fetch", f"Volume {vol['volume_number']}", vol.get('error_message', 'Unknown error'))
    
    return volumes


def validate_decisions(report: ValidationReport) -> Dict:
    """Validate decision manifest."""
    logger.info("Validating decision manifest...")
    
    if not config.DECISION_MANIFEST_JSON.exists():
        report.add_failure("Decision Manifest", "File", "Decision manifest not found")
        return {}
    
    with open(config.DECISION_MANIFEST_JSON, 'r') as f:
        decisions = json.load(f)
    
    report.decisions_discovered = len(decisions)
    
    # Check for duplicates
    decision_ids = [d['decision_id'] for d in decisions]
    duplicates = [id for id in decision_ids if decision_ids.count(id) > 1]
    report.duplicate_decision_ids = list(set(duplicates))
    
    if report.duplicate_decision_ids:
        for dup in report.duplicate_decision_ids[:10]:
            report.add_warning("Duplicate ID", dup, f"Appears {decision_ids.count(dup)} times")
    
    # Check for missing citations
    for d in decisions:
        if not d.get('full_citation'):
            report.missing_citations.append(d['decision_id'])
            report.add_warning("Missing Citation", d['decision_id'], "No citation field")
        
        if not d.get('pdf_url'):
            report.missing_pdf_urls.append(d['decision_id'])
            report.add_failure("Missing PDF URL", d['decision_id'], "No PDF URL")
    
    return decisions


def validate_pdfs(report: ValidationReport):
    """Validate downloaded PDFs."""
    logger.info("Validating PDFs...")
    
    if not config.PDFS_DIR.exists():
        report.add_failure("PDF Directory", "Directory", "PDF directory not found")
        return
    
    pdf_files = list(config.PDFS_DIR.glob("volume_*/ID_*.pdf"))
    report.pdfs_downloaded = len(pdf_files)
    
    # Validate each PDF
    for pdf_path in pdf_files:
        # Check file size
        if pdf_path.stat().st_size == 0:
            report.invalid_pdfs.append(str(pdf_path))
            report.add_failure("Empty PDF", pdf_path.name, "File size is 0")
            continue
        
        # Check PDF header
        with open(pdf_path, 'rb') as f:
            header = f.read(8)
            if not header.startswith(b'%PDF'):
                report.invalid_pdfs.append(str(pdf_path))
                report.add_failure("Invalid PDF", pdf_path.name, "Does not start with %PDF")
                continue
        
        # Verify SHA256 if available in manifest
        if config.DECISION_MANIFEST_JSON.exists():
            with open(config.DECISION_MANIFEST_JSON, 'r') as f:
                decisions = json.load(f)
            
            decision_id = pdf_path.stem.replace('ID_', '')
            for d in decisions:
                if d['decision_id'] == decision_id:
                    expected_sha = d.get('download_sha256')
                    if expected_sha:
                        actual_sha = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
                        if actual_sha != expected_sha:
                            report.add_failure("SHA256 Mismatch", pdf_path.name, "Hash mismatch")
                    break
    
    # Check for failed downloads
    if config.DECISION_MANIFEST_JSON.exists():
        with open(config.DECISION_MANIFEST_JSON, 'r') as f:
            decisions = json.load(f)
        
        failed = [d for d in decisions if d.get('download_status') == 'failed']
        report.pdfs_failed = len(failed)


def validate_text_extraction(report: ValidationReport):
    """Validate extracted text files."""
    logger.info("Validating text extraction...")
    
    if not config.JSON_DIR.exists():
        report.add_failure("JSON Directory", "Directory", "JSON directory not found")
        return
    
    json_files = list(config.JSON_DIR.glob("volume_*/ID_*.json"))
    
    for json_path in json_files:
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if data.get('extraction_status') == 'failed':
                report.text_extractions_failed += 1
                report.add_failure("Text Extraction", json_path.name, data.get('error_message', 'Unknown error'))
            
            if not data.get('full_text') or len(data.get('full_text', '').strip()) < 100:
                report.add_warning("Short Text", json_path.name, f"Only {len(data.get('full_text', ''))} chars")
                
        except Exception as e:
            report.add_failure("JSON Parse", json_path.name, str(e))


def validate_chunks(report: ValidationReport):
    """Validate RAG chunks."""
    logger.info("Validating chunks...")
    
    chunks_file = config.DATA_FINAL / "bia_precedent_chunks.jsonl"
    
    if not chunks_file.exists():
        report.add_failure("Chunks File", "File", "Chunks file not found")
        return
    
    chunk_count = 0
    with open(chunks_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                chunk = json.loads(line)
                chunk_count += 1
                
                # Validate required fields
                required = ['chunk_id', 'decision_id', 'text', 'citation']
                for field in required:
                    if not chunk.get(field):
                        report.add_warning("Missing Chunk Field", chunk.get('chunk_id', 'unknown'), f"Missing {field}")
                
            except json.JSONDecodeError as e:
                report.add_failure("Chunk Parse", chunks_file.name, str(e))
    
    report.total_chunks = chunk_count


def run_validation() -> ValidationReport:
    """Run all validations."""
    logger.info("Starting comprehensive validation...")
    
    report = ValidationReport()
    
    # Run all validations
    validate_volumes(report)
    validate_decisions(report)
    validate_pdfs(report)
    validate_text_extraction(report)
    validate_chunks(report)
    
    # Save report
    md_content = report.generate_markdown()
    with open(config.VALIDATION_REPORT, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    logger.info(f"Validation report saved: {config.VALIDATION_REPORT}")
    
    return report


def print_summary(report: ValidationReport):
    """Print validation summary."""
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    print(f"✓ Volumes discovered: {report.volumes_discovered}")
    print(f"✓ Decisions discovered: {report.decisions_discovered}")
    print(f"✓ PDFs downloaded: {report.pdfs_downloaded}")
    print(f"✗ PDFs failed: {report.pdfs_failed}")
    print(f"✗ Text extraction failures: {report.text_extractions_failed}")
    print(f"⚠ Duplicate decision IDs: {len(report.duplicate_decision_ids)}")
    print(f"⚠ Missing citations: {len(report.missing_citations)}")
    print(f"✗ Missing PDF URLs: {len(report.missing_pdf_urls)}")
    print(f"✗ Invalid PDFs: {len(report.invalid_pdfs)}")
    print(f"✓ Total chunks: {report.total_chunks}")
    print(f"\nFailures: {len(report.failures)}")
    print(f"Warnings: {len(report.warnings)}")
    print(f"\nReport: {config.VALIDATION_REPORT}")
    print("="*60)
    
    if report.failures:
        print("\n❌ CRITICAL FAILURES:")
        for f in report.failures[:5]:
            print(f"  - {f['category']}: {f['item']}")
        if len(report.failures) > 5:
            print(f"  ... and {len(report.failures) - 5} more")


def main():
    """Main entry point."""
    try:
        report = run_validation()
        print_summary(report)
        return 0 if len(report.failures) == 0 else 1
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
