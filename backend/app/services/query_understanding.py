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
    if understanding.topic != "l2_work_authorization":
        return results
    filtered = [r for r in results if _l2_keep_result(r)]
    return filtered if filtered else results
