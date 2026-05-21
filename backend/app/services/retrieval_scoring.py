"""MVP retrieval relevance boosts and authority weighting (post-RRF reranking).

Designed to improve top-3 citation quality for common immigration questions without
hard-coding exact rank-1 citations. Uses flexible phrase/topic/form signals derived
from the user query and chunk metadata.
"""

from __future__ import annotations

import re

# Post-RRF additive boosts (keep small relative to RRF scores ~0.015–0.035).
_MAX_BOOST = 0.028
_BIA_PENALTY = -0.022

_BIA_CITATION_RE = re.compile(r"\bBIA\b|I&N Dec\.", re.I)
_FORM_RE = re.compile(r"\bi[- ]?(\d{3,4}[a-z]?)\b", re.I)

# Known multi-word phrases → optional citation/topic needles (substring match).
_PHRASE_SIGNALS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("notice to appear", ("239.", "1239.", "notice to appear", "removal_proceeding")),
    ("adjustment of status", ("245.", "1245.", "adjustment", "i-485")),
    ("good moral character", ("316.", "moral character", "naturalization")),
    ("advance parole", ("1245.13", "parole", "i-131", "part f")),
    ("stem opt", ("214.2", "217.", "stem", "opt", "practical training")),
    ("optional practical training", ("214.2", "opt", "practical training")),
    ("request for evidence", ("rfe", "request for evidence", "part l")),
    ("work authorization", ("274a.", "208.7", "244.", "employment authorization", "i-765")),
    ("temporary protected status", ("244.", "tps", "274a.12")),
    ("asylum", ("208.", "1158", "asylum")),
    ("naturalization", ("316.", "naturalization", "n-400", "vol 12")),
    ("removal", ("239.", "240.", "removal")),
    ("overstay", ("244.", "unlawful presence", "245.")),
)

_TOPIC_AFFINITY: tuple[tuple[re.Pattern[str], tuple[str, ...]], ...] = (
    (re.compile(r"\basylum\b", re.I), ("208.", "1158", "asylum")),
    (re.compile(r"\btps\b|temporary protected", re.I), ("244.", "tps", "274a.12")),
    (re.compile(r"\bdaca\b", re.I), ("dac", "274a.12", "i-765")),
    (re.compile(r"\bstem\b|\bopt\b", re.I), ("214.2", "217.", "opt", "stem")),
    (re.compile(r"\bi[- ]?485\b|adjustment of status", re.I), ("1245.", "245.", "i-485")),
    (re.compile(r"\bi[- ]?765\b|\bead\b|employment authorization", re.I), ("274a.", "i-765", "217.2")),
    (re.compile(r"\bnotice to appear\b|\bnta\b", re.I), ("239.", "1239.", "notice to appear")),
    (re.compile(r"\brfe\b|request for evidence", re.I), ("rfe", "request for evidence", "part l")),
    (re.compile(r"\btravel\b.*\b485\b|485.*\bpending\b", re.I), ("1245.13", "advance parole", "i-131")),
    (re.compile(r"\bnaturalization\b|\bcitizen", re.I), ("316.", "naturalization", "vol 12")),
    (re.compile(r"\bfamily petition\b|\bi[- ]?130\b", re.I), ("i-130", "petition", "family")),
    (re.compile(r"\bi[- ]?864\b|affidavit of support", re.I), ("i-864", "213a", "affidavit")),
    (re.compile(r"\baddress\b.*\buscis\b|change of address", re.I), ("address", "265.", "official page")),
)


def query_mentions_bia(query: str) -> bool:
    q = query.lower()
    return any(
        token in q
        for token in (
            "bia",
            "board of immigration appeals",
            "precedent decision",
            "i&n dec",
        )
    )


def is_bia_chunk(citation: str, topic: str | None = None) -> bool:
    cite = citation or ""
    if _BIA_CITATION_RE.search(cite):
        return True
    return (topic or "").strip().lower() == "bia precedent"


def extract_supplemental_phrases(query: str) -> list[str]:
    """Return phrases for optional phraseto_tsquery supplemental keyword retrieval."""
    q = query.lower()
    phrases: list[str] = []
    for phrase, _needles in _PHRASE_SIGNALS:
        if phrase in q:
            phrases.append(phrase)
    return phrases[:3]


def compute_relevance_boost(
    query: str,
    *,
    citation: str,
    topic: str | None,
    subtopic: str | None,
    snippet: str,
    official_url: str | None = None,
) -> float:
    """Additive boost/penalty applied after RRF fusion."""
    cite = citation or ""
    blob = " ".join(
        filter(
            None,
            [
                cite.lower(),
                (topic or "").lower(),
                (subtopic or "").lower(),
                (snippet or "")[:400].lower(),
                (official_url or "").lower(),
            ],
        )
    )
    q = query.lower()
    boost = 0.0

    if is_bia_chunk(cite, topic) and not query_mentions_bia(query):
        boost += _BIA_PENALTY

    # Prefer MVP authority tiers over BIA for general questions.
    if cite.startswith("USCIS Form"):
        boost += 0.006
    elif cite.startswith("USCIS Official"):
        boost += 0.006
    elif cite.startswith("8 CFR"):
        boost += 0.004
    elif cite.startswith("Vol "):
        boost += 0.003
    elif cite.startswith("8 U.S.C."):
        boost += 0.002

    # Form number in query → boost matching USCIS form chunk.
    form_match = _FORM_RE.search(q)
    if form_match:
        num = form_match.group(1).lower().replace(" ", "")
        if f"i-{num}" in blob or f"i{num}" in blob.replace("-", ""):
            boost += 0.014

    for phrase, needles in _PHRASE_SIGNALS:
        if phrase in q and any(n in blob for n in needles):
            boost += 0.010
            # Strong tie-break for definitional regulatory sections.
            if phrase == "notice to appear" and "239." in blob:
                boost += 0.018
            elif phrase == "good moral character" and "316." in blob:
                boost += 0.016
            elif phrase == "stem opt" and ("214.2" in blob or "217." in blob):
                boost += 0.014
            break

    for pattern, needles in _TOPIC_AFFINITY:
        if pattern.search(query) and any(n in blob for n in needles):
            boost += 0.008

    if "adjustment of status" in q and "eligible" in q and "§ 245.1" in cite:
        boost += 0.014

    if re.search(r"\bcategor", q) and "274a.12" in blob:
        boost += 0.012

    # Penalize tangential definitional sections when user asks "what is X".
    if q.startswith("what is") or q.startswith("what's"):
        if "§ 324." in cite or "§ 287." in cite or "§ 292." in cite:
            if not any(
                p in q
                for p in ("324", "287", "292", "enforcement", "bond", "representative")
            ):
                boost -= 0.010
        if "good moral character" in q and "§ 245." in cite and "316." not in cite:
            boost -= 0.008

    return max(-0.025, min(_MAX_BOOST, boost))


def dedupe_by_citation(rows: list[dict]) -> list[dict]:
    """Keep the highest hybrid_score row per citation string for diverse top-k."""
    best: dict[str, dict] = {}
    for row in rows:
        cite = row.get("citation") or ""
        prev = best.get(cite)
        if prev is None or row["hybrid_score"] > prev["hybrid_score"]:
            best[cite] = row
    return sorted(best.values(), key=lambda x: x["hybrid_score"], reverse=True)
