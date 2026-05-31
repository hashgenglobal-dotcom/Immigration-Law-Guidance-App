"""Live retrieval eval cases for the optional live eval harness.

Requires a running backend server with an active Supabase DB.

Run the live harness with:
  RUN_LIVE_RETRIEVAL_EVALS=1 LIVE_API_BASE_URL=http://127.0.0.1:8000 \
    uv run --with pytest pytest tests/eval/test_live_retrieval.py -v

Field semantics
---------------
id                         : unique case identifier
query                      : raw query sent to POST /api/retrieve
use_query_understanding    : passed directly to the API; True rewrites via understand_query()
min_results                : minimum len(results) required
source_family_search_window: how many top results to inspect for source family assertions
citation_search_window     : how many top results to inspect for citation assertions
required_source_families   : at least one top-N result must carry each of these source_family values
forbidden_source_families  : no top-N result may carry any of these source_family values
required_citation_terms    : each term must appear case-insensitively in at least one top-N citation
forbidden_citation_terms   : no top-N citation may contain any of these terms
required_effective_query_terms  : each term must appear case-insensitively in effective_query
                                  (only checked when use_query_understanding=True)
forbidden_effective_query_terms : no term may appear in effective_query
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LiveRetrievalCase:
    id: str
    query: str
    use_query_understanding: bool = True
    min_results: int = 2
    source_family_search_window: int = 5
    citation_search_window: int = 5
    required_source_families: tuple[str, ...] = ()
    forbidden_source_families: tuple[str, ...] = ()
    required_citation_terms: tuple[str, ...] = ()
    forbidden_citation_terms: tuple[str, ...] = ()
    required_effective_query_terms: tuple[str, ...] = ()
    forbidden_effective_query_terms: tuple[str, ...] = ()


LIVE_RETRIEVAL_CASES: tuple[LiveRetrievalCase, ...] = (

    # A. L-2 spouse work authorization
    LiveRetrievalCase(
        id="live_l2_spouse_work",
        query="Can my spouse work if I am on L-1 visa?",
        use_query_understanding=True,
        min_results=1,
        required_source_families=("USCIS Policy Manual",),
        forbidden_source_families=("BIA Precedent Decisions",),
        required_citation_terms=("Vol 10",),
        required_effective_query_terms=("L-2", "L-2S", "I-94", "Form I-765"),
    ),

    # B. F-1 OPT work after graduation
    LiveRetrievalCase(
        id="live_f1_opt_work",
        query="Can I work after graduation on F-1 OPT?",
        use_query_understanding=True,
        min_results=1,
        required_source_families=("eCFR Title 8",),
        forbidden_source_families=("BIA Precedent Decisions",),
        required_citation_terms=("214.2",),
        required_effective_query_terms=("post-completion OPT", "Form I-765", "274a.12(c)(3)"),
    ),

    # C. F-1 CPT
    LiveRetrievalCase(
        id="live_f1_cpt",
        query="Can I do CPT as an F-1 student?",
        use_query_understanding=True,
        min_results=1,
        required_source_families=("eCFR Title 8",),
        forbidden_source_families=("BIA Precedent Decisions",),
        required_citation_terms=("214.2",),
        required_effective_query_terms=("CPT", "214.2(f)(10)(i)", "I-20"),
    ),

    # D. STEM OPT 24-month extension
    LiveRetrievalCase(
        id="live_stem_opt",
        query="How do I apply for STEM OPT extension?",
        use_query_understanding=True,
        min_results=1,
        required_source_families=("eCFR Title 8",),
        forbidden_source_families=("BIA Precedent Decisions",),
        required_citation_terms=("214.2",),
        required_effective_query_terms=("STEM OPT", "Form I-983", "E-Verify", "24-month"),
    ),

    # E. Asylum applicant EAD (8 CFR 208.7)
    LiveRetrievalCase(
        id="live_asylum_ead",
        query="My asylum application is pending, can I get an EAD?",
        use_query_understanding=True,
        min_results=1,
        required_source_families=("eCFR Title 8",),
        forbidden_source_families=("BIA Precedent Decisions",),
        required_citation_terms=("208.7",),
        required_effective_query_terms=("208.7", "274a.12(c)(8)", "180-day", "Form I-765"),
    ),

    # F. I-485 advance parole (8 CFR 245.2)
    LiveRetrievalCase(
        id="live_i485_advance_parole",
        query="Can I travel while my I-485 is pending?",
        use_query_understanding=True,
        min_results=1,
        required_source_families=("eCFR Title 8",),
        forbidden_source_families=("BIA Precedent Decisions",),
        required_citation_terms=("245",),
        required_effective_query_terms=("advance parole", "Form I-131", "abandonment", "245.2"),
    ),

    # G. NTA / removal — eCFR required; BIA eligible but not forced for typical NTA question
    LiveRetrievalCase(
        id="live_nta_removal",
        query="I received an NTA, what are my rights?",
        use_query_understanding=True,
        min_results=3,
        source_family_search_window=7,
        citation_search_window=7,
        required_source_families=("eCFR Title 8",),
        required_citation_terms=("239",),
        required_effective_query_terms=(
            "Notice to Appear",
            "in absentia",
            "BIA",
            "Board of Immigration Appeals",
        ),
    ),

    # H. Explicit BIA query — keyword-heavy, no query_understanding rewrite
    # Validates that BIA Precedent Decisions chunks surface when queried directly.
    LiveRetrievalCase(
        id="live_bia_explicit",
        query="Notice to Appear NTA removal proceedings BIA precedent decision",
        use_query_understanding=False,
        min_results=3,
        source_family_search_window=7,
        citation_search_window=7,
        required_source_families=("BIA Precedent Decisions",),
        required_citation_terms=("I&N Dec.",),
    ),
)
