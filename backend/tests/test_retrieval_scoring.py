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


if __name__ == "__main__":
    unittest.main()
