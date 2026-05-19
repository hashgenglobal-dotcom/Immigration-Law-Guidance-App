#!/usr/bin/env python3
"""Insert validated eCFR Title 8 preview data into the local PostgreSQL database.

This is the first real local ingestion script for public eCFR legal-source data.
It reads the validated preview JSON and companion raw XML from data/ecfr_samples/,
then inserts the data into the existing PostgreSQL schema inside one transaction.

Privacy
-------
This script handles public legal-source data only.
- It does NOT process user questions.
- It does NOT write to privacy_safe_answer_logs.
- It does NOT write to admin_users.
- It does NOT generate embeddings.
- It does NOT call Ollama, OpenAI, Anthropic, or any public AI API.

Usage
-----
    # Use newest preview and DATABASE_URL from backend/.env
    uv run --project backend python scripts/insert_ecfr_preview_to_db.py

    # Explicit preview file
    uv run --project backend python scripts/insert_ecfr_preview_to_db.py \\
        --preview-file data/ecfr_samples/title8_sample_preview_2026-05-12.json

    # Explicit database URL
    uv run --project backend python scripts/insert_ecfr_preview_to_db.py \\
        --database-url "postgresql://user@localhost:5432/immigration_law_dev"

Exit codes
----------
* 0 — all inserts committed successfully.
* 1 — validation failure, connection error, or insert failure.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

# psycopg (v3) is the only non-stdlib dependency.
# Run with: uv run --project backend python scripts/insert_ecfr_preview_to_db.py
try:
    import psycopg
except ImportError:
    print(
        "ERROR: psycopg (v3) is not installed in the current Python environment.\n"
        "       Run this script with:\n"
        "         uv run --project backend python scripts/insert_ecfr_preview_to_db.py"
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_PREVIEW_GLOB = "data/ecfr_samples/title8_sample_preview_*.json"
BACKEND_ENV_PATH = Path("backend/.env")
SOURCE_NAME = "eCFR Title 8"

# Deterministic topic mapping for the five MVP sections.
# Assigned by hand so inserts are reproducible without any AI classifier.
TOPIC_MAP: dict[str, dict[str, str]] = {
    "208.7":   {"topic": "asylum",                   "subtopic": "employment_authorization", "risk_level": "medium"},
    "208.4":   {"topic": "asylum",                   "subtopic": "filing_deadline",          "risk_level": "high"},
    "245.1":   {"topic": "adjustment_of_status",     "subtopic": "eligibility",              "risk_level": "medium"},
    "274a.12": {"topic": "employment_authorization", "subtopic": "categories",               "risk_level": "medium"},
    "239.1":   {"topic": "removal_proceedings",      "subtopic": "notice_to_appear",         "risk_level": "high"},
}

# Tables intentionally never written to by any ingestion script.
EXCLUDED_TABLES = ("privacy_safe_answer_logs", "admin_users")

_DIVIDER = "-" * 72


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Insert validated eCFR Title 8 preview data into PostgreSQL. "
            "Public legal-source data only; never touches user data or answer logs."
        ),
    )
    parser.add_argument(
        "--preview-file",
        default=None,
        help=(
            "Path to a specific preview JSON file. "
            f"Default: newest file matching {DEFAULT_PREVIEW_GLOB} "
            "(run from the repo root)."
        ),
    )
    parser.add_argument(
        "--database-url",
        default=None,
        help=(
            "PostgreSQL connection URL. Accepts postgresql://... or "
            "postgresql+psycopg://... (SQLAlchemy-style prefix is stripped). "
            "Default: DATABASE_URL env var, then backend/.env."
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
    return Path(f"data/ecfr_samples/raw_title8_{source_date}.xml")


# ---------------------------------------------------------------------------
# .env parser (stdlib only — no dotenv dependency)
# ---------------------------------------------------------------------------


def _read_env_file(path: Path) -> dict[str, str]:
    """Parse KEY=value lines from a .env file; handles double- and single-quoted values."""
    result: dict[str, str] = {}
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return result
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, raw_val = line.partition("=")
        key = key.strip()
        raw_val = raw_val.strip()
        if len(raw_val) >= 2 and raw_val[0] == raw_val[-1] and raw_val[0] in ('"', "'"):
            raw_val = raw_val[1:-1]
        result[key] = raw_val
    return result


def _resolve_database_url(arg_url: str | None) -> str | None:
    """Return the DATABASE_URL from CLI arg, env var, or backend/.env (in that order)."""
    if arg_url:
        return arg_url
    env_val = os.environ.get("DATABASE_URL")
    if env_val:
        return env_val
    dotenv = _read_env_file(BACKEND_ENV_PATH)
    return dotenv.get("DATABASE_URL")


def _normalize_db_url(url: str) -> str:
    """Strip SQLAlchemy driver suffix: postgresql+psycopg://... → postgresql://..."""
    for prefix in ("postgresql+psycopg://", "postgres+psycopg://"):
        if url.startswith(prefix):
            scheme = prefix.split("+")[0]
            return scheme + "://" + url[len(prefix):]
    return url


