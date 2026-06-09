#!/usr/bin/env python3
"""
Smart chunker for eCFR Title 8.
- Hierarchy-aware parsing (part → section → subsection → paragraph → clause)
- Boundary-aware chunking (never splits mid-sentence)
- Two-layer metadata (structural + semantic)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

import httpx

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ECFR_TITLES_URL = "https://www.ecfr.gov/api/versioner/v1/titles"
ECFR_VERSIONER_URL = "https://www.ecfr.gov/api/versioner/v1/full/{date}/title-8.xml"
ECFR_SECTION_URL = "https://www.ecfr.gov/current/title-8/section-{section}"

MAX_CHUNK_CHARS = 2000
MIN_CHUNK_CHARS = 100

USER_AGENT = "Immigration-Law-Guidance-App/2.0 (smart-chunker)"

# ---------------------------------------------------------------------------
# Layer 2: Semantic tagging maps
# ---------------------------------------------------------------------------

VISA_TYPE_MAP: dict[str, list[str]] = {
    "H-1B":       ["h-1b", "h1b", "specialty occupation", "214.2(h)"],
    "H-2A":       ["h-2a", "h2a", "agricultural worker"],
    "H-2B":       ["h-2b", "h2b", "temporary nonagricultural"],
    "H-4":        ["h-4", "h4", "214.2(h)(9)(iv)", "h-4 dependent"],
    "F-1":        ["f-1", "f1", "214.2(f)", "sevis", "student visa"],
    "F-2":        ["f-2", "f2", "214.2(f)(3)"],
    "J-1":        ["j-1", "j1", "214.2(j)", "exchange visitor"],
    "J-2":        ["j-2", "j2"],
    "L-1":        ["l-1", "l1", "intracompany transferee", "214.2(l)"],
    "O-1":        ["o-1", "o1", "extraordinary ability", "214.2(o)"],
    "TN":         ["tn status", "trade nafta", "usmca", "214.6"],
    "B-1":        ["b-1", "b1", "business visitor", "214.2(b)"],
    "B-2":        ["b-2", "b2", "tourist", "pleasure visitor"],
    "asylum":     ["asylum", "asylee", "208.", "pending asylum", "affirmative asylum"],
    "refugee":    ["refugee", "207.", "refugee status"],
    "green_card": ["lawful permanent resident", "lpr", "permanent residence", "adjustment of status", "245."],
    "EAD":        ["employment authorization", "274a.12", "i-765", "ead", "work permit"],
    "OPT":        ["optional practical training", "opt", "stem opt", "214.2(f)(10)"],
    "CPT":        ["curricular practical training", "cpt", "214.2(f)(10)(i)"],
    "DACA":       ["daca", "deferred action", "childhood arrivals"],
    "TPS":        ["temporary protected status", "tps", "244."],
    "removal":    ["removal proceedings", "deportation", "239.", "notice to appear"],
    "naturalization": ["naturalization", "citizenship", "316.", "n-400"],
    "parole":     ["parole", "212.5", "humanitarian parole"],
    "VAWA":       ["vawa", "violence against women", "204.2(c)"],
}

TOPIC_MAP: dict[str, list[str]] = {
    "employment_authorization": ["employment authorization", "work permit", "authorized to work", "274a"],
    "status_maintenance":       ["maintain status", "status violation", "out of status", "unlawful presence"],
    "extension":                ["extension of stay", "extend status", "i-129", "i-539"],
    "change_of_status":         ["change of status", "change nonimmigrant", "i-539"],
    "adjustment_of_status":     ["adjustment of status", "i-485", "245.", "lawful permanent"],
    "travel":                   ["advance parole", "travel document", "reentry permit", "131."],
    "cap":                      ["h-1b cap", "annual cap", "numerical limit", "lottery"],
    "portability":              ["portability", "ac21", "180 days", "same or similar"],
    "premium_processing":       ["premium processing", "i-907", "expedite"],
    "petition":                 ["petition", "i-129", "i-140", "i-130", "i-360"],
    "interview":                ["interview", "consular", "visa interview"],
    "biometrics":               ["biometrics", "fingerprint", "asis"],
    "fee":                      ["filing fee", "fee waiver", "i-912"],
    "appeal":                   ["appeal", "motion to reopen", "bia", "aao"],
    "inadmissibility":          ["inadmissible", "grounds of inadmissibility", "212(a)"],
    "deportability":            ["deportable", "grounds of deportability", "237(a)"],
    "bond":                     ["bond", "custody", "detention", "236."],
    "asylum_application":       ["asylum application", "i-589", "one year", "bar to asylum"],
    "withholding":              ["withholding of removal", "cat", "convention against torture"],
}

FORM_MAP: dict[str, list[str]] = {
    "I-129":  ["i-129", "form i-129", "petition for nonimmigrant worker"],
    "I-130":  ["i-130", "form i-130", "petition for alien relative"],
    "I-131":  ["i-131", "form i-131", "travel document"],
    "I-140":  ["i-140", "form i-140", "immigrant petition"],
    "I-485":  ["i-485", "form i-485", "adjustment of status application"],
    "I-539":  ["i-539", "form i-539", "change or extend status"],
    "I-589":  ["i-589", "form i-589", "asylum application"],
    "I-601":  ["i-601", "form i-601", "waiver"],
    "I-765":  ["i-765", "form i-765", "employment authorization"],
    "I-797":  ["i-797", "form i-797", "notice of action"],
    "I-864":  ["i-864", "form i-864", "affidavit of support"],
    "I-90":   ["i-90", "form i-90", "renew green card"],
    "I-9":    [" i-9 ", "form i-9", "employment eligibility verification"],
    "N-400":  ["n-400", "form n-400", "naturalization application"],
    "DS-160": ["ds-160", "nonimmigrant visa application"],
}

ACTION_MAP: dict[str, list[str]] = {
    "file":            ["must file", "shall file", "may file", "submit", "filing"],
    "renew":           ["renew", "renewal", "extend"],
    "apply":           ["apply", "application", "request"],
    "travel":          ["travel", "depart", "return", "reentry"],
    "change_employer": ["change employer", "new employer", "portability"],
    "work":            ["authorized to work", "employment authorized", "begin work"],
    "appeal":          ["appeal", "motion to reopen", "motion to reconsider"],
    "interview":       ["appear for interview", "attend interview"],
}

CONDITION_MAP: dict[str, list[str]] = {
    "pending_application":  ["application is pending", "while pending", "pending adjudication"],
    "cap_gap":              ["cap-gap", "cap gap", "october 1"],
    "expired_status":       ["expired", "status expired", "out of status"],
    "overstay":             ["overstay", "remained beyond", "unlawful presence"],
    "180_day_bar":          ["180 days", "180-day bar", "unlawful presence bar"],
    "3_year_bar":           ["3-year bar", "three year bar"],
    "10_year_bar":          ["10-year bar", "ten year bar"],
    "criminal_conviction":  ["convicted", "conviction", "criminal", "felony"],
    "previous_removal":     ["previously removed", "prior removal order", "reinstated"],
    "stem_extension":       ["stem extension", "24-month", "stem opt"],
}

RISK_MAP: dict[str, list[str]] = {
    "HIGH":   [
        "removal", "deportation", "criminal", "conviction", "felony",
        "bar", "inadmissible", "unlawful presence", "overstay",
        "misrepresentation", "fraud", "permanently barred",
        "mandatory detention", "aggravated felony",
    ],
    "MEDIUM": [
        "denial", "rejected", "out of status", "violation", "expired",
        "cap-gap", "pending", "overstay", "accruing unlawful",
        "employment authorization", "waiver required",
    ],
    "LOW": [],  # default
}

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class LegalChunk:
    # Content
    chunk_text: str
    citation: str
    official_url: str

    # Layer 1: Structural
    part: str
    section: str
    subsection: str
    paragraph: str
    level: str  # section | subsection | paragraph | clause

    # Layer 2: Semantic
    visa_types: list[str]
    topics: list[str]
    forms: list[str]
    actions: list[str]
    conditions: list[str]
    risk_level: str

    # Provenance
    source_date: str
    chunk_index: int = 0


@dataclass
class ParsedSection:
    section_number: str
    citation: str
    title: str | None
    official_url: str
    full_text: str
    source_date: str
    children: list[ParsedSection] = field(default_factory=list)


# ---------------------------------------------------------------------------
# XML Parsing — hierarchy aware
# ---------------------------------------------------------------------------

_WS_RE = re.compile(r"\s+")

def _clean(text: str) -> str:
    return _WS_RE.sub(" ", text).strip()

def _get_text(elem: ET.Element) -> str:
    return _clean("".join(elem.itertext()))

def _parse_hierarchy(root: ET.Element, source_date: str) -> list[ParsedSection]:
    """Walk XML tree and extract sections with their hierarchy."""
    sections = []
    for elem in root.iter():
        if elem.get("TYPE") == "SECTION" and elem.get("N"):
            section_number = elem.get("N", "").strip()
            if not section_number:
                continue
            heading_elem = elem.find("HEAD")
            title = _clean("".join(heading_elem.itertext())) if heading_elem is not None else None
            full_text = _get_text(elem)
            if len(full_text) < 50:
                continue
            sections.append(ParsedSection(
                section_number=section_number,
                citation=f"8 CFR § {section_number}",
                title=title,
                official_url=ECFR_SECTION_URL.format(section=section_number),
                full_text=full_text,
                source_date=source_date,
            ))
    return sections


# ---------------------------------------------------------------------------
# Layer 1: Structural metadata extractor
# ---------------------------------------------------------------------------

# Matches patterns like (a), (b)(1), (h)(9)(iv), (2)(i)(A)
_SUBSECTION_RE = re.compile(
    r'(\([a-zA-Z0-9]+\)(?:\([a-zA-Z0-9]+\))*)'
)


def canonicalize_ecfr_chunk_citation(section_number: str, chunk_text: str, chunk_citation: str) -> str:
    """Correct known eCFR hierarchy citations when flat XML text loses parent context.

    The smart chunker splits at visible markers like (i), but in sections such as
    214.2 and 274a.12 those markers may live under parent paragraphs like
    (f)(10) or (b)(6). These targeted overrides keep golden immigration topics
    from being mislabeled.
    """
    text = (chunk_text or "").lstrip()

    if section_number == "214.2":
        if text.startswith("(10) Practical training"):
            return "8 CFR § 214.2(f)(10)"
        if text.startswith("(i) Curricular practical training"):
            return "8 CFR § 214.2(f)(10)(i)"
        if text.startswith("(ii) Optional practical training"):
            return "8 CFR § 214.2(f)(10)(ii)"
        if text.startswith("(iii) Internship with an international organization"):
            return "8 CFR § 214.2(f)(10)(iii)"

    if section_number == "274a.12":
        if text.startswith("(iii) Curricular practical training"):
            return "8 CFR § 274a.12(b)(6)(iii)"

    return chunk_citation


def extract_structural_metadata(section_number: str, chunk_citation: str) -> dict[str, str]:
    """Extract part, section, subsection, paragraph, level from citation."""
    parts = section_number.split(".")
    part = parts[0] if parts else section_number
    section = section_number

    # Find subsection markers in the citation
    markers = _SUBSECTION_RE.findall(chunk_citation)

    subsection = ""
    paragraph = ""
    level = "section"

    if len(markers) >= 1:
        subsection = f"{section}{markers[0]}"
        level = "subsection"
    if len(markers) >= 2:
        paragraph = f"{section}{''.join(markers[:2])}"
        level = "paragraph"
    if len(markers) >= 3:
        level = "clause"

    return {
        "part": part,
        "section": section,
        "subsection": subsection,
        "paragraph": paragraph,
        "level": level,
    }


# ---------------------------------------------------------------------------
# Layer 2: Semantic tagger
# ---------------------------------------------------------------------------

def _match_keywords(text: str, keyword_map: dict[str, list[str]]) -> list[str]:
    """Return all keys whose keywords appear in text."""
    text_lower = text.lower()
    matched = []
    for key, keywords in keyword_map.items():
        if any(kw in text_lower for kw in keywords):
            matched.append(key)
    return matched

def _get_risk_level(text: str) -> str:
    text_lower = text.lower()
    for level in ("HIGH", "MEDIUM"):
        if any(kw in text_lower for kw in RISK_MAP[level]):
            return level
    return "LOW"

def tag_chunk(text: str, citation: str) -> dict[str, Any]:
    """Apply both structural and semantic tagging to a chunk."""
    combined = f"{citation} {text}"
    return {
        "visa_types":  _match_keywords(combined, VISA_TYPE_MAP),
        "topics":      _match_keywords(combined, TOPIC_MAP),
        "forms":       _match_keywords(combined, FORM_MAP),
        "actions":     _match_keywords(combined, ACTION_MAP),
        "conditions":  _match_keywords(combined, CONDITION_MAP),
        "risk_level":  _get_risk_level(combined),
    }


# ---------------------------------------------------------------------------
# Smart chunking — boundary aware
# ---------------------------------------------------------------------------

# Matches paragraph markers like (a), (1), (iv), (A) at start of text segment
_PARA_SPLIT_RE = re.compile(r'(?=\s\([a-zA-Z0-9]{1,4}\)\s)')

def _split_at_sentences(text: str, max_chars: int) -> list[str]:
    """Split text at sentence boundaries to fit within max_chars."""
    sentences = re.split(r'(?<=[.;])\s+', text)
    chunks = []
    current = ""
    for sentence in sentences:
        if len(current) + len(sentence) + 1 <= max_chars:
            current = f"{current} {sentence}".strip()
        else:
            if current:
                chunks.append(current)
            current = sentence
    if current:
        chunks.append(current)
    return chunks

def smart_chunk_section(section: ParsedSection) -> list[LegalChunk]:
    """
    Chunk a section using regulatory structure:
    1. Try to split at paragraph boundaries (a), (b), (c)(1) etc.
    2. If a paragraph is still too large, split at sentence boundaries.
    3. Never cut mid-sentence.
    """
    text = section.full_text
    citation = section.citation
    url = section.official_url
    source_date = section.source_date
    section_number = section.section_number

    chunks: list[LegalChunk] = []

    # Split at paragraph markers
    raw_splits = _PARA_SPLIT_RE.split(text)
    segments = [s.strip() for s in raw_splits if s.strip() and len(s.strip()) >= MIN_CHUNK_CHARS]

    # If no paragraph markers found or whole section is small — keep as one chunk
    if len(segments) <= 1 or len(text) <= MAX_CHUNK_CHARS:
        segments = [text]

    chunk_idx = 0
    for seg in segments:
        # If segment fits, use as-is
        if len(seg) <= MAX_CHUNK_CHARS:
            sub_chunks = [seg]
        else:
            # Split large segment at sentence boundaries
            sub_chunks = _split_at_sentences(seg, MAX_CHUNK_CHARS)

        for sub in sub_chunks:
            if len(sub) < MIN_CHUNK_CHARS:
                continue

            # Build citation for this chunk
            markers = _SUBSECTION_RE.findall(sub[:100])
            if markers:
                chunk_citation = f"{citation}{''.join(markers[0])}"
            else:
                chunk_citation = citation

            # Layer 1
            chunk_citation = canonicalize_ecfr_chunk_citation(section_number, sub, chunk_citation)

            structural = extract_structural_metadata(section_number, chunk_citation)

            # Layer 2
            semantic = tag_chunk(sub, chunk_citation)

            chunks.append(LegalChunk(
                chunk_text=sub,
                citation=chunk_citation,
                official_url=url,
                part=structural["part"],
                section=structural["section"],
                subsection=structural["subsection"],
                paragraph=structural["paragraph"],
                level=structural["level"],
                visa_types=semantic["visa_types"],
                topics=semantic["topics"],
                forms=semantic["forms"],
                actions=semantic["actions"],
                conditions=semantic["conditions"],
                risk_level=semantic["risk_level"],
                source_date=source_date,
                chunk_index=chunk_idx,
            ))
            chunk_idx += 1

    return chunks


# ---------------------------------------------------------------------------
# Fetch eCFR
# ---------------------------------------------------------------------------

def fetch_latest_date() -> str:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    resp = httpx.get(ECFR_TITLES_URL, headers=headers, timeout=60)
    resp.raise_for_status()
    titles = resp.json().get("titles", [])
    t8 = next((t for t in titles if t.get("number") == 8), None)
    if not t8:
        raise SystemExit("ERROR: Title 8 not found in eCFR API")
    return t8["latest_issue_date"]

def fetch_xml(date: str) -> bytes:
    url = ECFR_VERSIONER_URL.format(date=date)
    headers = {"User-Agent": USER_AGENT}
    resp = httpx.get(url, headers=headers, timeout=180)
    resp.raise_for_status()
    return resp.content


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

def insert_chunks(db_url: str, chunks: list[LegalChunk], source_date: str, xml_bytes: bytes, source_url: str) -> dict:
    import psycopg

    version_name = f"ecfr-title8-smart-{source_date}"
    xml_sha256 = hashlib.sha256(xml_bytes).hexdigest()

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:

            # source_registry
            cur.execute("SELECT id FROM source_registry WHERE source_name = %s", ("eCFR Title 8",))
            row = cur.fetchone()
            source_id = row[0] if row else None
            if not source_id:
                cur.execute(
                    "INSERT INTO source_registry "
                    "(source_name, source_type, publisher, base_url, access_method, update_frequency, is_official) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id",
                    (
                        "eCFR Title 8",
                        "regulation",
                        "GPO / eCFR",
                        "https://www.ecfr.gov/current/title-8",
                        "api",
                        "daily",
                        True,
                    ),
                )
                source_id = cur.fetchone()[0]

            # dataset_version
            cur.execute(
                "INSERT INTO dataset_versions (version_name, status, notes, created_by) VALUES (%s,'building','Smart chunked Title 8','smart_chunker') RETURNING id",
                (version_name,),
            )
            dataset_version_id = cur.fetchone()[0]

            # raw_document
            cur.execute(
                "INSERT INTO raw_documents (source_id, external_id, title, citation, official_url, raw_format, raw_content, content_hash, effective_date, version_date) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
                (source_id, f"title-8-smart-{source_date}", "eCFR Title 8", "8 CFR Title 8", source_url, "xml", xml_bytes.decode("utf-8", errors="replace"), xml_sha256, source_date, source_date),
            )
            raw_doc_id = cur.fetchone()[0]

            # legal_document
            cur.execute(
                "INSERT INTO legal_documents (raw_document_id, source_type, title, citation, jurisdiction, publisher, official_url, effective_date, version_date) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
                (raw_doc_id, "regulation", "eCFR Title 8 Smart", "8 CFR Title 8", "federal", "eCFR", source_url, source_date, source_date),
            )
            legal_doc_id = cur.fetchone()[0]

            # Group chunks by section
            sections_seen: dict[str, int] = {}

            inserted = 0
            for chunk in chunks:
                sec_key = chunk.section
                if sec_key not in sections_seen:
                    cur.execute(
                        "INSERT INTO legal_sections (document_id, section_number, citation, official_text, cleaned_text, topic, official_url, effective_date, version_date) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
                        (legal_doc_id, chunk.section, chunk.citation, chunk.chunk_text, chunk.chunk_text, ",".join(chunk.topics) or chunk.section, chunk.official_url, source_date, source_date),
                    )
                    sections_seen[sec_key] = cur.fetchone()[0]

                section_id = sections_seen[sec_key]

                cur.execute(
                    """INSERT INTO legal_chunks
                       (section_id, dataset_version_id, chunk_index, chunk_text, citation,
                        topic, official_url,
                        visa_types, topics, forms, actions, conditions, level, part, subsection, paragraph)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (
                        section_id, dataset_version_id, chunk.chunk_index,
                        chunk.chunk_text, chunk.citation,
                        ",".join(chunk.topics) or chunk.section,
                        chunk.official_url,
                        chunk.visa_types, chunk.topics, chunk.forms,
                        chunk.actions, chunk.conditions,
                        chunk.level, chunk.part, chunk.subsection, chunk.paragraph,
                    ),
                )
                inserted += 1

                if inserted % 200 == 0:
                    print(f"  → Inserted {inserted}/{len(chunks)} chunks...")
                    conn.commit()

            cur.execute(
                "UPDATE dataset_versions SET status='ready', completed_at=NOW() WHERE id=%s",
                (dataset_version_id,),
            )
            conn.commit()

    return {"dataset_version_id": dataset_version_id, "inserted": inserted, "version_name": version_name}


