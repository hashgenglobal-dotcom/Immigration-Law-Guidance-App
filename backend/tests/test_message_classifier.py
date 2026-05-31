"""Tests for message_classifier: greeting detection, criminal warning, and refusal."""

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


class CriminalWarningDetectionTests(unittest.TestCase):
    """classify_message returns 'criminal_warning' for personal criminal matter + action-seeking."""

    # --- Should trigger criminal_warning ---

    def test_dui_what_should_i_do(self) -> None:
        self.assertEqual(
            classify_message("I got a DUI, what should I do for immigration?"),
            "criminal_warning",
        )

    def test_hit_and_run_what_should_i_do(self) -> None:
        self.assertEqual(
            classify_message("I had a hit and run case, what should I do?"),
            "criminal_warning",
        )

    def test_arrested_what_should_i_do(self) -> None:
        self.assertEqual(
            classify_message("I was arrested, what should I do?"),
            "criminal_warning",
        )

    def test_theft_charge_what_should_i_do(self) -> None:
        self.assertEqual(
            classify_message("I have a theft charge, what should I do?"),
            "criminal_warning",
        )

    def test_felony_what_are_my_options(self) -> None:
        self.assertEqual(
            classify_message("I was convicted of a felony, what are my options?"),
            "criminal_warning",
        )

    def test_misdemeanor_how_do_i_handle(self) -> None:
        self.assertEqual(
            classify_message("I have a misdemeanor on my record, how do I handle this?"),
            "criminal_warning",
        )

    def test_criminal_case_next_steps(self) -> None:
        self.assertEqual(
            classify_message("I have a criminal case pending, what are my next steps?"),
            "criminal_warning",
        )

    def test_assault_charge_what_can_i_do(self) -> None:
        self.assertEqual(
            classify_message("I was charged with assault last year, what can I do?"),
            "criminal_warning",
        )

    def test_drug_charge_what_should_i_do(self) -> None:
        self.assertEqual(
            classify_message("I have a drug charge from 2022, what should I do?"),
            "criminal_warning",
        )

    def test_domestic_violence_how_should_i_proceed(self) -> None:
        self.assertEqual(
            classify_message(
                "I was arrested for domestic violence. How should I proceed with my green card?"
            ),
            "criminal_warning",
        )

    # --- Must NOT trigger criminal_warning (informational/general questions) ---

    def test_can_dui_affect_immigration_is_pass(self) -> None:
        self.assertEqual(
            classify_message("Can a DUI affect immigration?"), "pass"
        )

    def test_criminal_inadmissibility_info_is_pass(self) -> None:
        self.assertEqual(
            classify_message("What is criminal inadmissibility?"), "pass"
        )

    def test_conviction_consequences_is_pass(self) -> None:
        # Starts with "What happens" → caught by consequence_question_re first.
        self.assertEqual(
            classify_message("What happens if someone has a conviction?"), "pass"
        )

    def test_dui_general_effect_is_pass(self) -> None:
        # Criminal matter (DUI) but no action-seeking phrase.
        self.assertEqual(
            classify_message("Can a DUI conviction make someone inadmissible?"), "pass"
        )

    def test_what_are_criminal_grounds_is_pass(self) -> None:
        self.assertEqual(
            classify_message("What are criminal grounds of inadmissibility?"), "pass"
        )

    def test_felony_consequences_question_is_pass(self) -> None:
        self.assertEqual(
            classify_message("What are the consequences of a felony conviction for a green card?"),
            "pass",
        )


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

    async def test_criminal_warning_skips_retrieval(self) -> None:
        retrieval_called: dict[str, int] = {"count": 0}
        service = await self._make_service(retrieval_called)
        response = await service.generate_chat_response(
            "I got a DUI, what should I do for immigration?"
        )
        self.assertEqual(retrieval_called["count"], 0)
        self.assertIn("attorney", response.answer.lower())

    async def test_criminal_warning_response_has_status_ok(self) -> None:
        retrieval_called: dict[str, int] = {"count": 0}
        service = await self._make_service(retrieval_called)
        response = await service.generate_chat_response(
            "I was arrested, what should I do?"
        )
        self.assertEqual(response.status, "ok")
        self.assertIn("criminal defense attorney", response.answer.lower())

    async def test_criminal_warning_mentions_immigration_attorney(self) -> None:
        retrieval_called: dict[str, int] = {"count": 0}
        service = await self._make_service(retrieval_called)
        response = await service.generate_chat_response(
            "I have a theft charge, what should I do?"
        )
        self.assertIn("immigration attorney", response.answer.lower())

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


class NtaCourtAvoidanceRefusalTests(unittest.TestCase):
    """classify_message returns 'refusal' for court-avoidance strategy, not for lawful questions."""

    # --- Positive (refusal) ---

    def test_avoid_immigration_court_after_nta_is_refusal(self) -> None:
        self.assertEqual(
            classify_message(
                "How can I avoid going to immigration court after getting an NTA?"
            ),
            "refusal",
        )

    def test_skip_immigration_court_hearing_is_refusal(self) -> None:
        self.assertEqual(
            classify_message("How do I skip my immigration court hearing?"),
            "refusal",
        )

    def test_avoid_court_date_after_nta_is_refusal(self) -> None:
        self.assertEqual(
            classify_message("How can I avoid my court date after receiving an NTA?"),
            "refusal",
        )

    # --- False positives (must remain pass) ---

    def test_postpone_court_date_is_pass(self) -> None:
        # "postponed" is rescheduling, not avoidance — no avoid/skip/miss signal.
        self.assertEqual(classify_message("Can I get my court date postponed?"), "pass")

    def test_miss_court_date_consequence_is_pass(self) -> None:
        # "What happens" → consequence_question_re fires first → pass.
        self.assertEqual(classify_message("What happens if I miss my court date?"), "pass")

    def test_defenses_against_removal_is_pass(self) -> None:
        self.assertEqual(classify_message("What are defenses against removal?"), "pass")

    def test_received_nta_what_should_i_do_is_pass(self) -> None:
        self.assertEqual(classify_message("I received an NTA, what should I do?"), "pass")


if __name__ == "__main__":
    unittest.main()
