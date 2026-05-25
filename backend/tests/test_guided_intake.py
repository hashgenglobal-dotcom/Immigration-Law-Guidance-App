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


class ChatServiceClarificationTests(unittest.IsolatedAsyncioTestCase):
    async def test_broad_ead_returns_needs_clarification(self) -> None:
        class _FakeRetrieval:
            async def retrieve_hybrid(self, query: str, top_k: int = 5):
                raise AssertionError("retrieval should not run for clarification")

        service = ChatService(retrieval_service=_FakeRetrieval())
        response = await service.generate_chat_response("How do I apply for EAD?")
        self.assertEqual(response.status, "needs_clarification")
        self.assertTrue(response.options)
        values = {o.value for o in response.options or []}
        self.assertIn("f1_opt_stem_opt", values)
        self.assertIn("asylum_pending", values)

    async def test_selected_category_skips_clarification(self) -> None:
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


if __name__ == "__main__":
    unittest.main()
