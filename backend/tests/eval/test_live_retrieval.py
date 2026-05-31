"""Optional live retrieval evaluation harness.

Tests POST /api/retrieve against a running backend server with an active
Supabase DB and Ollama embedding service.  Skipped by default — does not
run in normal CI or local pytest without the guard env var.

Run with:
  RUN_LIVE_RETRIEVAL_EVALS=1 LIVE_API_BASE_URL=http://127.0.0.1:8000 \\
    uv run --with pytest pytest tests/eval/test_live_retrieval.py -v

Override the per-request timeout (default 60 s):
  LIVE_RETRIEVAL_TIMEOUT_SECONDS=90 RUN_LIVE_RETRIEVAL_EVALS=1 ...

Four test methods, one per assertion dimension:
  A. test_live_min_results          — result count >= case.min_results
  B. test_live_source_families      — required/forbidden source_family in top N
  C. test_live_citation_terms       — required/forbidden terms in top N citations
  D. test_live_effective_query_terms — rewritten query contains/excludes terms
"""

from __future__ import annotations

import os
import unittest

import httpx

from .live_cases import LIVE_RETRIEVAL_CASES

_BASE_URL = os.environ.get("LIVE_API_BASE_URL", "http://127.0.0.1:8000")
_RETRIEVE_TIMEOUT = float(os.environ.get("LIVE_RETRIEVAL_TIMEOUT_SECONDS", "60"))


