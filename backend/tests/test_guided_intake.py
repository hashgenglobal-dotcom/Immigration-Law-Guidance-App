"""Direct tests for guided intake routing (no DB or Ollama)."""

from __future__ import annotations

import unittest

from app.services.chat_service import ChatService
from app.services.guided_intake import (
    detect_broad_topic,
    is_specific_question,
    resolve_retrieval_query,
)


class GuidedIntakeDetectionTests(unittest.TestCase):
    def test_broad_ead_triggers_clarification_topic(self) -> None:
        self.assertEqual(detect_broad_topic("How do I apply for EAD?"), "ead")

    def test_specific_asylum_ead_is_direct(self) -> None:
        self.assertTrue(
            is_specific_question("Can asylum applicants get work authorization?")
        )
        self.assertIsNone(
            detect_broad_topic("Can asylum applicants get work authorization?")
        )

    def test_nta_definition_is_direct(self) -> None:
        self.assertTrue(is_specific_question("What is a Notice to Appear?"))
        self.assertIsNone(detect_broad_topic("What is a Notice to Appear?"))

    def test_green_card_is_broad(self) -> None:
        self.assertEqual(detect_broad_topic("Can I get a green card?"), "aos")

    def test_citizenship_is_broad(self) -> None:
        self.assertEqual(detect_broad_topic("How do I become a citizen?"), "naturalization")

    def test_category_changes_retrieval_query(self) -> None:
        q = resolve_retrieval_query(
            "How do I apply for EAD?",
            "f1_opt_stem_opt",
        )
        self.assertIn("STEM OPT", q)
        self.assertIn("214.2", q)

    def test_asylum_category_query(self) -> None:
        q = resolve_retrieval_query(
            "How do I apply for EAD?",
            "asylum_pending",
        )
        self.assertIn("asylum", q.lower())
        self.assertIn("208.7", q)

    # --- Asylum EAD specific detection ---

    def test_ead_as_asylum_applicant_is_specific(self) -> None:
        self.assertTrue(is_specific_question("How do I apply for an EAD as an asylum applicant?"))
        self.assertIsNone(detect_broad_topic("How do I apply for an EAD as an asylum applicant?"))

    def test_work_permit_as_asylum_applicant_is_specific(self) -> None:
        self.assertTrue(is_specific_question("How do I apply for a work permit as an asylum applicant?"))
        self.assertIsNone(detect_broad_topic("How do I apply for a work permit as an asylum applicant?"))

    def test_pending_asylum_applicants_ead_is_specific(self) -> None:
        self.assertTrue(is_specific_question("Can pending asylum applicants apply for EAD?"))
        self.assertIsNone(detect_broad_topic("Can pending asylum applicants apply for EAD?"))

    def test_filed_asylum_employment_auth_is_specific(self) -> None:
        self.assertTrue(
            is_specific_question("I filed asylum, can I apply for employment authorization?")
        )

    def test_i765_after_filing_asylum_is_specific(self) -> None:
        self.assertTrue(is_specific_question("How do I apply for Form I-765 after filing asylum?"))

    # --- I-485 travel specific detection ---

    def test_i485_travel_with_my_is_specific(self) -> None:
        self.assertTrue(is_specific_question("Can I travel while my I-485 is pending?"))
        self.assertIsNone(detect_broad_topic("Can I travel while my I-485 is pending?"))

    # --- Broad EAD still triggers clarification ---

    def test_broad_ead_no_asylum_context_triggers_clarification(self) -> None:
        self.assertEqual(detect_broad_topic("How do I apply for EAD?"), "ead")
        self.assertEqual(detect_broad_topic("Can I work in the United States?"), "ead")

    # --- Query rewriting without selected_category ---

    def test_asylum_ead_direct_resolves_to_asylum_pending_query(self) -> None:
        q = resolve_retrieval_query("How do I apply for an EAD as an asylum applicant?", None)
        self.assertIn("asylum", q.lower())
        self.assertIn("208.7", q)

    def test_i485_travel_resolves_to_travel_aos_query(self) -> None:
        q = resolve_retrieval_query("Can I travel while my I-485 is pending?", None)
        self.assertIn("advance parole", q.lower())
        self.assertIn("I-131", q)

    def test_f1_opt_ead_resolves_to_opt_query(self) -> None:
        q = resolve_retrieval_query("How do I get EAD as an F-1 student on OPT?", None)
        self.assertIn("post-completion OPT", q)
        self.assertIn("274a.12(c)(3)", q)

    def test_cpt_question_routes_to_cpt_query(self) -> None:
        q = resolve_retrieval_query("Can I do CPT while studying on F1?", None)
        self.assertIn("curricular practical training", q.lower())
        self.assertIn("214.2(f)(10)(i)", q)

    def test_stem_opt_resolves_to_opt_query(self) -> None:
        q = resolve_retrieval_query("How do I extend my STEM OPT work authorization?", None)
        self.assertIn("STEM OPT", q)

    def test_broad_ead_no_rewrite_without_category(self) -> None:
        q = resolve_retrieval_query("How do I apply for EAD?", None)
        self.assertEqual(q, "How do I apply for EAD?")

    # --- Naturalization requirements direct routing ---

    def test_naturalization_requirements_is_specific(self) -> None:
        self.assertTrue(is_specific_question("What are the requirements for naturalization?"))
        self.assertIsNone(detect_broad_topic("What are the requirements for naturalization?"))

    def test_naturalization_requirements_rewrites_to_rich_query(self) -> None:
        q = resolve_retrieval_query("What are the requirements for naturalization?", None)
        self.assertIn("N-400", q)
        self.assertIn("continuous residence", q)
        self.assertIn("physical presence", q)
        self.assertIn("good moral character", q)

    def test_naturalization_eligibility_phrasing_rewrites(self) -> None:
        q = resolve_retrieval_query("How do I qualify for naturalization?", None)
        self.assertIn("N-400", q)
        self.assertIn("continuous residence", q)

    def test_naturalization_requirements_does_not_trigger_clarification(self) -> None:
        self.assertIsNone(detect_broad_topic("What are the requirements for naturalization?"))
        self.assertIsNone(detect_broad_topic("Am I eligible for naturalization?"))

    # --- Criminal inadmissibility query rewriting ---

    def test_criminal_inadmissibility_rewrites_to_ina_212(self) -> None:
        q = resolve_retrieval_query("What is criminal inadmissibility?", None)
        self.assertIn("212(a)(2)", q)
        self.assertIn("moral turpitude", q.lower())

    def test_criminal_inadmissibility_rewrite_includes_usc_1182(self) -> None:
        q = resolve_retrieval_query("What is criminal inadmissibility?", None)
        self.assertIn("1182(a)(2)", q)

    def test_criminal_inadmissibility_rewrite_no_dui_term(self) -> None:
        # DUI was removed from the template to prevent the LLM grouping DUI
        # as automatically an aggravated felony.
        q = resolve_retrieval_query("What is criminal inadmissibility?", None)
        self.assertNotIn("DUI", q)

    def test_dui_affect_immigration_rewrites_to_criminal_inadmissibility(self) -> None:
        q = resolve_retrieval_query("Can a DUI affect immigration?", None)
        self.assertIn("212(a)(2)", q)
        self.assertIn("inadmissibility", q.lower())

    def test_criminal_conviction_green_card_rewrites(self) -> None:
        q = resolve_retrieval_query(
            "Can a criminal conviction affect my green card?", None
        )
        self.assertIn("212(a)(2)", q)

    def test_what_crimes_make_someone_inadmissible_rewrites(self) -> None:
        q = resolve_retrieval_query("What crimes can make someone inadmissible?", None)
        self.assertIn("212(a)(2)", q)
        self.assertIn("moral turpitude", q.lower())

    def test_cimt_rewrites_to_criminal_inadmissibility(self) -> None:
        q = resolve_retrieval_query("What is CIMT?", None)
        self.assertIn("moral turpitude", q.lower())
        self.assertIn("212(a)(2)", q)

    def test_criminal_record_affect_visa_rewrites(self) -> None:
        q = resolve_retrieval_query(
            "Can my criminal record affect my visa application?", None
        )
        self.assertIn("212(a)(2)", q)

    # --- Criminal deportability query rewriting ---

    def test_criminal_deportability_rewrites_to_ina_237(self) -> None:
        q = resolve_retrieval_query("What is criminal deportability?", None)
        self.assertIn("237(a)(2)", q)
        self.assertIn("deportability", q.lower())

    def test_criminal_deportability_rewrite_includes_usc_1227(self) -> None:
        q = resolve_retrieval_query("What is criminal deportability?", None)
        self.assertIn("1227(a)(2)", q)

    def test_criminal_deportability_rewrite_includes_domestic_violence(self) -> None:
        q = resolve_retrieval_query("What is criminal deportability?", None)
        self.assertIn("domestic violence", q.lower())

    def test_conviction_deportation_rewrites_to_ina_237(self) -> None:
        q = resolve_retrieval_query(
            "Can a conviction lead to deportation?", None
        )
        self.assertIn("237(a)(2)", q)

    def test_deportability_for_criminal_convictions_rewrites(self) -> None:
        q = resolve_retrieval_query(
            "What is deportability for criminal convictions?", None
        )
        self.assertIn("237(a)(2)", q)

    # --- Must NOT rewrite action-seeking or unrelated queries ---

    def test_dui_what_should_i_do_no_inadmissibility_rewrite(self) -> None:
        # Action-seeking form — resolve_retrieval_query sees raw message (classifier
        # short-circuits it first in ChatService); when called directly it must NOT
        # rewrite because it lacks the immigration-effect context words.
        q = resolve_retrieval_query("I had a DUI, what should I do?", None)
        self.assertEqual(q.strip(), "I had a DUI, what should I do?")

    def test_generic_criminal_question_no_rewrite(self) -> None:
        # No immigration context → returns raw message.
        q = resolve_retrieval_query("I was arrested last year.", None)
        self.assertEqual(q.strip(), "I was arrested last year.")


