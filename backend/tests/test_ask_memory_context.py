"""Tests for simple Ask in-session memory (no mandatory intake, no persistence)."""

from __future__ import annotations

import unittest

from app.services.ask_memory_context import (
    build_retrieval_query,
    is_likely_follow_up,
    is_new_topic_shift,
    sanitize_conversation,
    should_use_conversation_context,
)
from app.services.chat_service import ChatService
from app.services.guided_intake import is_specific_question


class AskMemoryContextTests(unittest.TestCase):
    def test_sanitize_caps_turns(self) -> None:
        raw = [{"role": "user", "content": "Hello"}] * 10
        out = sanitize_conversation(raw)
        self.assertEqual(len(out), 4)

    def test_normal_question_no_context(self) -> None:
        turns = sanitize_conversation(
            [
                {"role": "user", "content": "How do I apply for EAD?"},
                {"role": "assistant", "content": "EAD requires Form I-765."},
            ]
        )
        self.assertFalse(should_use_conversation_context("How do I apply for EAD?", turns))
        query = build_retrieval_query("How do I apply for EAD?", turns)
        self.assertEqual(query, "How do I apply for EAD?")

    def test_follow_up_uses_context(self) -> None:
        turns = sanitize_conversation(
            [
                {"role": "user", "content": "Can asylum applicants get work authorization?"},
                {"role": "assistant", "content": "They may apply for EAD."},
            ]
        )
        msg = "What about documents?"
        self.assertTrue(is_likely_follow_up(msg))
        self.assertTrue(should_use_conversation_context(msg, turns))
        query = build_retrieval_query(msg, turns)
        self.assertTrue(query.startswith("What about documents?"))
        self.assertIn("prior question", query.lower())

    def test_new_topic_does_not_use_prior_context(self) -> None:
        turns = sanitize_conversation(
            [
                {"role": "user", "content": "Can I get OPT on F-1?"},
                {"role": "assistant", "content": "OPT rules apply."},
            ]
        )
        msg = "How do I become a U.S. citizen through naturalization?"
        self.assertTrue(is_new_topic_shift(msg, "Can I get OPT on F-1?"))
        self.assertFalse(should_use_conversation_context(msg, turns))
        self.assertEqual(build_retrieval_query(msg, turns), msg)

    def test_specific_question_stays_specific(self) -> None:
        self.assertTrue(
            is_specific_question("Can asylum applicants get work authorization?")
        )


class ChatServiceSimpleAskTests(unittest.IsolatedAsyncioTestCase):
    async def test_broad_ead_answers_directly_no_clarification(self) -> None:
        captured: dict[str, str] = {}

        class _FakeRetrieval:
            async def retrieve_hybrid(self, query: str, top_k: int = 5):
                captured["query"] = query
                return [], ["test-dataset"], "test-dataset"

        class _FakeChat:
            async def generate_chat_response(self, **kwargs):
                return "Short answer:\nGeneral EAD information.\n\nWhat this means:\nDetail."

        service = ChatService(retrieval_service=_FakeRetrieval(), chat_client=_FakeChat())
        response = await service.generate_chat_response("How do I apply for EAD?")
        self.assertEqual(response.status, "ok")
        self.assertEqual(captured["query"], "How do I apply for EAD?")


if __name__ == "__main__":
    unittest.main()
