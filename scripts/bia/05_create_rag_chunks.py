#!/usr/bin/env python3
"""
Step 5: Create RAG Chunks from BIA Decisions

Chunks extracted text for retrieval with proper metadata preservation.
Uses token-based chunking with overlap.

Output:
- data/processed/bia/chunks/bia_chunks.jsonl
- data/final/bia_precedent_chunks.jsonl
"""

import sys
import json
import logging
import re
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional

import pandas as pd

# Add parent directory to path for config import
sys.path.insert(0, str(Path(__file__).parent))
from config import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOGS_DIR / "05_create_chunks.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """A single RAG chunk with metadata."""
    chunk_id: str
    source_type: str = "BIA_PRECEDENT_DECISION"
    decision_id: str = ""
    case_name: str = ""
    citation: str = ""
    volume: str = ""
    page: str = ""
    year: str = ""
    issuer: str = ""
    pdf_url: str = ""
    source_volume_url: str = ""
    text: str = ""
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    chunk_index: int = 0
    total_chunks: int = 0
    
    def to_dict(self) -> Dict:
        return asdict(self)


def estimate_tokens(text: str) -> int:
    """Estimate token count (rough: 1 token ≈ 4 chars for English)."""
    return len(text) // 4


def split_text_into_chunks(text: str, chunk_size_chars: int, overlap_chars: int) -> List[str]:
    """
    Split text into chunks with overlap.
    Tries to split at sentence boundaries when possible.
    """
    if len(text) <= chunk_size_chars:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size_chars
        
        # If we're at the end, just take what's left
        if end >= len(text):
            chunks.append(text[start:])
            break
        
        # Try to find a good split point (sentence boundary, paragraph, or newline)
        chunk_text = text[start:end]
        
        # Look for sentence boundary (". " or "\n")
        split_point = -1
        
        # Prefer paragraph breaks
        last_newline = chunk_text.rfind('\n\n')
        if last_newline > chunk_size_chars * 0.5:  # At least halfway
            split_point = last_newline
        
        # Otherwise look for sentence boundary
        if split_point == -1:
            last_period = chunk_text.rfind('. ')
            if last_period > chunk_size_chars * 0.5:
                split_point = last_period + 1  # Include the period
        
        # Otherwise look for any newline
        if split_point == -1:
            last_newline = chunk_text.rfind('\n')
            if last_newline > chunk_size_chars * 0.5:
                split_point = last_newline
        
        # If no good split point, just cut at chunk_size
        if split_point == -1:
            split_point = chunk_size_chars
        
        chunks.append(text[start:start + split_point])
        start = start + split_point - overlap_chars
        
        # Safety: prevent infinite loop
        if start <= 0 and len(text) > chunk_size_chars:
            start = end
    
    return chunks


def create_chunk_metadata(decision: Dict, chunk_index: int, total_chunks: int) -> Dict:
    """Create metadata dict for a chunk."""
    return {
        'chunk_id': f"BIA_ID_{decision['decision_id']}_chunk_{chunk_index:04d}",
        'source_type': 'BIA_PRECEDENT_DECISION',
        'decision_id': str(decision['decision_id']),
        'case_name': decision.get('case_name', ''),
        'citation': decision.get('citation', ''),
        'volume': str(decision.get('volume', '')),
        'page': str(decision.get('page', '')),
        'year': str(decision.get('year', '')),
        'issuer': decision.get('issuer', 'BIA'),
        'pdf_url': decision.get('pdf_url', ''),
        'source_volume_url': decision.get('source_volume_url', ''),
        'chunk_index': chunk_index,
        'total_chunks': total_chunks
    }


def process_decision_json(json_path: Path) -> List[Chunk]:
    """Process a single decision JSON file and create chunks."""
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            decision = json.load(f)
    except Exception as e:
        logger.error(f"Error reading {json_path}: {e}")
        return []
    
    full_text = decision.get('full_text', '')
    if not full_text or len(full_text.strip()) < 100:
        logger.warning(f"Skipping {json_path} - text too short or empty")
        return []
    
    # Calculate chunk parameters
    # config.CHUNK_SIZE is in tokens (~4 chars/token), convert to chars
    chunk_size_chars = config.CHUNK_SIZE * 4
    overlap_chars = config.CHUNK_OVERLAP * 4
    
    # Split text
    text_chunks = split_text_into_chunks(full_text, chunk_size_chars, overlap_chars)
    
    if not text_chunks:
        return []
    
    # Create Chunk objects
    chunks = []
    for i, text in enumerate(text_chunks):
        metadata = create_chunk_metadata(decision, i, len(text_chunks))
        
        chunk = Chunk(
            chunk_id=metadata['chunk_id'],
            text=text.strip(),
            decision_id=metadata['decision_id'],
            case_name=metadata['case_name'],
            citation=metadata['citation'],
            volume=metadata['volume'],
            page=metadata['page'],
            year=metadata['year'],
            issuer=metadata['issuer'],
            pdf_url=metadata['pdf_url'],
            source_volume_url=metadata['source_volume_url'],
            source_type=metadata['source_type'],
            chunk_index=i,
            total_chunks=len(text_chunks)
        )
        chunks.append(chunk)
    
    return chunks


def create_all_chunks(test_mode: bool = False) -> List[Chunk]:
    """
    Create chunks from all extracted decisions.
    """
    logger.info("Starting chunk creation...")
    
    all_chunks = []
    
    # Iterate through JSON files
    json_files = list(config.JSON_DIR.glob("volume_*/ID_*.json"))
    logger.info(f"Found {len(json_files)} decision JSON files")
    
    # Filter for test mode
    if test_mode and config.TEST_VOLUMES:
        original_count = len(json_files)
        json_files = [f for f in json_files if any(f"volume_{v.zfill(2)}" in str(f) for v in config.TEST_VOLUMES)]
        logger.info(f"Test mode: processing {len(json_files)} of {original_count} files")
    
    for json_path in json_files:
        chunks = process_decision_json(json_path)
        all_chunks.extend(chunks)
    
    logger.info(f"Created {len(all_chunks)} chunks from {len(json_files)} decisions")
    return all_chunks


def save_chunks(chunks: List[Chunk]):
    """Save chunks to JSONL files."""
    
    # Save to processed/chunks
    chunks_path = config.CHUNKS_DIR / "bia_chunks.jsonl"
    with open(chunks_path, 'w', encoding='utf-8') as f:
        for chunk in chunks:
            f.write(json.dumps(chunk.to_dict(), ensure_ascii=False) + '\n')
    logger.info(f"Saved chunks: {chunks_path}")
    
    # Save to final
    final_path = config.DATA_FINAL / "bia_precedent_chunks.jsonl"
    with open(final_path, 'w', encoding='utf-8') as f:
        for chunk in chunks:
            f.write(json.dumps(chunk.to_dict(), ensure_ascii=False) + '\n')
    logger.info(f"Saved final chunks: {final_path}")
    
    # Create summary CSV
    summary_data = []
    for chunk in chunks:
        summary_data.append({
            'chunk_id': chunk.chunk_id,
            'decision_id': chunk.decision_id,
            'case_name': chunk.case_name,
            'citation': chunk.citation,
            'chunk_index': chunk.chunk_index,
            'total_chunks': chunk.total_chunks,
            'text_length': len(chunk.text)
        })
    
    df = pd.DataFrame(summary_data)
    csv_path = config.DATA_FINAL / "bia_precedent_manifest.csv"
    df.to_csv(csv_path, index=False)
    logger.info(f"Saved manifest: {csv_path}")


def print_summary(chunks: List[Chunk]):
    """Print chunking summary."""
    total_chunks = len(chunks)
    total_decisions = len(set(c.decision_id for c in chunks))
    total_chars = sum(len(c.text) for c in chunks)
    avg_chunk_size = total_chars / total_chunks if total_chunks > 0 else 0
    
    print("\n" + "="*60)
    print("CHUNK CREATION SUMMARY")
    print("="*60)
    print(f"Total chunks created: {total_chunks:,}")
    print(f"Total decisions processed: {total_decisions}")
    print(f"Average chunks per decision: {total_chunks / total_decisions:.1f}")
    print(f"Total text: {total_chars:,} characters ({total_chars / 1024 / 1024:.2f} MB)")
    print(f"Average chunk size: {avg_chunk_size:.0f} chars (~{avg_chunk_size / 4:.0f} tokens)")
    print(f"\nOutput files:")
    print(f"  - {config.CHUNKS_DIR / 'bia_chunks.jsonl'}")
    print(f"  - {config.DATA_FINAL / 'bia_precedent_chunks.jsonl'}")
    print(f"  - {config.DATA_FINAL / 'bia_precedent_manifest.csv'}")
    print("="*60)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Create RAG chunks from BIA decisions")
    parser.add_argument("--test", action="store_true", help="Enable test mode")
    args = parser.parse_args()
    
    test_mode = args.test or config.TEST_MODE
    
    try:
        chunks = create_all_chunks(test_mode=test_mode)
        save_chunks(chunks)
        print_summary(chunks)
        return 0
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