class ChatServiceCategoryHintTests(unittest.IsolatedAsyncioTestCase):
    async def test_selected_category_uses_focused_retrieval_query(self) -> None:
        captured: dict[str, str] = {}

        class _FakeRetrieval:
            async def retrieve_hybrid(self, query: str, top_k: int = 5):
                captured["query"] = query
                return [], ["test-dataset"], "test-dataset"

        class _FakeChat:
            async def generate_chat_response(self, **kwargs):
                return "Focused OPT answer with 8 CFR § 214.2."

        service = ChatService(retrieval_service=_FakeRetrieval(), chat_client=_FakeChat())
        response = await service.generate_chat_response(
            "How do I apply for EAD?",
            selected_category="f1_opt_stem_opt",
        )
        self.assertEqual(response.status, "ok")
        self.assertIn("STEM OPT", captured["query"])


class QueryRewritingH4OPTTests(unittest.TestCase):
    """Tests for H-4 process, H-4 EAD, and OPT query rewriting."""

    # --- H-4 process ---

    def test_what_is_h4_process_rewrites(self) -> None:
        q = resolve_retrieval_query("What is H-4 process?", None)
        self.assertNotEqual(q.strip(), "What is H-4 process?")

    def test_h4_process_rewrite_does_not_include_naturalization(self) -> None:
        q = resolve_retrieval_query("What is H-4 process?", None)
        self.assertNotIn("N-400", q)
        self.assertNotIn("naturalization", q.lower())

    def test_h4_process_rewrite_includes_dependent(self) -> None:
        q = resolve_retrieval_query("What is H-4 process?", None)
        self.assertIn("dependent", q.lower())

    def test_h4_process_rewrite_includes_cfr_214_2h(self) -> None:
        q = resolve_retrieval_query("What is H-4 process?", None)
        self.assertIn("214.2(h)", q)

    def test_how_does_h4_status_work_rewrites_to_h4_process(self) -> None:
        q = resolve_retrieval_query("How does H-4 status work?", None)
        self.assertIn("dependent", q.lower())
        self.assertNotIn("N-400", q)

    def test_h4_spouse_rewrites_to_h4_process(self) -> None:
        q = resolve_retrieval_query("What is H-4 spouse visa?", None)
        self.assertIn("dependent", q.lower())

    # --- H-4 EAD ---

    def test_h4_ead_rewrites(self) -> None:
        q = resolve_retrieval_query("How does H-4 EAD work?", None)
        self.assertNotEqual(q.strip(), "How does H-4 EAD work?")

    def test_h4_ead_rewrite_includes_h4_spouse(self) -> None:
        q = resolve_retrieval_query("How does H-4 EAD work?", None)
        self.assertIn("H-4 spouse", q)

    def test_h4_ead_rewrite_includes_i765(self) -> None:
        q = resolve_retrieval_query("How does H-4 EAD work?", None)
        self.assertIn("I-765", q)

    def test_h4_ead_rewrite_includes_274a_12_c26(self) -> None:
        q = resolve_retrieval_query("How does H-4 EAD work?", None)
        self.assertIn("274a.12(c)(26)", q)

    def test_h4_ead_rewrite_does_not_include_naturalization(self) -> None:
        q = resolve_retrieval_query("How does H-4 EAD work?", None)
        self.assertNotIn("N-400", q)
        self.assertNotIn("naturalization", q.lower())

    def test_h4_employment_authorization_rewrites_to_h4_ead(self) -> None:
        q = resolve_retrieval_query("Can I get employment authorization on H-4?", None)
        self.assertIn("274a.12(c)(26)", q)

    # --- OPT general ---

    def test_what_is_opt_rewrites(self) -> None:
        q = resolve_retrieval_query("What is OPT?", None)
        self.assertNotEqual(q.strip(), "What is OPT?")

    def test_opt_rewrite_includes_f1(self) -> None:
        q = resolve_retrieval_query("What is OPT?", None)
        self.assertIn("F-1", q)

    def test_opt_rewrite_includes_optional_practical_training(self) -> None:
        q = resolve_retrieval_query("What is OPT?", None)
        self.assertIn("optional practical training", q.lower())

    def test_opt_rewrite_includes_214_2f(self) -> None:
        q = resolve_retrieval_query("What is OPT?", None)
        self.assertIn("214.2(f)", q)

    def test_opt_rewrite_includes_274a_12_c3(self) -> None:
        q = resolve_retrieval_query("What is OPT?", None)
        self.assertIn("274a.12(c)(3)", q)

    def test_f1_opt_direct_rewrites_to_opt_general(self) -> None:
        q = resolve_retrieval_query("How does F-1 OPT work?", None)
        self.assertIn("214.2(f)", q)

    # --- Priority ordering: H-4 EAD before H-4 process ---

    def test_h4_ead_takes_priority_over_h4_process(self) -> None:
        # "H-4 EAD" should route to h4_ead (274a.12(c)(26)), not h4_process.
        q = resolve_retrieval_query("What is H-4 EAD?", None)
        self.assertIn("274a.12(c)(26)", q)
        self.assertNotIn("I-539", q)

    # --- OPT EAD still routes to f1_opt_stem_opt (existing behavior preserved) ---

    def test_f1_ead_routes_to_f1_opt_query(self) -> None:
        q = resolve_retrieval_query("How do I get EAD as an F-1 student on OPT?", None)
        self.assertIn("post-completion OPT", q)
        self.assertIn("274a.12(c)(3)", q)


