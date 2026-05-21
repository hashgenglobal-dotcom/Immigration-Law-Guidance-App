"""Tests for structured chat answer formatting helpers."""

from __future__ import annotations

import unittest

from app.schemas.retrieval import RetrievalResult
from app.services.answer_formatting import (
    build_format_system_addon,
    ensure_structured_answer,
    has_required_sections,
    is_high_risk_topic,
    normalize_section_headers,
    retrieval_looks_weak,
)
from app.services.chat_service import ChatService


def _chunk(**kwargs) -> RetrievalResult:
    defaults = {
        "rank": 1,
        "chunk_id": 1,
        "citation": "8 CFR § 208.7",
        "official_url": None,
        "topic": "Asylum",
        "subtopic": None,
        "risk_level": "high",
        "hybrid_score": 0.02,
        "vector_rank": 1,
        "keyword_rank": None,
        "vector_distance": None,
        "keyword_score": None,
        "snippet": "Sample snippet about employment authorization.",
    }
    defaults.update(kwargs)
    return RetrievalResult(**defaults)


class AnswerFormattingTests(unittest.TestCase):
    def test_nta_is_high_risk(self) -> None:
        self.assertTrue(is_high_risk_topic("What is a Notice to Appear?"))

    def test_ead_apply_not_high_risk_by_default(self) -> None:
        self.assertFalse(is_high_risk_topic("How do I apply for EAD?"))

    def test_format_addon_includes_sections(self) -> None:
        addon = build_format_system_addon(high_risk=False, weak_sources=False, selected_category=None)
        self.assertIn("Short answer:", addon)
        self.assertIn("Important caution:", addon)
        self.assertIn("you may be eligible depending", addon)

    def test_high_risk_addon_mentions_attorney(self) -> None:
        addon = build_format_system_addon(high_risk=True, weak_sources=False, selected_category=None)
        self.assertIn("HIGH-RISK", addon)
        self.assertIn("immigration attorney", addon)

    def test_normalize_headers(self) -> None:
        raw = "short answer\nLine one\n\nwhat this means\nLine two"
        out = normalize_section_headers("Short answer:\nLine one\n\nWhat this means:\nLine two")
        self.assertIn("Short answer:", out)

    def test_ensure_structure_wraps_unstructured(self) -> None:
        out = ensure_structured_answer("Plain paragraph without headers.", high_risk=True)
        self.assertTrue(has_required_sections(out))
        self.assertIn("immigration attorney", out)

    def test_weak_retrieval_heuristic(self) -> None:
        weak = [_chunk(hybrid_score=0.01, snippet="short")]
        self.assertTrue(retrieval_looks_weak(weak))


class ChatServiceFormattingTests(unittest.IsolatedAsyncioTestCase):
    async def test_direct_answer_is_structured(self) -> None:
        class _FakeRetrieval:
            async def retrieve_hybrid(self, query: str, top_k: int = 5):
                return [
                    _chunk(citation="8 CFR § 274a.12", snippet="Employment authorization categories."),
                ], "test-dataset"

        class _FakeChat:
            async def generate_chat_response(self, **kwargs):
                return (
                    "Short answer:\nYou may request employment authorization depending on your category.\n\n"
                    "What this means:\nThis refers to permission to work in the U.S.\n\n"
                    "Typical next steps:\n1. Identify your category.\n2. File Form I-765 if required.\n\n"
                    "Official sources:\n8 CFR § 274a.12\n\n"
                    "Important caution:\nThis is general information only, not legal advice."
                )

        service = ChatService(retrieval_service=_FakeRetrieval(), chat_client=_FakeChat())
        response = await service.generate_chat_response(
            "Can asylum applicants get work authorization?",
            selected_category="asylum_pending",
        )
        self.assertEqual(response.status, "ok")
        self.assertIn("Short answer:", response.answer)
        self.assertIn("Important caution:", response.answer)


if __name__ == "__main__":
    unittest.main()
