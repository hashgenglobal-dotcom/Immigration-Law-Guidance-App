"""Unit tests for retrieval schema fields and query understanding integration.

No database or Ollama process required.
"""

from __future__ import annotations

import unittest

import pytest
from pydantic import ValidationError

from app.schemas.retrieval import RetrievalRequest, RetrievalResponse, RetrievalResult
from app.services.query_understanding import understand_query


# ---------------------------------------------------------------------------
# RetrievalRequest
# ---------------------------------------------------------------------------

class RetrievalRequestDefaultsTests(unittest.TestCase):
    def test_use_query_understanding_defaults_to_false(self) -> None:
        req = RetrievalRequest(query="What is OPT?")
        self.assertFalse(req.use_query_understanding)

    def test_top_k_defaults_to_five(self) -> None:
        req = RetrievalRequest(query="What is OPT?")
        self.assertEqual(req.top_k, 5)

    def test_accepts_use_query_understanding_true(self) -> None:
        req = RetrievalRequest(query="What is OPT?", use_query_understanding=True)
        self.assertTrue(req.use_query_understanding)

    def test_query_is_stripped_on_input(self) -> None:
        req = RetrievalRequest(query="  What is OPT?  ")
        self.assertEqual(req.query, "What is OPT?")

    def test_empty_query_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            RetrievalRequest(query="")

    def test_whitespace_only_query_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            RetrievalRequest(query="   ")


# ---------------------------------------------------------------------------
# RetrievalResponse
# ---------------------------------------------------------------------------

def _minimal_result() -> RetrievalResult:
    return RetrievalResult(
        rank=1,
        chunk_id=1,
        citation="8 CFR § 208.7",
        official_url=None,
        topic="asylum",
        subtopic=None,
        risk_level=None,
        hybrid_score=0.5,
        vector_rank=None,
        keyword_rank=None,
        vector_distance=None,
        keyword_score=None,
        snippet="snippet",
        dataset_version=None,
        source_family=None,
    )


class RetrievalResponseEffectiveQueryTests(unittest.TestCase):
    def _base_kwargs(self) -> dict:
        return {
            "query_hash": "abc123",
            "top_k": 5,
            "active_dataset": None,
            "active_datasets": [],
            "mvp_sources": [],
            "results": [_minimal_result()],
        }

    def test_effective_query_defaults_to_none(self) -> None:
        resp = RetrievalResponse(**self._base_kwargs())
        self.assertIsNone(resp.effective_query)

    def test_effective_query_accepts_string(self) -> None:
        resp = RetrievalResponse(**self._base_kwargs(), effective_query="L-2 spouse work authorization")
        self.assertEqual(resp.effective_query, "L-2 spouse work authorization")

    def test_effective_query_accepts_none_explicitly(self) -> None:
        resp = RetrievalResponse(**self._base_kwargs(), effective_query=None)
        self.assertIsNone(resp.effective_query)


# ---------------------------------------------------------------------------
# Query understanding integration (no DB, no Ollama)
# ---------------------------------------------------------------------------

class QueryUnderstandingIntegrationTests(unittest.TestCase):
    def test_l2_query_produces_l2_work_authorization_topic(self) -> None:
        result = understand_query("Can my spouse work if I am on L1 visa?")
        self.assertEqual(result.topic, "l2_work_authorization")

    def test_l2_retrieval_query_contains_l2s(self) -> None:
        result = understand_query("Can my spouse work if I am on L1 visa?")
        self.assertIn("L-2S", result.retrieval_query)

    def test_l2_retrieval_query_contains_i94(self) -> None:
        result = understand_query("Can my spouse work if I am on L1 visa?")
        self.assertIn("I-94", result.retrieval_query)

    def test_l2_retrieval_query_contains_spouses_of_l1_nonimmigrants(self) -> None:
        result = understand_query("Can my spouse work if I am on L1 visa?")
        self.assertIn("spouses of L-1 nonimmigrants", result.retrieval_query)

    def test_general_query_topic_is_general(self) -> None:
        result = understand_query("What is OPT?")
        self.assertEqual(result.topic, "general")

    def test_general_query_retrieval_query_equals_original(self) -> None:
        msg = "What is OPT?"
        result = understand_query(msg)
        self.assertEqual(result.retrieval_query, msg)

    def test_general_query_retrieval_query_is_stripped(self) -> None:
        msg = "  What is OPT?  "
        result = understand_query(msg)
        self.assertEqual(result.retrieval_query, msg.strip())


if __name__ == "__main__":
    unittest.main()
