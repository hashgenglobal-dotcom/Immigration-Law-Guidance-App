#!/usr/bin/env python3
"""Run RAG evaluation queries against local /api/retrieve (POST-08)."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_QUERIES = Path(__file__).resolve().parents[1] / "validation" / "rag-eval-queries.json"


def post_retrieve(base_url: str, query: str, top_k: int = 5) -> dict:
    payload = json.dumps({"query": query, "top_k": top_k}).encode()
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/retrieve",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode())


def post_chat_refusal(base_url: str, query: str) -> dict:
    payload = json.dumps({"message": query, "top_k": 3}).encode()
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read().decode())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--queries", type=Path, default=DEFAULT_QUERIES)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    data = json.loads(args.queries.read_text())
    results: list[dict] = []
    failures = 0

    for item in data.get("queries", []):
        qid = item["id"]
        query = item["query"]
        expect_refusal = item.get("expect_refusal", False)
        entry: dict = {"id": qid, "query_hash_only": True}

        try:
            if expect_refusal:
                body = post_chat_refusal(args.base_url, query)
                ok = body.get("status") == "refused"
                entry["check"] = "refusal"
                entry["pass"] = ok
                entry["status"] = body.get("status")
            else:
                body = post_retrieve(args.base_url, query)
                citations = [
                    (r.get("citation") or "") + " " + (r.get("snippet") or "")
                    for r in body.get("results", [])
                ]
                haystack = " ".join(citations).lower()
                expected = [s.lower() for s in item.get("expect_citation_contains", [])]
                ok = any(token in haystack for token in expected) if expected else bool(
                    body.get("results")
                )
                entry["check"] = "citation"
                entry["pass"] = ok
                entry["result_count"] = len(body.get("results", []))
        except urllib.error.HTTPError as exc:
            ok = False
            entry["pass"] = False
            entry["error"] = f"HTTP {exc.code}"
        except Exception as exc:  # noqa: BLE001
            ok = False
            entry["pass"] = False
            entry["error"] = type(exc).__name__

        if not entry.get("pass"):
            failures += 1
        results.append(entry)

    report = {"queries_run": len(results), "failures": failures, "results": results}
    out = args.output or (args.queries.parent / "rag-eval-results.json")
    out.write_text(json.dumps(report, indent=2))
    print(json.dumps({"failures": failures, "output": str(out)}, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
