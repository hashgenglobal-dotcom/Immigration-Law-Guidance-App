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


class F1OptDetectionTests(unittest.TestCase):
    """understand_query maps F-1 OPT work questions to f1_opt."""

    def _assert_f1_opt(self, message: str) -> None:
        result = understand_query(message)
        self.assertEqual(result.topic, "f1_opt", f"Expected f1_opt for: {message!r}")

    def _result(self) -> object:
        return understand_query("Can I work on OPT after graduation as an F1 student?")

    # --- Positive matches ---

    def test_can_i_work_on_opt_after_graduation_f1(self) -> None:
        self._assert_f1_opt("Can I work on OPT after graduation as an F1 student?")

    def test_how_to_get_ead_f1_student_on_opt(self) -> None:
        self._assert_f1_opt("How do I get EAD as an F-1 student on OPT?")

    def test_opt_work_authorization_process_f1(self) -> None:
        self._assert_f1_opt("What is the OPT work authorization process for F-1?")

    # --- "What is OPT?" invariant: no work context → general ---

    def test_what_is_opt_stays_general(self) -> None:
        result = understand_query("What is OPT?")
        self.assertEqual(result.topic, "general")

    # --- Priority: STEM OPT routes to stem_opt, not f1_opt ---

    def test_stem_opt_routes_to_stem_opt_not_f1_opt(self) -> None:
        result = understand_query("Who is eligible for STEM OPT extension?")
        self.assertEqual(result.topic, "stem_opt")

    # --- Priority: CPT routes to f1_cpt, not f1_opt ---

    def test_cpt_routes_to_f1_cpt_not_f1_opt(self) -> None:
        result = understand_query("Can I do CPT while studying on F1?")
        self.assertEqual(result.topic, "f1_cpt")

    # --- Retrieval query content ---

    def test_f1_opt_retrieval_query_contains_214_2f(self) -> None:
        self.assertIn("214.2(f)", self._result().retrieval_query)

    def test_f1_opt_retrieval_query_contains_274a_12_c3(self) -> None:
        self.assertIn("274a.12(c)(3)", self._result().retrieval_query)

    def test_f1_opt_retrieval_query_contains_post_completion_opt(self) -> None:
        self.assertIn("post-completion OPT", self._result().retrieval_query)

    def test_f1_opt_retrieval_query_contains_f1(self) -> None:
        self.assertIn("F-1", self._result().retrieval_query)

    # --- Answer guidance ---

    def test_f1_opt_answer_guidance_is_nonempty(self) -> None:
        self.assertTrue(self._result().answer_guidance)

    def test_f1_opt_answer_guidance_contains_form_i765(self) -> None:
        self.assertIn("Form I-765", self._result().answer_guidance)

    def test_f1_opt_answer_guidance_contains_dso(self) -> None:
        self.assertIn("DSO", self._result().answer_guidance)

    # --- Source families ---

    def test_f1_opt_preferred_source_families(self) -> None:
        self.assertEqual(
            self._result().preferred_source_families,
            ("eCFR Title 8", "USCIS Policy Manual"),
        )


class F1CptDetectionTests(unittest.TestCase):
    """understand_query maps F-1 CPT questions to f1_cpt."""

    def _assert_f1_cpt(self, message: str) -> None:
        result = understand_query(message)
        self.assertEqual(result.topic, "f1_cpt", f"Expected f1_cpt for: {message!r}")

    def _result(self) -> object:
        return understand_query("Can I do CPT while studying on F1?")

    # --- Positive matches ---

    def test_can_i_do_cpt_while_studying_f1(self) -> None:
        self._assert_f1_cpt("Can I do CPT while studying on F1?")

    def test_curriculum_practical_training_f1_students(self) -> None:
        self._assert_f1_cpt("What is curriculum practical training for F-1 students?")

    # --- Retrieval query content ---

    def test_f1_cpt_retrieval_query_contains_cpt(self) -> None:
        self.assertIn("CPT", self._result().retrieval_query)

    def test_f1_cpt_retrieval_query_contains_curriculum_practical_training(self) -> None:
        self.assertIn("curriculum practical training", self._result().retrieval_query.lower())

    def test_f1_cpt_retrieval_query_contains_214_2f10i(self) -> None:
        self.assertIn("214.2(f)(10)(i)", self._result().retrieval_query)

    def test_f1_cpt_retrieval_query_contains_dso(self) -> None:
        self.assertIn("DSO", self._result().retrieval_query)

    def test_f1_cpt_retrieval_query_contains_i20(self) -> None:
        self.assertIn("I-20", self._result().retrieval_query)

    # --- Answer guidance ---

    def test_f1_cpt_answer_guidance_is_nonempty(self) -> None:
        self.assertTrue(self._result().answer_guidance)

    def test_f1_cpt_answer_guidance_contains_cpt(self) -> None:
        self.assertIn("CPT", self._result().answer_guidance)

    def test_f1_cpt_answer_guidance_contains_i20(self) -> None:
        self.assertIn("I-20", self._result().answer_guidance)

    def test_f1_cpt_answer_guidance_contains_12_months(self) -> None:
        self.assertIn("12 or more months", self._result().answer_guidance)

    # --- Source families ---

    def test_f1_cpt_preferred_source_families(self) -> None:
        self.assertEqual(
            self._result().preferred_source_families,
            ("eCFR Title 8", "USCIS Policy Manual"),
        )


