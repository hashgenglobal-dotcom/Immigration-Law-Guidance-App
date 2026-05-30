"""Tests for the query understanding layer (no DB or Ollama required)."""

from __future__ import annotations

import types
import unittest

from app.services.query_understanding import filter_results_for_understanding, rerank_results_by_preferred_source_family, understand_query


class L2WorkAuthDetectionTests(unittest.TestCase):
    """understand_query maps L-1/L-2 spouse work questions to l2_work_authorization."""

    def _assert_l2(self, message: str) -> None:
        result = understand_query(message)
        self.assertEqual(
            result.topic,
            "l2_work_authorization",
            f"Expected topic 'l2_work_authorization' for: {message!r}",
        )

    # --- Positive matches ---

    def test_spouse_work_on_l1_visa(self) -> None:
        self._assert_l2("Can my spouse work if I am on L1 visa?")

    def test_wife_work_on_l1(self) -> None:
        self._assert_l2("Can my wife work if I am on L1?")

    def test_husband_work_on_l1(self) -> None:
        self._assert_l2("Can my husband work if I have L-1?")

    def test_l2_spouse_work(self) -> None:
        self._assert_l2("Can L2 spouse work?")

    def test_l2s_work_without_ead(self) -> None:
        self._assert_l2("Can L-2S work without EAD?")

    def test_l2_spouse_need_ead(self) -> None:
        self._assert_l2("Does L2 spouse need EAD?")

    def test_l1_dependent_spouse_work(self) -> None:
        self._assert_l2("I am L1, can my dependent spouse work?")

    # --- Retrieval query content (positive) ---

    def test_l2_retrieval_query_contains_l2(self) -> None:
        result = understand_query("Can my spouse work if I am on L1 visa?")
        self.assertIn("L-2", result.retrieval_query)

    def test_l2_retrieval_query_contains_l2s(self) -> None:
        result = understand_query("Can my spouse work if I am on L1 visa?")
        self.assertIn("L-2S", result.retrieval_query)

    def test_l2_retrieval_query_contains_i94(self) -> None:
        result = understand_query("Can my spouse work if I am on L1 visa?")
        self.assertIn("I-94", result.retrieval_query)

    def test_l2_retrieval_query_contains_employment_authorization(self) -> None:
        result = understand_query("Can my spouse work if I am on L1 visa?")
        self.assertIn("employment authorization", result.retrieval_query.lower())

    def test_l2_retrieval_query_contains_spouses_of_l1_nonimmigrants(self) -> None:
        result = understand_query("Can my spouse work if I am on L1 visa?")
        self.assertIn("spouses of L-1 nonimmigrants", result.retrieval_query)

    # --- Retrieval query content (exclusions) ---

    def test_l2_retrieval_query_excludes_naturalization(self) -> None:
        result = understand_query("Can my spouse work if I am on L1 visa?")
        self.assertNotIn("naturalization", result.retrieval_query.lower())

    def test_l2_retrieval_query_excludes_us_citizen_spouse(self) -> None:
        result = understand_query("Can my spouse work if I am on L1 visa?")
        self.assertNotIn("U.S. citizen spouse", result.retrieval_query)

    def test_l2_retrieval_query_excludes_i751(self) -> None:
        result = understand_query("Can my spouse work if I am on L1 visa?")
        self.assertNotIn("I-751", result.retrieval_query)

    def test_l2_retrieval_query_excludes_regularly_stationed_abroad(self) -> None:
        result = understand_query("Can my spouse work if I am on L1 visa?")
        self.assertNotIn("regularly stationed abroad", result.retrieval_query.lower())