# ---------------------------------------------------------------------------
# Embeddings
# ---------------------------------------------------------------------------

def _format_pgvector_literal(vector: list[float]) -> str:
    """Format a numeric vector for pgvector assignment."""
    return "[" + ",".join(str(float(v)) for v in vector) + "]"



def generate_embeddings(db_url: str, dataset_version_id: int, model: str = "mxbai-embed-large") -> int:
    import psycopg

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, chunk_text FROM legal_chunks WHERE dataset_version_id=%s AND embedding IS NULL",
                (dataset_version_id,),
            )
            chunks = cur.fetchall()

    if not chunks:
        print("  → All chunks already embedded")
        return 0

    print(f"  → Embedding {len(chunks)} chunks with {model}...")
    embedded = 0

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            for chunk_id, chunk_text in chunks:
                req = urllib.request.Request(
                    "http://localhost:11434/api/embeddings",
                    data=json.dumps({"model": model, "prompt": chunk_text}).encode(),
                    headers={"Content-Type": "application/json"},
                )
                try:
                    with urllib.request.urlopen(req, timeout=60) as resp:
                        result = json.loads(resp.read())
                        emb = result.get("embedding")
                except Exception as e:
                    print(f"  WARNING: chunk {chunk_id} failed: {e}")
                    continue

                if not emb or len(emb) != 1024:
                    continue

                cur.execute("UPDATE legal_chunks SET embedding=%s::vector WHERE id=%s", (_format_pgvector_literal(emb), chunk_id))
                embedded += 1

                if embedded % 100 == 0:
                    conn.commit()
                    print(f"  → {embedded}/{len(chunks)} embedded")

            conn.commit()

    return embedded