class StemOptDetectionTests(unittest.TestCase):
    """understand_query maps STEM OPT questions to stem_opt."""

    def _assert_stem_opt(self, message: str) -> None:
        result = understand_query(message)
        self.assertEqual(result.topic, "stem_opt", f"Expected stem_opt for: {message!r}")

    def _result(self) -> object:
        return understand_query("Who is eligible for STEM OPT extension?")

    # --- Positive matches ---

    def test_who_is_eligible_for_stem_opt_extension(self) -> None:
        self._assert_stem_opt("Who is eligible for STEM OPT extension?")

    def test_how_to_extend_stem_opt(self) -> None:
        self._assert_stem_opt("How do I extend my STEM OPT work authorization?")

    def test_what_are_stem_opt_requirements(self) -> None:
        self._assert_stem_opt("What are the STEM OPT requirements?")

    # --- Non-STEM OPT with work context stays f1_opt ---

    def test_can_i_work_on_opt_is_f1_opt_not_stem_opt(self) -> None:
        result = understand_query("Can I work on OPT after graduation?")
        self.assertEqual(result.topic, "f1_opt")

    # --- Retrieval query content ---

    def test_stem_opt_retrieval_query_contains_stem_opt(self) -> None:
        self.assertIn("STEM OPT", self._result().retrieval_query)

    def test_stem_opt_retrieval_query_contains_24_month(self) -> None:
        self.assertIn("24-month", self._result().retrieval_query)

    def test_stem_opt_retrieval_query_contains_form_i983(self) -> None:
        self.assertIn("Form I-983", self._result().retrieval_query)

    def test_stem_opt_retrieval_query_contains_e_verify(self) -> None:
        self.assertIn("E-Verify", self._result().retrieval_query)

    def test_stem_opt_retrieval_query_contains_214_2f10ii(self) -> None:
        self.assertIn("214.2(f)(10)(ii)", self._result().retrieval_query)

    def test_stem_opt_retrieval_query_contains_274a_12_c3c(self) -> None:
        self.assertIn("274a.12(c)(3)(C)", self._result().retrieval_query)

    # --- Answer guidance ---

    def test_stem_opt_answer_guidance_is_nonempty(self) -> None:
        self.assertTrue(self._result().answer_guidance)

    def test_stem_opt_answer_guidance_contains_i983(self) -> None:
        self.assertIn("I-983", self._result().answer_guidance)

    def test_stem_opt_answer_guidance_contains_e_verify(self) -> None:
        self.assertIn("E-Verify", self._result().answer_guidance)

    # --- Source families ---

    def test_stem_opt_preferred_source_families(self) -> None:
        self.assertEqual(
            self._result().preferred_source_families,
            ("eCFR Title 8", "USCIS Policy Manual"),
        )