class GeneralFallbackTests(unittest.TestCase):
    """understand_query returns topic='general' and the original message for unmatched input."""

    def test_opt_question_falls_back_to_general(self) -> None:
        result = understand_query("What is OPT?")
        self.assertEqual(result.topic, "general")

    def test_opt_question_preserves_original_retrieval_query(self) -> None:
        msg = "What is OPT?"
        result = understand_query(msg)
        self.assertEqual(result.retrieval_query, msg)

    def test_h4_process_question_falls_back_to_general(self) -> None:
        result = understand_query("What is H-4 process?")
        self.assertEqual(result.topic, "general")

    def test_h4_ead_question_falls_back_to_general(self) -> None:
        result = understand_query("How does H-4 EAD work?")
        self.assertEqual(result.topic, "general")

    def test_asylum_ead_falls_back_to_general(self) -> None:
        result = understand_query("How do I apply for EAD as an asylum applicant?")
        self.assertEqual(result.topic, "general")

    def test_generic_ead_falls_back_to_general(self) -> None:
        result = understand_query("How do I apply for EAD?")
        self.assertEqual(result.topic, "general")

    def test_naturalization_falls_back_to_general(self) -> None:
        result = understand_query("What are the requirements for naturalization?")
        self.assertEqual(result.topic, "general")

    def test_general_has_empty_preferred_source_families(self) -> None:
        result = understand_query("What is OPT?")
        self.assertEqual(result.preferred_source_families, ())

    def test_general_has_empty_missing_facts(self) -> None:
        result = understand_query("What is OPT?")
        self.assertEqual(result.missing_facts, ())

    def test_preserves_original_query_with_whitespace(self) -> None:
        msg = "  What is OPT?  "
        result = understand_query(msg)
        self.assertEqual(result.retrieval_query, msg.strip())

    # --- No false positives on L-2 status questions without work context ---

    def test_l2_status_denial_no_work_context_falls_back(self) -> None:
        result = understand_query("My L-2 visa was denied.")
        self.assertEqual(result.topic, "general")

    def test_l2_status_extension_falls_back(self) -> None:
        result = understand_query("How do I extend my L-2 status?")
        # "extend" has no work-auth signal → general fallback
        self.assertEqual(result.topic, "general")


class L2AnswerGuidanceTests(unittest.TestCase):
    """understand_query populates answer_guidance for l2_work_authorization; empty for general."""

    def _l2_result(self) -> object:
        return understand_query("Can my spouse work if I am on L1 visa?")

    def test_l2_answer_guidance_is_nonempty(self) -> None:
        self.assertTrue(self._l2_result().answer_guidance)

    def test_l2_answer_guidance_contains_l2(self) -> None:
        self.assertIn("L-2", self._l2_result().answer_guidance)

    def test_l2_answer_guidance_contains_l2s(self) -> None:
        self.assertIn("L-2S", self._l2_result().answer_guidance)

    def test_l2_answer_guidance_contains_i94(self) -> None:
        self.assertIn("I-94", self._l2_result().answer_guidance)

    def test_l2_answer_guidance_contains_incident_to_status(self) -> None:
        self.assertIn("incident to status", self._l2_result().answer_guidance)

    def test_l2_answer_guidance_contains_form_i765(self) -> None:
        self.assertIn("Form I-765", self._l2_result().answer_guidance)

    def test_general_fallback_answer_guidance_is_empty(self) -> None:
        self.assertEqual(understand_query("What is OPT?").answer_guidance, "")

    def test_general_h4_question_answer_guidance_is_empty(self) -> None:
        self.assertEqual(understand_query("How does H-4 EAD work?").answer_guidance, "")

    def test_l2_direct_signal_answer_guidance_is_nonempty(self) -> None:
        self.assertTrue(understand_query("Can L-2S work without EAD?").answer_guidance)


