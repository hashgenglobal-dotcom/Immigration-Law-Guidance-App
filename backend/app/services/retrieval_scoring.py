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
    ("crimes involving moral turpitude", ("moral turpitude", "cimt", "212(a)(2)", "237(a)(2)")),
    ("aggravated felony", ("aggravated felony", "1101(a)(43)", "237(a)(2)", "iiraira")),
    ("criminal inadmissibility", ("212(a)(2)", "1182(a)(2)", "criminal inadmissibility", "moral turpitude")),
)

# I-485 travel context: matches rewritten travel_aos query and direct travel+I-485 questions.
_I485_TRAVEL_CONTEXT_RE = re.compile(
    r"(\badvance parole\b.{0,100}\b(?:i[- ]?131|adjustment)\b"
    r"|\bi[- ]?485\b.{0,80}\btravel\b|\btravel\b.{0,80}\bi[- ]?485\b"
    r"|\badjustment of status\b.{0,80}\btravel\b|\btravel\b.{0,80}\badjustment of status\b)",
    re.I,
)

# Signals in chunk blob that indicate advance-parole relevance.
_TRAVEL_AOS_BOOST_SIGNALS = ("advance parole", "i-131", "travel document", "abandonment", "1245.13")

# Signals in chunk blob indicating Syria/Public Law 106-378 specificity (tangential for generic I-485 travel).
_SYRIA_CHUNK_SIGNALS = ("syrian", "public law 106-378", "public law 106378", "§ 1245.20", "§ 1245.19", "1245.20", "1245.19")

# T nonimmigrant signals — irrelevant for generic I-485/AOS travel queries.
_T_NONIMMIGRANT_SIGNALS = ("t nonimmigrant", "214.11", "t visa holder", "tvpa", "trafficking victim")

# Asylum EAD context — matches rewritten asylum_pending retrieval queries and direct phrases.
_ASYLUM_EAD_QUERY_RE = re.compile(
    r"(\basylu\w*\b.{0,120}\b(?:ead|i[- ]?765|work authorization|employment authorization)\b"
    r"|\b(?:ead|i[- ]?765|work authorization|employment authorization)\b.{0,120}\basylu\w*\b"
    r"|\bpending asylum\b)",
    re.I,
)

# Naturalization requirements context — matches the naturalization_residence rewritten query.
_NATURALIZATION_CONTEXT_RE = re.compile(
    r"(\bnaturalization\b.{0,100}\b(?:n-?400|continuous residence|physical presence|good moral character|english|civics)\b"
    r"|\b(?:n-?400|continuous residence|physical presence)\b.{0,100}\bnaturalization\b)",
    re.I,
)

# Criminal inadmissibility context — matches the criminal_inadmissibility rewritten query
# and direct user questions about criminal grounds / criminal record effects.
_CRIMINAL_INADMISSIBILITY_CONTEXT_RE = re.compile(
    r"(\bina\s*212\b|\b212\s*\(a\)\s*\(2\)\b"
    r"|\bcriminal\s+(?:grounds?\s+of\s+)?inadmissib\w+"
    r"|\bcrimes?\s+involving\s+moral\s+turpitude\b|\bcimt\b"
    r"|\baggravated\s+felon\w+\b.{0,80}\b(?:immigration|inadmissib|visa|green\s+card|bar)\b"
    r"|\bcontrolled\s+substance\b.{0,80}\binadmissib\w+\b)",
    re.I,
)

# Criminal deportability context — matches the criminal_deportability rewritten query.
_CRIMINAL_DEPORTABILITY_CONTEXT_RE = re.compile(
    r"(\bina\s*237\b|\b237\s*\(a\)\s*\(2\)\b"
    r"|\bcriminal\s+(?:grounds?\s+of\s+)?deportab\w+"
    r"|\baggravated\s+felon\w+\b.{0,80}\b(?:deport\w+|removal)\b)",
    re.I,
)

_CRIMINAL_INADMISSIBILITY_BOOST_SIGNALS = (
    "212(a)(2)", "1182(a)(2)", "moral turpitude", "cimt",
    "criminal inadmissibility", "inadmissibility",
    "aggravated felony", "controlled substance",
)
_CRIMINAL_DEPORTABILITY_BOOST_SIGNALS = (
    "237(a)(2)", "1227(a)(2)", "criminal deportability", "deportability",
    "aggravated felony", "moral turpitude",
)
# Penalize public-charge and special-immigrant sections for criminal-grounds queries.
_PUBLIC_CHARGE_CHUNK_SIGNALS = (
    "212(a)(4)", "1182(a)(4)", "public charge",
)
_SPECIAL_IMMIGRANT_CHUNK_SIGNALS = (
    "101(a)(27)", "1101(a)(27)", "special immigrant",
)
# Naturalization-GMC chunks are about citizenship eligibility, not inadmissibility bars.
# Penalize them for criminal inadmissibility queries unless the query asks about naturalization.
_NATURALIZATION_GMC_CHUNK_SIGNALS = (
    "316.", "n-400", "n400", "vol 12", "naturalization",
)
# Criminal-grounds signals that must be absent from a chunk for the naturalization penalty to fire.
# If the chunk ALSO discusses criminal grounds it's relevant — don't penalize it.
_CRIMINAL_GROUNDS_CHUNK_SIGNALS = (
    "212(a)(2)", "1182(a)(2)", "237(a)(2)", "1227(a)(2)",
    "criminal grounds", "criminal inadmissibility", "criminal deportability",
    "moral turpitude",
)
# Asylum-eligibility procedure chunks are about how to file asylum, not about deportability.
# Penalize them for criminal deportability queries unless the query asks about asylum.
_ASYLUM_FILING_CHUNK_SIGNALS = (
    "i-589", "208.1", "208.2", "208.3", "208.4", "208.5", "208.6",
    "asylum eligibility", "asylum application",
)