class ChatServiceAutoRoutingTests(unittest.IsolatedAsyncioTestCase):
    """Auto-detected query rewrites fire even without an explicit selected_category."""

    async def _capture_query(self, message: str) -> str:
        """Run generate_chat_response and return the query passed to retrieve_hybrid."""
        captured: dict[str, str] = {}

        class _FakeRetrieval:
            async def retrieve_hybrid(self, query: str, top_k: int = 5):
                captured["query"] = query
                return [], ["test-dataset"], "test-dataset"

        class _FakeChat:
            async def generate_chat_response(self, **kwargs):
                raise AssertionError("LLM must not be called when retrieval returns empty")

        service = ChatService(retrieval_service=_FakeRetrieval(), chat_client=_FakeChat())
        await service.generate_chat_response(message, selected_category=None)
        return captured["query"]

    async def test_i485_travel_no_category_rewrites_to_advance_parole_query(self) -> None:
        """I-485 travel question without a category must reach retrieval with the advance
        parole rewritten query, not the raw user message."""
        q = await self._capture_query("Can I travel while my I-485 is pending?")
        self.assertIn("advance parole", q.lower())
        self.assertIn("I-131", q)

    async def test_i485_travel_alternate_phrasing_rewrites(self) -> None:
        q = await self._capture_query(
            "Can I travel abroad while my adjustment of status application is pending?"
        )
        self.assertIn("advance parole", q.lower())
        self.assertIn("I-131", q)

    async def test_asylum_ead_no_category_rewrites_to_asylum_pending_query(self) -> None:
        q = await self._capture_query(
            "How do I apply for an EAD as an asylum applicant?"
        )
        self.assertIn("208.7", q)
        self.assertIn("asylum", q.lower())

    async def test_stem_opt_no_category_rewrites(self) -> None:
        q = await self._capture_query(
            "How do I extend my STEM OPT work authorization?"
        )
        self.assertIn("STEM OPT", q)
        self.assertIn("214.2", q)

    async def test_naturalization_requirements_no_category_rewrites(self) -> None:
        q = await self._capture_query("What are the requirements for naturalization?")
        self.assertIn("N-400", q)
        self.assertIn("continuous residence", q)

    async def test_generic_ead_no_auto_rewrite(self) -> None:
        """A broad EAD question without category should NOT be rewritten
        (no auto-detection pattern matches it)."""
        q = await self._capture_query("How do I apply for EAD?")
        self.assertEqual(q.strip(), "How do I apply for EAD?")

    async def test_criminal_inadmissibility_rewrites_at_retrieval(self) -> None:
        q = await self._capture_query("What is criminal inadmissibility?")
        self.assertIn("212(a)(2)", q)
        self.assertIn("moral turpitude", q.lower())

    async def test_dui_affect_immigration_short_circuits_before_retrieval(self) -> None:
        """DUI info queries now return a prebuilt safe answer — retrieval is never called."""

        class _NoRetrieval:
            async def retrieve_hybrid(self, query: str, top_k: int = 5):
                raise AssertionError("Retrieval must not be called for DUI info questions")

        class _NoChat:
            async def generate_chat_response(self, **kwargs):
                raise AssertionError("LLM must not be called for DUI info questions")

        from app.services.chat_service import ChatService

        service = ChatService(retrieval_service=_NoRetrieval(), chat_client=_NoChat())
        response = await service.generate_chat_response(
            "Can a DUI affect immigration?", selected_category=None
        )
        self.assertEqual(response.status, "ok")
        self.assertIn("fact-specific", response.answer)

    async def test_criminal_deportability_rewrites_at_retrieval(self) -> None:
        q = await self._capture_query("What is criminal deportability?")
        self.assertIn("237(a)(2)", q)

    async def test_h4_process_faq_bypasses_retrieval_no_category(self) -> None:
        # "What is H-4 process?" now returns a prebuilt FAQ answer — retrieval is never
        # called. Verify the service returns ok without hitting retrieval.

        class _NoRetrieval:
            async def retrieve_hybrid(self, query: str, top_k: int = 5):
                raise AssertionError("Retrieval must not be called for H-4 process FAQ")

        class _NoChat:
            async def generate_chat_response(self, **kwargs):
                raise AssertionError("LLM must not be called for H-4 process FAQ")

        service = ChatService(retrieval_service=_NoRetrieval(), chat_client=_NoChat())
        response = await service.generate_chat_response("What is H-4 process?", selected_category=None)
        self.assertEqual(response.status, "ok")
        self.assertIn("H-1B", response.answer)

    async def test_h4_ead_faq_bypasses_retrieval_no_category(self) -> None:
        # "How does H-4 EAD work?" now returns a prebuilt FAQ answer — retrieval is never
        # called. Verify the service returns ok without hitting retrieval.

        class _NoRetrieval:
            async def retrieve_hybrid(self, query: str, top_k: int = 5):
                raise AssertionError("Retrieval must not be called for H-4 EAD FAQ")

        class _NoChat:
            async def generate_chat_response(self, **kwargs):
                raise AssertionError("LLM must not be called for H-4 EAD FAQ")

        service = ChatService(retrieval_service=_NoRetrieval(), chat_client=_NoChat())
        response = await service.generate_chat_response("How does H-4 EAD work?", selected_category=None)
        self.assertEqual(response.status, "ok")
        self.assertIn("274a.12(c)(26)", response.answer)

    async def test_opt_no_category_rewrites(self) -> None:
        q = await self._capture_query("What is OPT?")
        self.assertIn("214.2(f)", q)
        self.assertIn("274a.12(c)(3)", q)


