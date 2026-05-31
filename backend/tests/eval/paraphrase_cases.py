"""Paraphrase and holdout routing cases for the deterministic eval harness.

Extends GOLDEN_CASES with alternative phrasings to measure generalization.
No DB or Ollama required — all pure-function calls only.

Near-miss cases (expected_topic="general") are intentional: they document
phrasings that correctly fall through to general because only one of the
two required co-occurrence signals fires (e.g. OPT signal without work
context, L-2 signal without work context, NTA topic without personal signal).
These are not gaps — they guard against over-eager routing.
"""

from __future__ import annotations

from .golden_cases import (
    GoldenCase,
    _AP_QUERY_TERMS,
    _ASYLUM_EAD_QUERY_TERMS,
    _BIA_FORBIDDEN,
    _F1_CPT_QUERY_TERMS,
    _F1_OPT_QUERY_TERMS,
    _NTA_QUERY_TERMS,
    _NTA_SOURCE_FAMILIES,
    _STEM_OPT_QUERY_TERMS,
)

# ---------------------------------------------------------------------------
# Paraphrase-specific term sets
# ---------------------------------------------------------------------------

# L-2: golden set uses ("L-2S", "I-94", "incident to status").
# Paraphrases also verify "L-2" and "Form I-765" are in the retrieval query.
_L2_PARA_QUERY_TERMS = ("L-2", "L-2S", "I-94", "Form I-765")

# Asylum EAD: golden set uses ("208.7", "274a.12(c)(8)", "180-day").
# Paraphrases also verify "Form I-765" is present.
_ASYLUM_EAD_PARA_QUERY_TERMS = ("208.7", "274a.12(c)(8)", "180-day", "Form I-765")

# F-1 CPT: golden set uses ("CPT", "curriculum practical training", "214.2(f)(10)(i)").
# Paraphrases swap "curriculum practical training" for "I-20" to check DSO annotation.
_F1_CPT_PARA_QUERY_TERMS = ("CPT", "214.2(f)(10)(i)", "I-20")


# ---------------------------------------------------------------------------
# PARAPHRASE_CASES
# ---------------------------------------------------------------------------