# I-864 / affidavit of support chunks — irrelevant for H-4 and OPT queries.
_I864_CHUNK_SIGNALS = ("i-864", "i864", "213a", "affidavit of support")

# H-4 process context — matches rewritten h4_process query and direct H-4 status questions.
_H4_PROCESS_CONTEXT_RE = re.compile(
    r"(\bh[- ]?4\b.{0,80}\b(?:dependent|spouse|status|process|nonimmigrant|change\s+of\s+status|extension)\b"
    r"|\b214\.2\s*\(\s*h\s*\)\b"
    r"|\bh[- ]?4\s+(?:dependent|visa|status)\b)",
    re.I,
)

# H-4 EAD context — matches rewritten h4_ead query and direct H-4 employment authorization questions.
_H4_EAD_CONTEXT_RE = re.compile(
    r"(\bh[- ]?4\b.{0,80}\b(?:ead|employment\s+authorization|work\s+authorization|i[- ]?765)\b"
    r"|\b274a\.12\s*\(\s*c\s*\)\s*\(\s*26\s*\)\b"
    r"|\bh[- ]?4\s+ead\b)",
    re.I,
)

# OPT context — matches rewritten opt_general query and direct F-1 OPT questions.
_OPT_CONTEXT_RE = re.compile(
    r"(\boptional\s+practical\s+training\b"
    r"|\b214\.2\s*\(\s*f\s*\)\b"
    r"|\b274a\.12\s*\(\s*c\s*\)\s*\(\s*3\s*\)\b"
    r"|\bpost[- ]?completion\s+opt\b|\bpre[- ]?completion\s+opt\b)",
    re.I,
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
    (re.compile(r"\bcriminal\b.{0,60}\b(?:inadmissib|deportab|grounds?|conviction)\b", re.I),
     ("212(a)(2)", "237(a)(2)", "moral turpitude", "aggravated felony")),
    (re.compile(r"\bcimt\b|\bmoral turpitude\b", re.I), ("moral turpitude", "cimt", "212(a)(2)")),
    (re.compile(r"\baggravated felony\b", re.I), ("aggravated felony", "1101(a)(43)", "237(a)(2)")),
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

    # I-485 travel: boost advance-parole/I-131 chunks; penalize tangential chunks unless
    # the query explicitly asks about those specific topics.
    if _I485_TRAVEL_CONTEXT_RE.search(query):
        if any(s in blob for s in _TRAVEL_AOS_BOOST_SIGNALS):
            boost += 0.012
        if "syr" not in q and "public law 106" not in q:
            if any(s in blob for s in _SYRIA_CHUNK_SIGNALS):
                boost -= 0.024
        # Penalize T nonimmigrant/trafficking-specific chunks for generic I-485 travel queries.
        if not any(tok in q for tok in ("t nonimmig", "t visa", "trafficking", "tvpa")):
            if any(s in blob for s in _T_NONIMMIGRANT_SIGNALS):
                boost -= 0.022

    # Asylum EAD: boost 8 CFR 208.7 and 274a.12(c)(8) chunks specifically.
    if _ASYLUM_EAD_QUERY_RE.search(query):
        if "208.7" in blob:
            boost += 0.016
        if "274a.12" in blob:
            boost += 0.010
        if "i-765" in blob:
            boost += 0.008

    # Naturalization requirements: boost N-400, 8 CFR 316, USCIS Policy Manual Vol 12.
    if _NATURALIZATION_CONTEXT_RE.search(query):
        if "n-400" in blob or "n400" in blob:
            boost += 0.016
        if "316." in blob:
            boost += 0.012
        if "vol 12" in blob:
            boost += 0.010
        if "continuous residence" in blob or "physical presence" in blob:
            boost += 0.008

    # N-400 form number in query → boost matching USCIS N-400 chunks
    # (not covered by _FORM_RE which is scoped to I-xxx forms).
    if "n-400" in q or "n400" in q:
        if "n-400" in blob or "n400" in blob:
            boost += 0.014

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

    # Criminal inadmissibility: boost INA 212(a)(2)/CIMT/aggravated-felony chunks;
    # penalize unrelated inadmissibility grounds (public charge, special immigrant,
    # and naturalization-only GMC sections that are about citizenship eligibility,
    # not criminal bars).
    if _CRIMINAL_INADMISSIBILITY_CONTEXT_RE.search(query):
        if any(s in blob for s in _CRIMINAL_INADMISSIBILITY_BOOST_SIGNALS):
            boost += 0.012
        if "212(a)(2)" in blob or "1182(a)(2)" in blob:
            boost += 0.008
        if any(s in blob for s in _PUBLIC_CHARGE_CHUNK_SIGNALS):
            boost -= 0.018
        if any(s in blob for s in _SPECIAL_IMMIGRANT_CHUNK_SIGNALS):
            boost -= 0.014
        # Penalize naturalization/GMC-only chunks (8 CFR 316.x, N-400, Vol 12) when the
        # query is not about naturalization or citizenship.  If the chunk also contains
        # criminal-grounds signals it is still relevant, so skip the penalty.
        if "naturalization" not in q and "citizen" not in q:
            if any(s in blob for s in _NATURALIZATION_GMC_CHUNK_SIGNALS):
                if not any(s in blob for s in _CRIMINAL_GROUNDS_CHUNK_SIGNALS):
                    boost -= 0.012

    # Criminal deportability: boost INA 237(a)(2)/aggravated-felony chunks;
    # penalize unrelated grounds and asylum-filing-procedure chunks that have no
    # connection to the criminal deportability grounds being asked about.
    if _CRIMINAL_DEPORTABILITY_CONTEXT_RE.search(query):
        if any(s in blob for s in _CRIMINAL_DEPORTABILITY_BOOST_SIGNALS):
            boost += 0.012
        if "237(a)(2)" in blob or "1227(a)(2)" in blob:
            boost += 0.008
        if any(s in blob for s in _PUBLIC_CHARGE_CHUNK_SIGNALS):
            boost -= 0.018
        if any(s in blob for s in _SPECIAL_IMMIGRANT_CHUNK_SIGNALS):
            boost -= 0.014
        # Penalize asylum-eligibility/filing-procedure chunks (208.1–208.6, I-589)
        # when the query is not about asylum.  Chunks that also discuss criminal grounds
        # are still relevant, so skip the penalty in that case.
        if "asylum" not in q:
            if any(s in blob for s in _ASYLUM_FILING_CHUNK_SIGNALS):
                if not any(s in blob for s in _CRIMINAL_GROUNDS_CHUNK_SIGNALS):
                    boost -= 0.012

    # H-4 process: boost 8 CFR 214.2(h) / H-4 dependent chunks; penalize naturalization
    # and I-864/special-immigrant chunks that are irrelevant to nonimmigrant H-4 status.
    if _H4_PROCESS_CONTEXT_RE.search(query):
        if "214.2(h)" in blob:
            boost += 0.016
        if "h-4" in blob or "h4" in blob:
            boost += 0.008
        if "i-539" in blob:
            boost += 0.008
        if "naturalization" not in q and "citizen" not in q:
            if any(s in blob for s in _NATURALIZATION_GMC_CHUNK_SIGNALS):
                boost -= 0.018
        if any(s in blob for s in _SPECIAL_IMMIGRANT_CHUNK_SIGNALS):
            boost -= 0.016
        if any(s in blob for s in _I864_CHUNK_SIGNALS):
            boost -= 0.016

    # H-4 EAD: boost 8 CFR 274a.12(c)(26) / I-765 chunks; penalize naturalization
    # and I-864/special-immigrant chunks that are irrelevant to H-4 employment authorization.
    if _H4_EAD_CONTEXT_RE.search(query):
        if "274a.12(c)(26)" in blob:
            boost += 0.016
        if "274a.12" in blob:
            boost += 0.010
        if "i-765" in blob:
            boost += 0.008
        if "naturalization" not in q and "citizen" not in q:
            if any(s in blob for s in _NATURALIZATION_GMC_CHUNK_SIGNALS):
                boost -= 0.018
        if any(s in blob for s in _SPECIAL_IMMIGRANT_CHUNK_SIGNALS):
            boost -= 0.016
        if any(s in blob for s in _I864_CHUNK_SIGNALS):
            boost -= 0.016

    # OPT: boost 8 CFR 214.2(f) / 274a.12(c)(3) chunks; penalize naturalization
    # and I-864/special-immigrant chunks that are irrelevant to F-1 OPT.
    if _OPT_CONTEXT_RE.search(query):
        if "214.2(f)" in blob:
            boost += 0.014
        if "274a.12(c)(3)" in blob:
            boost += 0.012
        if "i-765" in blob:
            boost += 0.008
        if "optional practical training" in blob:
            boost += 0.006
        if "naturalization" not in q and "citizen" not in q:
            if any(s in blob for s in _NATURALIZATION_GMC_CHUNK_SIGNALS):
                boost -= 0.018
        if any(s in blob for s in _SPECIAL_IMMIGRANT_CHUNK_SIGNALS):
            boost -= 0.016
        if any(s in blob for s in _I864_CHUNK_SIGNALS):
            boost -= 0.016

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
