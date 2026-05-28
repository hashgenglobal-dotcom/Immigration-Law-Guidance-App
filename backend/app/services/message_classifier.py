"""Lightweight message classifier — runs before retrieval and LLM.

Handles two cases:
1. Casual greetings: return a friendly structured response without RAG or LLM.
2. Criminal/fraud/evasion strategy: return a pre-built refusal without RAG or LLM.

Patterns are deliberately narrow to avoid false positives on legitimate
legal-information questions like "What is unlawful presence?" or
"What happens if I overstay?".
"""

from __future__ import annotations

import re

# Messages longer than this are almost never pure casual greetings.
_MAX_GREETING_LEN = 80

_GREETING_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.I)
    for p in (
        r"^(hi|hello|hey|hiya|howdy)[!.,? ]*$",
        r"^(thanks|thank you|thank u|ty)[!.,? ]*$",
        r"^how are you( doing| today)?[?!.,]*$",
        r"^(good morning|good afternoon|good evening|good day)[!.,? ]*$",
        r"^(greetings|salutations)[!.,? ]*$",
        r"^(ok|okay|got it|i see|understood|great|perfect|sounds good)[!.,? ]*$",
    )
)

# Matches questions that seek consequences/information, never strategy.
# These are excluded from refusal even if they contain deceptive-verb words.
_CONSEQUENCE_QUESTION_RE = re.compile(
    r"^(what (happens?|are the consequences?|is the penalty|is the punishment"
    r"|are the risks?|could happen|will happen)|what could happen|what will happen"
    r"|what is the risk|what if i)",
    re.I,
)

# Refusal patterns: seek strategy for fraud/evasion/misrepresentation.
# Each requires both an intent signal AND an immigration-context anchor
# to avoid catching unrelated or informational uses.
_REFUSAL_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.I)
    for p in (
        # "hide X from USCIS/immigration/officer"
        r"\bhide\b.{0,80}\bfrom\b.{0,50}\b(uscis|immigration|dhs|cbp|ice|officer|agent|government)\b",
        # "how do I / want to conceal/omit/cover up criminal record"
        r"\b(how (do i|can i|should i|could i|to)|want to|trying to)\b"
        r".{0,60}\b(conceal|omit|hide|cover up)\b.{0,60}"
        r"\b(arrest|conviction|criminal|record|charge|removal|deportation)\b",
        # "lie on/about application/form/visa" (strategy phrasing, not consequence)
        r"\b(how (do i|can i|should i|could i)|is it (ok|okay|possible|safe) to"
        r"|can i|trying to)\b.{0,80}\b(lie|lying)\b.{0,60}"
        r"\b(application|form|i-485|i-131|n-400|visa|uscis|interview)\b",
        # "lie about [criminal/arrest] on application"
        r"\blie\b.{0,40}\b(about|on)\b.{0,40}"
        r"\b(application|form|i-485|i-131|n-400|visa|immigration form)\b",
        # "can I lie about [my arrest/conviction/criminal/deportation]"
        r"\bcan i\b.{0,60}\blie\b.{0,30}\b(about|my)\b.{0,60}"
        r"\b(arrest|conviction|criminal|deportation|removal|felony|misdemeanor)\b",
        # "fake/forge/falsify documents"
        r"\b(fake|forge|forgery|falsif|fabricat)\b.{0,60}"
        r"\b(documents?|id|passport|visa|records?|certificate|papers?|supporting)\b",
        # "how to misrepresent" (strategy-seeking only)
        r"\b(how (do i|can i|should i|to)|want to|trying to)\b.{0,60}\bmisrepresent\b",
        # "evade ICE/enforcement/deportation"
        r"\bevade\b.{0,60}\b(ice|immigration enforcement|deportation|removal|officer|agent)\b",
        # "how do I / can I avoid/escape ICE/deportation"
        r"\b(how (do i|can i|should i|to))\b.{0,60}\b(avoid|evade|escape)\b.{0,60}"
        r"\b(ice|deportation|removal|enforcement)\b",
        # "escape detention/ICE/custody"
        r"\bescape\b.{0,50}\b(ice|detention|custody|removal|deportation|immigration officers?)\b",
        # "hide/conceal/omit [criminal record] on/from [application/green card]"
        r"\b(hide|conceal|omit)\b.{0,80}"
        r"\b(arrest|criminal|conviction|charge|felony|misdemeanor|record)\b.{0,80}"
        r"\b(application|form|green card|uscis|visa|immigration)\b",
    )
)

# Pre-built 5-section answer texts.
# Format mirrors the structured prompt output so _to_payload_2 in the route
# layer parses them correctly into short_answer / eligibility_checklist / etc.

GREETING_ANSWER = (
    "Short answer:\n"
    "Hello! I'm here to help with U.S. immigration legal information. Feel free to ask "
    "about visas, work authorization, adjustment of status, asylum, naturalization, and more.\n\n"
    "What this means:\n"
    "This assistant provides general immigration information grounded in official U.S. government "
    "sources such as USCIS, the Code of Federal Regulations, and the Immigration and Nationality Act.\n\n"
    "Typical next steps:\n"
    "1. Ask your immigration question in as much detail as you can.\n"
    "2. Review the official sources cited with each answer to verify the information.\n"
    "3. Consult a qualified immigration attorney or accredited representative for case-specific guidance.\n\n"
    "Official sources:\n"
    "(No retrieval needed for this response.)\n\n"
    "Important caution:\n"
    "This assistant provides general legal information only, not legal advice, and does not create "
    "an attorney-client relationship. For case-specific guidance, consult a qualified immigration "
    "attorney or accredited representative."
)

REFUSAL_ANSWER = (
    "Short answer:\n"
    "I'm not able to provide guidance on hiding information from USCIS, misrepresenting facts "
    "on immigration forms, or evading immigration enforcement.\n\n"
    "What this means:\n"
    "Providing false information on USCIS applications, lying to immigration officers, or evading "
    "immigration enforcement are federal offenses. Consequences can include permanent bars to "
    "immigration benefits, removal from the United States, and criminal prosecution.\n\n"
    "Typical next steps:\n"
    "1. Consult a licensed immigration attorney or accredited representative about lawful options "
    "in your situation.\n"
    "2. An attorney can advise you honestly about your rights and legal paths forward under current law.\n\n"
    "Official sources:\n"
    "(No retrieval needed for this response.)\n\n"
    "Important caution:\n"
    "This is general legal information only, not legal advice. If you are facing removal or other "
    "enforcement action, speaking with a qualified immigration attorney promptly is strongly recommended."
)


def classify_message(message: str) -> str:
    """Return 'greeting', 'refusal', or 'pass' for a user message.

    Called before retrieval and LLM to short-circuit casual and harmful requests.
    Patterns are intentionally narrow — legitimate legal-information questions
    (e.g. "What is unlawful presence?") always return 'pass'.
    """
    text = message.strip()
    if not text:
        return "pass"

    # Greeting: short messages matching exact casual-greeting patterns.
    if len(text) <= _MAX_GREETING_LEN and any(p.search(text) for p in _GREETING_PATTERNS):
        return "greeting"

    # Consequence questions ask about effects, not strategy — never refused.
    if _CONSEQUENCE_QUESTION_RE.search(text):
        return "pass"

    # Refusal: messages seeking strategy for fraud, evasion, or misrepresentation.
    if any(p.search(text) for p in _REFUSAL_PATTERNS):
        return "refusal"

    return "pass"
