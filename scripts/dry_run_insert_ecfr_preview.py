#!/usr/bin/env python3
"""Dry-run simulation of eCFR Title 8 database inserts.

This script reads the validated eCFR Title 8 JSON preview and prints the
planned database inserts for every relevant table WITHOUT writing to
PostgreSQL. It is the verification step between preview validation and the
real insertion script.

Privacy
-------
This script handles public legal-source data only. It does NOT process user
questions. It does NOT write to privacy_safe_answer_logs. It does NOT write
to the database. It does NOT generate embeddings. It does NOT call Ollama,
OpenAI, Anthropic, or any public AI API.

Usage
-----
    # Dry-run against the newest preview under data/ecfr_samples/
    python scripts/dry_run_insert_ecfr_preview.py

    # Dry-run against a specific preview file
    python scripts/dry_run_insert_ecfr_preview.py \\
        --preview-file data/ecfr_samples/title8_sample_preview_2026-05-12.json

Exit codes
----------
* 0 — dry-run completed successfully; all planned inserts were printed.
* 1 — preview JSON is missing, invalid, or has no sections.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_PREVIEW_GLOB = "data/ecfr_samples/title8_sample_preview_*.json"

# Deterministic topic mapping for the five MVP sections.
# These values are assigned by hand so inserts are reproducible and do not
# depend on any AI classifier or external service.
TOPIC_MAP: dict[str, dict[str, str]] = {
    "208.7":  {"topic": "asylum",                   "subtopic": "employment_authorization", "risk_level": "medium"},
    "208.4":  {"topic": "asylum",                   "subtopic": "filing_deadline",          "risk_level": "high"},
    "245.1":  {"topic": "adjustment_of_status",     "subtopic": "eligibility",              "risk_level": "medium"},
    "274a.12":{"topic": "employment_authorization", "subtopic": "categories",               "risk_level": "medium"},
    "239.1":  {"topic": "removal_proceedings",      "subtopic": "notice_to_appear",         "risk_level": "high"},
}

# Tables intentionally not touched by any ingestion script.
EXCLUDED_TABLES = ["privacy_safe_answer_logs", "admin_users"]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Dry-run simulation of eCFR Title 8 database inserts. "
            "Reads public legal-source data only; never touches the database."
        ),
    )
    parser.add_argument(
        "--preview-file",
        default=None,
        help=(
            "Path to a specific preview JSON file. "
            f"Default: newest file matching {DEFAULT_PREVIEW_GLOB} "
            "(relative to the current working directory; run from the repo root)."
        ),
    )
    return parser.parse_args(argv)


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------


def _find_newest_preview() -> Path | None:
    """Return the newest preview JSON under data/ecfr_samples/, or None."""
    candidates = list(Path().glob(DEFAULT_PREVIEW_GLOB))
    if not candidates:
        return None
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def _companion_xml_path(source_date: str) -> Path:
    """Resolve the raw XML companion file path for a given source_date."""
    return Path(f"data/ecfr_samples/raw_title8_{source_date}.xml")


def _sha256_of_file(path: Path) -> str:
    """Return the hex SHA-256 digest of a file's bytes."""
    h = hashlib.sha256()
    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Dry-run planning
# ---------------------------------------------------------------------------


def _plan_dataset_version(source_date: str) -> dict[str, Any]:
    return {
        "version_name": f"ecfr-title8-sample-{source_date}",
        "status_start": "building",
        "status_end": "ready",
        "activated_at": None,
        "notes": (
            "First eCFR Title 8 sample (5 MVP sections) "
            "from scripts/fetch_ecfr_title8_sample.py"
        ),
        "created_by": "<local-username via whoami>",
    }


def _plan_ingestion_job(source_date: str, section_count: int) -> dict[str, Any]:
    return {
        "source_name": "eCFR Title 8",
        "status_start": "running",
        "status_end": "success",
        "triggered_by": "cli",
        "records_added": 1 + 1 + section_count + section_count,  # raw_doc + legal_doc + sections + chunks
        "records_updated": 1,  # dataset_version building→ready flip
        "error_message": None,
        "dataset_version_id": "<dataset_versions.id from above>",
    }


def _plan_raw_document(
    source_url: str,
    source_date: str,
    xml_exists: bool,
    xml_sha256: str | None,
) -> dict[str, Any]:
    return {
        "source_id": "<source_registry.id WHERE source_name='eCFR Title 8'>",
        "external_id": "title-8-full",
        "title": "eCFR Title 8 — Aliens and Nationality (full XML)",
        "citation": "8 CFR Title 8",
        "official_url": source_url,
        "raw_format": "xml",
        "raw_content": "<full XML from raw_title8_{source_date}.xml>" if xml_exists else "<NOT AVAILABLE>",
        "content_hash": xml_sha256 if xml_sha256 else "<not computable — raw XML missing>",
        "effective_date": source_date,
        "version_date": source_date,
        "idempotency_key": "content_hash",
    }


