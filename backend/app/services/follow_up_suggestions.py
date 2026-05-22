"""Grounded follow-up question suggestions for Ask (Phase 2).

Suggestions are derived only from the user's question, answer excerpt, and
retrieved chunk metadata — never from free-form LLM legal knowledge.
"""

from __future__ import annotations

import re

from app.schemas.retrieval import RetrievalResult
from app.services.conversation_context import extract_short_answer_section

_MAX_SUGGESTIONS = 3

_FORM_I_PATTERN = re.compile(r"\bform\s+i-?\s*(\d+[a-z]?)\b", re.I)
_CFR_PATTERN = re.compile(r"\b8\s+cfr\b", re.I)


def _blob_from_results(results: list[RetrievalResult]) -> str:
    parts: list[str] = []
    for r in results[:5]:
        parts.append(r.citation or "")
        parts.append(r.topic or "")
        parts.append(r.subtopic or "")
        parts.append((r.snippet or "")[:200])
    return " ".join(parts).lower()


def _add_unique(out: list[str], seen: set[str], text: str) -> None:
    key = text.strip().lower()
    if not key or key in seen or len(out) >= _MAX_SUGGESTIONS:
        return
    seen.add(key)
    out.append(text.strip())


def suggest_follow_ups(
    *,
    message: str,
    answer: str,
    results: list[RetrievalResult],
) -> list[str]:
    """Return up to 3 short follow-up questions grounded in retrieved material."""
    if not results:
        return []

    out: list[str] = []
    seen: set[str] = set()
    blob = _blob_from_results(results)
    msg_lower = message.strip().lower()
    short = extract_short_answer_section(answer).lower()
    combined = f"{msg_lower} {short} {blob}"

    forms = {m.group(1).replace(" ", "") for m in _FORM_I_PATTERN.finditer(blob + " " + msg_lower)}
    if forms:
        form = sorted(forms)[0]
        _add_unique(
            out,
            seen,
            f"What is Form I-{form.upper()} used for in this context?",
        )

    if any(
        k in combined
        for k in (
            "ead",
            "employment authorization",
            "work authorization",
            "i-765",
        )
    ):
        _add_unique(out, seen, "What if my work authorization application is still pending?")
        _add_unique(out, seen, "Which category of employment authorization might apply to my situation?")

    if any(k in combined for k in ("opt", "f-1", "f1", "214.2", "stem")):
        _add_unique(out, seen, "What are the main rules for OPT work authorization?")
        _add_unique(out, seen, "Can I travel while on OPT?")

    if any(k in combined for k in ("asylum", "208.7", "208")):
        _add_unique(out, seen, "Can asylum applicants apply for employment authorization?")
        _add_unique(out, seen, "What deadlines matter for asylum applications?")

    if any(k in combined for k in ("i-485", "adjustment of status", "green card", "permanent resident")):
        _add_unique(out, seen, "What is adjustment of status and when might it apply?")
        _add_unique(out, seen, "Can I travel while my adjustment application is pending?")

    if any(k in combined for k in ("advance parole", "i-131", "travel")):
        _add_unique(out, seen, "When is advance parole needed for travel during a pending case?")

    if any(k in combined for k in ("naturalization", "n-400", "citizen")):
        _add_unique(out, seen, "What are the basic eligibility requirements for naturalization?")

    if any(k in combined for k in ("notice to appear", "nta", "removal", "immigration court")):
        _add_unique(out, seen, "What is a Notice to Appear and what happens next?")

    if _CFR_PATTERN.search(blob) and len(out) < _MAX_SUGGESTIONS:
        _add_unique(
            out,
            seen,
            "Can you explain the main regulation cited in plain language?",
        )

    if not out:
        top = results[0]
        cite = (top.citation or "the top source").strip()
        _add_unique(out, seen, f"What else does {cite} say about this topic?")

    return out[:_MAX_SUGGESTIONS]