PARAPHRASE_CASES: tuple[GoldenCase, ...] = (

    # ── A. NTA / removal paraphrases ─────────────────────────────────────────
    # _NTA_PERSONAL_SIGNAL covers: "I received", "I got", "I have",
    # "I was given", "we received", "we got", "my NTA", "our NTA",
    # "after receiving", "receiving a Notice to Appear",
    # "received an NTA", "got an NTA".
    # Tests below probe each path and two gap phrasings.

    GoldenCase(
        id="para_nta_we_received",
        input="We received a Notice to Appear from immigration court. What should we do?",
        expected_classifier="pass",
        expected_topic="nta_removal_high_risk",
        expected_intent_label="case_specific_or_risk",
        required_query_terms=_NTA_QUERY_TERMS,
        required_source_families=_NTA_SOURCE_FAMILIES,
        expected_high_risk=True,
    ),
    GoldenCase(
        id="para_nta_served_routing_gap",
        input="I was served an NTA and have a court hearing coming up.",
        expected_classifier="pass",
        expected_topic="nta_removal_high_risk",
        expected_intent_label="case_specific_or_risk",
        required_query_terms=_NTA_QUERY_TERMS,
        required_source_families=_NTA_SOURCE_FAMILIES,
        expected_high_risk=True,
    ),
    GoldenCase(
        id="para_nta_in_proceedings_routing_gap",
        input="I am in removal proceedings and need to know my rights.",
        expected_classifier="pass",
        expected_topic="nta_removal_high_risk",
        expected_intent_label="case_specific_or_risk",
        required_query_terms=_NTA_QUERY_TERMS,
        required_source_families=_NTA_SOURCE_FAMILIES,
        expected_high_risk=True,
    ),
    # Near-miss: definitional question — no personal signal → topic stays general.
    # "Notice to Appear" still fires is_high_risk_topic.
    GoldenCase(
        id="para_nta_requirements_near_miss",
        input="What are the requirements for a Notice to Appear?",
        expected_classifier="pass",
        expected_topic="general",
        expected_intent_label="general_info",
        expected_high_risk=True,
    ),

    # ── B. L-2 spouse work authorization paraphrases ─────────────────────────
    # Three signal paths exercised:
    #   B1: L1 + wife + EAD       → l2_work_authorization (L1+spouse+work)
    #   B2: L1 + husband + work   → l2_work_authorization (L1+spouse+work)
    #   B3: L-2S + work           → l2_work_authorization (L2+work direct)

    GoldenCase(
        id="para_l2_wife_ead_on_l1",
        input="Does my wife need an EAD if I am on L-1?",
        expected_classifier="pass",
        expected_topic="l2_work_authorization",
        expected_intent_label="general_info",
        required_query_terms=_L2_PARA_QUERY_TERMS,
        required_source_families=("USCIS Policy Manual",),
        forbidden_source_families=_BIA_FORBIDDEN,
    ),
    GoldenCase(
        id="para_l2_husband_on_l1_employee",
        input="I am an L1 employee. Can my husband work in the US?",
        expected_classifier="pass",
        expected_topic="l2_work_authorization",
        expected_intent_label="general_info",
        required_query_terms=_L2_PARA_QUERY_TERMS,
        required_source_families=("USCIS Policy Manual",),
        forbidden_source_families=_BIA_FORBIDDEN,
    ),
    GoldenCase(
        id="para_l2s_holder_work_auth",
        input="L-2S holder, do I need to apply for work authorization?",
        expected_classifier="pass",
        expected_topic="l2_work_authorization",
        expected_intent_label="general_info",
        required_query_terms=_L2_PARA_QUERY_TERMS,
        required_source_families=("USCIS Policy Manual",),
        forbidden_source_families=_BIA_FORBIDDEN,
    ),

    # ── C. F-1 OPT paraphrases ───────────────────────────────────────────────
    # _OPT_WORK_CONTEXT covers: work, employ*, ead, employment authorization,
    # authorized, after graduation, post-completion.
    # All three paraphrases hit at least one work-context term.

    GoldenCase(
        id="para_f1_opt_eligible_to_work",
        input="Am I eligible to work using OPT after finishing school?",
        expected_classifier="pass",
        expected_topic="f1_opt",
        expected_intent_label="general_info",
        required_query_terms=_F1_OPT_QUERY_TERMS,
        forbidden_source_families=_BIA_FORBIDDEN,
    ),
    GoldenCase(
        id="para_f1_opt_post_completion_process",
        input="What is the work authorization process for post-completion OPT?",
        expected_classifier="pass",
        expected_topic="f1_opt",
        expected_intent_label="general_info",
        required_query_terms=_F1_OPT_QUERY_TERMS,
        forbidden_source_families=_BIA_FORBIDDEN,
    ),
    GoldenCase(
        id="para_f1_opt_employment_after_graduation",
        input="Can an F-1 student use OPT employment after graduation?",
        expected_classifier="pass",
        expected_topic="f1_opt",
        expected_intent_label="general_info",
        required_query_terms=_F1_OPT_QUERY_TERMS,
        forbidden_source_families=_BIA_FORBIDDEN,
    ),
    # Near-miss: OPT signal present but "rules" is not a work-context signal.
    # Confirms that OPT alone (without work context) falls through to general.
    GoldenCase(
        id="para_f1_opt_rules_near_miss",
        input="What are the rules for OPT?",
        expected_classifier="pass",
        expected_topic="general",
        expected_intent_label="general_info",
    ),

    # ── D. F-1 CPT paraphrases ───────────────────────────────────────────────
    # CPT routing requires _CPT_SIGNAL AND (_F1_STUDENT_CONTEXT OR _OPT_WORK_CONTEXT).
    # D1 works: F-1/student context present.
    # D2–D3 are routing gaps: CPT signal fires but neither context fires.

    GoldenCase(
        id="para_f1_cpt_cooperative_education",
        input="I am an F-1 student doing cooperative education. Is that CPT?",
        expected_classifier="pass",
        expected_topic="f1_cpt",
        expected_intent_label="general_info",
        required_query_terms=_F1_CPT_PARA_QUERY_TERMS,
        forbidden_source_families=_BIA_FORBIDDEN,
    ),
    GoldenCase(
        id="para_f1_cpt_internship_routing_gap",
        input="Can I do an internship through CPT authorization?",
        expected_classifier="pass",
        expected_topic="f1_cpt",
        expected_intent_label="general_info",
        required_query_terms=_F1_CPT_PARA_QUERY_TERMS,
        forbidden_source_families=_BIA_FORBIDDEN,
    ),
    GoldenCase(
        id="para_f1_cpt_opt_eligibility_routing_gap",
        input="Does full-time CPT affect my OPT eligibility?",
        expected_classifier="pass",
        expected_topic="f1_cpt",
        expected_intent_label="general_info",
        required_query_terms=_F1_CPT_PARA_QUERY_TERMS,
        forbidden_source_families=_BIA_FORBIDDEN,
    ),

    # ── E. STEM OPT paraphrases ──────────────────────────────────────────────
    # Single-phrase match on \bstem\s+opt\b is robust — all three paraphrases
    # route correctly regardless of surrounding context.

    GoldenCase(
        id="para_stem_opt_employer_requirements",
        input="What are the employer requirements for STEM OPT?",
        expected_classifier="pass",
        expected_topic="stem_opt",
        expected_intent_label="general_info",
        required_query_terms=_STEM_OPT_QUERY_TERMS,
        forbidden_source_families=_BIA_FORBIDDEN,
    ),
    GoldenCase(
        id="para_stem_opt_form_i983",
        input="Do I need Form I-983 for STEM OPT?",
        expected_classifier="pass",
        expected_topic="stem_opt",
        expected_intent_label="general_info",
        required_query_terms=_STEM_OPT_QUERY_TERMS,
        forbidden_source_families=_BIA_FORBIDDEN,
    ),
    GoldenCase(
        id="para_stem_opt_24_month_extension",
        input="How does the 24-month STEM OPT extension work?",
        expected_classifier="pass",
        expected_topic="stem_opt",
        expected_intent_label="general_info",
        required_query_terms=_STEM_OPT_QUERY_TERMS,
        forbidden_source_families=_BIA_FORBIDDEN,
    ),

    # ── F. Asylum EAD paraphrases ─────────────────────────────────────────────
    # _ASYLUM_EAD_WORK_SIGNAL covers: ead, employment authorization, work permit,
    # work authorization, Form I-765, I-765, authorized to work,
    # work (while|after|before|timing).
    # "Permission to work" is a routing gap — not in the signal.

    GoldenCase(
        id="para_asylum_ead_permission_to_work_routing_gap",
        input="I applied for asylum and need permission to work.",
        expected_classifier="pass",
        expected_topic="asylum_ead",
        expected_intent_label="case_specific_or_risk",
        required_query_terms=_ASYLUM_EAD_PARA_QUERY_TERMS,
        forbidden_source_families=_BIA_FORBIDDEN,
    ),
    GoldenCase(
        id="para_asylum_ead_work_permit_timeline",
        input="My asylum is pending. When can I get a work permit?",
        expected_classifier="pass",
        expected_topic="asylum_ead",
        expected_intent_label="case_specific_or_risk",
        required_query_terms=_ASYLUM_EAD_PARA_QUERY_TERMS,
        forbidden_source_families=_BIA_FORBIDDEN,
    ),
    GoldenCase(
        id="para_asylum_ead_timeline_terse",
        input="Asylum pending EAD timeline?",
        expected_classifier="pass",
        expected_topic="asylum_ead",
        expected_intent_label="case_specific_or_risk",
        required_query_terms=_ASYLUM_EAD_PARA_QUERY_TERMS,
        forbidden_source_families=_BIA_FORBIDDEN,
    ),
    # Near-miss: "asylee" matches _ASYLUM_SIGNAL but "benefits" is not in
    # _ASYLUM_EAD_WORK_SIGNAL → topic falls through to general.
    # Note: "asylee" ≠ "asylum" keyword, so no high-risk pattern fires.
    GoldenCase(
        id="para_asylum_ead_asylee_benefits_near_miss",
        input="I am an asylee, what benefits do I have?",
        expected_classifier="pass",
        expected_topic="general",
        expected_intent_label="general_info",
        expected_high_risk=False,
    ),

    # ── G. I-485 advance parole paraphrases ──────────────────────────────────
    # _I485_PENDING_SIGNAL covers: I-485, adjustment of status,
    # adjustment (application|pending|case), pending (adjustment|green card application).
    # "Applied for a green card" is a routing gap — not in the signal.

    GoldenCase(
        id="para_i485_ap_travel_while_processing",
        input="I need to travel internationally while my I-485 is processing.",
        expected_classifier="pass",
        expected_topic="i485_advance_parole",
        expected_intent_label="case_specific_or_risk",
        required_query_terms=_AP_QUERY_TERMS,
        forbidden_source_families=_BIA_FORBIDDEN,
    ),
    GoldenCase(
        id="para_i485_ap_adjustment_go_abroad",
        input="My adjustment of status is pending and I need to go abroad.",
        expected_classifier="pass",
        expected_topic="i485_advance_parole",
        expected_intent_label="case_specific_or_risk",
        required_query_terms=_AP_QUERY_TERMS,
        forbidden_source_families=_BIA_FORBIDDEN,
    ),
    GoldenCase(
        id="para_i485_green_card_travel_routing_gap",
        input="I applied for a green card. Can I leave the country before approval?",
        expected_classifier="pass",
        expected_topic="i485_advance_parole",
        expected_intent_label="case_specific_or_risk",
        required_query_terms=_AP_QUERY_TERMS,
        forbidden_source_families=_BIA_FORBIDDEN,
    ),
    # Near-miss: travel signal ("advance parole") fires but no I-485/adjustment
    # signal → topic stays general (same gating logic as golden case
    # i485_ap_definitional_no_i485_signal, different phrasing).
    GoldenCase(
        id="para_i485_ap_apply_near_miss",
        input="How do I apply for advance parole?",
        expected_classifier="pass",
        expected_topic="general",
        expected_intent_label="general_info",
    ),

    # ── H. Priority boundary ─────────────────────────────────────────────────
    # understand_query() evaluates nta_removal_high_risk before i485_advance_parole.
    # A message with both NTA personal+topic signals AND I-485+travel signals
    # must resolve to nta_removal_high_risk, confirming priority is enforced.

    GoldenCase(
        id="para_priority_nta_over_i485",
        input="I have an NTA and my I-485 is pending. Can I travel?",
        expected_classifier="pass",
        expected_topic="nta_removal_high_risk",
        expected_intent_label="case_specific_or_risk",
        required_query_terms=_NTA_QUERY_TERMS,
        required_source_families=_NTA_SOURCE_FAMILIES,
        expected_high_risk=True,
    ),
)