# ---------------------------------------------------------------------------
# SHA-256
# ---------------------------------------------------------------------------


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# Preview loading and validation
# ---------------------------------------------------------------------------

_REQUIRED_TOP_LEVEL = ("source_date", "source_url", "sections")
_REQUIRED_SECTION = (
    "citation", "section_number", "title",
    "official_url", "text_snippet", "text_length",
)


def _load_and_validate_preview(path: Path) -> dict[str, Any]:
    """Load and minimally validate the preview JSON. Raises ValueError on bad input."""
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"cannot read {path}: {exc}") from exc
    try:
        preview: Any = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(preview, dict):
        raise ValueError(f"{path} top-level JSON value is not an object")
    for field in _REQUIRED_TOP_LEVEL:
        if field not in preview:
            raise ValueError(f"{path}: missing required field {field!r}")
    sections = preview["sections"]
    if not isinstance(sections, list) or not sections:
        raise ValueError(f"{path}: 'sections' must be a non-empty list")
    for i, sec in enumerate(sections):
        if not isinstance(sec, dict):
            raise ValueError(f"{path}: sections[{i}] is not an object")
        for field in _REQUIRED_SECTION:
            if field not in sec:
                raise ValueError(f"{path}: sections[{i}] missing required field {field!r}")
    return preview


# ---------------------------------------------------------------------------
# Database insertion — one transaction
# ---------------------------------------------------------------------------