@unittest.skipUnless(
    os.environ.get("RUN_LIVE_RETRIEVAL_EVALS") == "1",
    "set RUN_LIVE_RETRIEVAL_EVALS=1 to enable live retrieval evals",
)
class LiveRetrievalTests(unittest.TestCase):
    """Optional live retrieval eval — requires running server and active Supabase DB."""

    # Populated once in setUpClass; keyed by case.id → parsed JSON response body.
    _responses_by_case_id: dict[str, dict] = {}

    @classmethod
    def setUpClass(cls) -> None:
        """Verify the server is reachable, then prefetch every case exactly once."""
        try:
            r = httpx.get(f"{_BASE_URL}/health", timeout=3)
        except (httpx.ConnectError, httpx.TimeoutException):
            raise unittest.SkipTest(f"server unreachable at {_BASE_URL}")
        if r.status_code != 200:
            cls._probe_retrieve()

        cls._responses_by_case_id = {}
        for case in LIVE_RETRIEVAL_CASES:
            top_k = max(7, case.source_family_search_window, case.citation_search_window)
            try:
                resp = httpx.post(
                    f"{_BASE_URL}/api/retrieve",
                    json={
                        "query": case.query,
                        "top_k": top_k,
                        "use_query_understanding": case.use_query_understanding,
                    },
                    timeout=_RETRIEVE_TIMEOUT,
                )
                resp.raise_for_status()
                cls._responses_by_case_id[case.id] = resp.json()
            except httpx.TimeoutException:
                raise unittest.SkipTest(
                    f"live retrieval prefetch timed out for case {case.id}; "
                    "rerun when local server/Ollama/Supabase is responsive "
                    f"(or increase LIVE_RETRIEVAL_TIMEOUT_SECONDS, currently {_RETRIEVE_TIMEOUT:.0f}s)"
                )

    @classmethod
    def _probe_retrieve(cls) -> None:
        """Probe POST /api/retrieve; raise SkipTest on any connection failure."""
        try:
            httpx.post(
                f"{_BASE_URL}/api/retrieve",
                json={"query": "test", "top_k": 1, "use_query_understanding": False},
                timeout=5,
            )
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            raise unittest.SkipTest(f"server unreachable at {_BASE_URL}: {exc}")

    def _body(self, case) -> dict:
        """Return the cached response body for a case."""
        return self._responses_by_case_id[case.id]

    # A. Minimum result count -------------------------------------------------

    def test_live_min_results(self) -> None:
        """Each query must return at least case.min_results results."""
        for case in LIVE_RETRIEVAL_CASES:
            with self.subTest(case=case.id):
                body = self._body(case)
                self.assertEqual(
                    body.get("status"),
                    "ok",
                    f"[{case.id}] status != 'ok': {body.get('status')!r}",
                )
                results = body.get("results", [])
                self.assertGreaterEqual(
                    len(results),
                    case.min_results,
                    f"[{case.id}] got {len(results)} results, need >= {case.min_results}",
                )

    # B. Source family assertions ----------------------------------------------

    def test_live_source_families(self) -> None:
        """required/forbidden source families must appear/be absent in the top N results."""
        for case in LIVE_RETRIEVAL_CASES:
            if not case.required_source_families and not case.forbidden_source_families:
                continue
            with self.subTest(case=case.id):
                body = self._body(case)
                top_n = body.get("results", [])[:case.source_family_search_window]
                families = {r.get("source_family") for r in top_n}
                for fam in case.required_source_families:
                    self.assertIn(
                        fam,
                        families,
                        f"[{case.id}] required source family {fam!r} not in top-"
                        f"{case.source_family_search_window} results: "
                        f"{sorted(f for f in families if f)}",
                    )
                for fam in case.forbidden_source_families:
                    self.assertNotIn(
                        fam,
                        families,
                        f"[{case.id}] forbidden source family {fam!r} found in top-"
                        f"{case.source_family_search_window} results",
                    )

    # C. Citation term assertions ----------------------------------------------

    def test_live_citation_terms(self) -> None:
        """required/forbidden citation terms must appear/be absent in the top N citations."""
        for case in LIVE_RETRIEVAL_CASES:
            if not case.required_citation_terms and not case.forbidden_citation_terms:
                continue
            with self.subTest(case=case.id):
                body = self._body(case)
                top_n = body.get("results", [])[:case.citation_search_window]
                citations = [r.get("citation", "") for r in top_n]
                citations_lower = [c.lower() for c in citations]
                for term in case.required_citation_terms:
                    self.assertTrue(
                        any(term.lower() in c for c in citations_lower),
                        f"[{case.id}] required citation term {term!r} not found in "
                        f"top-{case.citation_search_window} citations: {citations}",
                    )
                for term in case.forbidden_citation_terms:
                    self.assertFalse(
                        any(term.lower() in c for c in citations_lower),
                        f"[{case.id}] forbidden citation term {term!r} found in "
                        f"top-{case.citation_search_window} citations: {citations}",
                    )

    # D. Effective query term assertions --------------------------------------

    def test_live_effective_query_terms(self) -> None:
        """effective_query must contain required terms and exclude forbidden ones.

        Only exercised for cases where use_query_understanding=True.
        When routing fires, effective_query is the rewritten retrieval query;
        required terms verify that the expected query rewrite was applied.
        """
        for case in LIVE_RETRIEVAL_CASES:
            if not case.use_query_understanding:
                continue
            if not case.required_effective_query_terms and not case.forbidden_effective_query_terms:
                continue
            with self.subTest(case=case.id):
                body = self._body(case)
                effective_query = body.get("effective_query")
                self.assertIsNotNone(
                    effective_query,
                    f"[{case.id}] effective_query is None (unexpected — "
                    "use_query_understanding=True always sets effective_query)",
                )
                eq_lower = (effective_query or "").lower()
                for term in case.required_effective_query_terms:
                    self.assertIn(
                        term.lower(),
                        eq_lower,
                        f"[{case.id}] required term {term!r} missing from "
                        f"effective_query (routing may not have fired)",
                    )
                for term in case.forbidden_effective_query_terms:
                    self.assertNotIn(
                        term.lower(),
                        eq_lower,
                        f"[{case.id}] forbidden term {term!r} found in effective_query",
                    )


if __name__ == "__main__":
    unittest.main()
