"""Tests for grounded follow-up suggestions."""

from __future__ import annotations

import unittest

from app.schemas.retrieval import RetrievalResult
from app.services.follow_up_suggestions import suggest_follow_ups


def _chunk(**kwargs) -> RetrievalResult:
    defaults = {
        "rank": 1,
        "chunk_id": 1,
        "citation": "8 CFR § 214.2",
        "official_url": None,
        "topic": "students",
        "subtopic": "opt",
        "risk_level": "medium",
        "hybrid_score": 0.05,
        "snippet": "Optional Practical Training for F-1 students Form I-765",
        "vector_rank": 1,
        "keyword_rank": 2,
        "vector_distance": 0.1,
        "keyword_score": 0.2,
        "dataset_version": "test",
        "source_family": "ecfr",
    }
    defaults.update(kwargs)
    return RetrievalResult(**defaults)


class FollowUpSuggestionsTests(unittest.TestCase):
    def test_opt_question_gets_opt_followups(self) -> None:
        results = [_chunk()]
        suggestions = suggest_follow_ups(
            message="How does OPT work?",
            answer="Short answer:\nOPT allows work.\n\nWhat this means:\nDetail.",
            results=results,
        )
        self.assertGreaterEqual(len(suggestions), 1)
        self.assertLessEqual(len(suggestions), 3)
        combined = " ".join(suggestions).lower()
        self.assertTrue("opt" in combined or "travel" in combined or "form" in combined)

    def test_empty_results_returns_empty(self) -> None:
        self.assertEqual(suggest_follow_ups(message="Hi", answer="Short answer:\nX", results=[]), [])

    def test_no_duplicate_suggestions(self) -> None:
        results = [_chunk(snippet="Form I-765 employment authorization EAD pending")]
        suggestions = suggest_follow_ups(
            message="EAD",
            answer="Short answer:\nEAD info.",
            results=results,
        )
        self.assertEqual(len(suggestions), len(set(s.lower() for s in suggestions)))


if __name__ == "__main__":
    unittest.main()
