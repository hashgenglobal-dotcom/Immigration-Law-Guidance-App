"""Tests for in-session conversation context (Phase 1)."""

from __future__ import annotations

import unittest

from app.services.chat_service import ChatService
from app.services.conversation_context import (
    build_retrieval_query,
    extract_short_answer_section,
    format_conversation_block,
    sanitize_conversation,
)
from app.services.guided_intake import (
    effective_category,
    resolve_category_from_message,
    resolve_retrieval_query,
)


class ConversationContextTests(unittest.TestCase):
    def test_sanitize_caps_turns_and_roles(self) -> None:
        raw = [{"role": "user", "content": "Hello"}] * 10
        out = sanitize_conversation(raw)
        self.assertEqual(len(out), 6)
        self.assertEqual(out[0].role, "user")

    def test_build_retrieval_query_merges_thread(self) -> None:
        thread = sanitize_conversation(
            [
                {"role": "user", "content": "I am on F-1 OPT"},
                {"role": "assistant", "content": "OPT allows limited work authorization."},
            ]
        )
        q = build_retrieval_query(
            "Can I travel?",
            thread,
            selected_category=None,
            category_resolver=resolve_retrieval_query,
        )
        self.assertIn("travel", q.lower())
        self.assertIn("OPT", q)

    def test_build_retrieval_query_category_template_wins(self) -> None:
        thread = sanitize_conversation([{"role": "user", "content": "EAD question"}])
        q = build_retrieval_query(
            "How do I apply for EAD?",
            thread,
            selected_category="f1_opt_stem_opt",
            category_resolver=resolve_retrieval_query,
        )
        self.assertIn("STEM OPT", q)

    def test_extract_short_answer_section(self) -> None:
        text = (
            "Short answer:\nYou may apply for OPT.\n\n"
            "What this means:\nMore detail here."
        )
        self.assertIn("OPT", extract_short_answer_section(text))

    def test_format_conversation_block(self) -> None:
        thread = sanitize_conversation(
            [{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello"}]
        )
        block = format_conversation_block(thread)
        self.assertIn("User: Hi", block)
        self.assertIn("Assistant: Hello", block)


class TypedClarificationTests(unittest.TestCase):
    def test_resolve_f1_opt_category(self) -> None:
        self.assertEqual(
            resolve_category_from_message("I'm on F-1 OPT"),
            "f1_opt_stem_opt",
        )

    def test_effective_category_prefers_explicit(self) -> None:
        self.assertEqual(
            effective_category("anything", "asylum_pending"),
            "asylum_pending",
        )


class ChatServiceConversationTests(unittest.IsolatedAsyncioTestCase):
    async def test_typed_category_skips_clarification(self) -> None:
        captured: dict[str, str] = {}

        class _FakeRetrieval:
            async def retrieve_hybrid(self, query: str, top_k: int = 5):
                captured["query"] = query
                return [], ["test-dataset"], "test-dataset"

        class _FakeChat:
            async def generate_chat_response(self, **kwargs):
                return "Short answer:\nOPT rules apply.\n\nWhat this means:\nDetail.\n\nTypical next steps:\n1. Step\n\nOfficial sources:\n8 CFR § 214.2\n\nImportant caution:\nCaution."

        service = ChatService(retrieval_service=_FakeRetrieval(), chat_client=_FakeChat())
        response = await service.generate_chat_response(
            "I'm on F-1 OPT",
            conversation=[
                {"role": "user", "content": "How do I apply for EAD?"},
            ],
        )
        self.assertEqual(response.status, "ok")
        self.assertIn("STEM OPT", captured["query"])


if __name__ == "__main__":
    unittest.main()
