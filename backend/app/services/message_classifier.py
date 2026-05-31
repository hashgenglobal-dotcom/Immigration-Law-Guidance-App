"""Lightweight message classifier — runs before retrieval and LLM.

Handles three cases:
1. Casual greetings: return a friendly structured response without RAG or LLM.
2. Criminal matter + action-seeking: return a safe referral response without RAG or LLM.
3. Criminal/fraud/evasion strategy: return a pre-built refusal without RAG or LLM.

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
# These are excluded from refusal and criminal_warning even if they contain
# criminal-matter words.
_CONSEQUENCE_QUESTION_RE = re.compile(
    r"^(what (happens?|are the consequences?|is the penalty|is the punishment"
    r"|are the risks?|could happen|will happen)|what could happen|what will happen"
    r"|what is the risk|what if i)",
    re.I,
)

# Criminal-matter terms that indicate the user has a personal criminal situation.
_CRIMINAL_MATTER_RE = re.compile(
    r"\b("
    r"dui|dwi"
    r"|hit[- ]and[- ]run|hit and run"
    r"|arrest(?:ed)?"
    r"|conviction|convicted"
    r"|criminal (?:charge|case|matter|record|history)"
    r"|theft|robbery|assault|battery|burglary"
    r"|felony|misdemeanor"
    r"|drug (?:charge|offense|arrest|conviction)"
    r"|domestic violence"
    r")\b",
    re.I,
)

# Action/strategy-seeking phrases that indicate the user wants personal guidance
# on what to do — not just general legal information.
_CRIMINAL_ACTION_SEEKING_RE = re.compile(
    r"\b("
    r"what should (?:i|we) do"
    r"|what do i do"
    r"|what can (?:i|we) do"
    r"|how (?:do|should|can) (?:i|we) (?:handle|deal with|proceed|approach)"
    r"|how to (?:handle|deal with|proceed)"
    r"|what are (?:my|our) (?:options|next steps|choices)"
    r"|what (?:is|are) my next steps?"
    r"|advise me"
    r"|help me (?:deal with|handle|navigate)"
    r")\b",
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
        # "how can I / how do I avoid/skip/miss immigration court / court hearing / court date"
        r"\b(how (can i|do i|should i|to))\b.{0,80}\b(avoid|skip|miss)\b"
        r".{0,60}\b(immigration court|court (?:hearing|date|appearance))\b",
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

CRIMINAL_WARNING_ANSWER = (
    "Short answer:\n"
    "This question may involve both criminal and immigration consequences. This assistant cannot "
    "advise you on what to do in a criminal matter or how to handle your specific case.\n\n"
    "What this means:\n"
    "Criminal charges, arrests, and convictions can have serious immigration consequences — "
    "including being found inadmissible or deportable. The right course of action depends on the "
    "specific facts of your criminal case, your current immigration status, and applicable law. "
    "Both the criminal and immigration dimensions require qualified legal counsel.\n\n"
    "Typical next steps:\n"
    "1. Consider speaking with a licensed criminal defense attorney about the criminal aspects of "
    "your situation as soon as possible — ideally before any court appearances or statements.\n"
    "2. Consider consulting a qualified immigration attorney to understand how your situation may "
    "affect your immigration status, benefits, or pending applications.\n"
    "3. If you would like, this assistant can help you prepare general questions to ask your "
    "attorney — just let me know what area you want to focus on.\n\n"
    "Official sources:\n"
    "(No retrieval performed — this response is a referral to qualified counsel, not a "
    "legal information answer.)\n\n"
    "Important caution:\n"
    "This is general information only, not legal advice. Criminal and immigration consequences "
    "can be serious and are highly case-specific. Do not delay speaking with qualified attorneys."
)


def classify_message(message: str) -> str:
    """Return 'greeting', 'criminal_warning', 'refusal', or 'pass' for a user message.

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

    # Consequence questions ask about effects, not strategy — always pass.
    if _CONSEQUENCE_QUESTION_RE.search(text):
        return "pass"

    # Criminal matter + personal action-seeking: user has a criminal situation and
    # is asking what to do. Return a safe referral instead of legal strategy.
    if _CRIMINAL_MATTER_RE.search(text) and _CRIMINAL_ACTION_SEEKING_RE.search(text):
        return "criminal_warning"

    # Refusal: messages seeking strategy for fraud, evasion, or misrepresentation.
    if any(p.search(text) for p in _REFUSAL_PATTERNS):
        return "refusal"

    return "pass"
