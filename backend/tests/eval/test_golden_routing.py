"""Deterministic golden routing evaluation harness.

Exercises the full classify → understand → source-family pipeline for every
golden case without touching a database or Ollama process.

Pure-function calls only:
    classify_message()       — message_classifier
    understand_query()       — query_understanding
    is_high_risk_topic()     — answer_formatting
    is_criminal_info_query() — answer_formatting

All test methods use subTest(case=case.id) so individual case failures are
clearly identified in pytest output without masking sibling cases.
"""

from __future__ import annotations

import unittest

from app.services.answer_formatting import is_criminal_info_query, is_high_risk_topic
from app.services.message_classifier import classify_message
from app.services.query_understanding import understand_query

from .golden_cases import GOLDEN_CASES
from .paraphrase_cases import PARAPHRASE_CASES

# Combined tuple: canonical golden cases first, then paraphrase/holdout cases.
# All six test methods iterate over this so both sets receive identical coverage.
ALL_ROUTING_CASES: tuple = (*GOLDEN_CASES, *PARAPHRASE_CASES)


class GoldenRoutingTests(unittest.TestCase):
    """Golden routing evaluation — deterministic, no DB or Ollama required."""

    # A. Classifier labels ---------------------------------------------------

    def test_classifier_labels(self) -> None:
        """classify_message() must return the expected label for every case."""
        for case in ALL_ROUTING_CASES:
            with self.subTest(case=case.id):
                actual = classify_message(case.input)
                self.assertEqual(
                    actual,
                    case.expected_classifier,
                    f"[{case.id}] classify_message({case.input!r}): "
                    f"got {actual!r}, expected {case.expected_classifier!r}",
                )

    # B. Query topic and intent label (pass cases only) ----------------------

    def test_query_topics_for_pass_cases(self) -> None:
        """understand_query() topic and intent_label must match for every pass case."""
        for case in ALL_ROUTING_CASES:
            if case.expected_classifier != "pass":
                continue
            with self.subTest(case=case.id):
                u = understand_query(case.input)
                self.assertEqual(
                    u.topic,
                    case.expected_topic,
                    f"[{case.id}] topic: got {u.topic!r}, "
                    f"expected {case.expected_topic!r}",
                )
                self.assertEqual(
                    u.intent_label,
                    case.expected_intent_label,
                    f"[{case.id}] intent_label: got {u.intent_label!r}, "
                    f"expected {case.expected_intent_label!r}",
                )

    # C. Required retrieval query terms (pass cases only) --------------------

    def test_retrieval_query_required_terms(self) -> None:
        """All required_query_terms must appear (case-insensitive) in retrieval_query."""
        for case in ALL_ROUTING_CASES:
            if case.expected_classifier != "pass" or not case.required_query_terms:
                continue
            with self.subTest(case=case.id):
                query = understand_query(case.input).retrieval_query.lower()
                for term in case.required_query_terms:
                    self.assertIn(
                        term.lower(),
                        query,
                        f"[{case.id}] required term {term!r} missing from "
                        f"retrieval_query for {case.input!r}",
                    )

    # D. Forbidden retrieval query terms (pass cases only) -------------------

    def test_retrieval_query_forbidden_terms(self) -> None:
        """No forbidden_query_terms may appear (case-insensitive) in retrieval_query."""
        for case in ALL_ROUTING_CASES:
            if case.expected_classifier != "pass" or not case.forbidden_query_terms:
                continue
            with self.subTest(case=case.id):
                query = understand_query(case.input).retrieval_query.lower()
                for term in case.forbidden_query_terms:
                    self.assertNotIn(
                        term.lower(),
                        query,
                        f"[{case.id}] forbidden term {term!r} found in "
                        f"retrieval_query for {case.input!r}",
                    )

    # E. Source family requirements (pass cases only) ------------------------

    def test_source_family_requirements(self) -> None:
        """required_source_families must be present; forbidden must not."""
        for case in ALL_ROUTING_CASES:
            if case.expected_classifier != "pass":
                continue
            if not case.required_source_families and not case.forbidden_source_families:
                continue
            with self.subTest(case=case.id):
                families = set(understand_query(case.input).preferred_source_families)
                for fam in case.required_source_families:
                    self.assertIn(
                        fam,
                        families,
                        f"[{case.id}] required source family {fam!r} missing "
                        f"from {families!r}",
                    )
                for fam in case.forbidden_source_families:
                    self.assertNotIn(
                        fam,
                        families,
                        f"[{case.id}] forbidden source family {fam!r} present "
                        f"in {families!r}",
                    )

    # F. Answer flags --------------------------------------------------------

    def test_answer_flags(self) -> None:
        """is_high_risk_topic() and is_criminal_info_query() must match expected flags."""
        for case in ALL_ROUTING_CASES:
            with self.subTest(case=case.id):
                high_risk = is_high_risk_topic(case.input)
                self.assertEqual(
                    high_risk,
                    case.expected_high_risk,
                    f"[{case.id}] is_high_risk_topic({case.input!r}): "
                    f"got {high_risk}, expected {case.expected_high_risk}",
                )
                criminal_info = is_criminal_info_query(case.input)
                self.assertEqual(
                    criminal_info,
                    case.expected_criminal_info,
                    f"[{case.id}] is_criminal_info_query({case.input!r}): "
                    f"got {criminal_info}, expected {case.expected_criminal_info}",
                )


if __name__ == "__main__":
    unittest.main()
