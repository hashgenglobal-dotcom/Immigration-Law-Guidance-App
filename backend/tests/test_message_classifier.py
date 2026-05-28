"""Tests for message_classifier: greeting detection and criminal/fraud refusal."""

from __future__ import annotations

import unittest

from app.services.message_classifier import classify_message
from app.services.chat_service import ChatService


# ---------------------------------------------------------------------------
# Pure classifier unit tests
# ---------------------------------------------------------------------------


class GreetingDetectionTests(unittest.TestCase):
    """classify_message returns 'greeting' for casual messages."""

    def test_hi_lowercase(self) -> None:
        self.assertEqual(classify_message("hi"), "greeting")

    def test_hi_uppercase(self) -> None:
        self.assertEqual(classify_message("Hi"), "greeting")

    def test_hello_with_exclamation(self) -> None:
        self.assertEqual(classify_message("Hello!"), "greeting")

    def test_hey(self) -> None:
        self.assertEqual(classify_message("hey"), "greeting")

    def test_thanks(self) -> None:
        self.assertEqual(classify_message("thanks"), "greeting")

    def test_thank_you(self) -> None:
        self.assertEqual(classify_message("thank you"), "greeting")

    def test_how_are_you(self) -> None:
        self.assertEqual(classify_message("how are you?"), "greeting")

    def test_how_are_you_doing(self) -> None:
        self.assertEqual(classify_message("how are you doing"), "greeting")

    def test_good_morning(self) -> None:
        self.assertEqual(classify_message("good morning"), "greeting")

    def test_good_afternoon(self) -> None:
        self.assertEqual(classify_message("good afternoon!"), "greeting")

    # --- Non-greeting messages must not match ---

    def test_hi_with_question_is_pass(self) -> None:
        # Greeting word present but message contains a substantive question.
        self.assertEqual(classify_message("hi, can I get work authorization?"), "pass")

    def test_immigration_question_is_pass(self) -> None:
        self.assertEqual(
            classify_message("Can I travel while my I-485 is pending?"), "pass"
        )

    def test_ead_question_is_pass(self) -> None:
        self.assertEqual(classify_message("How do I apply for an EAD?"), "pass")

    def test_empty_string_is_pass(self) -> None:
        self.assertEqual(classify_message(""), "pass")


class RefusalDetectionTests(unittest.TestCase):
    """classify_message returns 'refusal' for criminal/fraud/evasion strategy."""

    def test_hide_arrest_from_uscis(self) -> None:
        self.assertEqual(
            classify_message("How do I hide my arrest from USCIS?"), "refusal"
        )

    def test_lie_about_deportation_on_application(self) -> None:
        self.assertEqual(
            classify_message(
                "Can I lie about my deportation on the visa application?"
            ),
            "refusal",
        )

    def test_can_i_lie_about_criminal_record(self) -> None:
        self.assertEqual(
            classify_message(
                "Can I lie about my criminal record on my green card application?"
            ),
            "refusal",
        )

    def test_avoid_ice(self) -> None:
        self.assertEqual(
            classify_message("How can I avoid ICE?"), "refusal"
        )

    def test_evade_deportation(self) -> None:
        self.assertEqual(
            classify_message("How do I evade deportation?"), "refusal"
        )

    def test_fake_documents(self) -> None:
        self.assertEqual(
            classify_message("How do I fake documents for my immigration case?"), "refusal"
        )

    def test_forge_passport(self) -> None:
        self.assertEqual(
            classify_message("Can I forge my passport for the visa interview?"), "refusal"
        )

    def test_hide_criminal_record_on_green_card(self) -> None:
        self.assertEqual(
            classify_message(
                "Can I hide my criminal record on my green card application?"
            ),
            "refusal",
        )

    def test_escape_ice_detention(self) -> None:
        self.assertEqual(
            classify_message("How can I escape ICE detention?"), "refusal"
        )

    def test_conceal_conviction_from_immigration(self) -> None:
        self.assertEqual(
            classify_message(
                "How do I conceal my conviction from immigration officers?"
            ),
            "refusal",
        )

    # --- Legitimate questions must NOT be refused ---

    def test_what_is_unlawful_presence_is_pass(self) -> None:
        self.assertEqual(classify_message("What is unlawful presence?"), "pass")

    def test_what_happens_overstay_is_pass(self) -> None:
        self.assertEqual(
            classify_message("What happens if I overstay my visa?"), "pass"
        )

    def test_criminal_inadmissibility_info_is_pass(self) -> None:
        self.assertEqual(
            classify_message("What are criminal grounds of inadmissibility?"), "pass"
        )

    def test_can_ice_detain_at_airport_is_pass(self) -> None:
        self.assertEqual(
            classify_message("Can ICE detain me at the airport?"), "pass"
        )

    def test_removal_consequences_is_pass(self) -> None:
        self.assertEqual(
            classify_message("What are the consequences of removal?"), "pass"
        )

    def test_naturalization_question_is_pass(self) -> None:
        self.assertEqual(
            classify_message("What are the requirements for naturalization?"), "pass"
        )

    def test_ead_application_is_pass(self) -> None:
        self.assertEqual(
            classify_message("How do I apply for an EAD as an asylum applicant?"), "pass"
        )

    def test_i485_travel_question_is_pass(self) -> None:
        self.assertEqual(
            classify_message("Can I travel while my I-485 is pending?"), "pass"
        )


