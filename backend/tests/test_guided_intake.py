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
        self.assertIn("STEM OPT", q)
        self.assertIn("214.2", q)

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


if __name__ == "__main__":
    unittest.main()