class H4FAQDetectionTests(unittest.TestCase):
    """Unit tests for is_h4_process_faq_query and is_h4_ead_faq_query."""

    def setUp(self) -> None:
        from app.services.answer_formatting import is_h4_ead_faq_query, is_h4_process_faq_query
        self.h4_process = is_h4_process_faq_query
        self.h4_ead = is_h4_ead_faq_query

    # --- H-4 process positive matches ---

    def test_what_is_h4_process_matches_process_faq(self) -> None:
        self.assertTrue(self.h4_process("What is H-4 process?"))

    def test_what_is_h4_visa_matches_process_faq(self) -> None:
        self.assertTrue(self.h4_process("What is an H-4 visa?"))

    def test_how_does_h4_work_matches_process_faq(self) -> None:
        self.assertTrue(self.h4_process("How does H-4 work?"))

    def test_h4_visa_requirements_matches_process_faq(self) -> None:
        self.assertTrue(self.h4_process("H-4 visa requirements"))

    def test_h4_status_matches_process_faq(self) -> None:
        self.assertTrue(self.h4_process("What is H-4 status?"))

    # --- H-4 EAD positive matches ---

    def test_how_does_h4_ead_work_matches_ead_faq(self) -> None:
        self.assertTrue(self.h4_ead("How does H-4 EAD work?"))

    def test_what_is_h4_ead_matches_ead_faq(self) -> None:
        self.assertTrue(self.h4_ead("What is H-4 EAD?"))

    def test_h4_employment_authorization_matches_ead_faq(self) -> None:
        self.assertTrue(self.h4_ead("What is H-4 employment authorization?"))

    def test_can_h4_holders_work_matches_ead_faq(self) -> None:
        self.assertTrue(self.h4_ead("Can H-4 holders work?"))

    # --- EAD FAQ takes priority over process FAQ ---

    def test_h4_ead_query_does_not_match_process_faq(self) -> None:
        # "What is H-4 EAD?" has EAD context; it must be caught by EAD FAQ.
        # The process FAQ would also match "What is...H-4", so the service
        # must check EAD first. Verify EAD detection works.
        self.assertTrue(self.h4_ead("What is H-4 EAD?"))

    # --- Case-specific exclusions (must NOT match either FAQ) ---

    def test_my_h4_was_denied_not_process_faq(self) -> None:
        self.assertFalse(self.h4_process("My H-4 was denied, what should I do?"))

    def test_my_h4_was_denied_not_ead_faq(self) -> None:
        self.assertFalse(self.h4_ead("My H-4 was denied, what should I do?"))

    def test_my_h4_ead_application_pending_not_ead_faq(self) -> None:
        self.assertFalse(self.h4_ead("My H-4 EAD application is pending."))

    def test_what_should_i_do_excluded_from_process_faq(self) -> None:
        self.assertFalse(self.h4_process("H-4 visa process, what should I do?"))

    def test_h4_denied_excluded_from_process_faq(self) -> None:
        self.assertFalse(self.h4_process("H-4 visa was denied."))

    # --- OPT / other topics do not match H-4 FAQs ---

    def test_opt_question_does_not_match_h4_process_faq(self) -> None:
        self.assertFalse(self.h4_process("What is OPT?"))

    def test_opt_question_does_not_match_h4_ead_faq(self) -> None:
        self.assertFalse(self.h4_ead("What is OPT?"))


