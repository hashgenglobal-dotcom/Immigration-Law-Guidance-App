"""Structured chat answer formatting for MVP (mobile-friendly sections)."""

from __future__ import annotations

import re

from app.schemas.retrieval import RetrievalResult

# User question + retrieval signals that need stronger caution language.
_HIGH_RISK_QUERY_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.I)
    for p in (
        r"\bnotice to appear\b",
        r"\bnta\b",
        r"\bremoval\b",
        r"\bdeportation\b",
        r"\bimmigration court\b",
        r"\bcourt hearing\b",
        r"\basylum\b.*\b(deadline|one year|1 year|barred)\b",
        r"\b(one year|1 year)\b.*\basylum\b",
        r"\bunlawful presence\b",
        r"\boverstay\b",
        r"\bvisa overstay\b",
        r"\bcriminal\b",
        r"\bfraud\b",
        r"\bmisrepresent\b",
        r"\bprior denial\b",
        r"\bdenied\b.*\b(visa|petition|application)\b",
        r"\bdetention\b",
        r"\bice\b.*\b(custody|detain)\b",
    )
)

_SECTION_HEADERS = (
    "Short answer:",
    "What this means:",
    "Typical next steps:",
    "Official sources:",
    "Important caution:",
)

_WEAK_RETRIEVAL_SCORE_THRESHOLD = 0.017

# Matches informational questions about criminal grounds of inadmissibility or deportability.
# Used to inject DUI/offense-specific caution into the system prompt so the LLM does not
# overstate that a particular offense automatically constitutes an aggravated felony or CIMT.
_CRIMINAL_INFO_QUERY_RE = re.compile(
    r"("
    r"\bcriminal\b.{0,60}\b(?:inadmissib\w*|deportab\w*|grounds?|bar)\b"
    r"|\b(?:dui|dwi|felony|misdemeanor|conviction|cimt)\b.{0,100}"
    r"\b(?:immigration|visa|green\s*card|inadmissib\w*|deportab\w*|naturalization)\b"
    r"|\bmoral\s+turpitude\b"
    r"|\b212\s*\(\s*a\s*\)\s*\(\s*2\s*\)\b|\b237\s*\(\s*a\s*\)\s*\(\s*2\s*\)\b"
    r"|\bcriminal\s+grounds?\b|\bcriminal\s+inadmissibility\b|\bcriminal\s+deportability\b"
    r"|\binadmissib\w+.{0,80}\b(?:criminal|crime|felony|conviction|dui)\b"
    r"|\bdeportab\w+.{0,80}\b(?:criminal|crime|felony|conviction|dui)\b"
    r"|\b(?:what|which)\s+crimes?\b.{0,80}\b(?:inadmissib\w*|ineligible|bar|deportab\w*)\b"
    r")",
    re.I,
)


def is_criminal_info_query(message: str) -> bool:
    """Return True for informational questions about criminal grounds of inadmissibility/deportability."""
    return bool(_CRIMINAL_INFO_QUERY_RE.search(message.strip()))


# Matches informational "can DUI/DWI affect immigration" questions.
# Action-seeking DUI messages (criminal_warning) are filtered by message_classifier before this runs.
_DUI_INFO_QUERY_RE = re.compile(
    r"("
    r"\b(?:dui|dwi)\b.{0,100}"
    r"\b(?:affect|impact|immigration|visa|green\s*card|inadmissib\w*|deportab\w*"
    r"|naturalization|citizenship|removal|deportation|status|bar)\b"
    r"|\b(?:immigration|visa|green\s*card|inadmissib\w*|deportab\w*"
    r"|naturalization|citizenship|removal|deportation)\b.{0,100}\b(?:dui|dwi)\b"
    r")",
    re.I,
)


def is_dui_info_query(message: str) -> bool:
    """Return True for informational questions about DUI/DWI and immigration consequences."""
    return bool(_DUI_INFO_QUERY_RE.search(message.strip()))


# ---- H-4 FAQ bypass detectors -------------------------------------------

# Broad informational questions about H-4 process/visa/status (not case-specific).
_H4_PROCESS_FAQ_RE = re.compile(
    r"("
    r"\bwhat\s+is\b.{0,80}\bh[- ]?4\b"
    r"|\bwhat\s+are\b.{0,80}\bh[- ]?4\b"
    r"|\bhow\s+does\b.{0,80}\bh[- ]?4\b"
    r"|\bexplain\b.{0,60}\bh[- ]?4\b"
    r"|\bh[- ]?4\s+(?:visa\s+)?process\b"
    r"|\bh[- ]?4\s+(?:visa|status|dependent)\b"
    r"|\bwhat\s+are\s+the\s+(?:requirements?|eligib\w*)\s+for\s+(?:an?\s+)?h[- ]?4\b"
    r"|\bhow\s+do\s+(?:i|you)\b.{0,80}\bh[- ]?4\b"
    r")",
    re.I,
)

