"""Unit tests for RetrievalService static helpers and keyword-only fallback path.

These tests exercise the pure-function helpers (_fuse_rrf, _merge_keyword_rows,
_filter_keyword_candidates) in the context of keyword-only retrieval — the path
taken when embed_query raises EmbeddingClientError (e.g. Ollama Cloud 401).

No real database or Ollama process is required.
"""

from __future__ import annotations

import unittest

from app.services.retrieval_service import (
    RetrievalService,
    _KEYWORD_CANDIDATES,
)


def _kw_row(chunk_id: int, citation: str, kw_score: float) -> dict:
    return {
        "chunk_id": chunk_id,
        "citation": citation,
        "topic": "removal proceedings",
        "subtopic": None,
        "risk_level": "high",
        "official_url": None,
        "dataset_version": "ina-v1",
        "kw_score": kw_score,
        "snippet": f"snippet for {citation}",
    }


class FuseRrfKeywordOnlyTests(unittest.TestCase):
    """_fuse_rrf with empty vector_rows simulates the embedding-fallback path."""

    def test_keyword_only_produces_results(self) -> None:
        kw_rows = [
            _kw_row(1, "8 CFR § 208.7", 0.9),
            _kw_row(2, "INA § 212(a)", 0.7),
        ]
        fused = RetrievalService._fuse_rrf([], kw_rows, top_k=5, query="asylum")
        self.assertEqual(len(fused), 2)
        # No vector contribution — vector_rank and vector_distance must be None.
        for row in fused:
            self.assertIsNone(row["vector_rank"])
            self.assertIsNone(row["vector_distance"])
        # Keyword signal drives a positive hybrid score.
        self.assertGreater(fused[0]["hybrid_score"], 0)

    def test_keyword_only_respects_top_k(self) -> None:
        kw_rows = [_kw_row(i, f"8 CFR § {i}", 1.0 / i) for i in range(1, 8)]
        fused = RetrievalService._fuse_rrf([], kw_rows, top_k=3, query="visa")
        self.assertLessEqual(len(fused), 3)

    def test_empty_both_returns_empty(self) -> None:
        fused = RetrievalService._fuse_rrf([], [], top_k=5, query="anything")
        self.assertEqual(fused, [])

    def test_keyword_only_preserves_rank_order(self) -> None:
        # RRF is rank-based: chunk at position 0 in kw_rows gets rank 1 (highest signal).
        kw_rows = [
            _kw_row(1, "8 CFR § 208.7", 0.9),  # rank 1 → highest RRF contribution
            _kw_row(2, "INA § 212(a)", 0.7),   # rank 2
        ]
        fused = RetrievalService._fuse_rrf([], kw_rows, top_k=5, query="")
        self.assertEqual(fused[0]["chunk_id"], 1)

    def test_keyword_rank_assigned_correctly(self) -> None:
        kw_rows = [
            _kw_row(10, "8 CFR § 208.7", 0.9),
            _kw_row(20, "INA § 212(a)", 0.7),
        ]
        fused = RetrievalService._fuse_rrf([], kw_rows, top_k=5, query="")
        by_id = {r["chunk_id"]: r for r in fused}
        self.assertEqual(by_id[10]["keyword_rank"], 1)
        self.assertEqual(by_id[20]["keyword_rank"], 2)

    def test_keyword_only_dedupes_by_citation(self) -> None:
        # Two rows with identical citations but different chunk_ids should be deduped.
        kw_rows = [
            _kw_row(1, "8 CFR § 208.7", 0.9),
            _kw_row(2, "8 CFR § 208.7", 0.8),
        ]
        fused = RetrievalService._fuse_rrf([], kw_rows, top_k=5, query="")
        citations = [r["citation"] for r in fused]
        self.assertEqual(len(citations), len(set(citations)))