# ---------------------------------------------------------------------------
# ChatService integration: classifier short-circuits retrieval
# ---------------------------------------------------------------------------


class ChatServiceClassifierTests(unittest.IsolatedAsyncioTestCase):
    """Greeting and refusal messages skip retrieval and LLM entirely."""

    async def _make_service(self, retrieval_called: dict) -> ChatService:
        class _FakeRetrieval:
            async def retrieve_hybrid(self, query: str, top_k: int = 5):
                retrieval_called["count"] += 1
                return [], [], None

        class _NoopChat:
            async def generate_chat_response(self, **kwargs):
                raise AssertionError("LLM should not be called for greeting/refusal")

        return ChatService(
            retrieval_service=_FakeRetrieval(), chat_client=_NoopChat()
        )

    async def test_greeting_skips_retrieval(self) -> None:
        retrieval_called: dict[str, int] = {"count": 0}
        service = await self._make_service(retrieval_called)
        response = await service.generate_chat_response("hi")
        self.assertEqual(retrieval_called["count"], 0)
        self.assertIn("Hello", response.answer)

    async def test_thanks_skips_retrieval(self) -> None:
        retrieval_called: dict[str, int] = {"count": 0}
        service = await self._make_service(retrieval_called)
        response = await service.generate_chat_response("thanks")
        self.assertEqual(retrieval_called["count"], 0)
        self.assertIn("Hello", response.answer)

    async def test_refusal_skips_retrieval(self) -> None:
        retrieval_called: dict[str, int] = {"count": 0}
        service = await self._make_service(retrieval_called)
        response = await service.generate_chat_response(
            "How do I hide my arrest from USCIS?"
        )
        self.assertEqual(retrieval_called["count"], 0)
        self.assertIn("attorney", response.answer.lower())

    async def test_greeting_response_has_status_ok(self) -> None:
        retrieval_called: dict[str, int] = {"count": 0}
        service = await self._make_service(retrieval_called)
        response = await service.generate_chat_response("Hello!")
        self.assertEqual(response.status, "ok")

    async def test_refusal_response_has_status_ok(self) -> None:
        retrieval_called: dict[str, int] = {"count": 0}
        service = await self._make_service(retrieval_called)
        response = await service.generate_chat_response(
            "How can I avoid ICE?"
        )
        self.assertEqual(response.status, "ok")
        self.assertIn("attorney", response.answer.lower())

    async def test_immigration_question_does_reach_retrieval(self) -> None:
        """Normal immigration questions still go through retrieval."""
        retrieval_called: dict[str, int] = {"count": 0}

        class _FakeRetrieval:
            async def retrieve_hybrid(self, query: str, top_k: int = 5):
                retrieval_called["count"] += 1
                return [], ["test-dataset"], "test-dataset"

        class _NoopChat:
            async def generate_chat_response(self, **kwargs):
                raise AssertionError("Should not be called when retrieval returns empty")

        service = ChatService(
            retrieval_service=_FakeRetrieval(), chat_client=_NoopChat()
        )
        await service.generate_chat_response("How do I apply for an EAD?")
        self.assertEqual(retrieval_called["count"], 1)


if __name__ == "__main__":
    unittest.main()
