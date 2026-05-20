#!/usr/bin/env python3
"""Validate hybrid retrieval coverage for common immigration categories.

Uses RetrievalService (local Ollama embeddings). Prints citation summaries only —
no raw user text stored. Writes JSON summary to
data/common-immigration-coverage/validation-results.json when --output is set.

Usage:
    uv run --project backend python review/scripts/validate_common_immigration_coverage.py
    uv run --project backend python review/scripts/validate_common_immigration_coverage.py --output
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure backend/.env is visible when run from repo root.
if Path("backend/.env").is_file():
    for _line in Path("backend/.env").read_text(encoding="utf-8").splitlines():
        _s = _line.strip()
        if _s.startswith("DATABASE_URL=") and not _s.startswith("#"):
            _key, _, _val = _s.partition("=")
            os.environ.setdefault(_key, _val.strip().strip('"').strip("'"))
            break

from app.core.config import get_settings
from app.services.retrieval_service import RetrievalService

INVENTORY = Path("data/common-immigration-coverage/source-inventory.json")
OUTPUT = Path("data/common-immigration-coverage/validation-results.json")

# category_id -> needles that should appear in top-5 blob (citation/topic/snippet)
CATEGORY_RULES: dict[str, list[str]] = {
    "ead_i765": ["765", "274a", "employment", "Vol 10", "EAD"],
    "opt_stem": ["214.2", "217", "OPT", "STEM", "F-1", "Part F", "Part K"],
    "asylum_ead": ["208", "1158", "asylum", "274a"],
    "aos_i485": ["245", "1245", "Adjustment", "485"],
    "advance_parole": ["131", "parole", "1245", "Part B", "Part F"],
    "naturalization": ["316", "naturalization", "Part D", "Part F", "N-400"],
    "nta_removal": ["239", "Notice", "Appear", "NTA", "Part E"],
    "status_i539": ["539", "214", "extension", "change"],
    "family_i130": ["130", "petition", "family", "Part A"],
    "affidavit_i864": ["864", "affidavit", "support", "213a", "Part G"],
    "tps_daca_ead": ["244", "TPS", "DACA", "protected", "274a"],
    "case_admin": ["RFE", "evidence", "biometric", "address", "103", "Part A", "Part L"],
}

# Queries from task + inventory
VALIDATION_QUERIES: list[tuple[str, str, str]] = [
    ("ead_i765", "How do I apply for EAD?", "ead_i765"),
    ("ead_i765", "What is Form I-765?", "ead_i765"),
    ("asylum_ead", "Can asylum applicants get work authorization?", "asylum_ead"),
    ("opt_stem", "What is OPT?", "opt_stem"),
    ("opt_stem", "What is STEM OPT?", "opt_stem"),
    ("opt_stem", "Can F-1 students work?", "opt_stem"),
    ("aos_i485", "What is adjustment of status?", "aos_i485"),
    ("advance_parole", "Can I travel while I-485 is pending?", "advance_parole"),
    ("advance_parole", "What is advance parole?", "advance_parole"),
    ("naturalization", "What is good moral character for naturalization?", "naturalization"),
    ("nta_removal", "What is a Notice to Appear?", "nta_removal"),
    ("case_admin", "What is an RFE?", "case_admin"),
    ("case_admin", "How do I change my address with USCIS?", "case_admin"),
    ("family_i130", "What is Form I-130?", "family_i130"),
    ("affidavit_i864", "What is Form I-864?", "affidavit_i864"),
    ("tps_daca_ead", "Can TPS holders get work authorization?", "tps_daca_ead"),
    ("status_i539", "What is Form I-539?", "status_i539"),
]

ASYLUM_ONLY_PATTERN = re.compile(r"208\.|asylum", re.I)


def _result_blob(results: list) -> str:
    parts: list[str] = []
    for r in results:
        parts.extend(
            [
                r.citation or "",
                r.topic or "",
                r.subtopic or "",
                (r.snippet or "")[:300],
                r.official_url or "",
            ]
        )
    return " ".join(parts).lower()


def _is_asylum_only_top3(results: list) -> bool:
    if len(results) < 3:
        return False
    for r in results[:3]:
        cite = r.citation or ""
        if not ASYLUM_ONLY_PATTERN.search(cite):
            if "274a" not in cite and "765" not in cite and "217" not in cite and "214.2" not in cite:
                continue
            return False
        if "217" in cite or "214.2" in cite or "765" in cite or "274a" in cite:
            return False
    return all(ASYLUM_ONLY_PATTERN.search(r.citation or "") for r in results[:3])


async def run_validation(output: bool) -> dict:
    svc = RetrievalService(get_settings())
    rows: list[dict] = []
    categories_passed: set[str] = set()

    for qid, query, cat_id in VALIDATION_QUERIES:
        results, active_dataset = await svc.retrieve_hybrid(query, top_k=5)
        # RetrievalResult may include source_family on branches with MVP reporting
        def _fam(r: object) -> str:
            return getattr(r, "source_family", None) or ""
        blob = _result_blob(results) + " " + " ".join(_fam(r) for r in results).lower()
        needles = CATEGORY_RULES.get(cat_id, [])
        matched = [n for n in needles if n.lower() in blob]
        ok = len(matched) > 0
        if ok:
            categories_passed.add(cat_id)

        asylum_only = _is_asylum_only_top3(results) if cat_id == "opt_stem" and "STEM" in query else False
        if cat_id == "opt_stem" and "STEM" in query and asylum_only:
            ok = False

        top_cites = [
            {
                "citation": r.citation,
                "official_url": r.official_url,
                "topic": r.topic,
            }
            for r in results[:5]
        ]
        rows.append(
            {
                "query_id": qid,
                "query_label": query[:80],
                "category_id": cat_id,
                "pass": ok,
                "matched_signals": matched,
                "asylum_only_top3": asylum_only,
                "active_dataset": active_dataset,
                "top_citations": top_cites,
            }
        )

    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    cat_status = []
    for cat in inventory.get("categories", []):
        cid = cat["id"]
        declared = cat.get("coverage_status", "unknown")
        validated = cid in categories_passed
        cat_status.append(
            {
                "id": cid,
                "title": cat["title"],
                "declared_status": declared,
                "validation_passed": validated,
                "effective_status": "covered" if validated else "coverage_missing",
            }
        )

    covered_count = sum(1 for c in cat_status if c["validation_passed"])
    summary = {
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "queries_run": len(rows),
        "queries_passed": sum(1 for r in rows if r["pass"]),
        "categories_with_passing_query": covered_count,
        "categories": cat_status,
        "queries": rows,
    }

    print(f"Queries passed: {summary['queries_passed']}/{summary['queries_run']}")
    print(f"Categories with ≥1 passing query: {covered_count}/12")
    for r in rows:
        flag = "PASS" if r["pass"] else "MISS"
        cites = ", ".join(c["citation"] or "?" for c in r["top_citations"][:3])
        print(f"  [{flag}] {r['query_label'][:50]} → {cites}")

    if output:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"Wrote {OUTPUT}")

    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", action="store_true", help="Write validation-results.json")
    args = parser.parse_args()
    try:
        summary = asyncio.run(run_validation(args.output))
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}")
        return 1
    return 0 if summary["categories_with_passing_query"] >= 10 else 1


if __name__ == "__main__":
    raise SystemExit(main())
