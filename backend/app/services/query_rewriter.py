"""
Query rewriter for multi-topic immigration questions.

Takes a user question and:
1. Detects if it contains multiple visa types / topics
2. Splits into focused sub-queries
3. Returns list of queries for parallel retrieval

Uses rule-based detection (fast, no LLM needed for splitting).
LLM rewriting only for ambiguous single-topic queries.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# ── Visa type detection patterns ────────────────────────────────────────────

VISA_PATTERNS: dict[str, list[str]] = {
    "H-1B":          [r"\bh-?1b\b", r"specialty occupation", r"h1b"],
    "H-4":           [r"\bh-?4\b", r"h4 ead", r"h-4 dependent"],
    "H-4 EAD":       [r"h-?4 ead", r"h4ead", r"h-4 employment"],
    "F-1":           [r"\bf-?1\b", r"student visa", r"sevis", r"\bopt\b", r"\bcpt\b"],
    "OPT":           [r"\bopt\b", r"optional practical training", r"stem opt"],
    "J-1":           [r"\bj-?1\b", r"exchange visitor"],
    "L-1":           [r"\bl-?1\b", r"intracompany"],
    "O-1":           [r"\bo-?1\b", r"extraordinary ability"],
    "TN":            [r"\btn\b", r"trade nafta", r"usmca"],
    "asylum":        [r"\basylum\b", r"asylee", r"asylum applicant"],
    "EAD":           [r"\bead\b", r"employment authorization", r"work permit", r"i-765", r"form i-765"],
    "green_card":    [r"green card", r"lawful permanent", r"\blpr\b", r"adjustment of status", r"i-485"],
    "naturalization":[r"naturalization", r"citizenship", r"n-400"],
    "removal":       [r"removal", r"deportation", r"notice to appear"],
    "TPS":           [r"\btps\b", r"temporary protected status"],
    "DACA":          [r"\bdaca\b", r"deferred action"],
    "parole":        [r"\bparole\b", r"advance parole"],
    "cap_gap":       [r"cap.?gap", r"october 1", r"h-1b cap"],
    "221g":          [r"221\(?g\)?", r"blue slip", r"administrative processing"],
    "consular":      [r"consular", r"visa stamp", r"stamping", r"embassy", r"consulate"],
    "I-94":          [r"\bi-94\b", r"admission record"],
    "I-140":         [r"\bi-140\b", r"immigrant petition"],
    "pending":       [r"pending", r"while.*pending", r"application.*pending"],
}

TOPIC_PATTERNS: dict[str, list[str]] = {
    "employment_authorization": [r"can i work", r"authorized to work", r"work.*while", r"continue working", r"start working"],
    "extension":               [r"extend", r"extension", r"renew", r"renewal"],
    "travel":                  [r"travel", r"return.*us", r"leave.*us", r"reenter"],
    "status_maintenance":      [r"maintain.*status", r"out of status", r"status.*expire"],
    "change_employer":         [r"change.*employer", r"new.*employer", r"transfer.*h.?1b"],
    "dependent":               [r"spouse", r"dependent", r"family member", r"child"],
    "interview":               [r"interview", r"stamping", r"consular"],
}


def _find_matches(text: str, patterns: dict[str, list[str]]) -> list[str]:
    text_lower = text.lower()
    matched = []
    for key, pats in patterns.items():
        if any(re.search(p, text_lower) for p in pats):
            matched.append(key)
    return matched


@dataclass
class RewrittenQueries:
    original: str
    sub_queries: list[str]
    detected_visas: list[str]
    detected_topics: list[str]
    is_multi_topic: bool


def rewrite_query(question: str) -> RewrittenQueries:
    """
    Analyze a user question and return focused sub-queries for retrieval.

    For simple single-topic questions, returns the original question.
    For multi-topic questions, splits into focused sub-queries.
    """
    detected_visas = _find_matches(question, VISA_PATTERNS)
    detected_topics = _find_matches(question, TOPIC_PATTERNS)

    # Remove redundant visa tags (H-4 EAD is more specific than H-4 + EAD)
    if "H-4 EAD" in detected_visas:
        detected_visas = [v for v in detected_visas if v not in ("H-4", "EAD")]

    is_multi_topic = (
        len([v for v in detected_visas if v not in ("EAD", "pending")]) >= 2
        or len(detected_topics) >= 2
    )

    if not is_multi_topic:
        return RewrittenQueries(
            original=question,
            sub_queries=[question],
            detected_visas=detected_visas,
            detected_topics=detected_topics,
            is_multi_topic=False,
        )

    sub_queries = _build_sub_queries(question, detected_visas, detected_topics)

    return RewrittenQueries(
        original=question,
        sub_queries=sub_queries,
        detected_visas=detected_visas,
        detected_topics=detected_topics,
        is_multi_topic=True,
    )


def _build_sub_queries(
    question: str,
    visas: list[str],
    topics: list[str],
) -> list[str]:
    """Build focused sub-queries from detected visa types and topics."""
    sub_queries = []

    # Always include original question
    sub_queries.append(question)

    # Build visa-specific queries
    visa_query_map: dict[str, str] = {
        "H-1B":          "H-1B nonimmigrant worker visa regulations employment",
        "H-4":           "H-4 dependent nonimmigrant status regulations",
        "H-4 EAD":       "H-4 EAD employment authorization form I-765 pending renewal",
        "F-1":           "F-1 student visa status regulations SEVIS",
        "OPT":           "F-1 OPT optional practical training employment authorization",
        "asylum":        "asylum application pending employment authorization",
        "EAD":           "employment authorization document I-765 application",
        "green_card":    "adjustment of status lawful permanent resident I-485",
        "naturalization":"naturalization citizenship application N-400",
        "cap_gap":       "H-1B cap gap employment authorization October 1",
        "221g":          "221(g) administrative processing consular visa refusal",
        "consular":      "consular processing visa stamping interview",
        "removal":       "removal proceedings deportation notice to appear",
        "TPS":           "temporary protected status employment authorization",
        "parole":        "advance parole travel document pending application",
        "I-140":         "I-140 immigrant petition approved employment authorization",
    }

    topic_query_map: dict[str, str] = {
        "employment_authorization": "employment authorization work permit while application pending",
        "extension":               "extension of status renewal application pending",
        "travel":                  "travel outside united states reentry return status",
        "change_employer":         "change employer H-1B portability AC21",
        "dependent":               "dependent spouse employment authorization status",
        "interview":               "consular interview visa stamping administrative processing",
    }

    # Add visa-specific sub-queries
    for visa in visas:
        if visa in visa_query_map:
            q = visa_query_map[visa]
            if q not in sub_queries:
                sub_queries.append(q)

    # Add topic-specific sub-queries
    for topic in topics:
        if topic in topic_query_map:
            q = topic_query_map[topic]
            if q not in sub_queries:
                sub_queries.append(q)

    # Special combinations
    q_lower = question.lower()

    # H-4 EAD pending + H-1B extension
    if "H-4 EAD" in visas and "H-1B" in visas:
        sub_queries.append(
            "H-4 EAD automatic extension H-1B extension pending I-765 renewal cap gap"
        )

    # Asylum + EAD
    if "asylum" in visas and ("EAD" in visas or "employment_authorization" in topics):
        sub_queries.append(
            "asylum applicant employment authorization I-765 180 day rule 274a.12(c)(8)"
        )

    # F-1 OPT + STEM
    if "OPT" in visas and "stem" in q_lower:
        sub_queries.append(
            "F-1 STEM OPT 24 month extension employment authorization"
        )

    # 221(g) + H-1B
    if "221g" in visas and "H-1B" in visas:
        sub_queries.append(
            "H-1B visa 221(g) administrative processing consular return status"
        )

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for q in sub_queries:
        if q not in seen:
            seen.add(q)
            unique.append(q)

    # Cap at 4 sub-queries to avoid too much noise
    return unique[:4]


def build_metadata_filter(rewritten: RewrittenQueries) -> dict:
    """
    Build a metadata filter dict from detected visa types and topics.
    Used to boost retrieval precision via tag matching.
    """
    visa_filter = []
    for v in rewritten.detected_visas:
        # Map detected visa keys to the tags stored in legal_chunks.visa_types
        tag_map = {
            "H-1B": "H-1B", "H-4": "H-4", "H-4 EAD": "H-4",
            "F-1": "F-1", "OPT": "F-1", "asylum": "asylum",
            "EAD": "EAD", "green_card": "green_card",
            "naturalization": "naturalization", "TPS": "TPS",
            "DACA": "DACA", "parole": "parole",
        }
        if v in tag_map:
            visa_filter.append(tag_map[v])

    return {
        "visa_types": list(set(visa_filter)),
        "topics": rewritten.detected_topics,
    }
