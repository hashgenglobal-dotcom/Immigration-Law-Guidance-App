"""Guided intake routing for broad immigration questions.

Detects when a user question is too broad for a single retrieval path and
returns clarification options. Category selection is passed on the next
request via ``selected_category`` (in-memory on the client only — never stored).
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ClarificationOption:
    label: str
    value: str


@dataclass(frozen=True)
class ClarificationPayload:
    topic: str
    answer: str
    clarifying_question: str
    options: tuple[ClarificationOption, ...]


# Retrieval-focused query templates keyed by option value.
_CATEGORY_RETRIEVAL_QUERIES: dict[str, str] = {
    "asylum_pending": (
        "Can asylum applicants get work authorization and apply for Form I-765 EAD "
        "8 CFR 208.7 pending asylum"
    ),
    "adjustment_pending": (
        "Employment authorization while adjustment of status Form I-485 is pending "
        "Form I-765 category c9"
    ),
    "f1_opt_stem_opt": (
        "F-1 optional practical training OPT STEM OPT extension employment authorization "
        "Form I-765 8 CFR 214.2 217"
    ),
    "tps": (
        "Temporary Protected Status TPS employment authorization Form I-765 8 CFR 244"
    ),
    "daca": (
        "DACA deferred action employment authorization Form I-765 renewal"
    ),
    "ead_other": (
        "Employment authorization categories Form I-765 8 CFR 274a.12"
    ),
    "asylum_eligibility": (
        "Asylum application eligibility filing deadline Form I-589 8 CFR 208"
    ),
    "asylum_defensive": (
        "Defensive asylum removal proceedings immigration judge Form I-589"
    ),
    "asylum_not_sure": (
        "Asylum application overview eligibility 8 CFR 208 INA 208"
    ),
    "aos_family": (
        "Adjustment of status family-based Form I-485 immediate relative"
    ),
    "aos_employment": (
        "Adjustment of status employment-based Form I-485 priority date"
    ),
    "aos_other": (
        "Adjustment of status eligibility Form I-485 requirements"
    ),
    "naturalization_residence": (
        "Naturalization Form N-400 continuous residence physical presence good moral character"
    ),
    "naturalization_marriage": (
        "Naturalization through marriage to U.S. citizen Form N-400 3 year residence"
    ),
    "naturalization_military": (
        "Naturalization military service INA 328 329"
    ),
    "naturalization_other": (
        "Naturalization eligibility Form N-400 requirements 8 CFR 316"
    ),
    "nta_court": (
        "Notice to Appear removal proceedings immigration court 8 CFR 239 EOIR"
    ),
    "nta_attorney": (
        "Notice to Appear right to counsel removal proceedings"
    ),
    "nta_not_sure": (
        "Notice to Appear removal proceedings what happens next 8 CFR 239"
    ),
    "status_extend": (
        "Extension of nonimmigrant status Form I-539 8 CFR 214"
    ),
    "status_change": (
        "Change of nonimmigrant status Form I-539 eligibility 8 CFR 214"
    ),
    "status_not_sure": (
        "Change or extension of status Form I-539 overview"
    ),
    "travel_aos": (
        "Advance parole travel while adjustment of status I-485 pending Form I-131"
    ),
    "travel_pending_other": (
        "Travel while immigration application pending advance parole 8 CFR 223"
    ),
    "travel_not_sure": (
        "Advance parole travel authorization pending immigration case Form I-131"
    ),
    "family_immediate": (
        "Form I-130 family petition immediate relative spouse parent child"
    ),
    "family_preference": (
        "Form I-130 family preference categories F1 F2 F3 F4"
    ),
    "family_not_sure": (
        "Form I-130 family-based immigration petition overview"
    ),
}

_EAD_OPTIONS = (
    ClarificationOption("Pending asylum", "asylum_pending"),
    ClarificationOption("Adjustment of status pending", "adjustment_pending"),
    ClarificationOption("F-1 OPT / STEM OPT", "f1_opt_stem_opt"),
    ClarificationOption("TPS", "tps"),
    ClarificationOption("DACA", "daca"),
    ClarificationOption("Other / not sure", "ead_other"),
)

_ASYLUM_OPTIONS = (
    ClarificationOption("Affirmative asylum (not in removal)", "asylum_eligibility"),
    ClarificationOption("In removal / immigration court", "asylum_defensive"),
    ClarificationOption("Not sure", "asylum_not_sure"),
)

_AOS_OPTIONS = (
    ClarificationOption("Family-based green card", "aos_family"),
    ClarificationOption("Employment-based green card", "aos_employment"),
    ClarificationOption("Other / not sure", "aos_other"),
)

_NATURALIZATION_OPTIONS = (
    ClarificationOption("General naturalization (5 years)", "naturalization_residence"),
    ClarificationOption("Marriage to U.S. citizen (3 years)", "naturalization_marriage"),
    ClarificationOption("Military service", "naturalization_military"),
    ClarificationOption("Other / not sure", "naturalization_other"),
)

_NTA_OPTIONS = (
    ClarificationOption("What a Notice to Appear means", "nta_court"),
    ClarificationOption("Court hearing / deadlines", "nta_attorney"),
    ClarificationOption("Other / not sure", "nta_not_sure"),
)

_STATUS_OPTIONS = (
    ClarificationOption("Extend current status", "status_extend"),
    ClarificationOption("Change to a different status", "status_change"),
    ClarificationOption("Not sure", "status_not_sure"),
)

_TRAVEL_OPTIONS = (
    ClarificationOption("I-485 adjustment of status pending", "travel_aos"),
    ClarificationOption("Other application pending", "travel_pending_other"),
    ClarificationOption("Not sure", "travel_not_sure"),
)

_FAMILY_OPTIONS = (
    ClarificationOption("Immediate relative (spouse, parent, child)", "family_immediate"),
    ClarificationOption("Family preference category", "family_preference"),
    ClarificationOption("Not sure", "family_not_sure"),
)

_CLARIFICATIONS: dict[str, ClarificationPayload] = {
    "ead": ClarificationPayload(
        topic="ead",
        answer="Employment authorization depends on your current immigration category.",
        clarifying_question="Which category best matches you?",
        options=_EAD_OPTIONS,
    ),
    "asylum": ClarificationPayload(
        topic="asylum",
        answer="Asylum rules depend on whether you are applying affirmatively or in removal proceedings.",
        clarifying_question="Which situation best matches you?",
        options=_ASYLUM_OPTIONS,
    ),
    "aos": ClarificationPayload(
        topic="aos",
        answer="Paths to a green card (lawful permanent residence) depend on how you qualify.",
        clarifying_question="Which path are you asking about?",
        options=_AOS_OPTIONS,
    ),
    "naturalization": ClarificationPayload(
        topic="naturalization",
        answer="U.S. citizenship through naturalization depends on how you qualify.",
        clarifying_question="Which situation best matches you?",
        options=_NATURALIZATION_OPTIONS,
    ),
    "nta": ClarificationPayload(
        topic="nta",
        answer="Next steps after a Notice to Appear depend on your court case and deadlines.",
        clarifying_question="What do you need help with?",
        options=_NTA_OPTIONS,
    ),
    "status_change": ClarificationPayload(
        topic="status_change",
        answer="Changing or extending status depends on your current visa and what you want next.",
        clarifying_question="Which best matches you?",
        options=_STATUS_OPTIONS,
    ),
    "travel": ClarificationPayload(
        topic="travel",
        answer="Travel during a pending case depends on your application type and whether you have advance parole.",
        clarifying_question="Which situation best matches you?",
        options=_TRAVEL_OPTIONS,
    ),
    "family_petition": ClarificationPayload(
        topic="family_petition",
        answer="Family petitions depend on your relationship to the U.S. citizen or permanent resident sponsor.",
        clarifying_question="Which relationship category applies?",
        options=_FAMILY_OPTIONS,
    ),
}

# Specific questions: answer directly without clarification.
_SPECIFIC_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.I)
    for p in (
        r"\basylum applicants?\b.*\b(work authorization|ead|employ)",
        r"\bcan asylum applicants?\b",
        r"\bwhat is a notice to appear\b",
        r"\bwhat is an? rfe\b",
        r"\bwhat is (?:a )?form i-\d+",
        r"\bwhat is advance parole\b",
        r"\bcan tps holders?\b.*\b(work|ead|employ)",
        r"\bhow do i change my address with uscis\b",
        r"\boptional practical training\b.*\b(apply|eligib|work)",
        r"\bstem opt\b.*\b(apply|eligib|extension|work)",
        r"\b8 cfr\b",
        r"\b8 u\.s\.c\b",
        r"\bgood moral character\b.*\bnaturalization\b",
        r"\bcan i travel while i-485 is pending\b",
        r"\bcan i travel while .*adjustment of status\b",
    )
)

_BROAD_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "ead",
        re.compile(
            r"(\bhow do i apply for (?:an? )?ead\b|\bapply for employment authorization\b|"
            r"\bget (?:an? )?ead\b|\bcan i work\b.*\b(?:u\.?s\.?|united states)\b|"
            r"\bwork authorization\b(?!\s+(?:while|under|for)\s+(?:asylum|pending asylum)))",
            re.I,
        ),
    ),
    (
        "asylum",
        re.compile(
            r"(\bcan i apply for asylum\b|\bhow do i apply for asylum\b|"
            r"\bshould i apply for asylum\b)(?!.*\bapplicants?\b)",
            re.I,
        ),
    ),
    (
        "aos",
        re.compile(
            r"(\bhow do i get (?:a )?green card\b|\bget (?:a )?green card\b|"
            r"\blawful permanent resident\b.*\bhow\b|\badjustment of status\b.*\bhow do i\b)(?!.*\bi-485 is pending\b)",
            re.I,
        ),
    ),
    (
        "naturalization",
        re.compile(
            r"(\bhow do i become (?:a )?(?:u\.?s\.? )?citizen\b|\bhow do i get citizenship\b|"
            r"\bbecome (?:a )?citizen\b)(?!.*\bgood moral character\b)",
            re.I,
        ),
    ),
    (
        "nta",
        re.compile(
            r"(\bwhat should i do after (?:receiving )?a notice to appear\b|"
            r"\breceived a notice to appear\b.*\bwhat (?:now|should)\b)",
            re.I,
        ),
    ),
    (
        "status_change",
        re.compile(
            r"(\bcan i change my status\b|\bchange my immigration status\b|"
            r"\bextend my status\b)(?!.*\bform i-539\b)",
            re.I,
        ),
    ),
    (
        "travel",
        re.compile(
            r"\bcan i travel while (?:my |a )?(?:case|application) is pending\b(?!.*\bi-485\b)",
            re.I,
        ),
    ),
    (
        "family_petition",
        re.compile(
            r"(\bhow do i (?:file|submit) (?:a )?form i-130\b|\bfamily petition\b.*\bhow\b)(?!.*\bwhat is form i-130\b)",
            re.I,
        ),
    ),
)


def is_specific_question(message: str) -> bool:
    """Return True when the question is narrow enough to answer directly."""
    text = message.strip().lower()
    if not text:
        return False
    return any(p.search(text) for p in _SPECIFIC_PATTERNS)


def detect_broad_topic(message: str) -> str | None:
    """Return clarification topic key if the message is broad, else None."""
    text = message.strip().lower()
    if not text or is_specific_question(message):
        return None
    for topic, pattern in _BROAD_RULES:
        if pattern.search(text):
            return topic
    return None


def build_clarification(topic: str) -> ClarificationPayload | None:
    return _CLARIFICATIONS.get(topic)


def resolve_retrieval_query(message: str, selected_category: str | None) -> str:
    """Build the retrieval query from the user message and optional category selection."""
    if selected_category:
        template = _CATEGORY_RETRIEVAL_QUERIES.get(selected_category)
        if template:
            return template
    return message.strip()


def is_valid_category_value(value: str) -> bool:
    return value in _CATEGORY_RETRIEVAL_QUERIES