# ---------------------------------------------------------------------------
# Activation
# ---------------------------------------------------------------------------

def activate(db_url: str, dataset_version_id: int) -> None:
    """Activate the new smart eCFR dataset without disabling BIA/INA/USCIS sources."""
    import psycopg
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            # Replace only older eCFR Title 8 datasets. Keep BIA, INA, USCIS Policy Manual,
            # and USCIS Official Pages active so the MVP remains multi-source.
            cur.execute(
                """
                UPDATE legal_chunks
                SET is_active = FALSE
                WHERE dataset_version_id IN (
                    SELECT id
                    FROM dataset_versions
                    WHERE version_name LIKE 'ecfr-title8-%'
                )
                """
            )
            cur.execute(
                """
                UPDATE dataset_versions
                SET status = 'ready', activated_at = NULL
                WHERE status = 'active'
                  AND version_name LIKE 'ecfr-title8-%'
                """
            )
            cur.execute("UPDATE dataset_versions SET status='active', activated_at=NOW() WHERE id=%s", (dataset_version_id,))
            cur.execute("UPDATE legal_chunks SET is_active=TRUE WHERE dataset_version_id=%s", (dataset_version_id,))
            conn.commit()
    print("  → Smart eCFR dataset activated; non-eCFR sources preserved ✓")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Smart chunker for eCFR Title 8")
    parser.add_argument("--date", default=None)
    parser.add_argument("--yes", action="store_true")
    parser.add_argument("--no-embed", action="store_true")
    parser.add_argument("--no-activate", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    # Get date
    source_date = args.date or fetch_latest_date()
    print(f"Source date: {source_date}")

    # Fetch XML
    print("Fetching eCFR Title 8 XML...")
    xml_bytes = fetch_xml(source_date)
    print(f"  → {len(xml_bytes):,} bytes downloaded")

    # Parse
    print("Parsing sections...")
    root = ET.fromstring(xml_bytes)
    sections = _parse_hierarchy(root, source_date)
    if args.limit:
        sections = sections[:args.limit]
    print(f"  → {len(sections)} sections found")

    # Chunk
    print("Smart chunking...")
    all_chunks: list[LegalChunk] = []
    for sec in sections:
        all_chunks.extend(smart_chunk_section(sec))
    print(f"  → {len(all_chunks)} chunks created")

    # Stats
    levels = {}
    for c in all_chunks:
        levels[c.level] = levels.get(c.level, 0) + 1
    print(f"  → Chunk levels: {levels}")

    if not args.yes:
        print("\n--- DRY RUN --- pass --yes to insert")
        # Show sample
        if all_chunks:
            sample = all_chunks[0]
            print(f"\nSample chunk:")
            print(f"  citation:   {sample.citation}")
            print(f"  level:      {sample.level}")
            print(f"  visa_types: {sample.visa_types}")
            print(f"  topics:     {sample.topics}")
            print(f"  forms:      {sample.forms}")
            print(f"  risk:       {sample.risk_level}")
            print(f"  text[:200]: {sample.chunk_text[:200]}")
        return

    # Get DB URL
    db_url = os.environ.get("DATABASE_URL", "")
    if db_url.startswith("postgresql+psycopg://"):
        db_url = db_url.replace("postgresql+psycopg://", "postgresql://", 1)
    if not db_url:
        raise SystemExit("ERROR: DATABASE_URL not set")

    # Insert
    print("Inserting into database...")
    source_url = ECFR_VERSIONER_URL.format(date=source_date)
    result = insert_chunks(db_url, all_chunks, source_date, xml_bytes, source_url)
    print(f"  → {result['inserted']} chunks inserted (version: {result['version_name']})")

    # Embed
    if not args.no_embed:
        print("Generating embeddings...")
        n = generate_embeddings(db_url, result["dataset_version_id"])
        print(f"  → {n} chunks embedded")

    # Activate
    if not args.no_activate:
        print("Activating dataset...")
        activate(db_url, result["dataset_version_id"])

    print("\n✅ Smart chunking complete!")


if __name__ == "__main__":
    main()