# Broad informational questions about H-4 EAD/employment authorization (not case-specific).
# Must be checked BEFORE _H4_PROCESS_FAQ_RE because both match queries mentioning H-4.
_H4_EAD_FAQ_RE = re.compile(
    r"("
    r"\bwhat\s+is\b.{0,80}\bh[- ]?4\b.{0,80}\b(?:ead|employment\s+authorization|work\s+authorization)\b"
    r"|\bwhat\s+is\s+h[- ]?4\s+ead\b"
    r"|\bhow\s+does\b.{0,80}\bh[- ]?4\b.{0,100}\b(?:ead|employment\s+authorization)\b"
    r"|\bhow\s+does\b.{0,80}\b(?:ead|employment\s+authorization)\b.{0,80}\bh[- ]?4\b"
    r"|\bh[- ]?4\s+ead\b"
    r"|\bh[- ]?4\b.{0,80}\b(?:ead|employment\s+authorization)\b.{0,80}"
    r"\b(?:requirements?|eligib\w*|process|overview)\b"
    r"|\bcan\s+h[- ]?4\b.{0,80}\bwork\b"
    r"|\bhow\s+do\b.{0,80}\bh[- ]?4\b.{0,80}\b(?:get|obtain)\b"
    r".{0,80}\b(?:ead|employment\s+authorization|work\s+authorization)\b"
    r"|\bh[- ]?4\s+(?:employment|work)\s+authorization\b"
    r")",
    re.I,
)

# Excludes personal/case-specific H-4 questions from FAQ bypass.
_H4_FAQ_EXCLUSION_RE = re.compile(
    r"("
    r"\bmy\s+h[- ]?4\b"
    r"|\bmy\s+(?:application|case|status|visa|petition)\b"
    r"|\bh[- ]?4\b.{0,80}\b(?:denied|rejected|expired|rfe)\b"
    r"|\b(?:denied|rejected)\b.{0,80}\bh[- ]?4\b"
    r"|\bwhat\s+should\s+i\s+do\b"
    r"|\bi\s+(?:was|have\s+been)\s+(?:denied|rejected)\b"
    r"|\bhelp\s+(?:me|with)\s+my\b"
    r")",
    re.I,
)


def is_h4_process_faq_query(message: str) -> bool:
    """Return True for broad informational H-4 process/visa/status questions.

    Returns False for case-specific questions (denials, personal possessives, RFEs).
    """
    text = message.strip()
    if _H4_FAQ_EXCLUSION_RE.search(text):
        return False
    return bool(_H4_PROCESS_FAQ_RE.search(text))


def is_h4_ead_faq_query(message: str) -> bool:
    """Return True for broad informational H-4 EAD/employment authorization questions.

    Returns False for case-specific questions (denials, personal possessives, RFEs).
    """
    text = message.strip()
    if _H4_FAQ_EXCLUSION_RE.search(text):
        return False
    return bool(_H4_EAD_FAQ_RE.search(text))


# ---- Answer intent classifier -------------------------------------------

# "What is X?", "What are X?", "What does X mean?", "Explain X", "Tell me about X"
_DEFINITIONAL_RE = re.compile(
    r"^\s*(?:what\s+is\b|what\s+are\b|what\s+does\b|explain\b|define\b|"
    r"how\s+is\b|tell\s+me\s+about\b)",
    re.I,
)

# "How do I?", "How does X work?", "How can I?", "What is the process?", "What are the steps?"
_PROCESS_QUESTION_RE = re.compile(
    r"^\s*(?:how\s+do\s+i\b|how\s+does\b|how\s+can\s+i\b|how\s+would\s+i\b|"
    r"how\s+to\b|what\s+are\s+the\s+steps\b|what\s+is\s+the\s+process\b)",
    re.I,
)

# Personal situation or case-specific risk signals.
_PERSONAL_RISK_RE = re.compile(
    r"(?:"
    r"\bmy\s+(?:case|application|status|record|visa|petition|appeal|denial)\b"
    r"|\bi\s+(?:was\s+denied|have\s+been\s+denied|was\s+arrested|"
    r"have\s+an?\s+arrest\b|have\s+a\s+conviction\b|have\s+a\s+criminal\s+record\b|"
    r"overstayed\b|am\s+detained\b)"
    r"|\bprior\s+(?:denial|refusal|conviction|arrest)\b"
    r"|\bunlawful\s+presence\b|\boverstay(?:ed|ing)?\b|\bcriminal\s+record\b"
    r"|\bfraud\b|\bmisrepresent\w*\b"
    r")",
    re.I,
)