class F1PracticalTrainingFilterTests(unittest.TestCase):
    """filter_results_for_understanding removes contaminating chunks for F-1 practical training."""

    def _make(self, *, citation: str = "", topic: str = "", subtopic: str | None = None, snippet: str = "") -> object:
        return types.SimpleNamespace(citation=citation, topic=topic, subtopic=subtopic, snippet=snippet)

    def _f1_opt(self) -> object:
        return understand_query("Can I work on OPT after graduation as an F1 student?")

    def _f1_cpt(self) -> object:
        return understand_query("Can I do CPT while studying on F1?")

    def _stem_opt(self) -> object:
        return understand_query("Who is eligible for STEM OPT extension?")

    def _general(self) -> object:
        return understand_query("What is OPT?")

    # --- f1_opt ---

    def test_f1_opt_keeps_opt_chunk(self) -> None:
        r = self._make(snippet="F-1 student optional practical training post-completion OPT.")
        self.assertIn(r, filter_results_for_understanding([r], self._f1_opt()))

    def test_f1_opt_rejects_cpt_chunk(self) -> None:
        opt_r = self._make(snippet="F-1 optional practical training OPT 274a.12(c)(3).")
        cpt_r = self._make(snippet="curriculum practical training CPT authorized on I-20.")
        filtered = filter_results_for_understanding([opt_r, cpt_r], self._f1_opt())
        self.assertNotIn(cpt_r, filtered)

    def test_f1_opt_rejects_h3_chunk(self) -> None:
        opt_r = self._make(snippet="F-1 optional practical training OPT 274a.12(c)(3).")
        h3_r = self._make(snippet="H-3 trainee visa for aliens coming to receive training.")
        filtered = filter_results_for_understanding([opt_r, h3_r], self._f1_opt())
        self.assertNotIn(h3_r, filtered)

    def test_f1_opt_fallback_returns_original_if_all_rejected(self) -> None:
        results = [
            self._make(snippet="curriculum practical training CPT authorized."),
            self._make(snippet="H-3 trainee program."),
        ]
        filtered = filter_results_for_understanding(list(results), self._f1_opt())
        self.assertEqual(filtered, results)

    # --- f1_cpt ---

    def test_f1_cpt_keeps_cpt_chunk(self) -> None:
        r = self._make(snippet="curriculum practical training CPT authorized by DSO on I-20.")
        self.assertIn(r, filter_results_for_understanding([r], self._f1_cpt()))

    def test_f1_cpt_rejects_stem_opt_chunk(self) -> None:
        cpt_r = self._make(snippet="curriculum practical training authorized under 214.2(f)(10)(i).")
        stem_r = self._make(snippet="STEM OPT 24-month extension Form I-983 E-Verify.")
        filtered = filter_results_for_understanding([cpt_r, stem_r], self._f1_cpt())
        self.assertNotIn(stem_r, filtered)

    def test_f1_cpt_rejects_tn_chunk(self) -> None:
        cpt_r = self._make(snippet="CPT authorized integral part of established curriculum.")
        tn_r = self._make(snippet="TN occupation list for Canadian and Mexican citizens.")
        filtered = filter_results_for_understanding([cpt_r, tn_r], self._f1_cpt())
        self.assertNotIn(tn_r, filtered)

    def test_f1_cpt_fallback_returns_original_if_all_rejected(self) -> None:
        results = [
            self._make(snippet="STEM OPT extension Form I-983 E-Verify employer."),
            self._make(snippet="TN occupation Canada Mexico NAFTA USMCA."),
        ]
        filtered = filter_results_for_understanding(list(results), self._f1_cpt())
        self.assertEqual(filtered, results)

    # --- stem_opt ---

    def test_stem_opt_keeps_stem_opt_chunk(self) -> None:
        r = self._make(snippet="STEM OPT 24-month extension Form I-983 Training Plan E-Verify.")
        self.assertIn(r, filter_results_for_understanding([r], self._stem_opt()))

    def test_stem_opt_rejects_cpt_chunk(self) -> None:
        stem_r = self._make(snippet="STEM OPT 24-month extension 274a.12(c)(3)(C).")
        cpt_r = self._make(snippet="curriculum practical training CPT DSO authorized.")
        filtered = filter_results_for_understanding([stem_r, cpt_r], self._stem_opt())
        self.assertNotIn(cpt_r, filtered)

    def test_stem_opt_rejects_h3_chunk(self) -> None:
        stem_r = self._make(snippet="STEM OPT extension Form I-983 E-Verify employer.")
        h3_r = self._make(snippet="H-3 trainee program for alien trainees.")
        filtered = filter_results_for_understanding([stem_r, h3_r], self._stem_opt())
        self.assertNotIn(h3_r, filtered)

    def test_stem_opt_fallback_returns_original_if_all_rejected(self) -> None:
        results = [
            self._make(snippet="curriculum practical training CPT authorized."),
            self._make(snippet="H-3 trainee program for alien trainees."),
        ]
        filtered = filter_results_for_understanding(list(results), self._stem_opt())
        self.assertEqual(filtered, results)

    # --- general topic passthrough ---

    def test_general_topic_returns_opt_result_unchanged(self) -> None:
        r = self._make(snippet="F-1 optional practical training OPT.")
        result = filter_results_for_understanding([r], self._general())
        self.assertIn(r, result)


