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

    def test_duplicate_headers_collapsed_to_one(self) -> None:
        duped = (
            "Short answer:\n"
            "Short answer:\n"
            "F-1 students may work.\n\n"
            "What this means:\n"
            "What this means:\n"
            "Practical training.\n\n"
            "Typical next steps:\n"
            "Typical next steps:\n"
            "1. File I-765.\n\n"
            "Official sources:\n"
            "Official sources:\n"
            "8 CFR § 214.2\n\n"
            "Important caution:\n"
            "Important caution:\n"
            "Not legal advice."
        )
        out = ensure_structured_answer(duped, high_risk=False)
        for header in (
            "short answer:",
            "what this means:",
            "typical next steps:",
            "official sources:",
            "important caution:",
        ):
            self.assertEqual(out.lower().count(header), 1, f"Expected exactly one '{header}'")
        self.assertIn("F-1 students may work.", out)

    def test_structured_missing_caution_appends_not_wraps(self) -> None:
        no_caution = (
            "Short answer:\n"
            "You may request EAD.\n\n"
            "What this means:\n"
            "This is work authorization.\n\n"
            "Typical next steps:\n"
            "1. File I-765.\n\n"
            "Official sources:\n"
            "8 CFR § 274a.12"
        )
        out = ensure_structured_answer(no_caution, high_risk=False)
        self.assertIn("Important caution:", out)
        self.assertEqual(out.lower().count("important caution:"), 1)
        self.assertEqual(out.lower().count("short answer:"), 1)
        self.assertIn("You may request EAD.", out)
        self.assertNotIn("See the short answer above.", out)

    def test_each_header_at_most_once(self) -> None:
        mixed_dups = (
            "Short answer:\n"
            "Short answer:\n"
            "Content.\n\n"
            "What this means:\n"
            "Something.\n\n"
            "Typical next steps:\n"
            "1. Step.\n\n"
            "Official sources:\n"
            "Citation.\n\n"
            "Important caution:\n"
            "Important caution:\n"
            "Not legal advice."
        )
        out = ensure_structured_answer(mixed_dups, high_risk=False)
        for header in (
            "short answer:",
            "what this means:",
            "typical next steps:",
            "official sources:",
            "important caution:",
        ):
            self.assertLessEqual(out.lower().count(header), 1, f"Duplicate header: {header}")


class ChatServiceFormattingTests(unittest.IsolatedAsyncioTestCase):
    async def test_direct_answer_is_structured(self) -> None:
        class _FakeRetrieval:
            async def retrieve_hybrid(self, query: str, top_k: int = 5):
                return [
                    _chunk(citation="8 CFR § 274a.12", snippet="Employment authorization categories."),
                ], ["test-dataset"], "test-dataset"

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