def classify_answer_intent(message: str) -> str:
    """Return 'general_info', 'process_info', or 'case_specific_or_risk'.

    Controls attorney-referral tone in Typical next steps.
    is_high_risk_topic() is a separate, higher-priority safety check that
    overrides this for NTA, removal, criminal, fraud, and similar topics.
    """
    text = message.strip()
    if _PERSONAL_RISK_RE.search(text):
        return "case_specific_or_risk"
    if _DEFINITIONAL_RE.search(text):
        return "general_info"
    if _PROCESS_QUESTION_RE.search(text):
        return "process_info"
    return "general_info"


def is_high_risk_topic(
    message: str,
    results: list[RetrievalResult] | None = None,
) -> bool:
    """Return True when the question or top sources involve high-risk immigration topics."""
    text = message.strip().lower()
    if any(p.search(text) for p in _HIGH_RISK_QUERY_PATTERNS):
        return True
    if results:
        combined = " ".join(
            (r.citation or "")
            + " "
            + (r.topic or "")
            + " "
            + (r.subtopic or "")
            + " "
            + (r.snippet or "")[:200]
            for r in results[:3]
        ).lower()
        if any(p.search(combined) for p in _HIGH_RISK_QUERY_PATTERNS):
            return True
    return False


def retrieval_looks_weak(results: list[RetrievalResult]) -> bool:
    """Heuristic: top fused scores are low or snippets are very thin."""
    if not results:
        return True
    if results[0].hybrid_score < _WEAK_RETRIEVAL_SCORE_THRESHOLD:
        return True
    thin = sum(1 for r in results[:5] if len((r.snippet or "").strip()) < 80)
    return thin >= 3


def build_format_system_addon(
    *,
    high_risk: bool,
    weak_sources: bool,
    selected_category: str | None,
    criminal_info: bool = False,
    answer_intent: str = "general_info",
) -> str:
    """Extra system instructions for structured, plain-language answers."""
    lines = [
        "STRUCTURED ANSWER FORMAT (required for every direct answer):",
        "Use exactly these section headers in this order. Keep each section brief for mobile.",
        "",
        "Short answer:",
        "(1–3 short sentences in plain language.)",
        "",
        "What this means:",
        "(2–4 short sentences explaining the idea for a non-expert.)",
        "",
        "Typical next steps:",
        "1. (only steps supported by the retrieved sources)",
        "2. (add a second step if supported)",
        "3. (optional third step — omit extra steps if sources do not support them)",
        "",
        "Official sources:",
        "(List the exact citation strings you used, one per line, from the retrieved sources.)",
        "",
        "Important caution:",
        "(Brief limits on what the sources do and do not cover.)",
        "",
        "STYLE RULES:",
        "- Never say \"you are eligible\" or guarantee an outcome. Use phrasing like "
        "\"you may be eligible depending on your situation and the evidence in your case.\"",
        "- Do not give legal advice, do not act as the user's lawyer, and do not tell the user "
        "what they must do in their specific case.",
        "- Do not include immigration scenarios unrelated to the question.",
        "- Do not over-explain or copy long statutory text.",
        "- This is general legal information only, not legal advice.",
    ]

    # Next-steps tone: practical for informational questions, hedged for personal/risk questions.
    if not high_risk and answer_intent in ("general_info", "process_info"):
        lines.append(
            "- In Typical next steps, use practical, informational language. Describe concrete "
            "steps to understand or begin the process — for example: 'Review the official USCIS "
            "instructions for the relevant form on uscis.gov', 'Identify whether the applicant "
            "is inside or outside the U.S.', 'Check the official eligibility criteria in the "
            "sources cited above'. You may include a step to consult a qualified immigration "
            "attorney for complex or unusual cases, but do not make attorney consultation the "
            "only step."
        )
    else:
        lines.append(
            "- In Typical next steps, use hedged language: prefer 'You may need to discuss [X] with a "
            "qualified immigration attorney, DSO, or accredited representative' or 'Consider asking "
            "whether [Form/Action] is required before proceeding'. Do not write direct commands like "
            "'File Form X', 'Submit', 'Apply for', or 'Do X' — users must make their own decisions "
            "with qualified counsel."
        )
    if selected_category:
        lines.append(
            f"- The user already selected category \"{selected_category}\". "
            "Answer only for that pathway; do not survey unrelated categories."
        )
    if weak_sources:
        lines.append(
            "- Source coverage for this question appears limited in the retrieved material. "
            "In Important caution, state clearly that the available sources may not fully "
            "address the question and the user should verify with official USCIS/DHS materials "
            "or a qualified immigration attorney."
        )
    if high_risk:
        lines.append(
            "- HIGH-RISK TOPIC: In Important caution, state that mistakes or missed deadlines "
            "can have serious consequences, and strongly recommend consulting a qualified "
            "immigration attorney promptly. If the topic involves a Notice to Appear, removal, "
            "or court, mention appearing as required and not ignoring government notices."
        )
    if criminal_info:
        lines.append(
            "- CRIMINAL IMMIGRATION GROUNDS: Do not state that a specific offense (such as a DUI, "
            "misdemeanor, or any particular crime) is automatically or generally an aggravated felony "
            "or a crime involving moral turpitude. Whether a conviction constitutes a ground of "
            "inadmissibility or deportability depends on the specific offense, sentence imposed, "
            "applicable state law, and the facts of the individual case. Use hedged language such as "
            "'may constitute' or 'could be considered' rather than absolute statements. "
            "Always recommend consulting a qualified immigration attorney for any offense-specific question."
        )
    return "\n".join(lines)