class F1PracticalTrainingStrictFilterTests(unittest.TestCase):
    """Stricter filtering for f1_opt and stem_opt: hard rejects + prefer-strong behavior."""

    def _make(self, *, citation: str = "", topic: str = "", subtopic: str | None = None, snippet: str = "") -> object:
        return types.SimpleNamespace(citation=citation, topic=topic, subtopic=subtopic, snippet=snippet)

    def _f1_opt(self) -> object:
        return understand_query("Can I work on OPT after graduation as an F1 student?")

    def _stem_opt(self) -> object:
        return understand_query("Who is eligible for STEM OPT extension?")

    def _l2(self) -> object:
        return understand_query("Can my spouse work if I am on L1 visa?")

    # ---- f1_opt hard rejects ------------------------------------------------

    def test_f1_opt_rejects_214_13_chunk_even_with_opt_mention(self) -> None:
        # 214.13 SEVIS fee chunk that says "optional practical training" — hard reject overrides keep.
        valid_r = self._make(snippet="F-1 optional practical training OPT 274a.12(c)(3).")
        fee_r = self._make(citation="8 CFR 214.13", snippet="optional practical training SEVIS fee no new fee.")
        filtered = filter_results_for_understanding([valid_r, fee_r], self._f1_opt())
        self.assertIn(valid_r, filtered)
        self.assertNotIn(fee_r, filtered)

    def test_f1_opt_rejects_sevis_fee_snippet(self) -> None:
        valid_r = self._make(snippet="F-1 optional practical training OPT 274a.12(c)(3).")
        fee_r = self._make(snippet="SEVIS fee is required; no new fee for certain categories.")
        filtered = filter_results_for_understanding([valid_r, fee_r], self._f1_opt())
        self.assertNotIn(fee_r, filtered)

    def test_f1_opt_rejects_generic_274a12_dependent_chunk(self) -> None:
        # "alien spouse or unmarried dependent child" is an f1_opt hard reject.
        valid_r = self._make(snippet="F-1 optional practical training OPT 274a.12(c)(3).")
        dep_r = self._make(citation="8 CFR 274a.12", snippet="alien spouse or unmarried dependent child employment authorization.")
        filtered = filter_results_for_understanding([valid_r, dep_r], self._f1_opt())
        self.assertIn(valid_r, filtered)
        self.assertNotIn(dep_r, filtered)

    def test_f1_opt_rejects_tps_chunk(self) -> None:
        valid_r = self._make(snippet="F-1 optional practical training OPT 274a.12(c)(3).")
        tps_r = self._make(snippet="Temporary Protected Status pending applicants may apply for EAD.")
        filtered = filter_results_for_understanding([valid_r, tps_r], self._f1_opt())
        self.assertNotIn(tps_r, filtered)

    def test_f1_opt_keeps_214_2_opt_chunk(self) -> None:
        r = self._make(citation="8 CFR 214.2(f)", snippet="F-1 student optional practical training employment authorization.")
        self.assertIn(r, filter_results_for_understanding([r], self._f1_opt()))

    def test_f1_opt_drops_neutral_when_strong_keeps_exist(self) -> None:
        opt_r = self._make(snippet="F-1 optional practical training OPT 274a.12(c)(3).")
        neutral_r = self._make(snippet="Employment authorization documents are issued for various immigration categories.")
        filtered = filter_results_for_understanding([opt_r, neutral_r], self._f1_opt())
        self.assertIn(opt_r, filtered)
        self.assertNotIn(neutral_r, filtered)

    def test_f1_opt_fallback_if_all_hard_rejected(self) -> None:
        results = [
            self._make(citation="8 CFR 214.13", snippet="SEVIS fee optional practical training."),
            self._make(snippet="Temporary Protected Status TPS pending EAD."),
        ]
        filtered = filter_results_for_understanding(list(results), self._f1_opt())
        self.assertEqual(filtered, results)

    # ---- stem_opt hard rejects ----------------------------------------------

    def test_stem_opt_rejects_274a13_tps_chunk_when_valid_stem_opt_exists(self) -> None:
        stem_r = self._make(snippet="STEM OPT 24-month extension Form I-983 Training Plan E-Verify.")
        tps_r = self._make(citation="8 CFR 274a.13", snippet="Temporary Protected Status pending TPS EAD automatic extension.")
        filtered = filter_results_for_understanding([stem_r, tps_r], self._stem_opt())
        self.assertIn(stem_r, filtered)
        self.assertNotIn(tps_r, filtered)

    def test_stem_opt_rejects_274a13_without_stem_key_terms(self) -> None:
        # 274a.13 citation with no STEM OPT topic content → hard reject.
        stem_r = self._make(snippet="STEM OPT extension 214.2(f)(10)(ii) 24-month E-Verify.")
        generic_274a13_r = self._make(citation="8 CFR 274a.13", snippet="Employment authorization renewal for pending applicants.")
        filtered = filter_results_for_understanding([stem_r, generic_274a13_r], self._stem_opt())
        self.assertNotIn(generic_274a13_r, filtered)

    def test_stem_opt_keeps_214_2_stem_opt_chunk(self) -> None:
        r = self._make(citation="8 CFR 214.2(f)(10)(ii)", snippet="STEM OPT 24-month extension for F-1 students with STEM degree.")
        self.assertIn(r, filter_results_for_understanding([r], self._stem_opt()))

    def test_stem_opt_keeps_vol2_partf_ch5_stem_opt_mention(self) -> None:
        r = self._make(citation="USCIS Policy Manual Vol 2 Part F Ch 5", snippet="STEM OPT extension requirements Training Plan employer E-Verify.")
        self.assertIn(r, filter_results_for_understanding([r], self._stem_opt()))

    def test_stem_opt_rejects_214_13_sevis_fee_chunk(self) -> None:
        stem_r = self._make(snippet="STEM OPT 24-month extension Form I-983.")
        fee_r = self._make(citation="8 CFR 214.13", snippet="SEVIS fee no new fee extension of stay.")
        filtered = filter_results_for_understanding([stem_r, fee_r], self._stem_opt())
        self.assertNotIn(fee_r, filtered)

    def test_stem_opt_fallback_if_all_hard_rejected(self) -> None:
        results = [
            self._make(citation="8 CFR 274a.13", snippet="Temporary Protected Status TPS pending EAD."),
            self._make(snippet="SEVIS fee 214.13 no new fee."),
        ]
        filtered = filter_results_for_understanding(list(results), self._stem_opt())
        self.assertEqual(filtered, results)

    # ---- l2 unaffected ------------------------------------------------------

    def test_l2_filter_not_affected_by_strict_filter_changes(self) -> None:
        l2_r = self._make(snippet="L-2 spouse employment authorized incident to status.")
        h4_r = self._make(topic="H-4 Employment Authorization", snippet="H-4 spouses may apply for EAD.")
        filtered = filter_results_for_understanding([l2_r, h4_r], self._l2())
        self.assertIn(l2_r, filtered)
        self.assertNotIn(h4_r, filtered)