def _run_insertion(
    db_url: str,
    preview: dict[str, Any],
    xml_bytes: bytes,
    xml_sha256: str,
    preview_path: Path,
) -> dict[str, Any]:
    """Execute all inserts inside one transaction. Returns a result summary dict.

    On success the transaction is committed. On any exception the transaction
    is rolled back, including the ingestion_jobs 'running' row, so no partial
    state is left in the database.
    """
    source_date_str: str = preview["source_date"]
    source_url: str = preview["source_url"]
    sections: list[dict[str, Any]] = preview["sections"]

    try:
        source_date = datetime.date.fromisoformat(source_date_str)
    except ValueError as exc:
        raise ValueError(f"invalid source_date {source_date_str!r}: {exc}") from exc

    version_name = f"ecfr-title8-sample-{source_date_str}"
    xml_text = xml_bytes.decode("utf-8", errors="replace")

    # Per-table counters
    ins: dict[str, int] = {t: 0 for t in (
        "dataset_versions", "ingestion_jobs",
        "raw_documents", "legal_documents",
        "legal_sections", "legal_chunks",
    )}
    reu: dict[str, int] = {t: 0 for t in ins}

    ids: dict[str, int] = {}
    section_rows: list[dict[str, Any]] = []

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:

            # ------------------------------------------------------------------
            # source_registry — read-only lookup; must exist from migration seed
            # ------------------------------------------------------------------
            cur.execute(
                "SELECT id FROM source_registry WHERE source_name = %s",
                (SOURCE_NAME,),
            )
            row = cur.fetchone()
            if row is None:
                raise RuntimeError(
                    f"source_registry row for {SOURCE_NAME!r} not found. "
                    "Re-run database/migrations/001-initial-schema.sql to seed source_registry."
                )
            ids["source_registry_id"] = row[0]

            # ------------------------------------------------------------------
            # dataset_versions — reuse if version_name already exists
            # ------------------------------------------------------------------
            cur.execute(
                "SELECT id FROM dataset_versions WHERE version_name = %s",
                (version_name,),
            )
            row = cur.fetchone()
            if row:
                ids["dataset_version_id"] = row[0]
                reu["dataset_versions"] += 1
            else:
                cur.execute(
                    """
                    INSERT INTO dataset_versions (version_name, status, notes, created_by)
                    VALUES (%s, 'building', %s, 'cli')
                    RETURNING id
                    """,
                    (
                        version_name,
                        "First eCFR Title 8 sample ingestion from validated preview",
                    ),
                )
                ids["dataset_version_id"] = cur.fetchone()[0]
                ins["dataset_versions"] += 1

            # ------------------------------------------------------------------
            # ingestion_jobs — always a new row per run (status starts 'running')
            # ------------------------------------------------------------------
            cur.execute(
                """
                INSERT INTO ingestion_jobs (
                    source_name, status, triggered_by,
                    started_at, dataset_version_id
                ) VALUES (%s, 'running', 'cli', NOW(), %s)
                RETURNING id
                """,
                (SOURCE_NAME, ids["dataset_version_id"]),
            )
            ids["ingestion_job_id"] = cur.fetchone()[0]
            ins["ingestion_jobs"] += 1

            # ------------------------------------------------------------------
            # raw_documents — reuse if content_hash already exists
            # ------------------------------------------------------------------
            cur.execute(
                "SELECT id FROM raw_documents WHERE content_hash = %s",
                (xml_sha256,),
            )
            row = cur.fetchone()
            if row:
                ids["raw_document_id"] = row[0]
                reu["raw_documents"] += 1
            else:
                cur.execute(
                    """
                    INSERT INTO raw_documents (
                        source_id, external_id, title, citation,
                        official_url, raw_format, raw_content,
                        content_hash, effective_date, version_date
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        ids["source_registry_id"],
                        f"title-8-full-{source_date_str}",
                        "eCFR Title 8 — Aliens and Nationality",
                        "8 CFR Title 8",
                        source_url,
                        "xml",
                        xml_text,
                        xml_sha256,
                        source_date,
                        source_date,
                    ),
                )
                ids["raw_document_id"] = cur.fetchone()[0]
                ins["raw_documents"] += 1

            # ------------------------------------------------------------------
            # legal_documents — reuse if (raw_document_id, citation) exists
            # ------------------------------------------------------------------
            legal_doc_citation = "8 CFR Title 8"
            cur.execute(
                """
                SELECT id FROM legal_documents
                WHERE raw_document_id = %s AND citation = %s
                """,
                (ids["raw_document_id"], legal_doc_citation),
            )
            row = cur.fetchone()
            if row:
                ids["legal_document_id"] = row[0]
                reu["legal_documents"] += 1
            else:
                cur.execute(
                    """
                    INSERT INTO legal_documents (
                        raw_document_id, source_type, title, citation,
                        jurisdiction, publisher, official_url,
                        effective_date, version_date
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        ids["raw_document_id"],
                        "regulation",
                        "eCFR Title 8 Sample",
                        legal_doc_citation,
                        "federal",
                        "eCFR",
                        source_url,
                        source_date,
                        source_date,
                    ),
                )
                ids["legal_document_id"] = cur.fetchone()[0]
                ins["legal_documents"] += 1

            # ------------------------------------------------------------------
            # legal_sections + legal_chunks — one row per section
            # ------------------------------------------------------------------
            for section in sections:
                sec_num: str = section["section_number"]
                mapping = TOPIC_MAP.get(sec_num, {})

                # TODO: full section text extraction should be improved in a later
                # milestone (see docs/ecfr-preview-to-db-mapping-plan.md §8.1).
                # For now, text_snippet is used as official_text.
                text = section.get("text_snippet", "")
                cleaned = " ".join(text.split())

                # legal_sections: reuse if (document_id, section_number) exists
                cur.execute(
                    """
                    SELECT id FROM legal_sections
                    WHERE document_id = %s AND section_number = %s
                    """,
                    (ids["legal_document_id"], sec_num),
                )
                row = cur.fetchone()
                if row:
                    section_id: int = row[0]
                    reu["legal_sections"] += 1
                    sec_action = "reused"
                else:
                    cur.execute(
                        """
                        INSERT INTO legal_sections (
                            document_id, section_number, section_title, citation,
                            official_text, cleaned_text,
                            topic, subtopic, audience,
                            official_url, effective_date, version_date
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                        """,
                        (
                            ids["legal_document_id"],
                            sec_num,
                            section.get("title"),
                            section.get("citation"),
                            text,
                            cleaned,
                            mapping.get("topic"),
                            mapping.get("subtopic"),
                            None,  # audience: deferred to later milestone
                            section.get("official_url"),
                            source_date,
                            source_date,
                        ),
                    )
                    section_id = cur.fetchone()[0]
                    ins["legal_sections"] += 1
                    sec_action = "inserted"

                # legal_chunks: reuse if (section_id, chunk_index, dataset_version_id) exists
                cur.execute(
                    """
                    SELECT id FROM legal_chunks
                    WHERE section_id = %s AND chunk_index = %s AND dataset_version_id = %s
                    """,
                    (section_id, 0, ids["dataset_version_id"]),
                )
                row = cur.fetchone()
                if row:
                    reu["legal_chunks"] += 1
                    chunk_action = "reused"
                else:
                    # search_vector is populated automatically by the DB trigger.
                    cur.execute(
                        """
                        INSERT INTO legal_chunks (
                            section_id, chunk_index, chunk_text,
                            plain_language_summary, citation,
                            topic, subtopic, risk_level, official_url,
                            embedding, dataset_version_id, is_active
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            section_id,
                            0,
                            cleaned,
                            None,   # plain_language_summary: deferred
                            section.get("citation"),
                            mapping.get("topic"),
                            mapping.get("subtopic"),
                            mapping.get("risk_level"),
                            section.get("official_url"),
                            None,   # embedding: NULL until Ollama phase
                            ids["dataset_version_id"],
                            False,  # is_active: FALSE until explicit publish step
                        ),
                    )
                    ins["legal_chunks"] += 1
                    chunk_action = "inserted"

                section_rows.append({
                    "section_number": sec_num,
                    "section_id": section_id,
                    "topic": mapping.get("topic", "<unmapped>"),
                    "subtopic": mapping.get("subtopic", "<unmapped>"),
                    "risk_level": mapping.get("risk_level", "<unmapped>"),
                    "section_action": sec_action,
                    "chunk_action": chunk_action,
                })

            # ------------------------------------------------------------------
            # Mark dataset_version ready (building → ready)
            # ------------------------------------------------------------------
            cur.execute(
                """
                UPDATE dataset_versions
                SET status = 'ready', completed_at = NOW()
                WHERE id = %s
                """,
                (ids["dataset_version_id"],),
            )

            # ------------------------------------------------------------------
            # Finalize ingestion_job with actual counts (success)
            # ------------------------------------------------------------------
            total_added = sum(ins.values())
            total_reused = sum(reu.values())
            cur.execute(
                """
                UPDATE ingestion_jobs
                SET status = 'success',
                    finished_at = NOW(),
                    records_added = %s,
                    records_updated = %s,
                    error_message = NULL
                WHERE id = %s
                """,
                (total_added, total_reused, ids["ingestion_job_id"]),
            )

        # psycopg3 connection context manager commits here on normal exit.

    return {
        "preview_file": str(preview_path),
        "source_date": source_date_str,
        "version_name": version_name,
        "ids": ids,
        "inserted": ins,
        "reused": reu,
        "total_added": total_added,
        "total_reused": total_reused,
        "section_rows": section_rows,
    }


# ---------------------------------------------------------------------------
# Summary printing
# ---------------------------------------------------------------------------


def _print_summary(result: dict[str, Any]) -> None:
    ids = result["ids"]
    ins = result["inserted"]
    reu = result["reused"]

    print(_DIVIDER)
    print("eCFR Title 8 → PostgreSQL insert complete")
    print(_DIVIDER)
    print(f"  preview file          : {result['preview_file']}")
    print(f"  source_date           : {result['source_date']}")
    print(f"  dataset_version_name  : {result['version_name']}")
    print(f"  dataset_version_id    : {ids['dataset_version_id']}")
    print(f"  ingestion_job_id      : {ids['ingestion_job_id']}")
    print(f"  source_registry_id    : {ids['source_registry_id']}")
    print(f"  raw_document_id       : {ids['raw_document_id']}")
    print(f"  legal_document_id     : {ids['legal_document_id']}")
    print()
    print(f"  {'Table':<26} {'inserted':>8}  {'reused':>6}")
    print("  " + "-" * 44)
    for table in ("dataset_versions", "ingestion_jobs", "raw_documents",
                  "legal_documents", "legal_sections", "legal_chunks"):
        print(f"  {table:<26} {ins[table]:>8}  {reu[table]:>6}")
    print("  " + "-" * 44)
    print(f"  {'TOTAL':<26} {result['total_added']:>8}  {result['total_reused']:>6}")
    print()
    print("  Sections:")
    for s in result["section_rows"]:
        print(
            f"    {s['section_number']:<12} "
            f"section={s['section_action']:8}  chunk={s['chunk_action']:8}  "
            f"topic={s['topic']}  risk={s['risk_level']}"
        )
    print()
    print("  dataset_versions.status  : ready")
    print("  legal_chunks.is_active   : FALSE  (not activated — intentional)")
    print("  legal_chunks.embedding   : NULL   (embeddings deferred to Ollama phase)")
    print()
    print("  NOTE: The dataset is NOT activated. To make chunks retrievable, run")
    print("        a separate activation step that sets:")
    print("          dataset_versions.status     = 'active'")
    print("          legal_chunks.is_active      = TRUE")
    print("          dataset_versions.activated_at = NOW()")
    print()
    print(f"  Tables NOT written: {', '.join(EXCLUDED_TABLES)}")
    print(_DIVIDER)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    # ---- resolve preview file ----
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

    # ---- load and validate preview JSON ----
    try:
        preview = _load_and_validate_preview(preview_path)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1

    # ---- locate and read companion raw XML ----
    source_date: str = preview["source_date"]
    xml_path = _companion_xml_path(source_date)
    if not xml_path.is_file():
        print(f"ERROR: companion raw XML not found: {xml_path}")
        print(
            "       Run `python scripts/fetch_ecfr_title8_sample.py` to fetch "
            f"the raw XML for source_date {source_date!r}."
        )
        return 1
    try:
        xml_bytes = xml_path.read_bytes()
    except OSError as exc:
        print(f"ERROR: could not read {xml_path}: {type(exc).__name__}")
        return 1
    xml_sha256 = _sha256_hex(xml_bytes)

    # ---- resolve database URL ----
    raw_url = _resolve_database_url(args.database_url)
    if not raw_url:
        print("ERROR: no DATABASE_URL found.")
        print(
            "       Set DATABASE_URL in the environment, pass --database-url, "
            "or add DATABASE_URL to backend/.env."
        )
        return 1
    db_url = _normalize_db_url(raw_url)

    # ---- run insertion ----
    print(f"Inserting eCFR Title 8 preview ({source_date}) → PostgreSQL ...")
    try:
        result = _run_insertion(db_url, preview, xml_bytes, xml_sha256, preview_path)
    except psycopg.OperationalError:
        # OperationalError messages may contain connection details — print class only.
        print("ERROR: could not connect to PostgreSQL (psycopg.OperationalError).")
        print(
            "       Check that PostgreSQL is running and DATABASE_URL points to "
            "the correct host/database."
        )
        return 1
    except (psycopg.Error, RuntimeError) as exc:
        print(f"ERROR: insertion failed ({type(exc).__name__}): {exc}")
        print("       Transaction has been rolled back; the database is unchanged.")
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: unexpected failure ({type(exc).__name__}): {exc}")
        print("       Transaction has been rolled back; the database is unchanged.")
        return 1

    _print_summary(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
