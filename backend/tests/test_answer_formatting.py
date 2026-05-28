"""Tests for structured chat answer formatting helpers."""

from __future__ import annotations

import unittest

from app.schemas.retrieval import RetrievalResult
from app.services.answer_formatting import (
    build_format_system_addon,
    classify_answer_intent,
    ensure_structured_answer,
    has_required_sections,
    is_criminal_info_query,
    is_dui_info_query,
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

    def test_format_addon_has_safe_next_steps_guidance(self) -> None:
        """For case_specific_or_risk intent, format addon must instruct hedged next-steps language."""
        addon = build_format_system_addon(
            high_risk=False, weak_sources=False, selected_category=None,
            answer_intent="case_specific_or_risk",
        )
        # Safe phrasing example must be present
        self.assertIn("You may need to", addon)
        # Explicitly avoided command forms must be named
        self.assertIn("File Form", addon)

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


class CriminalInfoQueryDetectionTests(unittest.TestCase):
    """is_criminal_info_query correctly identifies criminal immigration info questions."""

    def test_dui_affect_immigration_is_criminal_info(self) -> None:
        self.assertTrue(is_criminal_info_query("Can a DUI affect immigration?"))

    def test_criminal_inadmissibility_is_criminal_info(self) -> None:
        self.assertTrue(is_criminal_info_query("What is criminal inadmissibility?"))

    def test_criminal_deportability_is_criminal_info(self) -> None:
        self.assertTrue(is_criminal_info_query("What is criminal deportability?"))

    def test_conviction_affect_green_card_is_criminal_info(self) -> None:
        self.assertTrue(is_criminal_info_query("Can a criminal conviction affect my green card?"))

    def test_what_crimes_make_inadmissible_is_criminal_info(self) -> None:
        self.assertTrue(is_criminal_info_query("What crimes can make someone inadmissible?"))

    def test_moral_turpitude_is_criminal_info(self) -> None:
        self.assertTrue(is_criminal_info_query("What is a crime involving moral turpitude?"))

    def test_dui_make_inadmissible_is_criminal_info(self) -> None:
        self.assertTrue(is_criminal_info_query("Can a DUI conviction make someone inadmissible?"))

    def test_ead_question_is_not_criminal_info(self) -> None:
        self.assertFalse(is_criminal_info_query("How do I apply for an EAD?"))

    def test_naturalization_requirements_is_not_criminal_info(self) -> None:
        self.assertFalse(is_criminal_info_query("What are the requirements for naturalization?"))

    def test_i485_travel_is_not_criminal_info(self) -> None:
        self.assertFalse(is_criminal_info_query("Can I travel while my I-485 is pending?"))


class CriminalInfoAddonTests(unittest.TestCase):
    """build_format_system_addon with criminal_info=True includes DUI/offense-specific caution."""

    def test_criminal_info_addon_warns_against_dui_as_aggravated_felony(self) -> None:
        addon = build_format_system_addon(
            high_risk=False, weak_sources=False, selected_category=None, criminal_info=True
        )
        self.assertIn("CRIMINAL IMMIGRATION GROUNDS", addon)
        self.assertIn("DUI", addon)
        self.assertIn("aggravated felony", addon.lower())

    def test_criminal_info_addon_requires_hedged_language(self) -> None:
        addon = build_format_system_addon(
            high_risk=False, weak_sources=False, selected_category=None, criminal_info=True
        )
        self.assertIn("may constitute", addon)

    def test_criminal_info_addon_recommends_attorney(self) -> None:
        addon = build_format_system_addon(
            high_risk=False, weak_sources=False, selected_category=None, criminal_info=True
        )
        self.assertIn("immigration attorney", addon.lower())

    def test_no_criminal_info_flag_omits_caution(self) -> None:
        addon = build_format_system_addon(
            high_risk=False, weak_sources=False, selected_category=None, criminal_info=False
        )
        self.assertNotIn("CRIMINAL IMMIGRATION GROUNDS", addon)


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


class DUIInfoQueryDetectionTests(unittest.TestCase):
    """is_dui_info_query identifies informational DUI/immigration questions."""

    def test_can_dui_affect_immigration_matches(self) -> None:
        self.assertTrue(is_dui_info_query("Can a DUI affect immigration?"))

    def test_dui_affect_visa_matches(self) -> None:
        self.assertTrue(is_dui_info_query("Can a DUI affect my visa?"))

    def test_dui_make_inadmissible_matches(self) -> None:
        self.assertTrue(is_dui_info_query("Can a DUI conviction make someone inadmissible?"))

    def test_dui_green_card_matches(self) -> None:
        self.assertTrue(is_dui_info_query("Can a DUI affect my green card application?"))

    def test_dwi_affect_immigration_matches(self) -> None:
        self.assertTrue(is_dui_info_query("Does a DWI affect immigration status?"))

    def test_immigration_consequence_of_dui_matches(self) -> None:
        self.assertTrue(is_dui_info_query("What is the immigration consequence of a DUI?"))

    def test_dui_deportation_matches(self) -> None:
        self.assertTrue(is_dui_info_query("Can a DUI lead to deportation?"))

    def test_dui_naturalization_matches(self) -> None:
        self.assertTrue(is_dui_info_query("Does a DUI affect naturalization?"))

    def test_ead_question_does_not_match(self) -> None:
        self.assertFalse(is_dui_info_query("How do I apply for an EAD?"))

    def test_criminal_inadmissibility_does_not_match(self) -> None:
        self.assertFalse(is_dui_info_query("What is criminal inadmissibility?"))

    def test_what_crimes_inadmissible_does_not_match(self) -> None:
        self.assertFalse(is_dui_info_query("What crimes can make someone inadmissible?"))

    def test_i485_travel_does_not_match(self) -> None:
        self.assertFalse(is_dui_info_query("Can I travel while my I-485 is pending?"))

    def test_action_seeking_dui_no_immigration_word_does_not_match(self) -> None:
        # "I had a DUI, what should I do?" — no immigration effect word near DUI
        self.assertFalse(is_dui_info_query("I had a DUI, what should I do?"))


class DUISafeResponseTests(unittest.IsolatedAsyncioTestCase):
    """DUI informational questions return a prebuilt safe answer without LLM or retrieval."""

    async def _get_dui_response(self, message: str):
        class _NoRetrieval:
            async def retrieve_hybrid(self, query: str, top_k: int = 5):
                raise AssertionError("Retrieval must not be called for DUI info response")

        class _NoChat:
            async def generate_chat_response(self, **kwargs):
                raise AssertionError("LLM must not be called for DUI info response")

        service = ChatService(retrieval_service=_NoRetrieval(), chat_client=_NoChat())
        return await service.generate_chat_response(message, selected_category=None)

    async def test_dui_affect_immigration_returns_ok(self) -> None:
        response = await self._get_dui_response("Can a DUI affect immigration?")
        self.assertEqual(response.status, "ok")

    async def test_dui_response_is_structured(self) -> None:
        response = await self._get_dui_response("Can a DUI affect immigration?")
        self.assertTrue(has_required_sections(response.answer))

    async def test_dui_response_does_not_say_dui_is_aggravated_felony(self) -> None:
        response = await self._get_dui_response("Can a DUI affect immigration?")
        self.assertNotIn("DUI is an aggravated felony", response.answer)

    async def test_dui_response_does_not_have_risky_dui_felony_phrasing(self) -> None:
        import re as _re
        response = await self._get_dui_response("Can a DUI affect immigration?")
        risky = _re.search(
            r"dui.{0,50}(could|can|may|might|would)\s+be\s+an?\s+aggravated\s+felony",
            response.answer,
            _re.I,
        )
        self.assertIsNone(risky, f"Risky aggravated felony phrasing found in answer")

    async def test_dui_response_mentions_sentence_and_facts(self) -> None:
        response = await self._get_dui_response("Can a DUI affect immigration?")
        lower = response.answer.lower()
        self.assertIn("sentence", lower)
        self.assertIn("specific", lower)

    async def test_dui_response_mentions_status(self) -> None:
        response = await self._get_dui_response("Can a DUI affect immigration?")
        self.assertIn("immigration status", response.answer.lower())

    async def test_dui_response_recommends_immigration_attorney(self) -> None:
        response = await self._get_dui_response("Can a DUI affect immigration?")
        self.assertIn("immigration attorney", response.answer.lower())

    async def test_dui_response_recommends_criminal_defense_attorney(self) -> None:
        response = await self._get_dui_response("Can a DUI affect immigration?")
        self.assertIn("criminal defense attorney", response.answer.lower())

    async def test_dui_response_has_at_least_two_used_chunks(self) -> None:
        response = await self._get_dui_response("Can a DUI affect immigration?")
        self.assertGreaterEqual(len(response.used_chunks), 2)

    async def test_dui_response_used_chunks_include_212a2(self) -> None:
        response = await self._get_dui_response("Can a DUI affect immigration?")
        self.assertTrue(
            any("212(a)(2)" in c.citation for c in response.used_chunks),
            "used_chunks must include INA 212(a)(2)",
        )

    async def test_dui_response_used_chunks_include_237a2(self) -> None:
        response = await self._get_dui_response("Can a DUI affect immigration?")
        self.assertTrue(
            any("237(a)(2)" in c.citation for c in response.used_chunks),
            "used_chunks must include INA 237(a)(2)",
        )

    async def test_dui_used_chunks_have_non_empty_snippets(self) -> None:
        response = await self._get_dui_response("Can a DUI affect immigration?")
        for chunk in response.used_chunks:
            self.assertTrue(chunk.snippet.strip(), f"Chunk {chunk.citation} has empty snippet")

    async def test_hit_and_run_action_seeking_returns_criminal_warning_not_dui_answer(self) -> None:
        """hit-and-run action-seeking must return CRIMINAL_WARNING_ANSWER, not the DUI safe answer."""
        class _NoRetrieval:
            async def retrieve_hybrid(self, query: str, top_k: int = 5):
                raise AssertionError("Retrieval must not be called for criminal_warning")

        class _NoChat:
            async def generate_chat_response(self, **kwargs):
                raise AssertionError("LLM must not be called for criminal_warning")

        service = ChatService(retrieval_service=_NoRetrieval(), chat_client=_NoChat())
        response = await service.generate_chat_response(
            "I had a hit and run case, what should I do?"
        )
        self.assertIn("criminal defense attorney", response.answer.lower())
        # Must NOT be the DUI safe answer
        self.assertNotIn("fact-specific", response.answer)


class AnswerIntentClassifierTests(unittest.TestCase):
    """classify_answer_intent returns the correct intent for common question types."""

    # --- General info / definitional questions ---

    def test_what_is_h4_process_is_general_info(self) -> None:
        self.assertEqual(classify_answer_intent("What is H-4 process?"), "general_info")

    def test_what_is_opt_is_general_info(self) -> None:
        self.assertEqual(classify_answer_intent("What is OPT?"), "general_info")

    def test_what_is_form_i765_is_general_info(self) -> None:
        self.assertEqual(classify_answer_intent("What is Form I-765?"), "general_info")

    def test_what_are_naturalization_requirements_is_general_info(self) -> None:
        self.assertEqual(
            classify_answer_intent("What are the requirements for naturalization?"),
            "general_info",
        )

    def test_what_does_ead_mean_is_general_info(self) -> None:
        self.assertEqual(classify_answer_intent("What does EAD mean?"), "general_info")

    # --- Process questions ---

    def test_how_does_h4_ead_work_is_process_or_general(self) -> None:
        result = classify_answer_intent("How does H-4 EAD work?")
        self.assertIn(result, ("general_info", "process_info"))

    def test_how_do_i_apply_for_ead_is_process_or_general(self) -> None:
        result = classify_answer_intent("How do I apply for EAD?")
        self.assertIn(result, ("general_info", "process_info"))

    def test_how_does_h4_process_work_is_process_or_general(self) -> None:
        result = classify_answer_intent("How does the H-4 visa process work?")
        self.assertIn(result, ("general_info", "process_info"))

    # --- Case-specific / risk questions ---

    def test_arrest_green_card_is_case_specific(self) -> None:
        self.assertEqual(
            classify_answer_intent("I have an arrest and want a green card, what should I do?"),
            "case_specific_or_risk",
        )

    def test_prior_denial_is_case_specific(self) -> None:
        self.assertEqual(
            classify_answer_intent("My application was denied last year."),
            "case_specific_or_risk",
        )

    def test_overstayed_is_case_specific(self) -> None:
        self.assertEqual(
            classify_answer_intent("I overstayed my visa, what happens?"),
            "case_specific_or_risk",
        )

    def test_criminal_record_is_case_specific(self) -> None:
        self.assertEqual(
            classify_answer_intent("I have a criminal record and want to apply for citizenship."),
            "case_specific_or_risk",
        )

    def test_was_arrested_is_case_specific(self) -> None:
        self.assertEqual(
            classify_answer_intent("I was arrested last year, can I still get a visa?"),
            "case_specific_or_risk",
        )

    def test_unlawful_presence_is_case_specific(self) -> None:
        self.assertEqual(
            classify_answer_intent("Does unlawful presence affect my green card?"),
            "case_specific_or_risk",
        )

    def test_prior_conviction_is_case_specific(self) -> None:
        self.assertEqual(
            classify_answer_intent("Prior conviction can affect adjustment of status."),
            "case_specific_or_risk",
        )


class AnswerIntentToneTests(unittest.TestCase):
    """build_format_system_addon uses the right next-steps tone per intent."""

    def test_general_info_addon_uses_practical_next_steps(self) -> None:
        addon = build_format_system_addon(
            high_risk=False, weak_sources=False, selected_category=None,
            answer_intent="general_info",
        )
        self.assertIn("practical", addon.lower())
        # Attorney-first hedged command ban should NOT dominate general info questions
        self.assertNotIn("Do not write direct commands like", addon)

    def test_process_info_addon_uses_practical_next_steps(self) -> None:
        addon = build_format_system_addon(
            high_risk=False, weak_sources=False, selected_category=None,
            answer_intent="process_info",
        )
        self.assertIn("practical", addon.lower())
        self.assertNotIn("Do not write direct commands like", addon)

    def test_general_info_addon_still_allows_attorney_mention(self) -> None:
        addon = build_format_system_addon(
            high_risk=False, weak_sources=False, selected_category=None,
            answer_intent="general_info",
        )
        # Attorney referral is still permitted as an optional step
        self.assertIn("immigration attorney", addon.lower())

    def test_case_specific_addon_uses_hedged_next_steps(self) -> None:
        addon = build_format_system_addon(
            high_risk=False, weak_sources=False, selected_category=None,
            answer_intent="case_specific_or_risk",
        )
        self.assertIn("You may need to", addon)
        self.assertIn("Do not write direct commands like", addon)

    def test_high_risk_overrides_general_info_to_attorney_language(self) -> None:
        """high_risk=True forces hedged next-steps even for general_info questions."""
        addon = build_format_system_addon(
            high_risk=True, weak_sources=False, selected_category=None,
            answer_intent="general_info",
        )
        # HIGH-RISK block is added
        self.assertIn("HIGH-RISK", addon)
        self.assertIn("immigration attorney", addon.lower())
        # Hedged next-steps rule is used (not practical language)
        self.assertIn("Do not write direct commands like", addon)

    def test_h4_process_question_gets_practical_tone_in_system_prompt(self) -> None:
        """End-to-end: classify_answer_intent + build_format_system_addon for H-4 question."""
        intent = classify_answer_intent("What is H-4 process?")
        addon = build_format_system_addon(
            high_risk=False, weak_sources=False, selected_category=None,
            answer_intent=intent,
        )
        self.assertIn("practical", addon.lower())
        self.assertNotIn("Do not write direct commands like", addon)

    def test_opt_question_gets_practical_tone_in_system_prompt(self) -> None:
        intent = classify_answer_intent("What is OPT?")
        addon = build_format_system_addon(
            high_risk=False, weak_sources=False, selected_category=None,
            answer_intent=intent,
        )
        self.assertIn("practical", addon.lower())

    def test_arrest_question_gets_hedged_tone_in_system_prompt(self) -> None:
        intent = classify_answer_intent(
            "I have an arrest and want a green card, what should I do?"
        )
        addon = build_format_system_addon(
            high_risk=False, weak_sources=False, selected_category=None,
            answer_intent=intent,
        )
        self.assertIn("Do not write direct commands like", addon)


if __name__ == "__main__":
    unittest.main()