def _plan_legal_document(source_url: str, source_date: str) -> dict[str, Any]:
    return {
        "raw_document_id": "<raw_documents.id from above>",
        "source_type": "regulation",
        "title": "eCFR Title 8 Sample",
        "citation": "8 CFR Title 8",
        "jurisdiction": "federal",
        "publisher": "eCFR",
        "official_url": source_url,
        "effective_date": source_date,
        "version_date": source_date,
        "idempotency_key": "(raw_document_id, source_type)",
    }


def _plan_section(section: dict[str, Any]) -> dict[str, Any]:
    sec_num = section.get("section_number", "")
    mapping = TOPIC_MAP.get(sec_num, {})
    snippet = section.get("text_snippet", "")
    cleaned = " ".join(snippet.split())  # whitespace-normalized
    return {
        "section_number": sec_num,
        "section_title": section.get("title"),
        "citation": section.get("citation"),
        "official_url": section.get("official_url"),
        "text_length": section.get("text_length"),
        "topic": mapping.get("topic", "<unmapped>"),
        "subtopic": mapping.get("subtopic", "<unmapped>"),
        "risk_level": mapping.get("risk_level", "<unmapped>"),
        "official_text": f"<text_snippet ({len(snippet)} chars — full extraction deferred)>",
        "cleaned_text": f"<whitespace-normalized snippet ({len(cleaned)} chars)>",
        "effective_date": section.get("source_date"),
        "version_date": section.get("source_date"),
        "document_id": "<legal_documents.id from above>",
        "idempotency_key": "(document_id, section_number)",
    }


def _plan_chunk(section_plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "section_id": f"<legal_sections.id WHERE section_number='{section_plan['section_number']}'>",
        "chunk_index": 0,
        "chunk_text": section_plan["cleaned_text"],
        "plain_language_summary": None,
        "citation": section_plan["citation"],
        "topic": section_plan["topic"],
        "subtopic": section_plan["subtopic"],
        "risk_level": section_plan["risk_level"],
        "official_url": section_plan["official_url"],
        "embedding": None,
        "dataset_version_id": "<dataset_versions.id from above>",
        "is_active": False,
        "idempotency_key": "(section_id, chunk_index, dataset_version_id)",
    }


# ---------------------------------------------------------------------------
# Report printing
# ---------------------------------------------------------------------------

_DIVIDER = "-" * 72


def _print_report(
    preview_path: Path,
    preview: dict[str, Any],
    xml_path: Path,
    xml_exists: bool,
    xml_sha256: str | None,
    section_plans: list[dict[str, Any]],
    chunk_plans: list[dict[str, Any]],
    dataset_version: dict[str, Any],
    ingestion_job: dict[str, Any],
    raw_doc: dict[str, Any],
    legal_doc: dict[str, Any],
) -> None:
    source_date = preview.get("source_date", "<unknown>")

    print(_DIVIDER)
    print("DRY-RUN: eCFR Title 8 → Database Insert Simulation")
    print("(No database writes. No embeddings. Public legal-source data only.)")
    print(_DIVIDER)

    print("\n[INPUT]")
    print(f"  preview file    : {preview_path}")
    print(f"  source_date     : {source_date}")
    print(f"  section count   : {len(section_plans)}")
    print(f"  raw XML path    : {xml_path}")
    print(f"  raw_xml_exists  : {xml_exists}")
    if xml_sha256:
        print(f"  raw_xml_sha256  : {xml_sha256}")

    print("\n[source_registry lookup — READ ONLY, no insert]")
    print("  SELECT id FROM source_registry WHERE source_name = 'eCFR Title 8'")
    print("  → expected: 1 row (inserted by initial migration seed)")

    print("\n[dataset_versions — WOULD INSERT 1 row]")
    for k, v in dataset_version.items():
        print(f"  {k:<22}: {v!r}")

    print("\n[ingestion_jobs — WOULD INSERT 1 row]")
    for k, v in ingestion_job.items():
        print(f"  {k:<22}: {v!r}")

    print("\n[raw_documents — WOULD INSERT 1 row]")
    for k, v in raw_doc.items():
        print(f"  {k:<22}: {v!r}")

    print("\n[legal_documents — WOULD INSERT 1 row]")
    for k, v in legal_doc.items():
        print(f"  {k:<22}: {v!r}")

    print(f"\n[legal_sections — WOULD INSERT {len(section_plans)} rows]")
    for i, sp in enumerate(section_plans, 1):
        print(f"  --- section {i}: {sp['section_number']} ---")
        for k in ("section_title", "citation", "topic", "subtopic", "risk_level",
                  "text_length", "effective_date", "idempotency_key"):
            print(f"    {k:<22}: {sp[k]!r}")

    print(f"\n[legal_chunks — WOULD INSERT {len(chunk_plans)} rows]")
    for i, cp in enumerate(chunk_plans, 1):
        print(f"  --- chunk {i} (section {section_plans[i-1]['section_number']}) ---")
        for k in ("chunk_index", "topic", "subtopic", "risk_level",
                  "embedding", "is_active", "idempotency_key"):
            print(f"    {k:<22}: {cp[k]!r}")

    print("\n[tables NOT written by ingestion — intentionally excluded]")
    for t in EXCLUDED_TABLES:
        print(f"  {t}")

    print()
    print(_DIVIDER)