class AsylumEadDetectionTests(unittest.TestCase):
    """understand_query maps pending-asylum EAD questions to asylum_ead."""

    def _assert_asylum_ead(self, message: str) -> None:
        result = understand_query(message)
        self.assertEqual(result.topic, "asylum_ead", f"Expected asylum_ead for: {message!r}")

    def _result(self) -> object:
        return understand_query("When can I apply for EAD after filing asylum?")

    # --- Positive matches ---

    def test_when_can_i_apply_for_ead_after_filing_asylum(self) -> None:
        self._assert_asylum_ead("When can I apply for EAD after filing asylum?")

    def test_pending_asylum_work_authorization(self) -> None:
        self._assert_asylum_ead("Can I get work authorization with pending asylum?")

    def test_filed_asylum_how_long_before_ead(self) -> None:
        self._assert_asylum_ead("I filed asylum, how long before I can get an EAD?")

    def test_ead_as_asylum_applicant(self) -> None:
        self._assert_asylum_ead("How do I apply for EAD as an asylum applicant?")

    # --- Negative: asylum without EAD signal stays general ---

    def test_asylum_without_ead_signal_remains_general(self) -> None:
        result = understand_query("Can I apply for asylum?")
        self.assertEqual(result.topic, "general")

    # --- Negative: generic EAD without asylum stays general ---

    def test_generic_ead_without_asylum_remains_general(self) -> None:
        result = understand_query("How do I apply for EAD?")
        self.assertEqual(result.topic, "general")

    # --- Retrieval query content ---

    def test_retrieval_query_contains_208_7(self) -> None:
        self.assertIn("208.7", self._result().retrieval_query)

    def test_retrieval_query_contains_274a12_c8(self) -> None:
        self.assertIn("274a.12(c)(8)", self._result().retrieval_query)

    def test_retrieval_query_contains_180_day(self) -> None:
        self.assertIn("180-day", self._result().retrieval_query)

    def test_retrieval_query_contains_form_i765(self) -> None:
        self.assertIn("Form I-765", self._result().retrieval_query)

    # --- Answer guidance ---

    def test_answer_guidance_contains_180_day(self) -> None:
        self.assertIn("180", self._result().answer_guidance)

    def test_answer_guidance_contains_c8(self) -> None:
        self.assertIn("(c)(8)", self._result().answer_guidance)

    def test_answer_guidance_contains_form_i765(self) -> None:
        self.assertIn("Form I-765", self._result().answer_guidance)

    # --- Source families and intent ---

    def test_preferred_source_families(self) -> None:
        self.assertEqual(
            self._result().preferred_source_families,
            ("eCFR Title 8", "USCIS Policy Manual"),
        )

    def test_intent_label_is_case_specific_or_risk(self) -> None:
        self.assertEqual(self._result().intent_label, "case_specific_or_risk")


class I485AdvanceParoleDetectionTests(unittest.TestCase):
    """understand_query maps pending I-485 travel questions to i485_advance_parole."""

    def _assert_i485_ap(self, message: str) -> None:
        result = understand_query(message)
        self.assertEqual(
            result.topic, "i485_advance_parole", f"Expected i485_advance_parole for: {message!r}"
        )

    def _result(self) -> object:
        return understand_query(
            "Can I travel while my I-485 is pending if I have advance parole?"
        )

    # --- Positive matches ---

    def test_travel_pending_i485_advance_parole(self) -> None:
        self._assert_i485_ap(
            "Can I travel while my I-485 is pending if I have advance parole?"
        )

    def test_travel_without_advance_parole_i485(self) -> None:
        self._assert_i485_ap(
            "What happens if I travel without advance parole while I-485 is pending?"
        )

    def test_adjustment_status_travel_abroad(self) -> None:
        self._assert_i485_ap(
            "Can I travel abroad while my adjustment of status application is pending?"
        )

    # --- Negative: advance parole without I-485 context stays general ---

    def test_generic_advance_parole_without_i485_remains_general(self) -> None:
        result = understand_query("How do I apply for advance parole?")
        self.assertEqual(result.topic, "general")

    # --- Retrieval query content ---

    def test_retrieval_query_contains_advance_parole(self) -> None:
        self.assertIn("advance parole", self._result().retrieval_query.lower())

    def test_retrieval_query_contains_form_i131(self) -> None:
        self.assertIn("Form I-131", self._result().retrieval_query)

    def test_retrieval_query_contains_abandonment(self) -> None:
        self.assertIn("abandonment", self._result().retrieval_query.lower())

    def test_retrieval_query_contains_245_2(self) -> None:
        self.assertIn("245.2", self._result().retrieval_query)

    # --- Answer guidance ---

    def test_answer_guidance_contains_abandonment(self) -> None:
        self.assertIn("abandoned", self._result().answer_guidance.lower())

    def test_answer_guidance_contains_form_i131(self) -> None:
        self.assertIn("Form I-131", self._result().answer_guidance)

    def test_answer_guidance_contains_245_2(self) -> None:
        self.assertIn("245.2", self._result().answer_guidance)

    # --- Source families and intent ---

    def test_preferred_source_families(self) -> None:
        self.assertEqual(
            self._result().preferred_source_families,
            ("eCFR Title 8", "USCIS Policy Manual"),
        )

    def test_intent_label_is_case_specific_or_risk(self) -> None:
        self.assertEqual(self._result().intent_label, "case_specific_or_risk")