class L2ResultFilterTests(unittest.TestCase):
    """filter_results_for_understanding removes contaminating chunks for l2_work_authorization."""

    def _make(self, *, citation: str = "", topic: str = "", subtopic: str | None = None, snippet: str = "") -> object:
        return types.SimpleNamespace(citation=citation, topic=topic, subtopic=subtopic, snippet=snippet)

    def _l2(self) -> object:
        return understand_query("Can my spouse work if I am on L1 visa?")

    def _general(self) -> object:
        return understand_query("What is OPT?")

    # --- Keep signals ---

    def test_l2_snippet_is_kept(self) -> None:
        r = self._make(snippet="L-2 spouse employment authorized incident to status.")
        self.assertIn(r, filter_results_for_understanding([r], self._l2()))

    def test_l2s_citation_is_kept(self) -> None:
        r = self._make(citation="USCIS Policy Manual Vol 10 Part B Ch 2", topic="L-2S Employment Authorization")
        self.assertIn(r, filter_results_for_understanding([r], self._l2()))

    def test_spouses_of_l1_nonimmigrants_snippet_is_kept(self) -> None:
        r = self._make(snippet="spouses of L-1 nonimmigrants are authorized to work incident to status.")
        self.assertIn(r, filter_results_for_understanding([r], self._l2()))

    def test_ina_214_c2e_citation_is_kept(self) -> None:
        r = self._make(citation="INA 214(c)(2)(E)", topic="L Nonimmigrant Spouses")
        self.assertIn(r, filter_results_for_understanding([r], self._l2()))

    def test_employment_authorized_incident_to_status_is_kept(self) -> None:
        r = self._make(snippet="L-2 dependents are employment authorized incident to status.")
        self.assertIn(r, filter_results_for_understanding([r], self._l2()))

    # --- Reject signals (tested with an L-2 anchor so fallback doesn't trigger) ---

    def test_h4_topic_is_rejected(self) -> None:
        l2_r = self._make(snippet="L-2 spouse employment authorized incident to status.")
        h4_r = self._make(topic="H-4 Employment Authorization", snippet="H-4 spouses may apply for EAD.")
        filtered = filter_results_for_understanding([l2_r, h4_r], self._l2())
        self.assertNotIn(h4_r, filtered)

    def test_naturalization_snippet_is_rejected(self) -> None:
        l2_r = self._make(snippet="L-2 spouse employment authorized incident to status.")
        nat_r = self._make(snippet="Requirements for naturalization of alien spouses of U.S. citizens.")
        filtered = filter_results_for_understanding([l2_r, nat_r], self._l2())
        self.assertNotIn(nat_r, filtered)

    def test_v_nonimmigrant_snippet_is_rejected(self) -> None:
        l2_r = self._make(snippet="L-2 spouse employment authorized incident to status.")
        v_r = self._make(snippet="V nonimmigrant spouse of lawful permanent resident may apply for EAD.")
        filtered = filter_results_for_understanding([l2_r, v_r], self._l2())
        self.assertNotIn(v_r, filtered)

    def test_lpr_spouse_snippet_is_rejected(self) -> None:
        l2_r = self._make(snippet="L-2 spouse employment authorized incident to status.")
        lpr_r = self._make(snippet="Certain lawful permanent residents may petition for their spouse.")
        filtered = filter_results_for_understanding([l2_r, lpr_r], self._l2())
        self.assertNotIn(lpr_r, filtered)

    def test_asylum_snippet_is_rejected(self) -> None:
        l2_r = self._make(snippet="L-2 spouse employment authorized incident to status.")
        asy_r = self._make(snippet="An asylum applicant may apply for employment authorization.")
        filtered = filter_results_for_understanding([l2_r, asy_r], self._l2())
        self.assertNotIn(asy_r, filtered)

    # --- Priority: keep signal wins over reject signal ---

    def test_keep_wins_when_both_signals_present(self) -> None:
        r = self._make(
            snippet="L-2 spouse employment authorized incident to status. H-4 content also referenced.",
        )
        self.assertIn(r, filter_results_for_understanding([r], self._l2()))

    # --- Neutral result (no signals) ---

    def test_neutral_result_is_kept(self) -> None:
        r = self._make(snippet="General immigration information about work authorization documents.")
        self.assertIn(r, filter_results_for_understanding([r], self._l2()))

    # --- Fallback: never return empty list ---

    def test_fallback_returns_original_if_all_rejected(self) -> None:
        results = [
            self._make(topic="H-4 Employment Authorization", snippet="H-4 spouses."),
            self._make(snippet="naturalization requirements for spouses."),
        ]
        filtered = filter_results_for_understanding(list(results), self._l2())
        self.assertEqual(filtered, results)

    # --- General topic passthrough ---

    def test_general_topic_returns_h4_result_unchanged(self) -> None:
        r = self._make(topic="H-4 Employment Authorization")
        result = filter_results_for_understanding([r], self._general())
        self.assertIn(r, result)

    def test_general_topic_returns_naturalization_result_unchanged(self) -> None:
        r = self._make(snippet="naturalization requirements")
        result = filter_results_for_understanding([r], self._general())
        self.assertIn(r, result)

    def test_empty_list_returns_empty(self) -> None:
        self.assertEqual(filter_results_for_understanding([], self._l2()), [])

    # --- Mixed list: only L-2 results survive ---

    def test_mixed_list_keeps_l2_removes_h4(self) -> None:
        l2_r = self._make(snippet="L-2 spouse employment authorized incident to status.")
        h4_r = self._make(topic="H-4 Employment Authorization", snippet="H-4 EAD.")
        filtered = filter_results_for_understanding([l2_r, h4_r], self._l2())
        self.assertIn(l2_r, filtered)
        self.assertNotIn(h4_r, filtered)

    def test_mixed_list_keeps_l2_removes_naturalization(self) -> None:
        l2_r = self._make(citation="INA 214(c)(2)(E)")
        nat_r = self._make(snippet="naturalization requirements for spouses of citizens.")
        filtered = filter_results_for_understanding([l2_r, nat_r], self._l2())
        self.assertIn(l2_r, filtered)
        self.assertNotIn(nat_r, filtered)


