from __future__ import annotations

import sys
from pathlib import Path

# Make repo-root scripts importable when pytest is run with --project backend.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.services.mvp_source_scope import source_family_from_version
from app.services.query_understanding import (
    filter_results_for_understanding,
    understand_query,
)
from scripts.smart_chunker import canonicalize_ecfr_chunk_citation


class DummyResult:
    def __init__(
        self,
        *,
        citation: str = "",
        topic: str = "",
        subtopic: str = "",
        snippet: str = "",
        source_family: str = "",
        hybrid_score: float = 0.02,
        rank: int = 1,
    ) -> None:
        self.citation = citation
        self.topic = topic
        self.subtopic = subtopic
        self.snippet = snippet
        self.source_family = source_family
        self.hybrid_score = hybrid_score
        self.rank = rank


def test_ecfr_smart_dataset_maps_to_ecfr_title_8() -> None:
    assert source_family_from_version("ecfr-title8-smart-2026-05-29") == "eCFR Title 8"


def test_l2_filter_keeps_l2_and_removes_wrong_employment_categories() -> None:
    understanding = understand_query(
        "Can an L-2 spouse work with an L-2S I-94, or do they need an EAD?"
    )
    assert understanding.topic == "l2_work_authorization"

    good_l2 = DummyResult(
        citation="Vol 10, Part B, Ch 2",
        source_family="USCIS Policy Manual",
        snippet=(
            "USCIS considers certain E-1, E-2, E-3 and L-2 nonimmigrant "
            "dependent spouses employment authorized incident to status."
        ),
    )
    wrong_j2 = DummyResult(
        citation="Vol 2, Part D, Ch 6",
        source_family="USCIS Policy Manual",
        snippet="J-2 nonimmigrants may be eligible for employment authorization.",
    )
    wrong_u = DummyResult(
        citation="8 CFR § 214.14(7)",
        source_family="eCFR Title 8",
        snippet="U-2, U-3, U-4, or U-5 nonimmigrant status is employment authorized incident to status.",
    )
    wrong_i765v = DummyResult(
        citation="8 CFR § 106.2(45)",
        source_family="eCFR Title 8",
        snippet="Application for Employment Authorization for Abused Nonimmigrant Spouse, Form I-765V.",
    )

    filtered = filter_results_for_understanding(
        [good_l2, wrong_j2, wrong_u, wrong_i765v],
        understanding,
    )

    assert filtered == [good_l2]


def test_l2_filter_does_not_confuse_vol_2_with_l2() -> None:
    understanding = understand_query(
        "Can an L-2 spouse work with an L-2S I-94, or do they need an EAD?"
    )

    good_l2 = DummyResult(
        citation="Vol 10, Part B, Ch 2",
        snippet="L-2 nonimmigrant dependent spouses employment authorized incident to status.",
    )
    vol_2_j2 = DummyResult(
        citation="Vol 2, Part D, Ch 6",
        snippet="J-2 nonimmigrants may be eligible for employment authorization.",
    )

    filtered = filter_results_for_understanding([good_l2, vol_2_j2], understanding)

    assert filtered == [good_l2]


def test_smart_chunker_canonicalizes_cpt_citations() -> None:
    assert (
        canonicalize_ecfr_chunk_citation(
            "214.2",
            "(i) Curricular practical training. An F-1 student may be authorized by the DSO.",
            "8 CFR § 214.2(i)",
        )
        == "8 CFR § 214.2(f)(10)(i)"
    )

    assert (
        canonicalize_ecfr_chunk_citation(
            "274a.12",
            "(iii) Curricular practical training (internships, cooperative training programs).",
            "8 CFR § 274a.12(iii)",
        )
        == "8 CFR § 274a.12(b)(6)(iii)"
    )
