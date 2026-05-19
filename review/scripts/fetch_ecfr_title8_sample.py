#!/usr/bin/env python3
"""Fetch a small public eCFR Title 8 sample and write a JSON preview.

This is the first ingestion-milestone script described in
``docs/ecfr-ingestion-milestone-plan.md``. It deliberately does the
*minimum* useful thing so the parser can be inspected by hand before
we wire any of this into PostgreSQL.

What this script does
---------------------
1. Resolves the snapshot date. If ``--date YYYY-MM-DD`` is passed, that
   value is used as-is. Otherwise the script asks the official titles
   metadata endpoint
       https://www.ecfr.gov/api/versioner/v1/titles
   for Title 8's ``latest_issue_date``. (Today's calendar date is *not*
   used as a default, because eCFR Title 8 is not published every day —
   e.g., 2026-05-14 returns HTTP 404 while the latest issue is
   2026-05-12.)
2. Calls the official eCFR Versioner full-XML API for the resolved date:
       https://www.ecfr.gov/api/versioner/v1/full/{date}/title-8.xml
3. Saves the raw XML response to a git-ignored local folder.
4. Walks the XML and pulls out a small, fixed set of MVP-relevant
   sections (8 CFR § 208.7, § 208.4, § 245.1, § 274a.12, § 239.1).
5. Writes a human-readable JSON preview describing those sections.
6. Prints a short summary.

What this script does NOT do
----------------------------
* It does **not** write to PostgreSQL. There is no `psycopg` call.
* It does **not** generate embeddings.
* It does **not** call Ollama, OpenAI, Anthropic, or any other AI API.
* It does **not** chunk the text for retrieval. That belongs to a
  later milestone.

Privacy
-------
The eCFR (Electronic Code of Federal Regulations) is *public* legal-
source data published by the U.S. Government Publishing Office. No
user questions, user-provided facts, or private case details are
processed by this script. The output is safe to inspect, but the
generated files under ``data/`` are git-ignored and must not be
committed (the root ``.gitignore`` already enforces that).

Usage
-----
    # Auto-detect Title 8's latest available issue date:
    python scripts/fetch_ecfr_title8_sample.py

    # Pin to a specific snapshot date:
    python scripts/fetch_ecfr_title8_sample.py --date 2026-05-12

    # Choose a different output folder (still inside the git-ignored data/ tree):
    python scripts/fetch_ecfr_title8_sample.py --output-dir data/ecfr_samples

Dependencies: Python standard library plus ``requests`` (already used
by ``scripts/test-ollama-embeddings.py``; install with
``pip install requests`` or ``uv pip install requests`` if missing).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import date as date_cls
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET

import requests

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ECFR_TITLES_URL = "https://www.ecfr.gov/api/versioner/v1/titles"
ECFR_VERSIONER_URL = "https://www.ecfr.gov/api/versioner/v1/full/{date}/title-8.xml"
ECFR_SECTION_URL = "https://www.ecfr.gov/current/title-8/section-{section}"
TITLE8_NUMBER = 8

# Target sections for this first milestone (see docs/ecfr-ingestion-milestone-plan.md).
TARGET_SECTIONS: tuple[str, ...] = (
    "208.7",     # Employment authorization for asylum applicants
    "208.4",     # Asylum filing deadlines and exceptions
    "245.1",     # Adjustment of status eligibility
    "274a.12",   # Employment authorization classes
    "239.1",     # Notice to Appear
)

DEFAULT_OUTPUT_DIR = Path("data/ecfr_samples")
TEXT_SNIPPET_CHARS = 1200
HTTP_TIMEOUT_SECONDS = 60
USER_AGENT = (
    "Immigration-Law-Guidance-App/0.1 "
    "(development; public legal-source ingestion sample; contact: hash@hashgen.global)"
)


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class SectionPreview:
    """One parsed eCFR section, in the shape we want to inspect."""

    citation: str
    section_number: str
    title: str | None
    official_url: str
    text_snippet: str
    text_length: int
    source_date: str


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch a small public eCFR Title 8 XML sample and write a JSON preview.",
    )
    parser.add_argument(
        "--date",
        default=None,
        help=(
            "eCFR snapshot date in YYYY-MM-DD form. "
            "If omitted, the script asks the eCFR titles API for "
            "Title 8's latest_issue_date and uses that."
        ),
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help=f"Where to write the raw XML and JSON preview (default: {DEFAULT_OUTPUT_DIR}).",
    )
    return parser.parse_args(argv)


def _validate_date(value: str) -> str:
    """Reject obviously malformed --date inputs early."""
    try:
        date_cls.fromisoformat(value)
    except ValueError as exc:
        raise SystemExit(f"ERROR: --date must be YYYY-MM-DD, got {value!r} ({exc})")
    return value


# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------


def fetch_latest_title8_issue_date() -> str:
    """Return the ``latest_issue_date`` for CFR Title 8 from the eCFR titles API.

    The titles endpoint
    (`https://www.ecfr.gov/api/versioner/v1/titles`) returns a list of
    every CFR title and per-title metadata, including the most recent
    date for which a snapshot exists. We use Title 8's
    ``latest_issue_date`` instead of today's calendar date because the
    full-XML endpoint 404s for dates with no issue (e.g., 2026-05-14
    returned 404 while the latest issue was 2026-05-12).

    Raises ``SystemExit`` with a clear message on network failure,
    non-200 response, malformed JSON, missing Title 8 entry, or a
    missing/blank ``latest_issue_date``.
    """
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }
    try:
        response = requests.get(
            ECFR_TITLES_URL, headers=headers, timeout=HTTP_TIMEOUT_SECONDS
        )
    except requests.RequestException as exc:
        raise SystemExit(
            f"ERROR: network failure fetching {ECFR_TITLES_URL}: "
            f"{type(exc).__name__}"
        )

    if response.status_code != 200:
        snippet = response.text[:300].replace("\n", " ")
        raise SystemExit(
            f"ERROR: eCFR titles API returned HTTP {response.status_code} "
            f"for {ECFR_TITLES_URL}\n       Response snippet: {snippet}"
        )

    try:
        payload = response.json()
    except ValueError as exc:
        raise SystemExit(
            f"ERROR: eCFR titles API returned non-JSON body ({exc}). "
            "Cannot auto-detect Title 8 latest_issue_date; "
            "retry with --date YYYY-MM-DD."
        )

    titles = payload.get("titles") if isinstance(payload, dict) else None
    if not isinstance(titles, list):
        raise SystemExit(
            "ERROR: eCFR titles API JSON did not contain a 'titles' list. "
            "Retry with --date YYYY-MM-DD."
        )

    title8 = next(
        (
            t for t in titles
            if isinstance(t, dict) and t.get("number") == TITLE8_NUMBER
        ),
        None,
    )
    if title8 is None:
        raise SystemExit(
            "ERROR: eCFR titles API response did not include Title 8. "
            "Retry with --date YYYY-MM-DD."
        )

    latest_issue_date = title8.get("latest_issue_date")
    if not isinstance(latest_issue_date, str) or not latest_issue_date.strip():
        raise SystemExit(
            "ERROR: eCFR titles API did not return a usable "
            "latest_issue_date for Title 8. Retry with --date YYYY-MM-DD."
        )

    return _validate_date(latest_issue_date.strip())


def fetch_title8_xml(snapshot_date: str) -> tuple[str, bytes]:
    """Return ``(url, raw_xml_bytes)``. Raises ``SystemExit`` on failure."""
    url = ECFR_VERSIONER_URL.format(date=snapshot_date)
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/xml",
    }
    try:
        response = requests.get(url, headers=headers, timeout=HTTP_TIMEOUT_SECONDS)
    except requests.RequestException as exc:
        raise SystemExit(f"ERROR: network failure fetching {url}: {type(exc).__name__}")

    if response.status_code != 200:
        # Print only status + a short body excerpt; the eCFR API returns
        # small JSON error bodies on 4xx, which are safe to surface.
        snippet = response.text[:300].replace("\n", " ")
        raise SystemExit(
            f"ERROR: eCFR API returned HTTP {response.status_code} for {url}\n"
            f"       Response snippet: {snippet}"
        )

    return url, response.content


# ---------------------------------------------------------------------------
# Parse
# ---------------------------------------------------------------------------


_WHITESPACE_RE = re.compile(r"\s+")


def _clean_text(raw: str) -> str:
    """Collapse runs of whitespace and strip."""
    return _WHITESPACE_RE.sub(" ", raw).strip()


def _iter_section_elements(root: ET.Element) -> Iterable[ET.Element]:
    """Yield every element in the tree that represents a CFR SECTION.

    eCFR/CFR XML marks section containers with ``TYPE="SECTION"``
    (usually on ``DIV8``). We match by attribute rather than by tag
    name so changes in the XHTML schema don't silently break us.
    """
    for elem in root.iter():
        if elem.get("TYPE") == "SECTION" and elem.get("N"):
            yield elem


def _extract_heading(section_elem: ET.Element) -> str | None:
    """Return the first ``<HEAD>`` text inside a section, if any."""
    head = section_elem.find("HEAD")
    if head is None:
        return None
    text = _clean_text("".join(head.itertext()))
    return text or None


def _extract_section_text(section_elem: ET.Element) -> str:
    """Return all descendant text of a section as a single cleaned string."""
    return _clean_text("".join(section_elem.itertext()))


def parse_target_sections(
    xml_bytes: bytes,
    targets: Iterable[str],
    snapshot_date: str,
) -> dict[str, SectionPreview]:
    """Parse the XML and return ``{section_number: SectionPreview}`` for hits."""
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        raise SystemExit(f"ERROR: failed to parse eCFR XML: {exc}")

    wanted = set(targets)
    found: dict[str, SectionPreview] = {}

    for section_elem in _iter_section_elements(root):
        section_number = section_elem.get("N") or ""
        if section_number not in wanted:
            continue

        full_text = _extract_section_text(section_elem)
        heading = _extract_heading(section_elem)
        official_url = ECFR_SECTION_URL.format(section=section_number)

        found[section_number] = SectionPreview(
            citation=f"8 CFR § {section_number}",
            section_number=section_number,
            title=heading,
            official_url=official_url,
            text_snippet=full_text[:TEXT_SNIPPET_CHARS],
            text_length=len(full_text),
            source_date=snapshot_date,
        )

        if len(found) == len(wanted):
            break

    return found


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def _write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _build_preview_payload(
    snapshot_date: str,
    fetch_url: str,
    targeted: Iterable[str],
    found: dict[str, SectionPreview],
) -> dict:
    targeted_list = list(targeted)
    missing = [s for s in targeted_list if s not in found]
    sections = [asdict(found[s]) for s in targeted_list if s in found]
    return {
        "source_name": "eCFR Title 8",
        "source_url": fetch_url,
        "source_date": snapshot_date,
        "targeted_section_count": len(targeted_list),
        "found_section_count": len(sections),
        "missing_sections": missing,
        "sections": sections,
        "note": (
            "Public legal-source data only. Generated by "
            "scripts/fetch_ecfr_title8_sample.py. Do not commit this file."
        ),
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    if args.date is None:
        snapshot_date = fetch_latest_title8_issue_date()
        print(f"Using latest eCFR Title 8 issue date: {snapshot_date}")
    else:
        snapshot_date = _validate_date(args.date)
        print(f"Using user-supplied --date: {snapshot_date}")

    output_dir = Path(args.output_dir)

    raw_path = output_dir / f"raw_title8_{snapshot_date}.xml"
    preview_path = output_dir / f"title8_sample_preview_{snapshot_date}.json"

    fetch_url, xml_bytes = fetch_title8_xml(snapshot_date)
    _write_bytes(raw_path, xml_bytes)

    found = parse_target_sections(xml_bytes, TARGET_SECTIONS, snapshot_date)
    payload = _build_preview_payload(snapshot_date, fetch_url, TARGET_SECTIONS, found)
    _write_json(preview_path, payload)

    missing = payload["missing_sections"]

    print("eCFR Title 8 sample fetch complete.")
    print(f"  fetch URL   : {fetch_url}")
    print(f"  raw XML     : {raw_path}")
    print(f"  JSON preview: {preview_path}")
    print(f"  targeted    : {len(TARGET_SECTIONS)} ({', '.join(TARGET_SECTIONS)})")
    print(f"  found       : {payload['found_section_count']}")
    if missing:
        print(f"  missing     : {', '.join(missing)}")
    else:
        print("  missing     : (none)")
    print(
        "  reminder    : data/ is git-ignored. Do not commit the raw XML "
        "or the JSON preview."
    )

    # Exit non-zero only on hard failures (handled via SystemExit above).
    # Missing target sections are reported but not treated as fatal — the
    # caller can decide whether to retry with a different --date.
    return 0


if __name__ == "__main__":
    sys.exit(main())