class L2SourceFamilyRerankerTests(unittest.TestCase):
    """rerank_results_by_preferred_source_family softly boosts preferred-source results."""

    def _make(self, *, source_family: str | None = None, hybrid_score: float = 0.020, rank: int = 1) -> object:
        return types.SimpleNamespace(source_family=source_family, hybrid_score=hybrid_score, rank=rank)

    def _l2(self) -> object:
        return understand_query("Can my spouse work if I am on L1 visa?")

    def _general(self) -> object:
        return understand_query("What is OPT?")

    def test_empty_results_returns_empty(self) -> None:
        self.assertEqual(rerank_results_by_preferred_source_family([], self._l2()), [])

    def test_empty_preferred_families_returns_unchanged(self) -> None:
        r = self._make(source_family="USCIS Policy Manual")
        result = rerank_results_by_preferred_source_family([r], self._general())
        self.assertIs(result[0], r)

    def test_general_topic_returns_unchanged(self) -> None:
        r1 = self._make(source_family="USCIS Policy Manual", rank=1)
        r2 = self._make(source_family="eCFR Title 8", rank=2)
        original = [r1, r2]
        result = rerank_results_by_preferred_source_family(original, self._general())
        self.assertEqual(result, original)

    def test_no_matching_source_family_returns_unchanged(self) -> None:
        r1 = self._make(source_family="eCFR Title 8", hybrid_score=0.025, rank=1)
        r2 = self._make(source_family="INA / U.S. Code Title 8", hybrid_score=0.020, rank=2)
        original = [r1, r2]
        result = rerank_results_by_preferred_source_family(original, self._l2())
        self.assertEqual(result, original)

    def test_preferred_result_already_first_stays_first(self) -> None:
        r1 = self._make(source_family="USCIS Policy Manual", hybrid_score=0.030, rank=1)
        r2 = self._make(source_family="eCFR Title 8", hybrid_score=0.020, rank=2)
        result = rerank_results_by_preferred_source_family([r1, r2], self._l2())
        self.assertEqual(result[0].source_family, "USCIS Policy Manual")
        self.assertEqual(result[0].rank, 1)

    def test_preferred_result_promoted_when_score_gap_small(self) -> None:
        # Preferred starts second; boost (0.004) exceeds the gap (0.003)
        r1 = self._make(source_family="eCFR Title 8", hybrid_score=0.020, rank=1)
        r2 = self._make(source_family="USCIS Policy Manual", hybrid_score=0.017, rank=2)
        result = rerank_results_by_preferred_source_family([r1, r2], self._l2())
        self.assertEqual(result[0].source_family, "USCIS Policy Manual")

    def test_preferred_result_not_promoted_when_score_gap_large(self) -> None:
        # Preferred starts second; boost (0.004) is smaller than the gap (0.025)
        r1 = self._make(source_family="eCFR Title 8", hybrid_score=0.035, rank=1)
        r2 = self._make(source_family="USCIS Policy Manual", hybrid_score=0.010, rank=2)
        result = rerank_results_by_preferred_source_family([r1, r2], self._l2())
        self.assertEqual(result[0].source_family, "eCFR Title 8")

    def test_ranks_reassigned_after_reorder(self) -> None:
        r1 = self._make(source_family="eCFR Title 8", hybrid_score=0.020, rank=1)
        r2 = self._make(source_family="USCIS Policy Manual", hybrid_score=0.017, rank=2)
        result = rerank_results_by_preferred_source_family([r1, r2], self._l2())
        self.assertEqual(result[0].rank, 1)
        self.assertEqual(result[1].rank, 2)

    def test_mixed_list_preferred_floats_up_no_result_removed(self) -> None:
        r1 = self._make(source_family="eCFR Title 8", hybrid_score=0.020, rank=1)
        r2 = self._make(source_family="USCIS Policy Manual", hybrid_score=0.017, rank=2)
        r3 = self._make(source_family="INA / U.S. Code Title 8", hybrid_score=0.015, rank=3)
        result = rerank_results_by_preferred_source_family([r1, r2, r3], self._l2())
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].source_family, "USCIS Policy Manual")

    def test_all_preferred_results_sorted_by_score(self) -> None:
        r1 = self._make(source_family="USCIS Policy Manual", hybrid_score=0.025, rank=1)
        r2 = self._make(source_family="USCIS Policy Manual", hybrid_score=0.020, rank=2)
        result = rerank_results_by_preferred_source_family([r1, r2], self._l2())
        self.assertGreater(result[0].hybrid_score, result[1].hybrid_score)


if __name__ == "__main__":
    unittest.main()
