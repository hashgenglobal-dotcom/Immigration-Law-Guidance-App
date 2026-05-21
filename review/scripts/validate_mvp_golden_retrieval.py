#!/usr/bin/env python3
"""Validate MVP golden retrieval queries (top-1 / top-3 hit rates).

Uses RetrievalService with local Ollama embeddings. Read-only; synthetic queries only.

Usage:
    uv run --project backend python review/scripts/validate_mvp_golden_retrieval.py
    uv run --project backend python review/scripts/validate_mvp_golden_retrieval.py --output
    uv run --project backend python review/scripts/validate_mvp_golden_retrieval.py --relaxed
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

GOLDEN_PATH = Path("review/validation/mvp-golden-retrieval-queries.json")
OUTPUT_PATH = Path("review/validation/retrieval-quality-mvp-results.json")

if Path("backend/.env").is_file():
    for _line in Path("backend/.env").read_text(encoding="utf-8").splitlines():
        _s = _line.strip()
        if _s.startswith("DATABASE_URL=") and not _s.startswith("#"):
            _key, _, _val = _s.partition("=")
            os.environ.setdefault(_key, _val.strip().strip('"').strip("'"))
            break

from app.core.config import get_settings
from app.services.guided_intake import detect_broad_topic
from app.services.retrieval_service import RetrievalService


def _matches(citation: str, needles: list[str]) -> bool:
    cite = (citation or "").lower()
    return any(n.lower() in cite for n in needles)


async def run_validation(write_output: bool) -> dict:
    spec = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    top_k = int(spec.get("top_k", 5))
    svc = RetrievalService(get_settings())
    rows: list[dict] = []

    for case in spec["queries"]:
        query = case["query"]
        needles = case["match_any"]
        broad_topic = detect_broad_topic(query)
        results, active_datasets, active_dataset = await svc.retrieve_hybrid(query, top_k=top_k)
        ranks = [r.rank for r in results if _matches(r.citation, needles)]
        top1 = 1 in ranks
        top3 = any(r <= 3 for r in ranks)
        top5 = any(r <= top_k for r in ranks)

        rows.append(
            {
                "id": case["id"],
                "query": query,
                "category": case.get("category"),
                "expects_clarification": case.get("expects_clarification", False),
                "detected_broad_topic": broad_topic,
                "match_any": needles,
                "expected_rank": ranks[0] if ranks else None,
                "top1_hit": top1,
                "top3_hit": top3,
                "top5_hit": top5,
                "pass": top3,
                "active_dataset": active_dataset,
                "active_datasets": active_datasets,
                "top_citations": [r.citation for r in results[:top_k]],
            }
        )

    n = len(rows)
    top1_rate = sum(1 for r in rows if r["top1_hit"]) / n
    top3_rate = sum(1 for r in rows if r["top3_hit"]) / n

    summary = {
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "golden_version": spec.get("version"),
        "queries_total": n,
        "top1_hits": sum(1 for r in rows if r["top1_hit"]),
        "top3_hits": sum(1 for r in rows if r["top3_hit"]),
        "top1_rate": round(top1_rate, 4),
        "top3_rate": round(top3_rate, 4),
        "accept_top3_rate": spec.get("accept_top3_rate", 0.85),
        "passed": top3_rate >= float(spec.get("accept_top3_rate", 0.85)),
        "queries": rows,
    }

    print(f"Golden retrieval: top-1 {summary['top1_hits']}/{n}  top-3 {summary['top3_hits']}/{n}")
    for r in rows:
        flag = "PASS" if r["top3_hit"] else "FAIL"
        rank = r["expected_rank"] or "-"
        print(f"  [{flag}] rank {rank}  {r['query'][:55]}")
        print(f"         top: {', '.join(r['top_citations'][:3])}")

    if write_output:
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"Wrote {OUTPUT_PATH}")

    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", action="store_true", help="Write JSON results artifact")
    parser.add_argument(
        "--relaxed",
        action="store_true",
        help="Exit 0 even if top-3 rate is below threshold (use on sample-only local DB)",
    )
    args = parser.parse_args()
    try:
        summary = asyncio.run(run_validation(args.output))
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}")
        return 1
    if args.relaxed:
        print("NOTE: --relaxed mode; exit 0 regardless of score (sample-only DB expected)")
        return 0
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