class MergeKeywordRowsTests(unittest.TestCase):
    def _row(self, chunk_id: int, kw_score: float) -> dict:
        return {
            "chunk_id": chunk_id,
            "citation": f"citation-{chunk_id}",
            "topic": "topic",
            "subtopic": None,
            "risk_level": "medium",
            "official_url": None,
            "dataset_version": "v1",
            "kw_score": kw_score,
            "snippet": "",
        }

    def test_dedup_keeps_best_score(self) -> None:
        primary = [self._row(1, 0.5), self._row(2, 0.7)]
        extra = [self._row(1, 0.9), self._row(3, 0.6)]
        merged = RetrievalService._merge_keyword_rows(primary, extra)
        by_id = {r["chunk_id"]: r for r in merged}
        self.assertAlmostEqual(by_id[1]["kw_score"], 0.9)

    def test_merge_includes_new_chunks(self) -> None:
        primary = [self._row(1, 0.5)]
        extra = [self._row(2, 0.8)]
        merged = RetrievalService._merge_keyword_rows(primary, extra)
        ids = {r["chunk_id"] for r in merged}
        self.assertIn(2, ids)

    def test_lower_extra_score_does_not_overwrite(self) -> None:
        primary = [self._row(1, 0.8)]
        extra = [self._row(1, 0.2)]
        merged = RetrievalService._merge_keyword_rows(primary, extra)
        by_id = {r["chunk_id"]: r for r in merged}
        self.assertAlmostEqual(by_id[1]["kw_score"], 0.8)

    def test_merge_capped_at_keyword_candidates(self) -> None:
        primary = [self._row(i, 1.0 / i) for i in range(1, _KEYWORD_CANDIDATES + 3)]
        extra = [self._row(100 + i, 0.1) for i in range(5)]
        merged = RetrievalService._merge_keyword_rows(primary, extra)
        self.assertLessEqual(len(merged), _KEYWORD_CANDIDATES)

    def test_sorted_by_kw_score_descending(self) -> None:
        primary = [self._row(1, 0.3), self._row(2, 0.9), self._row(3, 0.6)]
        merged = RetrievalService._merge_keyword_rows(primary, [])
        scores = [r["kw_score"] for r in merged]
        self.assertEqual(scores, sorted(scores, reverse=True))


class FilterKeywordCandidatesTests(unittest.TestCase):
    def _bia_row(self, chunk_id: int) -> dict:
        return {
            "chunk_id": chunk_id,
            "citation": "Matter of X, 28 I&N Dec. 100 (BIA 2024)",
            "topic": "BIA Precedent",
            "subtopic": None,
            "risk_level": "high",
            "official_url": None,
            "dataset_version": "bia-v1",
            "kw_score": 0.8,
            "snippet": "",
        }

    def _cfr_row(self, chunk_id: int) -> dict:
        return {
            "chunk_id": chunk_id,
            "citation": f"8 CFR § {chunk_id}",
            "topic": "CFR",
            "subtopic": None,
            "risk_level": "medium",
            "official_url": None,
            "dataset_version": "cfr-v1",
            "kw_score": 0.5,
            "snippet": "",
        }

    def test_bia_rows_filtered_without_bia_query(self) -> None:
        rows = [self._bia_row(1), self._cfr_row(2)]
        filtered = RetrievalService._filter_keyword_candidates(rows, "asylum application")
        ids = {r["chunk_id"] for r in filtered}
        self.assertNotIn(1, ids)
        self.assertIn(2, ids)

    def test_bia_rows_kept_with_bia_query(self) -> None:
        rows = [self._bia_row(1), self._cfr_row(2)]
        filtered = RetrievalService._filter_keyword_candidates(rows, "BIA precedent removal")
        ids = {r["chunk_id"] for r in filtered}
        self.assertIn(1, ids)

    def test_empty_rows_returns_empty(self) -> None:
        filtered = RetrievalService._filter_keyword_candidates([], "anything")
        self.assertEqual(filtered, [])


class SourceFamilyFromVersionTests(unittest.TestCase):
    """source_family_from_version maps dataset version names to source family strings."""

    def setUp(self) -> None:
        from app.services.mvp_source_scope import source_family_from_version
        self._fn = source_family_from_version

    # --- BIA ---

    def test_bia_canonical_returns_bia_precedent_decisions(self) -> None:
        self.assertEqual(self._fn("bia-2026-05-21"), "BIA Precedent Decisions")

    def test_bia_canonical_no_post_mvp_suffix(self) -> None:
        self.assertNotIn("post-MVP", self._fn("bia-2026-05-21") or "")

    def test_bia_underscore_prefix_also_maps(self) -> None:
        self.assertEqual(self._fn("bia_2025"), "BIA Precedent Decisions")

    # --- Existing families unaffected ---

    def test_ecfr_full_returns_ecfr_title8(self) -> None:
        self.assertEqual(self._fn("ecfr-title8-full-2026"), "eCFR Title 8")

    def test_ina_returns_ina_title8(self) -> None:
        self.assertTrue((self._fn("ina-2026-01") or "").startswith("INA"))

    def test_uscis_pm_returns_uscis_policy_manual(self) -> None:
        self.assertEqual(self._fn("uscis-pm-2026-01"), "USCIS Policy Manual")

    def test_none_returns_none(self) -> None:
        self.assertIsNone(self._fn(None))

    def test_empty_string_returns_none(self) -> None:
        self.assertIsNone(self._fn(""))


if __name__ == "__main__":
    unittest.main()
