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


def ensure_structured_answer(answer: str, *, high_risk: bool) -> str:
    """Light post-processing if the model omitted section headers."""
    normalized = normalize_section_headers(answer)
    if has_required_sections(normalized):
        return normalized

    caution = (
        "This is general information from the retrieved sources only, not legal advice. "
        "You may wish to consult a qualified immigration attorney for your situation."
    )
    if high_risk:
        caution += (
            " This topic can have serious consequences if deadlines or court dates are missed. "
            "Consider speaking with a qualified immigration attorney promptly."
        )

    return (
        "Short answer:\n"
        f"{normalized}\n\n"
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