def _print_json_summary(
    source_date: str,
    dataset_version_name: str,
    xml_exists: bool,
    xml_sha256: str | None,
    section_count: int,
) -> None:
    summary: dict[str, Any] = {
        "status": "dry_run_ok",
        "would_insert": {
            "dataset_versions": 1,
            "ingestion_jobs": 1,
            "raw_documents": 1,
            "legal_documents": 1,
            "legal_sections": section_count,
            "legal_chunks": section_count,
        },
        "would_not_write_tables": EXCLUDED_TABLES,
        "source_date": source_date,
        "dataset_version_name": dataset_version_name,
        "raw_xml_exists": xml_exists,
    }
    if xml_sha256:
        summary["raw_xml_sha256"] = xml_sha256

    print(json.dumps(summary, indent=2))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    # Resolve preview file
    if args.preview_file is not None:
        preview_path = Path(args.preview_file)
        if not preview_path.is_file():
            print(f"ERROR: --preview-file does not exist: {preview_path}")
            return 1
    else:
        found = _find_newest_preview()
        if found is None:
            print(f"ERROR: no preview file matches {DEFAULT_PREVIEW_GLOB}.")
            print(
                "       Run `python scripts/fetch_ecfr_title8_sample.py` first, "
                "then run this script from the repo root."
            )
            return 1
        preview_path = found

    # Load and basic-check the preview JSON
    try:
        with preview_path.open("r", encoding="utf-8") as fp:
            preview: dict[str, Any] = json.load(fp)
    except json.JSONDecodeError as exc:
        print(f"ERROR: {preview_path} is not valid JSON: {exc}")
        return 1
    except OSError as exc:
        print(f"ERROR: could not read {preview_path}: {exc}")
        return 1

    if not isinstance(preview, dict):
        print(f"ERROR: {preview_path} top-level JSON is not an object.")
        return 1

    sections = preview.get("sections")
    if not isinstance(sections, list) or not sections:
        print(f"ERROR: {preview_path} has no sections. Run the fetcher first.")
        return 1

    source_date: str = preview.get("source_date", "")
    source_url: str = preview.get("source_url", "")

    # Locate companion raw XML
    xml_path = _companion_xml_path(source_date)
    xml_exists = xml_path.is_file()
    xml_sha256: str | None = None
    if xml_exists:
        xml_sha256 = _sha256_of_file(xml_path)

    # Build planned inserts
    section_plans = [_plan_section(s) for s in sections]
    chunk_plans = [_plan_chunk(sp) for sp in section_plans]
    dataset_version = _plan_dataset_version(source_date)
    ingestion_job = _plan_ingestion_job(source_date, len(section_plans))
    raw_doc = _plan_raw_document(source_url, source_date, xml_exists, xml_sha256)
    legal_doc = _plan_legal_document(source_url, source_date)

    # Print human-readable report
    _print_report(
        preview_path=preview_path,
        preview=preview,
        xml_path=xml_path,
        xml_exists=xml_exists,
        xml_sha256=xml_sha256,
        section_plans=section_plans,
        chunk_plans=chunk_plans,
        dataset_version=dataset_version,
        ingestion_job=ingestion_job,
        raw_doc=raw_doc,
        legal_doc=legal_doc,
    )

    # Print compact JSON summary
    _print_json_summary(
        source_date=source_date,
        dataset_version_name=dataset_version["version_name"],
        xml_exists=xml_exists,
        xml_sha256=xml_sha256,
        section_count=len(section_plans),
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