class ChatServiceH4FAQBypassTests(unittest.IsolatedAsyncioTestCase):
    """H-4 FAQ safe responses bypass retrieval and LLM for broad informational questions."""

    async def _run_faq_bypass(self, message: str):
        """Run generate_chat_response asserting retrieval and LLM are never called."""

        class _NoRetrieval:
            async def retrieve_hybrid(self, query: str, top_k: int = 5):
                raise AssertionError(
                    f"Retrieval must not be called for FAQ message: {message!r}"
                )

        class _NoChat:
            async def generate_chat_response(self, **kwargs):
                raise AssertionError(
                    f"LLM must not be called for FAQ message: {message!r}"
                )

        service = ChatService(retrieval_service=_NoRetrieval(), chat_client=_NoChat())
        return await service.generate_chat_response(message, selected_category=None)

    # --- H-4 process FAQ ---

    async def test_h4_process_faq_bypasses_retrieval_and_llm(self) -> None:
        response = await self._run_faq_bypass("What is H-4 process?")
        self.assertEqual(response.status, "ok")

    async def test_h4_process_faq_has_required_sections(self) -> None:
        response = await self._run_faq_bypass("What is H-4 process?")
        lower = response.answer.lower()
        for header in ("short answer:", "what this means:", "typical next steps:",
                       "official sources:", "important caution:"):
            self.assertIn(header, lower)

    async def test_h4_process_faq_does_not_mention_naturalization(self) -> None:
        response = await self._run_faq_bypass("What is H-4 process?")
        self.assertNotIn("N-400", response.answer)
        self.assertNotIn("naturalization", response.answer.lower())

    async def test_h4_process_faq_mentions_h1b_not_h3_only(self) -> None:
        response = await self._run_faq_bypass("What is H-4 process?")
        # Answer must describe H-1B as a common H principal.
        self.assertIn("H-1B", response.answer)

    async def test_h4_process_faq_next_steps_identify_inside_outside(self) -> None:
        response = await self._run_faq_bypass("What is H-4 process?")
        self.assertIn("inside or outside", response.answer.lower())

    async def test_h4_process_faq_mentions_i539_for_inside_us(self) -> None:
        response = await self._run_faq_bypass("What is H-4 process?")
        self.assertIn("I-539", response.answer)

    async def test_h4_process_faq_has_used_chunks_with_cfr_214_2h(self) -> None:
        response = await self._run_faq_bypass("What is H-4 process?")
        citations = [c.citation for c in response.used_chunks]
        self.assertTrue(any("214.2(h)" in c for c in citations))

    async def test_h4_process_faq_has_used_chunks(self) -> None:
        response = await self._run_faq_bypass("What is H-4 process?")
        self.assertGreater(len(response.used_chunks), 0)

    # --- H-4 EAD FAQ ---

    async def test_h4_ead_faq_bypasses_retrieval_and_llm(self) -> None:
        response = await self._run_faq_bypass("How does H-4 EAD work?")
        self.assertEqual(response.status, "ok")

    async def test_h4_ead_faq_has_required_sections(self) -> None:
        response = await self._run_faq_bypass("How does H-4 EAD work?")
        lower = response.answer.lower()
        for header in ("short answer:", "what this means:", "typical next steps:",
                       "official sources:", "important caution:"):
            self.assertIn(header, lower)

    async def test_h4_ead_faq_does_not_say_incident_to_status(self) -> None:
        response = await self._run_faq_bypass("How does H-4 EAD work?")
        self.assertNotIn("incident to status", response.answer.lower())

    async def test_h4_ead_faq_does_not_mention_e_l_spouse(self) -> None:
        response = await self._run_faq_bypass("How does H-4 EAD work?")
        lower = response.answer.lower()
        # Must not reference E or L spouse incident-to-status rules.
        self.assertNotIn("e-3 spouse", lower)
        self.assertNotIn("l-2 spouse", lower)
        self.assertNotIn("e spouse", lower)

    async def test_h4_ead_faq_says_certain_eligible_not_all(self) -> None:
        response = await self._run_faq_bypass("How does H-4 EAD work?")
        lower = response.answer.lower()
        self.assertTrue(
            "certain eligible" in lower or "eligible h-4 spouse" in lower
        )
        self.assertNotIn("all h-4 dependents", lower)

    async def test_h4_ead_faq_mentions_i765(self) -> None:
        response = await self._run_faq_bypass("How does H-4 EAD work?")
        self.assertIn("I-765", response.answer)

    async def test_h4_ead_faq_mentions_i140_or_ac21(self) -> None:
        response = await self._run_faq_bypass("How does H-4 EAD work?")
        self.assertIn("I-140", response.answer)
        self.assertIn("AC21", response.answer)

    async def test_h4_ead_faq_has_used_chunks_with_274a_12_c26(self) -> None:
        response = await self._run_faq_bypass("How does H-4 EAD work?")
        citations = [c.citation for c in response.used_chunks]
        self.assertTrue(any("274a.12(c)(26)" in c for c in citations))

    async def test_h4_ead_faq_has_used_chunks(self) -> None:
        response = await self._run_faq_bypass("How does H-4 EAD work?")
        self.assertGreater(len(response.used_chunks), 0)

    # --- Case-specific H-4 questions must NOT bypass FAQ ---

    async def test_h4_denial_does_not_bypass_faq(self) -> None:
        """'My H-4 was denied' must reach retrieval, not the FAQ bypass."""
        captured: dict[str, str] = {}

        class _FakeRetrieval:
            async def retrieve_hybrid(self, query: str, top_k: int = 5):
                captured["query"] = query
                return [], ["test-dataset"], "test-dataset"

        class _FakeChat:
            async def generate_chat_response(self, **kwargs):
                raise AssertionError("LLM must not be called when retrieval returns empty")

        service = ChatService(retrieval_service=_FakeRetrieval(), chat_client=_FakeChat())
        response = await service.generate_chat_response(
            "My H-4 was denied, what should I do?", selected_category=None
        )
        self.assertIn("query", captured, "Retrieval should have been called for case-specific question")

    async def test_h4_ead_denial_does_not_bypass_faq(self) -> None:
        """'My H-4 EAD application is pending' must reach retrieval."""
        captured: dict[str, str] = {}

        class _FakeRetrieval:
            async def retrieve_hybrid(self, query: str, top_k: int = 5):
                captured["query"] = query
                return [], ["test-dataset"], "test-dataset"

        class _FakeChat:
            async def generate_chat_response(self, **kwargs):
                raise AssertionError("LLM must not be called when retrieval returns empty")

        service = ChatService(retrieval_service=_FakeRetrieval(), chat_client=_FakeChat())
        await service.generate_chat_response(
            "My H-4 EAD application is pending. What are my next steps?",
            selected_category=None,
        )
        self.assertIn("query", captured, "Retrieval should have been called for case-specific question")


