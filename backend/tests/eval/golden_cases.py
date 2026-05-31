"""Golden routing cases for the deterministic eval harness.

No DB or Ollama required.  All cases are exercised by pure-function calls
in test_golden_routing.py.

Field semantics
---------------
expected_classifier  : "pass" | "greeting" | "criminal_warning" | "refusal"
expected_topic       : only checked when expected_classifier == "pass"; "" otherwise
expected_intent_label: only checked when expected_classifier == "pass"; "" otherwise
required_query_terms : substring match (case-insensitive); all must appear in retrieval_query
forbidden_query_terms: substring match (case-insensitive); none may appear in retrieval_query
required_source_families : must each be present in preferred_source_families
forbidden_source_families: none may be present in preferred_source_families
expected_high_risk   : is_high_risk_topic(input) expected value
expected_criminal_info: is_criminal_info_query(input) expected value
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GoldenCase:
    id: str
    input: str
    expected_classifier: str
    expected_topic: str
    expected_intent_label: str
    required_query_terms: tuple[str, ...] = ()
    forbidden_query_terms: tuple[str, ...] = ()
    required_source_families: tuple[str, ...] = ()
    forbidden_source_families: tuple[str, ...] = ()
    expected_high_risk: bool = False
    expected_criminal_info: bool = False


# ---------------------------------------------------------------------------
# Shared term / source-family constants
# ---------------------------------------------------------------------------

# NTA/removal retrieval query must carry BIA terms (so BIA chunks are not penalized
# by retrieval_scoring._BIA_PENALTY — see query_understanding._NTA_REMOVAL_QUERY).
_NTA_QUERY_TERMS = ("BIA", "Board of Immigration Appeals", "I&N Dec.", "in absentia")

# NTA routing includes BIA case law alongside regulatory sources.
_NTA_SOURCE_FAMILIES = ("eCFR Title 8", "USCIS Policy Manual", "BIA Precedent Decisions")

# All non-NTA routed topics must not include BIA in preferred_source_families.
_BIA_FORBIDDEN = ("BIA Precedent Decisions",)

_AP_QUERY_TERMS = ("advance parole", "Form I-131", "abandonment", "245.2")
_ASYLUM_EAD_QUERY_TERMS = ("208.7", "274a.12(c)(8)", "180-day")
_STEM_OPT_QUERY_TERMS = ("STEM OPT", "Form I-983", "E-Verify", "24-month")
_F1_CPT_QUERY_TERMS = ("CPT", "curriculum practical training", "214.2(f)(10)(i)")
_F1_OPT_QUERY_TERMS = ("post-completion OPT", "Form I-765", "274a.12(c)(3)")
_L2_QUERY_TERMS = ("L-2S", "I-94", "incident to status")


# ---------------------------------------------------------------------------
# GOLDEN_CASES
# ---------------------------------------------------------------------------

GOLDEN_CASES: tuple[GoldenCase, ...] = (

    # ── NTA / removal high-risk ─────────────────────────────────────────────
    # Requires both _NTA_PERSONAL_SIGNAL ("I received", "I got", "I have", …)
    # AND _NTA_TOPIC_SIGNAL ("NTA", "Notice to Appear", "removal order", …).
    # BIA source family and BIA query terms are required.

    GoldenCase(
        id="nta_received_rights",
        input="I received an NTA, what are my rights?",
        expected_classifier="pass",
        expected_topic="nta_removal_high_risk",
        expected_intent_label="case_specific_or_risk",
        required_query_terms=_NTA_QUERY_TERMS,
        required_source_families=_NTA_SOURCE_FAMILIES,
        expected_high_risk=True,
    ),
    GoldenCase(
        id="nta_got_notice_lawyer",
        input="I got a Notice to Appear last week, do I need a lawyer?",
        expected_classifier="pass",
        expected_topic="nta_removal_high_risk",
        expected_intent_label="case_specific_or_risk",
        required_query_terms=_NTA_QUERY_TERMS,
        required_source_families=_NTA_SOURCE_FAMILIES,
        expected_high_risk=True,
    ),
    GoldenCase(
        id="nta_pending_removal_order",
        input="I have a pending removal order, what should I do?",
        expected_classifier="pass",
        expected_topic="nta_removal_high_risk",
        expected_intent_label="case_specific_or_risk",
        required_query_terms=_NTA_QUERY_TERMS,
        required_source_families=_NTA_SOURCE_FAMILIES,
        expected_high_risk=True,
    ),
    # Definitional — "Notice to Appear" triggers is_high_risk_topic even though
    # there is no personal signal, so topic falls back to "general".
    GoldenCase(
        id="nta_definitional_no_personal_signal",
        input="What is a Notice to Appear?",
        expected_classifier="pass",
        expected_topic="general",
        expected_intent_label="general_info",
        expected_high_risk=True,
    ),
    # "immigration court" in text triggers is_high_risk_topic even without
    # a personal NTA signal — topic stays "general".
    GoldenCase(
        id="nta_missed_court_no_personal_signal",
        input="What happens if I miss my immigration court date?",
        expected_classifier="pass",
        expected_topic="general",
        expected_intent_label="general_info",
        expected_high_risk=True,
    ),

    # ── I-485 advance parole ─────────────────────────────────────────────────
    # Requires _I485_PENDING_SIGNAL (I-485 / adjustment of status) AND
    # _TRAVEL_AP_SIGNAL (travel / go abroad / advance parole).
    # BIA source family must not appear.

    GoldenCase(
        id="i485_travel_pending",
        input="Can I travel while my I-485 is pending?",
        expected_classifier="pass",
        expected_topic="i485_advance_parole",
        expected_intent_label="case_specific_or_risk",
        required_query_terms=_AP_QUERY_TERMS,
        forbidden_source_families=_BIA_FORBIDDEN,
    ),
    GoldenCase(
        id="i485_adjustment_go_abroad",
        input="My adjustment of status is pending, I need to go abroad",
        expected_classifier="pass",
        expected_topic="i485_advance_parole",
        expected_intent_label="case_specific_or_risk",
        required_query_terms=_AP_QUERY_TERMS,
        forbidden_source_families=_BIA_FORBIDDEN,
    ),
    # No I-485/adjustment signal — travel signal alone falls through to general.
    GoldenCase(
        id="i485_ap_definitional_no_i485_signal",
        input="What is advance parole?",
        expected_classifier="pass",
        expected_topic="general",
        expected_intent_label="general_info",
    ),

    # ── Asylum EAD ───────────────────────────────────────────────────────────
    # Requires _ASYLUM_SIGNAL (asylum / I-589 / asylee) AND
    # _ASYLUM_EAD_WORK_SIGNAL (EAD / work authorization / I-765).
    # BIA source family must not appear.

    GoldenCase(
        id="asylum_ead_pending_application",
        input="My asylum application is pending, can I get an EAD?",
        expected_classifier="pass",
        expected_topic="asylum_ead",
        expected_intent_label="case_specific_or_risk",
        required_query_terms=_ASYLUM_EAD_QUERY_TERMS,
        forbidden_source_families=_BIA_FORBIDDEN,
    ),
    GoldenCase(
        id="asylum_ead_i589_work_auth",
        input="I filed an I-589, when can I apply for work authorization?",
        expected_classifier="pass",
        expected_topic="asylum_ead",
        expected_intent_label="case_specific_or_risk",
        required_query_terms=_ASYLUM_EAD_QUERY_TERMS,
        forbidden_source_families=_BIA_FORBIDDEN,
    ),
    # Asylum signal present but no EAD/work signal — falls through to general.
    GoldenCase(
        id="asylum_definitional_no_work_signal",
        input="Can I apply for asylum?",
        expected_classifier="pass",
        expected_topic="general",
        expected_intent_label="general_info",
    ),

    # ── STEM OPT ─────────────────────────────────────────────────────────────
    # Matched on "STEM OPT" phrase alone; highest priority among F-1 topics.
    # BIA source family must not appear.

    GoldenCase(
        id="stem_opt_apply_extension",
        input="How do I apply for STEM OPT extension?",
        expected_classifier="pass",
        expected_topic="stem_opt",
        expected_intent_label="general_info",
        required_query_terms=_STEM_OPT_QUERY_TERMS,
        forbidden_source_families=_BIA_FORBIDDEN,
    ),
    GoldenCase(
        id="stem_opt_approved_i983",
        input="My STEM OPT was approved, what is Form I-983?",
        expected_classifier="pass",
        expected_topic="stem_opt",
        expected_intent_label="general_info",
        required_query_terms=_STEM_OPT_QUERY_TERMS,
        forbidden_source_families=_BIA_FORBIDDEN,
    ),

    # ── F-1 CPT ──────────────────────────────────────────────────────────────
    # CPT signal + F-1 student context (or work context).
    # BIA source family must not appear.

    GoldenCase(
        id="f1_cpt_student_question",
        input="Can I do CPT as an F-1 student?",
        expected_classifier="pass",
        expected_topic="f1_cpt",
        expected_intent_label="general_info",
        required_query_terms=_F1_CPT_QUERY_TERMS,
        forbidden_source_families=_BIA_FORBIDDEN,
    ),
    GoldenCase(
        id="f1_cpt_affects_opt",
        input="Does CPT affect OPT eligibility as an F-1 student?",
        expected_classifier="pass",
        expected_topic="f1_cpt",
        expected_intent_label="general_info",
        required_query_terms=_F1_CPT_QUERY_TERMS,
        forbidden_source_families=_BIA_FORBIDDEN,
    ),

    # ── F-1 OPT ──────────────────────────────────────────────────────────────
    # OPT signal + work/employment context required.
    # "What is OPT?" has the OPT signal but no work context → falls through to general.
    # BIA source family must not appear.

    GoldenCase(
        id="f1_opt_work_after_graduation",
        input="Can I work after graduation on F-1 OPT?",
        expected_classifier="pass",
        expected_topic="f1_opt",
        expected_intent_label="general_info",
        required_query_terms=_F1_OPT_QUERY_TERMS,
        forbidden_source_families=_BIA_FORBIDDEN,
    ),
    GoldenCase(
        id="f1_opt_apply_post_completion",
        input="How do I apply for post-completion OPT as an F-1 student?",
        expected_classifier="pass",
        expected_topic="f1_opt",
        expected_intent_label="general_info",
        required_query_terms=_F1_OPT_QUERY_TERMS,
        forbidden_source_families=_BIA_FORBIDDEN,
    ),
    # OPT signal present but no work context — falls through to general.
    GoldenCase(
        id="f1_opt_definitional_no_work_context",
        input="What is OPT?",
        expected_classifier="pass",
        expected_topic="general",
        expected_intent_label="general_info",
    ),

    # ── L-2 spouse work authorization ─────────────────────────────────────────
    # (L-1 principal + spouse + work) OR (L-2/L-2S direct + work).
    # "Can I extend my L-2 status?" has L-2 signal but no work signal → general.
    # BIA source family must not appear.

    GoldenCase(
        id="l2_spouse_on_l1",
        input="Can my spouse work if I am on L-1 visa?",
        expected_classifier="pass",
        expected_topic="l2_work_authorization",
        expected_intent_label="general_info",
        required_query_terms=_L2_QUERY_TERMS,
        forbidden_source_families=_BIA_FORBIDDEN,
    ),
    GoldenCase(
        id="l2_spouse_need_ead",
        input="Does L-2 spouse need an EAD?",
        expected_classifier="pass",
        expected_topic="l2_work_authorization",
        expected_intent_label="general_info",
        required_query_terms=_L2_QUERY_TERMS,
        forbidden_source_families=_BIA_FORBIDDEN,
    ),
    GoldenCase(
        id="l2s_work_without_ead",
        input="Can my L-2S spouse work without an EAD?",
        expected_classifier="pass",
        expected_topic="l2_work_authorization",
        expected_intent_label="general_info",
        required_query_terms=_L2_QUERY_TERMS,
        forbidden_source_families=_BIA_FORBIDDEN,
    ),
    # L-2 signal present but no work-auth signal — falls through to general.
    GoldenCase(
        id="l2_no_work_signal",
        input="Can I extend my L-2 status?",
        expected_classifier="pass",
        expected_topic="general",
        expected_intent_label="general_info",
    ),

    # ── Classifier: refusal ──────────────────────────────────────────────────
    # Strategy-seeking fraud / evasion messages short-circuit before retrieval.
    # expected_topic and expected_intent_label are "" (not checked for refusal).

    GoldenCase(
        id="refusal_hide_arrest",
        input="How do I hide my arrest from USCIS?",
        expected_classifier="refusal",
        expected_topic="",
        expected_intent_label="",
    ),
    GoldenCase(
        id="refusal_lie_i485_criminal",
        input="Can I lie on my I-485 about my criminal record?",
        expected_classifier="refusal",
        expected_topic="",
        expected_intent_label="",
        expected_high_risk=True,  # "criminal" in text triggers is_high_risk_topic
    ),
    GoldenCase(
        id="refusal_avoid_ice",
        input="How do I avoid ICE?",
        expected_classifier="refusal",
        expected_topic="",
        expected_intent_label="",
    ),

    # ── Classifier: greeting ─────────────────────────────────────────────────

    GoldenCase(
        id="greeting_hi",
        input="Hi",
        expected_classifier="greeting",
        expected_topic="",
        expected_intent_label="",
    ),
    GoldenCase(
        id="greeting_thanks",
        input="Thanks",
        expected_classifier="greeting",
        expected_topic="",
        expected_intent_label="",
    ),

    # ── Classifier: criminal warning ─────────────────────────────────────────
    # Criminal-matter word + action-seeking phrase → safe referral, no retrieval.

    GoldenCase(
        id="criminal_warning_dui",
        input="I was arrested for DUI, what should I do?",
        expected_classifier="criminal_warning",
        expected_topic="",
        expected_intent_label="",
    ),
    GoldenCase(
        id="criminal_warning_drug_conviction",
        input="I have a drug conviction, what are my options?",
        expected_classifier="criminal_warning",
        expected_topic="",
        expected_intent_label="",
    ),

    # ── General fallback ─────────────────────────────────────────────────────

    GoldenCase(
        id="general_green_card_documents",
        input="What documents do I need for a green card?",
        expected_classifier="pass",
        expected_topic="general",
        expected_intent_label="general_info",
    ),
)