def normalize_section_headers(answer: str) -> str:
    """Normalize common LLM header variants to the canonical section labels."""
    text = answer.strip()
    replacements = (
        (r"(?im)^\s*short answer\s*:?\s*$", "Short answer:"),
        (r"(?im)^\s*what this means\s*:?\s*$", "What this means:"),
        (r"(?im)^\s*typical next steps\s*:?\s*$", "Typical next steps:"),
        (r"(?im)^\s*official sources\s*:?\s*$", "Official sources:"),
        (r"(?im)^\s*important caution\s*:?\s*$", "Important caution:"),
    )
    for pattern, header in replacements:
        text = re.sub(pattern, header, text)
    return text


def has_required_sections(answer: str) -> bool:
    lower = answer.lower()
    return all(h.lower() in lower for h in _SECTION_HEADERS)


def _deduplicate_sections(text: str) -> str:
    """Remove duplicate required section headers, keeping first non-empty content per header."""
    lower = text.lower()
    if not any(lower.count(h.lower()) > 1 for h in _SECTION_HEADERS):
        return text

    header_pat = re.compile(
        r'^(' + '|'.join(re.escape(h) for h in _SECTION_HEADERS) + r')[ \t]*$',
        re.MULTILINE,
    )
    matches = list(header_pat.finditer(text))
    if len(matches) < 2:
        return text

    preamble = text[: matches[0].start()].strip()

    raw: list[tuple[str, str]] = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        raw.append((m.group(1), text[m.end() : end].strip()))

    best: dict[str, str] = {}
    order: list[str] = []
    for header, content in raw:
        if header not in best:
            best[header] = content
            order.append(header)
        elif content.strip() and not best[header].strip():
            best[header] = content

    parts: list[str] = []
    if preamble:
        parts.append(preamble)
    for header in order:
        c = best[header]
        parts.append(f"{header}\n{c}" if c else header)

    return "\n\n".join(parts)


def ensure_structured_answer(answer: str, *, high_risk: bool) -> str:
    """Post-process LLM answer: normalize headers, deduplicate, add missing caution, or wrap if unstructured."""
    normalized = normalize_section_headers(answer)
    deduped = _deduplicate_sections(normalized)

    if has_required_sections(deduped):
        return deduped

    caution = (
        "This is general information from the retrieved sources only, not legal advice. "
        "You may wish to consult a qualified immigration attorney for your situation."
    )
    if high_risk:
        caution += (
            " This topic can have serious consequences if deadlines or court dates are missed. "
            "Consider speaking with a qualified immigration attorney promptly."
        )

    lower = deduped.lower()
    if "short answer:" in lower and "important caution:" not in lower:
        return deduped.rstrip() + f"\n\nImportant caution:\n{caution}"

    return (
        "Short answer:\n"
        f"{deduped}\n\n"
        "What this means:\n"
        "See the short answer above.\n\n"
        "Typical next steps:\n"
        "1. Review the official sources listed in this app.\n"
        "2. Confirm requirements on the official government pages cited.\n"
        "3. Consult a qualified immigration attorney if your situation is urgent or complex.\n\n"
        "Official sources:\n"
        "(See citations below.)\n\n"
        f"Important caution:\n{caution}"
    )
