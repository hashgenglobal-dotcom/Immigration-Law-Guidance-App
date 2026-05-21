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