class NtaRemovalHighRiskDetectionTests(unittest.TestCase):
    """understand_query maps personal NTA/removal questions to nta_removal_high_risk."""

    def _assert_nta(self, message: str) -> None:
        result = understand_query(message)
        self.assertEqual(
            result.topic, "nta_removal_high_risk", f"Expected nta_removal_high_risk for: {message!r}"
        )

    def _result(self) -> object:
        return understand_query(
            "I received a Notice to Appear for removal proceedings. What should I do?"
        )

    # --- Positive matches ---

    def test_received_nta_removal_proceedings(self) -> None:
        self._assert_nta(
            "I received a Notice to Appear for removal proceedings. What should I do?"
        )

    def test_got_nta_next_steps(self) -> None:
        self._assert_nta("I got an NTA, what are my next steps?")

    def test_what_to_do_after_receiving_nta(self) -> None:
        self._assert_nta("What should I do after receiving a Notice to Appear?")

    def test_have_immigration_court_after_nta(self) -> None:
        self._assert_nta("I have immigration court next month after an NTA")

    # --- Negative: definitional / general NTA questions stay general ---

    def test_what_is_nta_remains_general(self) -> None:
        result = understand_query("What is a Notice to Appear?")
        self.assertEqual(result.topic, "general")

    def test_nta_requirements_remains_general(self) -> None:
        result = understand_query("What are NTA requirements?")
        self.assertEqual(result.topic, "general")

    # --- Retrieval query content ---

    def test_retrieval_query_contains_239_1(self) -> None:
        self.assertIn("239.1", self._result().retrieval_query)

    def test_retrieval_query_contains_in_absentia(self) -> None:
        self.assertIn("in absentia", self._result().retrieval_query.lower())

    def test_retrieval_query_contains_eoir(self) -> None:
        self.assertIn("EOIR", self._result().retrieval_query)

    def test_retrieval_query_contains_removal_proceedings(self) -> None:
        self.assertIn("removal proceedings", self._result().retrieval_query.lower())

    # --- Answer guidance ---

    def test_answer_guidance_contains_in_absentia(self) -> None:
        self.assertIn("in absentia", self._result().answer_guidance.lower())

    def test_answer_guidance_recommends_attorney(self) -> None:
        guidance = self._result().answer_guidance.lower()
        self.assertTrue(
            "attorney" in guidance or "accredited representative" in guidance,
            "Answer guidance must recommend consulting an attorney or accredited representative",
        )

    def test_answer_guidance_not_advise_court_avoidance(self) -> None:
        self.assertIn("do not advise", self._result().answer_guidance.lower())

    # --- Source families and intent ---

    def test_intent_label_is_case_specific_or_risk(self) -> None:
        self.assertEqual(self._result().intent_label, "case_specific_or_risk")

    def test_preferred_source_families(self) -> None:
        self.assertEqual(
            self._result().preferred_source_families,
            ("eCFR Title 8", "USCIS Policy Manual", "BIA Precedent Decisions"),
        )


