"""
Metadata-boosted reranker for retrieved legal chunks.

After hybrid retrieval returns top-N chunks, this reranker:
1. Matches chunk metadata (visa_types, topics) against query intent
2. Boosts relevant chunks, penalizes off-topic ones
3. Re-sorts by boosted score

No LLM calls — pure metadata + score math. Fast on CPU.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.schemas.retrieval import RetrievalResult
from app.services.query_rewriter import RewrittenQueries


# ── Score weights ───────────────────────────────────────────────────────────

VISA_MATCH_BOOST = 0.04       # Per matching visa type
TOPIC_MATCH_BOOST = 0.03      # Per matching topic
FORM_MATCH_BOOST = 0.02       # Per matching form
NO_MATCH_PENALTY = 0.6        # Multiply score by this if zero metadata matches
EXACT_SECTION_BOOST = 0.05    # Boost if chunk citation matches a known section for the visa


# ── Known visa-to-section mappings ──────────────────────────────────────────

VISA_SECTION_MAP: dict[str, list[str]] = {
    "H-1B":          ["214.2(h)", "214.2"],
    "H-4":           ["214.2(h)(9)", "214.2"],
    "EAD":           ["274a.12", "274a.13"],
    "H-4 EAD":       ["274a.12(c)(26)", "274a.12", "214.2(h)(9)(iv)"],
    "F-1":           ["214.2(f)"],
    "OPT":           ["214.2(f)(10)", "274a.12(c)(3)"],
    "asylum":        ["208.", "274a.12(c)(8)"],
    "green_card":    ["245."],
    "naturalization": ["316.", "312."],
    "TPS":           ["244."],
    "removal":       ["239.", "240."],
    "L-1":           ["214.2(l)"],
    "O-1":           ["214.2(o)"],
}

# ── Form detection ──────────────────────────────────────────────────────────

FORM_PATTERNS: dict[str, str] = {
    r"\bi-765\b": "I-765",
    r"\bi-129\b": "I-129",
    r"\bi-140\b": "I-140",
    r"\bi-485\b": "I-485",
    r"\bi-539\b": "I-539",
    r"\bi-589\b": "I-589",
    r"\bi-130\b": "I-130",
    r"\bi-131\b": "I-131",
    r"\bn-400\b": "N-400",
}


def _detect_forms_in_query(query: str) -> list[str]:
    query_lower = query.lower()
    forms = []
    for pattern, form_name in FORM_PATTERNS.items():
        if re.search(pattern, query_lower):
            forms.append(form_name)
    return forms


def _chunk_has_visa_match(chunk: RetrievalResult, visa_types: list[str]) -> int:
    """Count how many visa types from the query match the chunk's metadata."""
    if not hasattr(chunk, 'topic') or not chunk.topic:
        return 0

    chunk_text = f"{chunk.citation} {chunk.topic} {chunk.snippet or ''}"
    chunk_lower = chunk_text.lower()

    matches = 0
    for visa in visa_types:
        visa_lower = visa.lower().replace("-", "").replace(" ", "")
        # Check direct text match
        if visa_lower in chunk_lower.replace("-", "").replace(" ", ""):
            matches += 1
            continue
        # Check section match
        if visa in VISA_SECTION_MAP:
            for section in VISA_SECTION_MAP[visa]:
                if section.lower() in chunk_lower:
                    matches += 1
                    break
    return matches


def _chunk_has_topic_match(chunk: RetrievalResult, topics: list[str]) -> int:
    """Count how many topics from the query match the chunk."""
    if not chunk.topic and not chunk.snippet:
        return 0

    chunk_text = f"{chunk.topic or ''} {chunk.snippet or ''}"
    chunk_lower = chunk_text.lower()

    topic_keywords: dict[str, list[str]] = {
        "employment_authorization": ["employment authorization", "authorized to work", "work permit", "ead"],
        "extension":               ["extension", "renew", "renewal"],
        "travel":                  ["travel", "advance parole", "reentry"],
        "change_employer":         ["change employer", "portability"],
        "dependent":               ["spouse", "dependent", "h-4"],
        "interview":               ["interview", "consular", "stamping"],
        "status_maintenance":      ["maintain status", "out of status"],
    }

    matches = 0
    for topic in topics:
        if topic in topic_keywords:
            if any(kw in chunk_lower for kw in topic_keywords[topic]):
                matches += 1
    return matches


def _chunk_has_form_match(chunk: RetrievalResult, forms: list[str]) -> int:
    """Count how many forms from the query appear in the chunk."""
    if not chunk.snippet and not chunk.citation:
        return 0

    chunk_text = f"{chunk.citation} {chunk.snippet or ''}"
    chunk_lower = chunk_text.lower()

    matches = 0
    for form in forms:
        if form.lower() in chunk_lower:
            matches += 1
    return matches


def _section_match_boost(chunk: RetrievalResult, visa_types: list[str]) -> float:
    """Extra boost if chunk citation directly matches a known section for the visa."""
    citation_lower = chunk.citation.lower() if chunk.citation else ""

    for visa in visa_types:
        if visa in VISA_SECTION_MAP:
            for section in VISA_SECTION_MAP[visa]:
                if section.lower() in citation_lower:
                    return EXACT_SECTION_BOOST
    return 0.0


def rerank_results(
    results: list[RetrievalResult],
    rewritten: RewrittenQueries,
    query: str,
) -> list[RetrievalResult]:
    """
    Rerank retrieval results using metadata matching.

    Boosts chunks whose visa_types, topics, and forms match the query.
    Penalizes chunks with no metadata overlap.

    Returns re-sorted results with updated hybrid_score.
    """
    if not results:
        return results

    visa_types = rewritten.detected_visas
    topics = rewritten.detected_topics
    forms = _detect_forms_in_query(query)

    scored: list[tuple[float, RetrievalResult]] = []

    for r in results:
        base_score = r.hybrid_score

        visa_matches = _chunk_has_visa_match(r, visa_types)
        topic_matches = _chunk_has_topic_match(r, topics)
        form_matches = _chunk_has_form_match(r, forms)

        total_matches = visa_matches + topic_matches + form_matches

        # Calculate boost
        boost = (
            visa_matches * VISA_MATCH_BOOST
            + topic_matches * TOPIC_MATCH_BOOST
            + form_matches * FORM_MATCH_BOOST
            + _section_match_boost(r, visa_types)
        )

        if total_matches == 0:
            # Penalize chunks with no metadata overlap
            new_score = base_score * NO_MATCH_PENALTY
        else:
            new_score = base_score + boost

        scored.append((new_score, r))

    # Sort by new score descending
    scored.sort(key=lambda x: x[0], reverse=True)

    # Rebuild results with updated scores and ranks
    reranked = []
    for rank, (new_score, r) in enumerate(scored, 1):
        reranked.append(RetrievalResult(
            rank=rank,
            chunk_id=r.chunk_id,
            citation=r.citation,
            topic=r.topic,
            subtopic=r.subtopic,
            risk_level=r.risk_level,
            official_url=r.official_url,
            hybrid_score=new_score,
            snippet=r.snippet,
            vector_rank=r.vector_rank,
            keyword_rank=r.keyword_rank,
            vector_distance=r.vector_distance,
            keyword_score=r.keyword_score,
            dataset_version=r.dataset_version,
            source_family=r.source_family,
        ))

    return reranked
