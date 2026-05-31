"""Query understanding foundation for structured retrieval routing.

Maps a raw user message to a QueryUnderstanding that carries:
- topic: machine label for the matched intent (e.g. "l2_work_authorization")
- intent_label: broad intent class ("general_info" | "process_info" | "case_specific_or_risk")
- retrieval_query: rewritten query string optimised for hybrid retrieval
- preferred_source_families: hint for future source-level routing (unused by retrieval_service today)
- missing_facts: signals that a follow-up question might improve retrieval (reserved for future use)

Default fallback preserves current behavior exactly:
  topic="general", retrieval_query=original message, no source families, no missing facts.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class QueryUnderstanding:
    topic: str
    intent_label: str
    retrieval_query: str
    preferred_source_families: tuple[str, ...]
    missing_facts: tuple[str, ...]
    answer_guidance: str = ""


# ---- L-2 work authorization -------------------------------------------------
# Detects questions about whether an L-2 or L-2S dependent spouse/family member
# can work in the U.S., and whether an EAD is needed, when the L-1 principal
# is the context.  Three co-occurrence signals must appear:
#   Signal A: L-1 principal reference (l1, l-1)
#   Signal B: spouse / family-member reference (spouse, wife, husband, dependent)
#   Signal C: work authorization context (work, employ*, ead, authorized)
# OR independently:
#   Signal A': L-2 or L-2S direct reference (l2, l-2, l2s, l-2s)
#   Signal C (same): work authorization context

_L1_PRINCIPAL_SIGNAL = re.compile(r"\bl[- ]?1\b", re.I)
_L2_DIRECT_SIGNAL = re.compile(r"\bl[- ]?2s?\b", re.I)
_SPOUSE_FAMILY_SIGNAL = re.compile(r"\b(?:spouse|wife|husband|dependent)\b", re.I)
_WORK_AUTH_SIGNAL = re.compile(
    r"\b(?:work|employ\w*|ead|employment\s+authorization|authorized)\b", re.I
)

_L2_WORK_AUTH_QUERY = (
    "L-2 dependent spouse employment authorized incident to status "
    "L-2S I-94 employment authorization EAD Form I-765 spouses of L-1 nonimmigrants"
)

_L2_ANSWER_GUIDANCE = (
    "Answer only for L-2/L-2S spouse work authorization. "
    "Explain that certain L-2 spouses are employment authorized incident to status. "
    "Mention that the I-94 notation, such as L-2S, is important evidence of work authorization. "
    "Explain that Form I-765/EAD may be filed to obtain an EAD as evidence of identity and "
    "employment authorization, but avoid implying the EAD is always required for L-2S spouses. "
    "Do not discuss E-1, E-2, E-3 spouses unless directly asked. "
    "Do not mention H-4, I-140, AC21, naturalization, V visas, T visas, TPS, asylum, "
    "or unrelated categories."
)

# Soft additive boost for preferred-source results after RRF scoring.
# Typical RRF hybrid scores range ~0.015–0.035; 0.004 is meaningful but not dominant.
_SOURCE_FAMILY_BOOST = 0.004

# ---- F-1 practical training (OPT, CPT, STEM OPT) ---------------------------
# Priority: stem_opt > f1_cpt > f1_opt
# "What is OPT?" has no work context signal → falls through to general.

_STEM_OPT_SIGNAL = re.compile(r"\bstem\s+opt\b", re.I)
_CPT_SIGNAL = re.compile(r"\bcpt\b|curriculum\s+practical\s+training", re.I)
_OPT_SIGNAL = re.compile(r"\bopt\b|optional\s+practical\s+training", re.I)
_OPT_WORK_CONTEXT = re.compile(
    r"\b(?:work|employ\w*|ead|employment\s+authorization|authorized"
    r"|after\s+graduation|post[- ]?completion|internship|eligib\w*)\b",
    re.I,
)
_F1_STUDENT_CONTEXT = re.compile(r"\bf[- ]?1\b|\bstudent\b|\bi[- ]?20\b", re.I)

_F1_OPT_QUERY = (
    "F-1 optional practical training OPT post-completion OPT 8 CFR 214.2(f)(10) "
    "Form I-765 274a.12(c)(3) employment authorization DSO SEVIS graduation "
    "academic degree field of study"
)

_F1_CPT_QUERY = (
    "F-1 curriculum practical training CPT 8 CFR 214.2(f)(10)(i) "
    "cooperative education internship employer DSO authorization I-20 SEVIS "
    "integral part of established curriculum"
)

_STEM_OPT_QUERY = (
    "STEM OPT extension 24-month F-1 STEM degree 8 CFR 214.2(f)(10)(ii)(C) "
    "Form I-983 Training Plan E-Verify employer 274a.12(c)(3)(C) "
    "science technology engineering mathematics"
)

_F1_OPT_ANSWER_GUIDANCE = (
    "Answer only for F-1 post-completion OPT. "
    "Explain that F-1 students may apply for up to 12 months of OPT in their field of study "
    "after completing their academic program. "
    "Mention that OPT requires DSO recommendation on the I-20, USCIS approval via Form I-765, "
    "and work authorization under 8 CFR 274a.12(c)(3). "
    "Do not discuss CPT, STEM OPT extension, pre-completion OPT, H-3 training, naturalization, "
    "adjustment of status, or unrelated categories unless directly asked."
)

_F1_CPT_ANSWER_GUIDANCE = (
    "Answer only for F-1 CPT. "
    "Explain that CPT is authorized by the DSO on the student's I-20 under "
    "8 CFR 214.2(f)(10)(i) and does not require USCIS approval or Form I-765. "
    "Mention that CPT must be an integral part of the established curriculum. "
    "Note that 12 or more months of full-time CPT eliminates OPT eligibility. "
    "Do not discuss post-completion OPT, STEM OPT extension, H-3 training, TN occupations, "
    "M-2 status, or unrelated categories unless directly asked."
)

_STEM_OPT_ANSWER_GUIDANCE = (
    "Answer only for STEM OPT extension, the 24-month extension under "
    "8 CFR 214.2(f)(10)(ii)(C). "
    "Explain that eligible F-1 students with a qualifying STEM degree on an initial OPT period "
    "may apply for a 24-month extension. "
    "Mention that the employer must be enrolled in E-Verify and the student must complete a "
    "Training Plan on Form I-983. "
    "Mention 8 CFR 274a.12(c)(3)(C) as the work authorization category for STEM OPT. "
    "Do not discuss CPT, pre-completion OPT, H-3 training, TN occupations, M-1/M-2 status, "
    "or unrelated categories unless directly asked."
)

_F1_PRACTICAL_TRAINING_SOURCE_FAMILIES: tuple[str, ...] = (
    "eCFR Title 8",
    "USCIS Policy Manual",
)

# Shared source families for high-risk / humanitarian topics (no BIA).
_HUMANITARIAN_SOURCE_FAMILIES: tuple[str, ...] = (
    "eCFR Title 8",
    "USCIS Policy Manual",
)

# NTA/removal topics also include BIA case law alongside regulatory sources.
_NTA_SOURCE_FAMILIES: tuple[str, ...] = (
    "eCFR Title 8",
    "USCIS Policy Manual",
    "BIA Precedent Decisions",
)

# ---- Asylum EAD (8 CFR 208.7 / 274a.12(c)(8)) --------------------------------
# Detects questions about employment authorization timing for pending asylum
# applicants. Requires both an asylum context signal AND an EAD/work signal.
# Do not match: "Can I apply for asylum?" (no work signal) or
# "How do I apply for EAD?" (no asylum signal).

_ASYLUM_SIGNAL = re.compile(
    r"\b(?:asylum|asylee|affirmative\s+asylum|filed\s+asylum|filing\s+asylum"
    r"|pending\s+asylum|asylum\s+applicant|asylum\s+application|I[- ]?589)\b",
    re.I,
)
_ASYLUM_EAD_WORK_SIGNAL = re.compile(
    r"\b(?:ead|employment\s+authorization|work\s+permit|work\s+authorization"
    r"|Form\s+I[- ]?765|I[- ]?765|authorized\s+to\s+work"
    r"|work\s+(?:while|after|before|timing)|permission\s+to\s+work)\b",
    re.I,
)

_ASYLUM_EAD_QUERY = (
    "pending asylum applicant employment authorization EAD 8 CFR 208.7 "
    "Form I-765 274a.12(c)(8) 180-day waiting period asylee applicant "
    "affirmative asylum work permit category c8 employment authorization document"
)

_ASYLUM_EAD_ANSWER_GUIDANCE = (
    "Answer only for pending asylum applicants seeking employment authorization "
    "under 8 CFR 208.7 and 274a.12(c)(8). "
    "Explain the 180-day waiting period: an applicant generally may not file "
    "Form I-765 for an EAD until 180 days after filing a complete asylum application. "
    "Mention that the EAD category for pending asylum applicants is (c)(8). "
    "Mention Form I-765 as the required form. "
    "Do not discuss adjustment-of-status EAD (c)(9), TPS, DACA, OPT, L-2, H-4, or "
    "LPR/Form I-551 employment authorization unless directly asked. "
    "Do not discuss Form I-589/asylum filing process unless directly asked."
)

# ---- I-485 advance parole (8 CFR 245.2) --------------------------------------
# Detects pending I-485 adjustment + international travel questions.
# Requires both an I-485/adjustment signal AND a travel/advance-parole signal.
# Do not match: "How do I apply for advance parole?" without I-485/adjustment context.

_I485_PENDING_SIGNAL = re.compile(
    r"\bI[- ]?485\b|adjustment\s+of\s+status|adjustment\s+(?:application|pending|case)"
    r"|pending\s+(?:adjustment|green\s+card\s+application)"
    r"|applied\s+for\s+(?:a\s+)?green\s+card",
    re.I,
)
_TRAVEL_AP_SIGNAL = re.compile(
    r"\b(?:travel|advance\s+parole|Form\s+I[- ]?131|I[- ]?131|travel\s+document"
    r"|go\s+abroad|leave\s+the\s+(?:country|US|U\.S\.?))\b",
    re.I,
)

_I485_AP_QUERY = (
    "advance parole I-485 adjustment of status pending Form I-131 "
    "travel document abandonment 8 CFR 245.2 travel abroad return "
    "approval before departure risk of abandonment adjustment pending travel"
)

_I485_AP_ANSWER_GUIDANCE = (
    "Answer only for a pending I-485 adjustment-of-status applicant asking about "
    "international travel. "
    "Explain that traveling abroad while an I-485 is pending without an approved "
    "advance parole document generally results in the I-485 being considered abandoned, "
    "under 8 CFR 245.2(a)(4)(ii). "
    "Mention Form I-131 as the form to apply for advance parole before departing. "
    "Note that certain exceptions may apply, such as some H-1B or L-1 status holders, "
    "but these are fact-specific. "
    "If recommending legal help, refer to a qualified immigration attorney or accredited representative only. "
    "Do not cite or discuss asylum travel limitations under 8 CFR 208.8 or 1208.8. "
    "Do not discuss special adjustment provisions under 8 CFR 1245.12 or 1245.13 unless directly asked. "
    "Do not discuss TPS travel authorization, parole-in-place, naturalization travel, "
    "Syria/special immigrant provisions, or T nonimmigrant travel unless directly asked."
)

# ---- NTA / removal high-risk (8 CFR 239.1) -----------------------------------
# Detects personal NTA/removal situations. Requires both a personal signal
# (I received, I got, I have, etc.) AND a topic signal (NTA, Notice to Appear,
# removal proceedings, immigration court).
# Do not match: "What is a Notice to Appear?" or "What are NTA requirements?".

_NTA_PERSONAL_SIGNAL = re.compile(
    r"\b(?:I\s+received|I\s+got|I\s+have|I\s+was\s+given|I\s+was\s+served"
    r"|we\s+received|we\s+got"
    r"|my\s+NTA|our\s+NTA|after\s+receiving|receiving\s+a\s+Notice\s+to\s+Appear"
    r"|received\s+an?\s+NTA|got\s+an?\s+NTA"
    r"|I(?:'m|\s+am)\s+in\s+removal\s+proceedings)\b",
    re.I,
)
_NTA_TOPIC_SIGNAL = re.compile(
    r"\b(?:NTA|Notice\s+to\s+Appear|removal\s+proceedings|immigration\s+court"
    r"|removal\s+order|EOIR)\b",
    re.I,
)

_NTA_REMOVAL_QUERY = (
    "Notice to Appear NTA removal proceedings immigration court 8 CFR 239.1 "
    "EOIR right to counsel immigration attorney accredited representative "
    "master calendar hearing individual hearing in absentia removal order removal defense "
    "BIA Board of Immigration Appeals I&N Dec. precedent decision"
)

_NTA_REMOVAL_ANSWER_GUIDANCE = (
    "Answer only for a person who has received a Notice to Appear (NTA) and is now "
    "in removal proceedings. "
    "Explain that the NTA initiates formal removal proceedings before immigration "
    "court/EOIR under 8 CFR 239.1. "
    "State clearly that not appearing in immigration court as required can result in "
    "an in absentia removal order. "
    "Strongly recommend consulting a qualified immigration attorney or BIA-accredited "
    "representative as soon as possible. "
    "Mention the right to be represented by counsel at no expense to the government. "
    "Do not mention DSO or school official — those roles are not relevant to removal proceedings. "
    "Do not advise on how to avoid appearing in immigration court. "
    "Do not discuss Form I-751 removal of conditions, naturalization, or unrelated "
    "topics unless directly asked."
)


def understand_query(
    message: str,
    selected_category: str | None = None,  # noqa: ARG001 — reserved for future topic routing
) -> QueryUnderstanding:
    """Classify a user message into a QueryUnderstanding.

    Returns a default fallback (topic='general') when no pattern matches,
    preserving today's retrieval behavior exactly.

    Parameters
    ----------
    message:
        Raw user message, stripped.
    selected_category:
        Optional category already validated by the caller.  Not used in the
        current implementation — reserved for future topic-aware routing.
    """
    text = message.strip()

    # High-risk / humanitarian (priority: nta_removal_high_risk > i485_advance_parole > asylum_ead)
    if _NTA_PERSONAL_SIGNAL.search(text) and _NTA_TOPIC_SIGNAL.search(text):
        return QueryUnderstanding(
            topic="nta_removal_high_risk",
            intent_label="case_specific_or_risk",
            retrieval_query=_NTA_REMOVAL_QUERY,
            preferred_source_families=_NTA_SOURCE_FAMILIES,
            missing_facts=(),
            answer_guidance=_NTA_REMOVAL_ANSWER_GUIDANCE,
        )

    if _I485_PENDING_SIGNAL.search(text) and _TRAVEL_AP_SIGNAL.search(text):
        return QueryUnderstanding(
            topic="i485_advance_parole",
            intent_label="case_specific_or_risk",
            retrieval_query=_I485_AP_QUERY,
            preferred_source_families=_HUMANITARIAN_SOURCE_FAMILIES,
            missing_facts=(),
            answer_guidance=_I485_AP_ANSWER_GUIDANCE,
        )

    if _ASYLUM_SIGNAL.search(text) and _ASYLUM_EAD_WORK_SIGNAL.search(text):
        return QueryUnderstanding(
            topic="asylum_ead",
            intent_label="case_specific_or_risk",
            retrieval_query=_ASYLUM_EAD_QUERY,
            preferred_source_families=_HUMANITARIAN_SOURCE_FAMILIES,
            missing_facts=(),
            answer_guidance=_ASYLUM_EAD_ANSWER_GUIDANCE,
        )

    # F-1 practical training (priority: stem_opt > f1_cpt > f1_opt)
    if _STEM_OPT_SIGNAL.search(text):
        return QueryUnderstanding(
            topic="stem_opt",
            intent_label="general_info",
            retrieval_query=_STEM_OPT_QUERY,
            preferred_source_families=_F1_PRACTICAL_TRAINING_SOURCE_FAMILIES,
            missing_facts=(),
            answer_guidance=_STEM_OPT_ANSWER_GUIDANCE,
        )

    if _CPT_SIGNAL.search(text) and (
        _F1_STUDENT_CONTEXT.search(text) or _OPT_WORK_CONTEXT.search(text)
    ):
        return QueryUnderstanding(
            topic="f1_cpt",
            intent_label="general_info",
            retrieval_query=_F1_CPT_QUERY,
            preferred_source_families=_F1_PRACTICAL_TRAINING_SOURCE_FAMILIES,
            missing_facts=(),
            answer_guidance=_F1_CPT_ANSWER_GUIDANCE,
        )

    if _OPT_SIGNAL.search(text) and _OPT_WORK_CONTEXT.search(text):
        return QueryUnderstanding(
            topic="f1_opt",
            intent_label="general_info",
            retrieval_query=_F1_OPT_QUERY,
            preferred_source_families=_F1_PRACTICAL_TRAINING_SOURCE_FAMILIES,
            missing_facts=(),
            answer_guidance=_F1_OPT_ANSWER_GUIDANCE,
        )

    # L-2 / L-1 spouse work authorization
    has_l1 = bool(_L1_PRINCIPAL_SIGNAL.search(text))
    has_l2 = bool(_L2_DIRECT_SIGNAL.search(text))
    has_spouse = bool(_SPOUSE_FAMILY_SIGNAL.search(text))
    has_work_auth = bool(_WORK_AUTH_SIGNAL.search(text))

    if (has_l1 and has_spouse and has_work_auth) or (has_l2 and has_work_auth):
        return QueryUnderstanding(
            topic="l2_work_authorization",
            intent_label="general_info",
            retrieval_query=_L2_WORK_AUTH_QUERY,
            preferred_source_families=("USCIS Policy Manual",),
            missing_facts=(),
            answer_guidance=_L2_ANSWER_GUIDANCE,
        )

    # Default: no routing applied — caller preserves existing behavior.
    return QueryUnderstanding(
        topic="general",
        intent_label="general_info",
        retrieval_query=text,
        preferred_source_families=(),
        missing_facts=(),
    )


# ---- L-2 post-retrieval context filter -------------------------------------
# Removes contaminating chunks (H-4, naturalization, V visa, LPR spouse, etc.)
# that hybrid retrieval returns when the user asks about L-1/L-2 spouse work.
#
# Priority: keep signal wins over reject signal.
# Neutral result (neither signal matched): kept conservatively.
# Fallback: if filtering would empty the list, return the original list.

_L2_KEEP = re.compile(
    r"L-2S?|L spouses|spouses of L-1 nonimmigrants"
    r"|employment authorized incident to status"
    r"|INA 214\(c\)\(2\)\(E\)"
    r"|Vol\.?\s*10,?\s*Part\s*B,?\s*Ch\.?\s*2",
    re.I,
)

_L2_REJECT = re.compile(
    r"H-4|H-1B|approved Form I-140|AC21"
    r"|U\.S\. citizen spouse|naturalization"
    r"|regularly stationed abroad|I-751"
    r"|V nonimmigrant|lawful permanent residents?"
    r"|T-1 nonimmigrant|T nonimmigrant derivative"
    r"|O-3 dependent|CNMI Investor"
    r"|Temporary Protected Status|\bTPS\b"
    r"|\basylum\b|adjustment application",
    re.I,
)

# ---- F-1 OPT post-retrieval context filter ---------------------------------

_F1_OPT_KEEP = re.compile(
    r"optional\s+practical\s+training|post[- ]?completion\s+opt|\bopt\b"
    r"|214\.2\s*\(\s*f\s*\)|274a\.12\s*\(\s*c\s*\)\s*\(\s*3\s*\)|f[- ]?1\s+(?:student|opt)",
    re.I,
)

_F1_OPT_REJECT = re.compile(
    r"curriculum\s+practical\s+training|\bcpt\b|stem\s+opt|24[- ]?month\s+extension"
    r"|Form\s+I-983|\bH-3\b|\bM-2\b|\bTN\s+(?:visa|status|occupation)\b|adoption|214\.13",
    re.I,
)

# ---- F-1 CPT post-retrieval context filter ---------------------------------

_F1_CPT_KEEP = re.compile(
    r"curriculum\s+practical\s+training|\bcpt\b"
    r"|214\.2\s*\(\s*f\s*\)\s*\(\s*10\s*\)\s*\(\s*i\s*\)"
    r"|\bDSO\b|integral\s+part\s+of\s+(?:the\s+)?established\s+curriculum",
    re.I,
)

_F1_CPT_REJECT = re.compile(
    r"stem\s+opt|24[- ]?month\s+extension|Form\s+I-983|post[- ]?completion\s+opt"
    r"|\bH-3\b|\bM-2\b|\bTN\s+(?:visa|status|occupation)\b|adoption|214\.13|\bSEVIS\s+fee\b",
    re.I,
)

# ---- STEM OPT post-retrieval context filter --------------------------------

_STEM_OPT_KEEP = re.compile(
    r"stem\s+opt|24[- ]?month|Form\s+I-983|Training\s+Plan|E[- ]?Verify"
    r"|214\.2\s*\(\s*f\s*\)\s*\(\s*10\s*\)\s*\(\s*ii\s*\)"
    r"|274a\.12\s*\(\s*c\s*\)\s*\(\s*3\s*\)\s*\(\s*c\s*\)|STEM\s+degree",
    re.I,
)

_STEM_OPT_REJECT = re.compile(
    r"curriculum\s+practical\s+training|\bcpt\b|\bH-3\b|\bM-1\b|\bM-2\b"
    r"|\bTN\s+(?:visa|status|occupation)\b|adoption|214\.13",
    re.I,
)

# Hard rejects for f1_opt: always removed, even when a keep signal is also present.
# Catches SEVIS-fee/214.13 chunks that mention "optional practical training" as context.
_F1_OPT_HARD_REJECT = re.compile(
    r"214\.13|\bSEVIS\s+fee\b|no\s+new\s+fee"
    r"|extension\s+of\s+stay,?\s+transfer"
    r"|\bA-1\s+or\s+A-2\b|foreign\s+government\s+official"
    r"|alien\s+spouse\s+or\s+unmarried\s+dependent\s+child"
    r"|\bCNMI\b|Temporary\s+Protected\s+Status|\bTPS\b"
    r"|274a\.12\s*\(\s*c\s*\)\s*\(\s*19\s*\)"
    r"|pending\s+applicants\s+for\s+Temporary\s+Protected\s+Status",
    re.I,
)

# Hard rejects for stem_opt: always removed, even when a keep signal is also present.
_STEM_OPT_HARD_REJECT = re.compile(
    r"Temporary\s+Protected\s+Status|\bTPS\b"
    r"|274a\.12\s*\(\s*c\s*\)\s*\(\s*19\s*\)"
    r"|pending\s+applicants\s+for\s+Temporary\s+Protected\s+Status"
    r"|\bSEVIS\s+fee\b|214\.13",
    re.I,
)

# A 274a.13 citation without any STEM OPT topic content is a hard reject for stem_opt.
_STEM_OPT_274A13 = re.compile(r"\b274a\.13\b", re.I)
_STEM_OPT_KEY_TERMS = re.compile(
    r"stem\s+opt|I-983|E[- ]?Verify|24[- ]?month"
    r"|214\.2\s*\(\s*f\s*\)\s*\(\s*10\s*\)\s*\(\s*ii\s*\)",
    re.I,
)

# ---- Asylum EAD post-retrieval context filter --------------------------------
# Uses 3-tier strict filter (same as f1_opt/stem_opt).
# Hard rejects: LPR card (I-551), EOIR asylum form reg (1208.3), LPR employment
# auth (274a.12(a)(1)), removal of conditions (I-751), adjustment pending EAD (c)(9).
# Keep: 208.7, 274a.12(c)(8), 180-day, pending asylum EAD content.
# Soft reject: OPT, CPT, H-4, L-2, TPS, DACA, lawful permanent resident.

_ASYLUM_EAD_HARD_REJECT = re.compile(
    r"Form\s+I[- ]?551"
    r"|\b1208\.3\b"
    r"|274a\.12\s*\(\s*a\s*\)\s*\(\s*1\s*\)"
    r"|\bI[- ]?751\b"
    r"|274a\.12\s*\(\s*c\s*\)\s*\(\s*9\s*\)",
    re.I,
)

_ASYLUM_EAD_KEEP = re.compile(
    r"\b208\.7\b"
    r"|274a\.12\s*\(\s*c\s*\)\s*\(\s*8\s*\)"
    r"|180[- ]?day"
    r"|pending\s+asylum.{0,40}(?:ead|employment\s+authorization|work\s+authorization)"
    r"|asylee.{0,50}(?:employment\s+authorization|ead|work\s+authorization)",
    re.I,
)

_ASYLUM_EAD_SOFT_REJECT = re.compile(
    r"\bOPT\b|\bCPT\b|\bH[- ]?4\b|\bL[- ]?2\b"
    r"|Temporary\s+Protected\s+Status|\bTPS\b|\bDACA\b"
    r"|lawful\s+permanent\s+resident",
    re.I,
)

# ---- I-485 advance parole post-retrieval context filter ----------------------
# Binary keep/reject (same as l2, f1_cpt).
# Keep: advance parole, I-131, abandonment, travel document, 245.2.
# Reject: special 1245.x provisions, T nonimmigrant, trafficking, Syria.

_I485_AP_KEEP = re.compile(
    r"\badvance\s+parole\b"
    r"|\bForm\s+I[- ]?131\b|\bI[- ]?131\b"
    r"|\babandonment\b"
    r"|\btravel\s+document\b"
    r"|\b245\.2\b",
    re.I,
)

_I485_AP_HARD_REJECT = re.compile(
    r"\b208\.8\b"                                    # asylum travel limitation (8 CFR)
    r"|\b1208\.8\b"                                  # asylum travel limitation (EOIR)
    r"|\b1245\.(?:7|10|12|13|19|20)\b"               # special adjustment provisions
    r"|\b245\s*\(\s*i\s*\)"                           # 245(i) special adjustment
    r"|\bSupplement\s+A\b"                            # Supplement A to I-485 (245(i))
    r"|\bPublic\s+Law\s+105[- ]?100\b"               # NACARA
    r"|Foreign\s+Operations\s+Appropriations\s+Act"  # NACARA authorizing act
    r"|\bIndochinese\b.{0,60}\bparolee\b"            # NACARA-covered parolees
    r"|\bSoviet\b.{0,60}\bparolee\b"                 # NACARA-covered parolees
    r"|\bSyrian?\b"                                  # Syrian special immigrant
    r"|\bT\s+nonimmigrant\b"                         # T visa (trafficking)
    r"|\btrafficking\s+victim\b"                     # T visa context
    r"|claimed\s+persecution"                        # asylum-specific travel content
    r"|country\s+of\s+claimed\s+persecution",        # asylum-specific travel content
    re.I,
)

# 1245.2 (EOIR adjustment regulation) is a keep only when the snippet also discusses
# I-485/adjustment/advance parole/abandonment — otherwise it is neutral and dropped
# when strong keep results exist.
_I485_AP_1245_2 = re.compile(r"\b1245\.2\b", re.I)
_I485_AP_1245_2_CONTEXT = re.compile(
    r"\bI[- ]?485\b"
    r"|\badjustment\s+of\s+status\b"
    r"|\badvance\s+parole\b"
    r"|\babandonment\b",
    re.I,
)

# ---- NTA / removal high-risk post-retrieval context filter -------------------
# Binary keep/reject.
# Keep: 239., 1239., NTA/removal proceedings/EOIR/in absentia/master calendar.
# Reject: I-751, conditional resident, removal of conditions.

_NTA_REMOVAL_KEEP = re.compile(
    r"\b239\."
    r"|\b1239\."
    r"|notice\s+to\s+appear"
    r"|removal\s+proceedings"
    r"|immigration\s+court"
    r"|\bEOIR\b"
    r"|in\s+absentia"
    r"|removal\s+defense"
    r"|master\s+calendar",
    re.I,
)

_NTA_REMOVAL_REJECT = re.compile(
    r"\bI[- ]?751\b"
    r"|\bconditional\s+(?:resident|permanent\s+resident)\b"
    r"|\bremoval\s+of\s+conditions\b"
    r"|\bVAWA\s+removal\s+of\s+conditions\b",
    re.I,
)


def _result_text(result: object) -> str:
    parts = [
        getattr(result, "citation", "") or "",
        getattr(result, "topic", "") or "",
        getattr(result, "subtopic", "") or "",
        getattr(result, "snippet", "") or "",
    ]
    return " ".join(parts)


def _l2_keep_result(result: object) -> bool:
    text = _result_text(result)
    if _L2_KEEP.search(text):
        return True
    if _L2_REJECT.search(text):
        return False
    return True


def _f1_opt_classify(result: object) -> str:
    """Return 'hard_reject', 'keep', 'soft_reject', or 'neutral' for an f1_opt result."""
    text = _result_text(result)
    if _F1_OPT_HARD_REJECT.search(text):
        return "hard_reject"
    if _F1_OPT_KEEP.search(text):
        return "keep"
    if _F1_OPT_REJECT.search(text):
        return "soft_reject"
    return "neutral"


def _f1_cpt_keep_result(result: object) -> bool:
    text = _result_text(result)
    if _F1_CPT_KEEP.search(text):
        return True
    if _F1_CPT_REJECT.search(text):
        return False
    return True


def _stem_opt_classify(result: object) -> str:
    """Return 'hard_reject', 'keep', 'soft_reject', or 'neutral' for a stem_opt result."""
    text = _result_text(result)
    if _STEM_OPT_HARD_REJECT.search(text):
        return "hard_reject"
    if _STEM_OPT_274A13.search(text) and not _STEM_OPT_KEY_TERMS.search(text):
        return "hard_reject"
    if _STEM_OPT_KEEP.search(text):
        return "keep"
    if _STEM_OPT_REJECT.search(text):
        return "soft_reject"
    return "neutral"


def _apply_strict_filter(results: list, classify_fn) -> list:
    """3-tier filter for f1_opt, stem_opt, and asylum_ead.

    Priority:
    1. hard_reject results are always removed.
    2. If any strong keep results exist, return only those (drop neutrals).
    3. If no strong keeps, return non-rejected results (neutrals only).
    4. If all results were removed, return the original list unchanged.
    """
    classified = [(r, classify_fn(r)) for r in results]
    strong_kept = [r for r, cls in classified if cls == "keep"]
    if strong_kept:
        return strong_kept
    non_rejected = [r for r, cls in classified if cls not in ("hard_reject", "soft_reject")]
    return non_rejected if non_rejected else results


def _asylum_ead_classify(result: object) -> str:
    """Return 'hard_reject', 'keep', 'soft_reject', or 'neutral' for an asylum_ead result."""
    text = _result_text(result)
    if _ASYLUM_EAD_HARD_REJECT.search(text):
        return "hard_reject"
    if _ASYLUM_EAD_KEEP.search(text):
        return "keep"
    if _ASYLUM_EAD_SOFT_REJECT.search(text):
        return "soft_reject"
    return "neutral"


def _i485_ap_classify(result: object) -> str:
    """Return 'hard_reject', 'keep', or 'neutral' for an i485_advance_parole result."""
    text = _result_text(result)
    if _I485_AP_HARD_REJECT.search(text):
        return "hard_reject"
    if _I485_AP_KEEP.search(text):
        return "keep"
    if _I485_AP_1245_2.search(text) and _I485_AP_1245_2_CONTEXT.search(text):
        return "keep"
    return "neutral"


def _nta_removal_keep_result(result: object) -> bool:
    text = _result_text(result)
    if _NTA_REMOVAL_KEEP.search(text):
        return True
    if _NTA_REMOVAL_REJECT.search(text):
        return False
    return True


def filter_results_for_understanding(
    results: list,
    understanding: QueryUnderstanding,
) -> list:
    """Remove topic-contaminating chunks from retrieval results.

    For topic='l2_work_authorization': applies keep/reject signal matching
    across citation, topic, subtopic, and snippet.  Falls back to the
    original list if all results would be removed.

    For all other topics: returns results unchanged.
    """
    if understanding.topic == "l2_work_authorization":
        keep_fn = _l2_keep_result
    elif understanding.topic == "f1_cpt":
        keep_fn = _f1_cpt_keep_result
    elif understanding.topic == "f1_opt":
        return _apply_strict_filter(results, _f1_opt_classify)
    elif understanding.topic == "stem_opt":
        return _apply_strict_filter(results, _stem_opt_classify)
    elif understanding.topic == "asylum_ead":
        return _apply_strict_filter(results, _asylum_ead_classify)
    elif understanding.topic == "i485_advance_parole":
        return _apply_strict_filter(results, _i485_ap_classify)
    elif understanding.topic == "nta_removal_high_risk":
        keep_fn = _nta_removal_keep_result
    else:
        return results
    filtered = [r for r in results if keep_fn(r)]
    return filtered if filtered else results


def rerank_results_by_preferred_source_family(
    results: list,
    understanding: QueryUnderstanding,
) -> list:
    """Softly promote results from preferred source families.

    Adds _SOURCE_FAMILY_BOOST to hybrid_score for results whose source_family
    is in understanding.preferred_source_families, then re-sorts by boosted
    score descending and reassigns ranks 1..N.

    Fallbacks (return results unchanged):
    - results is empty
    - preferred_source_families is empty
    - no result matches any preferred family

    Never removes results; never hard-partitions. Handles both Pydantic
    RetrievalResult (via model_copy) and SimpleNamespace test objects (via
    setattr).
    """
    if not results:
        return results
    if not understanding.preferred_source_families:
        return results

    preferred = set(understanding.preferred_source_families)
    if not any(getattr(r, "source_family", None) in preferred for r in results):
        return results

    def _apply_boost(r: object) -> object:
        if getattr(r, "source_family", None) not in preferred:
            return r
        new_score = getattr(r, "hybrid_score", 0) + _SOURCE_FAMILY_BOOST
        try:
            return r.model_copy(update={"hybrid_score": new_score})
        except AttributeError:
            setattr(r, "hybrid_score", new_score)
            return r

    def _set_rank(r: object, rank: int) -> object:
        try:
            return r.model_copy(update={"rank": rank})
        except AttributeError:
            setattr(r, "rank", rank)
            return r

    boosted = [_apply_boost(r) for r in results]
    boosted.sort(key=lambda r: getattr(r, "hybrid_score", 0), reverse=True)
    return [_set_rank(r, i) for i, r in enumerate(boosted, start=1)]