class HumanitarianFilterTests(unittest.TestCase):
    """filter_results_for_understanding removes contaminating chunks for humanitarian topics."""

    def _make(self, *, citation: str = "", topic: str = "", subtopic: str | None = None, snippet: str = "") -> object:
        return types.SimpleNamespace(citation=citation, topic=topic, subtopic=subtopic, snippet=snippet)

    def _asylum_ead(self) -> object:
        return understand_query("When can I apply for EAD after filing asylum?")

    def _i485_ap(self) -> object:
        return understand_query("Can I travel while my I-485 is pending if I have advance parole?")

    def _nta_removal(self) -> object:
        return understand_query(
            "I received a Notice to Appear for removal proceedings. What should I do?"
        )

    def _l2(self) -> object:
        return understand_query("Can my spouse work if I am on L1 visa?")

    def _f1_opt(self) -> object:
        return understand_query("Can I work on OPT after graduation as an F1 student?")

    # --- asylum_ead ---

    def test_asylum_ead_keeps_208_7_chunk(self) -> None:
        r = self._make(
            citation="8 CFR 208.7",
            snippet="Asylum applicant EAD 180-day waiting period employment authorization.",
        )
        self.assertIn(r, filter_results_for_understanding([r], self._asylum_ead()))

    def test_asylum_ead_keeps_274a12_c8_chunk(self) -> None:
        r = self._make(snippet="274a.12(c)(8) pending asylum applicant employment authorization.")
        self.assertIn(r, filter_results_for_understanding([r], self._asylum_ead()))

    def test_asylum_ead_hard_rejects_i551_chunk_when_valid_exists(self) -> None:
        valid_r = self._make(
            citation="8 CFR 208.7",
            snippet="Asylum applicant 180-day EAD 274a.12(c)(8).",
        )
        lpr_r = self._make(snippet="Form I-551 lawful permanent resident employment authorization.")
        filtered = filter_results_for_understanding([valid_r, lpr_r], self._asylum_ead())
        self.assertIn(valid_r, filtered)
        self.assertNotIn(lpr_r, filtered)

    def test_asylum_ead_hard_rejects_1208_3_chunk_when_valid_exists(self) -> None:
        valid_r = self._make(
            citation="8 CFR 208.7",
            snippet="Asylum applicant 180-day EAD 274a.12(c)(8).",
        )
        form_r = self._make(
            citation="8 CFR 1208.3",
            snippet="Asylum application filing procedures Form I-589.",
        )
        filtered = filter_results_for_understanding([valid_r, form_r], self._asylum_ead())
        self.assertIn(valid_r, filtered)
        self.assertNotIn(form_r, filtered)

    def test_asylum_ead_fallback_returns_original_if_all_rejected(self) -> None:
        results = [
            self._make(snippet="Form I-551 lawful permanent resident employment authorization."),
            self._make(citation="8 CFR 1208.3", snippet="Asylum application filing procedures."),
        ]
        filtered = filter_results_for_understanding(list(results), self._asylum_ead())
        self.assertEqual(filtered, results)

    # --- i485_advance_parole ---

    def test_i485_ap_keeps_advance_parole_chunk(self) -> None:
        r = self._make(snippet="Advance parole travel document for I-485 pending adjustment.")
        self.assertIn(r, filter_results_for_understanding([r], self._i485_ap()))

    def test_i485_ap_keeps_abandonment_chunk(self) -> None:
        r = self._make(
            snippet="Travel abroad without advance parole results in abandonment under 8 CFR 245.2."
        )
        self.assertIn(r, filter_results_for_understanding([r], self._i485_ap()))

    def test_i485_ap_rejects_1245_13_chunk_when_valid_ap_chunk_exists(self) -> None:
        valid_r = self._make(snippet="Advance parole Form I-131 abandonment 245.2.")
        special_r = self._make(
            citation="8 CFR 1245.13",
            snippet="Special provisions for Cuban nationals.",
        )
        filtered = filter_results_for_understanding([valid_r, special_r], self._i485_ap())
        self.assertIn(valid_r, filtered)
        self.assertNotIn(special_r, filtered)

    def test_i485_ap_fallback_returns_original_if_all_rejected(self) -> None:
        results = [
            self._make(citation="8 CFR 1245.13", snippet="Special provisions for Cuban nationals."),
            self._make(snippet="Syrian special immigrant travel provisions Public Law special immigrant."),
        ]
        filtered = filter_results_for_understanding(list(results), self._i485_ap())
        self.assertEqual(filtered, results)

    def test_i485_ap_hard_rejects_208_8_asylum_travel_when_valid_exists(self) -> None:
        valid_r = self._make(snippet="Advance parole Form I-131 abandonment 245.2 pending I-485.")
        asylum_r = self._make(
            citation="8 CFR 208.8",
            snippet="Asylum applicant travel abroad country of claimed persecution 208.8.",
        )
        filtered = filter_results_for_understanding([valid_r, asylum_r], self._i485_ap())
        self.assertIn(valid_r, filtered)
        self.assertNotIn(asylum_r, filtered)

    def test_i485_ap_hard_rejects_1208_8_asylum_travel_when_valid_exists(self) -> None:
        valid_r = self._make(snippet="Advance parole Form I-131 abandonment 245.2 pending I-485.")
        asylum_r = self._make(
            citation="8 CFR 1208.8",
            snippet="Asylum applicant travel abroad 1208.8.",
        )
        filtered = filter_results_for_understanding([valid_r, asylum_r], self._i485_ap())
        self.assertIn(valid_r, filtered)
        self.assertNotIn(asylum_r, filtered)

    def test_i485_ap_hard_rejects_1245_12_when_valid_245_2_exists(self) -> None:
        valid_r = self._make(
            citation="8 CFR 245.2",
            snippet="Advance parole abandonment adjustment of status pending I-485.",
        )
        special_r = self._make(
            citation="8 CFR 1245.12",
            snippet="Special adjustment provisions 1245.12.",
        )
        filtered = filter_results_for_understanding([valid_r, special_r], self._i485_ap())
        self.assertIn(valid_r, filtered)
        self.assertNotIn(special_r, filtered)

    def test_i485_ap_keeps_245_2_abandonment_chunk(self) -> None:
        r = self._make(
            citation="8 CFR 245.2",
            snippet="Travel abroad without advance parole results in abandonment of pending I-485.",
        )
        self.assertIn(r, filter_results_for_understanding([r], self._i485_ap()))

    def test_i485_ap_keeps_1245_2_with_i485_context(self) -> None:
        r = self._make(
            citation="8 CFR 1245.2",
            snippet="Pending I-485 adjustment advance parole abandonment 1245.2.",
        )
        self.assertIn(r, filter_results_for_understanding([r], self._i485_ap()))

    def test_i485_ap_drops_1245_2_without_context_when_strong_keep_exists(self) -> None:
        valid_r = self._make(snippet="Advance parole Form I-131 abandonment 245.2 pending I-485.")
        neutral_r = self._make(
            citation="8 CFR 1245.2",
            snippet="Adjustment procedure 1245.2 unrelated context.",
        )
        filtered = filter_results_for_understanding([valid_r, neutral_r], self._i485_ap())
        self.assertIn(valid_r, filtered)
        self.assertNotIn(neutral_r, filtered)

    # --- nta_removal_high_risk ---

    def test_nta_removal_keeps_239_1_chunk(self) -> None:
        r = self._make(
            citation="8 CFR 239.1",
            snippet="Notice to Appear removal proceedings immigration court EOIR.",
        )
        self.assertIn(r, filter_results_for_understanding([r], self._nta_removal()))

    def test_nta_removal_keeps_in_absentia_chunk(self) -> None:
        r = self._make(
            snippet="In absentia removal order when respondent fails to appear in immigration court."
        )
        self.assertIn(r, filter_results_for_understanding([r], self._nta_removal()))

    def test_nta_removal_rejects_i751_chunk_when_valid_nta_chunk_exists(self) -> None:
        valid_r = self._make(
            citation="8 CFR 239.1",
            snippet="Notice to appear NTA removal proceedings.",
        )
        cpr_r = self._make(
            snippet="Form I-751 petition to remove conditions of residence conditional resident."
        )
        filtered = filter_results_for_understanding([valid_r, cpr_r], self._nta_removal())
        self.assertIn(valid_r, filtered)
        self.assertNotIn(cpr_r, filtered)

    def test_nta_removal_fallback_returns_original_if_all_rejected(self) -> None:
        results = [
            self._make(snippet="Form I-751 petition to remove conditions conditional permanent resident."),
            self._make(snippet="VAWA removal of conditions battered spouse conditional resident."),
        ]
        filtered = filter_results_for_understanding(list(results), self._nta_removal())
        self.assertEqual(filtered, results)

    def test_nta_answer_guidance_no_dso(self) -> None:
        result = understand_query(
            "I received a Notice to Appear for removal proceedings. What should I do?"
        )
        self.assertIn("Do not mention DSO", result.answer_guidance)

    def test_nta_answer_guidance_bia_accredited_representative(self) -> None:
        result = understand_query(
            "I received a Notice to Appear for removal proceedings. What should I do?"
        )
        self.assertTrue(
            "BIA-accredited representative" in result.answer_guidance
            or "accredited representative" in result.answer_guidance,
            "Expected 'BIA-accredited representative' or 'accredited representative' in answer_guidance",
        )

    # --- Existing filters unaffected ---

    def test_l2_filter_not_affected_by_humanitarian_changes(self) -> None:
        l2_r = self._make(snippet="L-2 spouse employment authorized incident to status.")
        h4_r = self._make(topic="H-4 Employment Authorization", snippet="H-4 spouses may apply for EAD.")
        filtered = filter_results_for_understanding([l2_r, h4_r], self._l2())
        self.assertIn(l2_r, filtered)
        self.assertNotIn(h4_r, filtered)

    def test_f1_opt_filter_not_affected_by_humanitarian_changes(self) -> None:
        opt_r = self._make(snippet="F-1 optional practical training OPT 274a.12(c)(3).")
        fee_r = self._make(citation="8 CFR 214.13", snippet="SEVIS fee optional practical training.")
        filtered = filter_results_for_understanding([opt_r, fee_r], self._f1_opt())
        self.assertIn(opt_r, filtered)
        self.assertNotIn(fee_r, filtered)


