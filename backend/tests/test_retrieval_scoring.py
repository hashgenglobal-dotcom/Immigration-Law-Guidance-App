"""Unit tests for MVP retrieval scoring helpers."""

from __future__ import annotations

import unittest

from app.services.retrieval_scoring import (
    compute_relevance_boost,
    dedupe_by_citation,
    extract_supplemental_phrases,
    is_bia_chunk,
    query_mentions_bia,
)


class RetrievalScoringTests(unittest.TestCase):
    def test_bia_chunk_detection(self) -> None:
        self.assertTrue(is_bia_chunk("Aguilar Hernandez,28 I&N Dec. 774 (BIA 2024)"))
        self.assertFalse(is_bia_chunk("8 CFR § 239.1", "239.1"))

    def test_bia_penalty_without_query_mention(self) -> None:
        boost = compute_relevance_boost(
            "What is a Notice to Appear?",
            citation="Aguilar Hernandez (BIA 2024)",
            topic="BIA Precedent",
            subtopic=None,
            snippet="notice to appear",
        )
        self.assertLess(boost, 0)

    def test_notice_to_appear_boosts_cfr_239(self) -> None:
        boost = compute_relevance_boost(
            "What is a Notice to Appear?",
            citation="8 CFR § 239.1",
            topic="239.1",
            subtopic=None,
            snippet="Notice to appear means ...",
        )
        self.assertGreater(boost, 0.015)

    def test_form_i765_boost(self) -> None:
        boost = compute_relevance_boost(
            "What is Form I-765?",
            citation="USCIS Form I-765",
            topic="I-765",
            subtopic=None,
            snippet="Application for employment authorization",
        )
        self.assertGreater(boost, 0.01)

    def test_extract_phrase_notice_to_appear(self) -> None:
        phrases = extract_supplemental_phrases("What is a Notice to Appear?")
        self.assertIn("notice to appear", phrases)

    def test_dedupe_by_citation_keeps_best_score(self) -> None:
        rows = [
            {"citation": "8 CFR § 208.7", "hybrid_score": 0.02, "chunk_id": 1},
            {"citation": "8 CFR § 208.7", "hybrid_score": 0.03, "chunk_id": 2},
            {"citation": "8 CFR § 274a.13", "hybrid_score": 0.025, "chunk_id": 3},
        ]
        out = dedupe_by_citation(rows)
        self.assertEqual(len(out), 2)
        self.assertEqual(out[0]["chunk_id"], 2)

    def test_query_mentions_bia(self) -> None:
        self.assertTrue(query_mentions_bia("BIA precedent on removal"))
        self.assertFalse(query_mentions_bia("What is a Notice to Appear?"))

    # --- I-485 travel scoring ---

    def test_i485_travel_boosts_advance_parole_chunk(self) -> None:
        # The rewritten travel_aos query should boost advance parole / I-131 chunks.
        query = "Advance parole travel while adjustment of status I-485 pending Form I-131"
        boost = compute_relevance_boost(
            query,
            citation="USCIS Policy Manual — Advance Parole",
            topic="advance parole",
            subtopic=None,
            snippet="Advance parole allows a person with a pending I-485 to travel abroad and return.",
        )
        self.assertGreater(boost, 0.01)

    def test_i485_travel_penalizes_syria_chunk(self) -> None:
        # Syria-specific chunks should be penalized for generic I-485 travel queries.
        query = "Advance parole travel while adjustment of status I-485 pending Form I-131"
        boost = compute_relevance_boost(
            query,
            citation="8 CFR § 1245.20",
            topic="Syrian nationals adjustment",
            subtopic=None,
            snippet="This section applies to Syrian nationals under Public Law 106-378.",
        )
        self.assertLess(boost, 0)

    def test_syria_query_no_penalty_for_syria_chunk(self) -> None:
        # When the user explicitly asks about Syria, the penalty must not apply.
        query = "Can Syrian nationals use Public Law 106-378 to adjust status?"
        boost = compute_relevance_boost(
            query,
            citation="8 CFR § 1245.20",
            topic="Syrian nationals",
            subtopic=None,
            snippet="Syrian nationals under Public Law 106-378 may adjust status.",
        )
        self.assertGreaterEqual(boost, -0.005)

    def test_general_adjustment_query_not_penalized(self) -> None:
        # Plain adjustment-of-status eligibility query must not trigger the Syria penalty.
        boost = compute_relevance_boost(
            "How do I become eligible for adjustment of status?",
            citation="8 CFR § 245.1",
            topic="adjustment of status",
            subtopic=None,
            snippet="An alien may apply for adjustment of status under section 245.",
        )
        self.assertGreaterEqual(boost, 0)

    def test_i485_travel_advance_parole_chunk_outranks_syria_chunk(self) -> None:
        # The advance-parole boost must produce a higher score than the penalized Syria chunk.
        query = "Advance parole travel while adjustment of status I-485 pending Form I-131"
        ap_boost = compute_relevance_boost(
            query,
            citation="USCIS Form I-131",
            topic="advance parole",
            subtopic=None,
            snippet="File Form I-131 to request advance parole before traveling with a pending I-485.",
        )
        syria_boost = compute_relevance_boost(
            query,
            citation="8 CFR § 1245.20",
            topic="Syrian nationals",
            subtopic=None,
            snippet="Syrian nationals under Public Law 106-378.",
        )
        self.assertGreater(ap_boost, syria_boost)


if __name__ == "__main__":
    unittest.main()