class L2WorkAuthRoutingTests(unittest.TestCase):
    """resolve_retrieval_query routes L-1/L-2 spouse work questions via understand_query."""

    def test_spouse_work_on_l1_resolves_to_l2_query(self) -> None:
        q = resolve_retrieval_query("Can my spouse work if I am on L1 visa?", None)
        self.assertIn("L-2", q)
        self.assertIn("L-2S", q)
        self.assertIn("I-94", q)
        self.assertIn("employment authorization", q.lower())
        self.assertIn("spouses of L-1 nonimmigrants", q)

    def test_l2_spouse_work_resolves_to_l2_query(self) -> None:
        q = resolve_retrieval_query("Can L2 spouse work?", None)
        self.assertIn("L-2", q)
        self.assertIn("spouses of L-1 nonimmigrants", q)

    def test_l2s_work_without_ead_resolves_to_l2_query(self) -> None:
        q = resolve_retrieval_query("Can L-2S work without EAD?", None)
        self.assertIn("L-2S", q)
        self.assertIn("incident to status", q.lower())

    def test_l2_query_excludes_naturalization(self) -> None:
        q = resolve_retrieval_query("Can my spouse work if I am on L1 visa?", None)
        self.assertNotIn("naturalization", q.lower())
        self.assertNotIn("I-751", q)
        self.assertNotIn("regularly stationed abroad", q.lower())

    def test_existing_selected_category_overrides_l2_routing(self) -> None:
        # selected_category that maps to a template must take priority over understand_query.
        q = resolve_retrieval_query("Can my spouse work if I am on L1 visa?", "h4_ead")
        self.assertIn("274a.12(c)(26)", q)
        self.assertNotIn("L-2S", q)

    def test_h4_ead_question_still_routes_via_existing_pattern(self) -> None:
        # H-4 EAD questions must still route through existing inline patterns,
        # not the understand_query layer (which returns general for H-4 EAD).
        q = resolve_retrieval_query("How does H-4 EAD work?", None)
        self.assertIn("274a.12(c)(26)", q)
        self.assertIn("I-765", q)

    def test_h4_process_question_still_routes_via_existing_pattern(self) -> None:
        q = resolve_retrieval_query("What is H-4 process?", None)
        self.assertIn("214.2(h)", q)
        self.assertIn("dependent", q.lower())

    def test_opt_question_still_routes_via_existing_pattern(self) -> None:
        q = resolve_retrieval_query("What is OPT?", None)
        self.assertIn("214.2(f)", q)
        self.assertIn("274a.12(c)(3)", q)


class HumanitarianQueryRewritingTests(unittest.TestCase):
    """resolve_retrieval_query routes high-risk/humanitarian queries via understand_query."""

    def test_asylum_ead_after_filing_resolves_to_208_7_query(self) -> None:
        q = resolve_retrieval_query("When can I apply for EAD after filing asylum?", None)
        self.assertIn("208.7", q)
        self.assertIn("274a.12(c)(8)", q)

    def test_i485_travel_with_advance_parole_resolves_to_ap_query(self) -> None:
        q = resolve_retrieval_query(
            "Can I travel while my I-485 is pending if I have advance parole?", None
        )
        self.assertIn("abandonment", q.lower())
        self.assertIn("245.2", q)

    def test_received_nta_removal_proceedings_resolves_to_nta_query(self) -> None:
        q = resolve_retrieval_query(
            "I received a Notice to Appear for removal proceedings. What should I do?", None
        )
        self.assertIn("239.1", q)
        self.assertIn("in absentia", q.lower())


if __name__ == "__main__":
    unittest.main()