class BiaSourceFamilyRoutingTests(unittest.TestCase):
    """BIA is a preferred source only for nta_removal_high_risk, never for other topics."""

    _NTA_MSG = "I received a Notice to Appear for removal proceedings. What should I do?"
    _ASYLUM_EAD_MSG = "I have a pending asylum application. Can I get an EAD?"
    _I485_MSG = "I have a pending I-485. Can I travel with advance parole?"
    _OPT_MSG = "Can I work on OPT after graduation?"
    _CPT_MSG = "I am an F-1 student. Can I do CPT?"
    _STEM_MSG = "I am on STEM OPT. Can I extend?"

    # --- NTA/removal must include BIA ---

    def test_nta_preferred_families_includes_bia(self) -> None:
        result = understand_query(self._NTA_MSG)
        self.assertEqual(result.topic, "nta_removal_high_risk")
        self.assertIn("BIA Precedent Decisions", result.preferred_source_families)

    def test_nta_preferred_families_includes_ecfr(self) -> None:
        result = understand_query(self._NTA_MSG)
        self.assertIn("eCFR Title 8", result.preferred_source_families)

    def test_nta_preferred_families_includes_uscis_pm(self) -> None:
        result = understand_query(self._NTA_MSG)
        self.assertIn("USCIS Policy Manual", result.preferred_source_families)

    # --- NTA retrieval query must contain BIA terms ---

    def test_nta_retrieval_query_contains_bia(self) -> None:
        result = understand_query(self._NTA_MSG)
        self.assertIn("BIA", result.retrieval_query)

    def test_nta_retrieval_query_contains_board_of_immigration_appeals(self) -> None:
        result = understand_query(self._NTA_MSG)
        self.assertIn("Board of Immigration Appeals", result.retrieval_query)

    def test_nta_retrieval_query_contains_in_dec(self) -> None:
        result = understand_query(self._NTA_MSG)
        self.assertIn("I&N Dec.", result.retrieval_query)

    def test_nta_retrieval_query_contains_precedent_decision(self) -> None:
        result = understand_query(self._NTA_MSG)
        self.assertIn("precedent decision", result.retrieval_query.lower())

    # --- Other topics must NOT include BIA ---

    def test_asylum_ead_preferred_families_excludes_bia(self) -> None:
        result = understand_query(self._ASYLUM_EAD_MSG)
        self.assertEqual(result.topic, "asylum_ead")
        self.assertNotIn("BIA Precedent Decisions", result.preferred_source_families)

    def test_i485_advance_parole_preferred_families_excludes_bia(self) -> None:
        result = understand_query(self._I485_MSG)
        self.assertEqual(result.topic, "i485_advance_parole")
        self.assertNotIn("BIA Precedent Decisions", result.preferred_source_families)

    def test_f1_opt_preferred_families_excludes_bia(self) -> None:
        result = understand_query(self._OPT_MSG)
        self.assertEqual(result.topic, "f1_opt")
        self.assertNotIn("BIA Precedent Decisions", result.preferred_source_families)

    def test_f1_cpt_preferred_families_excludes_bia(self) -> None:
        result = understand_query(self._CPT_MSG)
        self.assertEqual(result.topic, "f1_cpt")
        self.assertNotIn("BIA Precedent Decisions", result.preferred_source_families)

    def test_stem_opt_preferred_families_excludes_bia(self) -> None:
        result = understand_query(self._STEM_MSG)
        self.assertEqual(result.topic, "stem_opt")
        self.assertNotIn("BIA Precedent Decisions", result.preferred_source_families)

    def test_l2_preferred_families_excludes_bia(self) -> None:
        result = understand_query("Can my spouse work if I am on L1 visa?")
        self.assertEqual(result.topic, "l2_work_authorization")
        self.assertNotIn("BIA Precedent Decisions", result.preferred_source_families)


if __name__ == "__main__":
    unittest.main()
