"""Unit tests for MVP retrieval scoring helpers."""

from __future__ import annotations

import unittest

from app.services.retrieval_scoring import (
    compute_relevance_boost,
    dedupe_by_citation,
    extract_supplemental_phrases,
    is_bia_chunk,
    query_mentions_bia,
)


class RetrievalScoringTests(unittest.TestCase):
    def test_bia_chunk_detection(self) -> None:
        self.assertTrue(is_bia_chunk("Aguilar Hernandez,28 I&N Dec. 774 (BIA 2024)"))
        self.assertFalse(is_bia_chunk("8 CFR § 239.1", "239.1"))

    def test_bia_penalty_without_query_mention(self) -> None:
        boost = compute_relevance_boost(
            "What is a Notice to Appear?",
            citation="Aguilar Hernandez (BIA 2024)",
            topic="BIA Precedent",
            subtopic=None,
            snippet="notice to appear",
        )
        self.assertLess(boost, 0)

    def test_notice_to_appear_boosts_cfr_239(self) -> None:
        boost = compute_relevance_boost(
            "What is a Notice to Appear?",
            citation="8 CFR § 239.1",
            topic="239.1",
            subtopic=None,
            snippet="Notice to appear means ...",
        )
        self.assertGreater(boost, 0.015)

    def test_form_i765_boost(self) -> None:
        boost = compute_relevance_boost(
            "What is Form I-765?",
            citation="USCIS Form I-765",
            topic="I-765",
            subtopic=None,
            snippet="Application for employment authorization",
        )
        self.assertGreater(boost, 0.01)

    def test_extract_phrase_notice_to_appear(self) -> None:
        phrases = extract_supplemental_phrases("What is a Notice to Appear?")
        self.assertIn("notice to appear", phrases)

    def test_dedupe_by_citation_keeps_best_score(self) -> None:
        rows = [
            {"citation": "8 CFR § 208.7", "hybrid_score": 0.02, "chunk_id": 1},
            {"citation": "8 CFR § 208.7", "hybrid_score": 0.03, "chunk_id": 2},
            {"citation": "8 CFR § 274a.13", "hybrid_score": 0.025, "chunk_id": 3},
        ]
        out = dedupe_by_citation(rows)
        self.assertEqual(len(out), 2)
        self.assertEqual(out[0]["chunk_id"], 2)

    def test_query_mentions_bia(self) -> None:
        self.assertTrue(query_mentions_bia("BIA precedent on removal"))
        self.assertFalse(query_mentions_bia("What is a Notice to Appear?"))

    # --- I-485 travel scoring ---

    def test_i485_travel_boosts_advance_parole_chunk(self) -> None:
        # The rewritten travel_aos query should boost advance parole / I-131 chunks.
        query = "Advance parole travel while adjustment of status I-485 pending Form I-131"
        boost = compute_relevance_boost(
            query,
            citation="USCIS Policy Manual — Advance Parole",
            topic="advance parole",
            subtopic=None,
            snippet="Advance parole allows a person with a pending I-485 to travel abroad and return.",
        )
        self.assertGreater(boost, 0.01)

    def test_i485_travel_penalizes_syria_chunk(self) -> None:
        # Syria-specific chunks should be penalized for generic I-485 travel queries.
        query = "Advance parole travel while adjustment of status I-485 pending Form I-131"
        boost = compute_relevance_boost(
            query,
            citation="8 CFR § 1245.20",
            topic="Syrian nationals adjustment",
            subtopic=None,
            snippet="This section applies to Syrian nationals under Public Law 106-378.",
        )
        self.assertLess(boost, 0)

    def test_syria_query_no_penalty_for_syria_chunk(self) -> None:
        # When the user explicitly asks about Syria, the penalty must not apply.
        query = "Can Syrian nationals use Public Law 106-378 to adjust status?"
        boost = compute_relevance_boost(
            query,
            citation="8 CFR § 1245.20",
            topic="Syrian nationals",
            subtopic=None,
            snippet="Syrian nationals under Public Law 106-378 may adjust status.",
        )
        self.assertGreaterEqual(boost, -0.005)

    def test_general_adjustment_query_not_penalized(self) -> None:
        # Plain adjustment-of-status eligibility query must not trigger the Syria penalty.
        boost = compute_relevance_boost(
            "How do I become eligible for adjustment of status?",
            citation="8 CFR § 245.1",
            topic="adjustment of status",
            subtopic=None,
            snippet="An alien may apply for adjustment of status under section 245.",
        )
        self.assertGreaterEqual(boost, 0)

    def test_i485_travel_advance_parole_chunk_outranks_syria_chunk(self) -> None:
        # The advance-parole boost must produce a higher score than the penalized Syria chunk.
        query = "Advance parole travel while adjustment of status I-485 pending Form I-131"
        ap_boost = compute_relevance_boost(
            query,
            citation="USCIS Form I-131",
            topic="advance parole",
            subtopic=None,
            snippet="File Form I-131 to request advance parole before traveling with a pending I-485.",
        )
        syria_boost = compute_relevance_boost(
            query,
            citation="8 CFR § 1245.20",
            topic="Syrian nationals",
            subtopic=None,
            snippet="Syrian nationals under Public Law 106-378.",
        )
        self.assertGreater(ap_boost, syria_boost)

    # --- T nonimmigrant penalty for I-485 travel queries ---

    def test_i485_travel_penalizes_t_nonimmigrant_chunk(self) -> None:
        # A T nonimmigrant status chunk with no advance-parole signals should be penalized.
        query = "Advance parole travel while adjustment of status I-485 pending Form I-131"
        boost = compute_relevance_boost(
            query,
            citation="8 CFR § 214.11",
            topic="T nonimmigrant status",
            subtopic=None,
            snippet="T nonimmigrant status is granted to victims of trafficking under 8 CFR 214.11.",
        )
        self.assertLess(boost, 0)

    def test_t_nonimmigrant_query_no_penalty_for_t_chunk(self) -> None:
        # When the user explicitly asks about T visa/T nonimmigrant, the penalty must not apply.
        query = "Can a T nonimmigrant travel outside the U.S. while their case is pending?"
        boost = compute_relevance_boost(
            query,
            citation="8 CFR § 214.11",
            topic="T nonimmigrant status",
            subtopic=None,
            snippet="T nonimmigrant status is granted to victims of trafficking under 8 CFR 214.11.",
        )
        self.assertGreaterEqual(boost, 0)

    def test_i485_travel_advance_parole_outranks_t_nonimmigrant_chunk(self) -> None:
        query = "Advance parole travel while adjustment of status I-485 pending Form I-131"
        ap_boost = compute_relevance_boost(
            query,
            citation="USCIS Form I-131",
            topic="advance parole",
            subtopic=None,
            snippet="File Form I-131 to request advance parole before traveling with a pending I-485.",
        )
        t_boost = compute_relevance_boost(
            query,
            citation="8 CFR § 214.11",
            topic="T nonimmigrant status",
            subtopic=None,
            snippet="T nonimmigrant status is granted to victims of trafficking under 8 CFR 214.11.",
        )
        self.assertGreater(ap_boost, t_boost)

    # --- Asylum EAD specific boosts ---

    def test_asylum_ead_boosts_208_7_chunk(self) -> None:
        query = "Can asylum applicants get work authorization and apply for Form I-765 EAD 8 CFR 208.7 pending asylum"
        boost = compute_relevance_boost(
            query,
            citation="8 CFR § 208.7",
            topic="employment authorization for asylum applicants",
            subtopic=None,
            snippet="An asylum applicant may apply for employment authorization after 150 days from filing.",
        )
        self.assertGreater(boost, 0.015)

    def test_asylum_ead_boosts_274a_12_chunk(self) -> None:
        query = "Can asylum applicants get work authorization and apply for Form I-765 EAD 8 CFR 208.7 pending asylum"
        boost = compute_relevance_boost(
            query,
            citation="8 CFR § 274a.12(c)(8)",
            topic="employment authorization categories",
            subtopic=None,
            snippet="Category (c)(8) covers asylum applicants who have filed and whose case is pending.",
        )
        self.assertGreater(boost, 0.01)

    def test_asylum_ead_208_7_outranks_general_asylum_procedure(self) -> None:
        query = "Can asylum applicants get work authorization and apply for Form I-765 EAD 8 CFR 208.7 pending asylum"
        ead_boost = compute_relevance_boost(
            query,
            citation="8 CFR § 208.7",
            topic="asylum employment authorization",
            subtopic=None,
            snippet="An asylum applicant may apply for EAD 150 days after filing.",
        )
        procedure_boost = compute_relevance_boost(
            query,
            citation="8 CFR § 208.3",
            topic="asylum application procedure",
            subtopic=None,
            snippet="Applications for asylum must be filed on Form I-589.",
        )
        self.assertGreater(ead_boost, procedure_boost)

    # --- Naturalization requirements boosts ---

    def test_naturalization_requirements_boosts_n400_chunk(self) -> None:
        query = "Naturalization Form N-400 continuous residence physical presence good moral character"
        boost = compute_relevance_boost(
            query,
            citation="USCIS Form N-400",
            topic="naturalization",
            subtopic=None,
            snippet="Application for Naturalization. Eligibility requires 5 years as LPR, continuous residence, and good moral character.",
        )
        self.assertGreater(boost, 0.015)

    def test_naturalization_requirements_boosts_cfr_316_chunk(self) -> None:
        query = "Naturalization Form N-400 continuous residence physical presence good moral character"
        boost = compute_relevance_boost(
            query,
            citation="8 CFR § 316.2",
            topic="naturalization",
            subtopic=None,
            snippet="Requirements for naturalization: continuous residence of 5 years, physical presence, good moral character.",
        )
        self.assertGreater(boost, 0.015)

    def test_naturalization_requirements_boosts_vol12_chunk(self) -> None:
        query = "Naturalization Form N-400 continuous residence physical presence good moral character"
        boost = compute_relevance_boost(
            query,
            citation="Vol 12 USCIS Policy Manual — Citizenship",
            topic="naturalization",
            subtopic=None,
            snippet="Vol 12 covers naturalization eligibility including residence, presence, and good moral character requirements.",
        )
        self.assertGreater(boost, 0.01)

    def test_naturalization_n400_outranks_unrelated_cfr(self) -> None:
        query = "Naturalization Form N-400 continuous residence physical presence good moral character"
        n400_boost = compute_relevance_boost(
            query,
            citation="USCIS Form N-400",
            topic="naturalization",
            subtopic=None,
            snippet="N-400 application for naturalization. Continuous residence and physical presence required.",
        )
        unrelated_boost = compute_relevance_boost(
            query,
            citation="8 CFR § 208.3",
            topic="asylum application",
            subtopic=None,
            snippet="Applications for asylum must be filed on Form I-589.",
        )
        self.assertGreater(n400_boost, unrelated_boost)


    # --- Criminal inadmissibility scoring ---

    def test_criminal_inadmissibility_boosts_212a2_chunk(self) -> None:
        query = (
            "INA 212(a)(2) criminal grounds of inadmissibility crimes involving moral turpitude "
            "CIMT aggravated felony controlled substance violation conviction DUI immigration bar"
        )
        boost = compute_relevance_boost(
            query,
            citation="8 U.S.C. § 1182(a)(2)",
            topic="criminal inadmissibility",
            subtopic=None,
            snippet="A person is inadmissible if convicted of a crime involving moral turpitude. 212(a)(2)",
        )
        self.assertGreater(boost, 0.015)

    def test_criminal_inadmissibility_boosts_cimt_chunk(self) -> None:
        query = (
            "INA 212(a)(2) criminal grounds of inadmissibility crimes involving moral turpitude "
            "CIMT aggravated felony controlled substance violation conviction DUI immigration bar"
        )
        boost = compute_relevance_boost(
            query,
            citation="USCIS Policy Manual — Criminal Grounds",
            topic="crimes involving moral turpitude",
            subtopic=None,
            snippet="Crimes involving moral turpitude (CIMT) are a basis for inadmissibility under INA 212(a)(2).",
        )
        self.assertGreater(boost, 0.01)

    def test_criminal_inadmissibility_penalizes_public_charge_chunk(self) -> None:
        query = (
            "INA 212(a)(2) criminal grounds of inadmissibility crimes involving moral turpitude "
            "CIMT aggravated felony controlled substance violation conviction DUI immigration bar"
        )
        boost = compute_relevance_boost(
            query,
            citation="8 U.S.C. § 1182(a)(4)",
            topic="public charge",
            subtopic=None,
            snippet="An applicant is inadmissible if likely to become a public charge. 212(a)(4).",
        )
        self.assertLess(boost, 0)

    def test_criminal_inadmissibility_penalizes_special_immigrant_chunk(self) -> None:
        query = (
            "INA 212(a)(2) criminal grounds of inadmissibility crimes involving moral turpitude "
            "CIMT aggravated felony controlled substance violation conviction DUI immigration bar"
        )
        boost = compute_relevance_boost(
            query,
            citation="INA § 101(a)(27)",
            topic="special immigrant",
            subtopic=None,
            snippet="Special immigrants include certain religious workers under INA 101(a)(27).",
        )
        self.assertLess(boost, 0)

    def test_criminal_inadmissibility_212a2_outranks_public_charge(self) -> None:
        query = (
            "INA 212(a)(2) criminal grounds of inadmissibility crimes involving moral turpitude "
            "CIMT aggravated felony controlled substance violation conviction DUI immigration bar"
        )
        criminal_boost = compute_relevance_boost(
            query,
            citation="8 U.S.C. § 1182(a)(2)",
            topic="criminal inadmissibility",
            subtopic=None,
            snippet="Criminal grounds of inadmissibility under 212(a)(2) include CIMT and aggravated felony.",
        )
        public_charge_boost = compute_relevance_boost(
            query,
            citation="8 U.S.C. § 1182(a)(4)",
            topic="public charge",
            subtopic=None,
            snippet="Public charge inadmissibility under 212(a)(4).",
        )
        self.assertGreater(criminal_boost, public_charge_boost)

    # --- Criminal deportability scoring ---

    def test_criminal_deportability_boosts_237a2_chunk(self) -> None:
        query = (
            "INA 237(a)(2) criminal grounds of deportability aggravated felony crimes involving "
            "moral turpitude conviction removal deportation criminal record"
        )
        boost = compute_relevance_boost(
            query,
            citation="8 U.S.C. § 1227(a)(2)",
            topic="criminal deportability",
            subtopic=None,
            snippet="An alien is deportable under INA 237(a)(2) if convicted of an aggravated felony.",
        )
        self.assertGreater(boost, 0.015)

    def test_criminal_deportability_penalizes_public_charge_chunk(self) -> None:
        query = (
            "INA 237(a)(2) criminal grounds of deportability aggravated felony crimes involving "
            "moral turpitude conviction removal deportation criminal record"
        )
        boost = compute_relevance_boost(
            query,
            citation="8 U.S.C. § 1182(a)(4)",
            topic="public charge",
            subtopic=None,
            snippet="Public charge ground. 212(a)(4).",
        )
        self.assertLess(boost, 0)

    def test_criminal_deportability_237a2_outranks_public_charge(self) -> None:
        query = (
            "INA 237(a)(2) criminal grounds of deportability aggravated felony crimes involving "
            "moral turpitude conviction removal deportation criminal record"
        )
        deportability_boost = compute_relevance_boost(
            query,
            citation="8 U.S.C. § 1227(a)(2)",
            topic="criminal deportability",
            subtopic=None,
            snippet="Deportable aliens include those convicted under 237(a)(2) aggravated felony.",
        )
        public_charge_boost = compute_relevance_boost(
            query,
            citation="8 U.S.C. § 1182(a)(4)",
            topic="public charge",
            subtopic=None,
            snippet="Public charge ground 212(a)(4).",
        )
        self.assertGreater(deportability_boost, public_charge_boost)

    # --- Naturalization/GMC chunk penalty for criminal inadmissibility queries ---

    def test_criminal_inadmissibility_penalizes_naturalization_gmc_chunk(self) -> None:
        # A 8 CFR 316.x chunk about naturalization good moral character should be penalized
        # for a criminal inadmissibility query — it covers citizenship eligibility, not 212(a)(2) bars.
        query = (
            "INA 212(a)(2) 8 U.S.C. 1182(a)(2) criminal grounds of inadmissibility crimes involving "
            "moral turpitude CIMT controlled substance violation multiple criminal convictions "
            "trafficking aggravated felony conviction inadmissibility bar"
        )
        boost = compute_relevance_boost(
            query,
            citation="8 CFR § 316.10",
            topic="naturalization",
            subtopic="good moral character",
            snippet="Good moral character is required for naturalization under 8 CFR 316.10.",
        )
        self.assertLess(boost, 0)

    def test_criminal_inadmissibility_naturalization_chunk_outranked_by_212a2_chunk(self) -> None:
        query = (
            "INA 212(a)(2) 8 U.S.C. 1182(a)(2) criminal grounds of inadmissibility crimes involving "
            "moral turpitude CIMT controlled substance violation multiple criminal convictions "
            "trafficking aggravated felony conviction inadmissibility bar"
        )
        criminal_boost = compute_relevance_boost(
            query,
            citation="8 U.S.C. § 1182(a)(2)",
            topic="criminal inadmissibility",
            subtopic=None,
            snippet="Criminal grounds of inadmissibility include CIMT and aggravated felony. 212(a)(2)",
        )
        nat_boost = compute_relevance_boost(
            query,
            citation="8 CFR § 316.10",
            topic="naturalization",
            subtopic="good moral character",
            snippet="Good moral character for naturalization purposes under 8 CFR 316.10.",
        )
        self.assertGreater(criminal_boost, nat_boost)

    def test_naturalization_query_no_penalty_for_naturalization_chunk(self) -> None:
        # When the query explicitly asks about naturalization, the penalty must NOT apply.
        boost = compute_relevance_boost(
            "Naturalization Form N-400 continuous residence physical presence good moral character",
            citation="8 CFR § 316.10",
            topic="naturalization",
            subtopic="good moral character",
            snippet="Good moral character for naturalization under 8 CFR 316.10.",
        )
        self.assertGreaterEqual(boost, 0)

    # --- Asylum-eligibility chunk penalty for criminal deportability queries ---

    def test_criminal_deportability_penalizes_asylum_filing_chunk(self) -> None:
        # An 8 CFR 208.3 (asylum application procedure) chunk should be penalized for
        # a criminal deportability query — it's about how to apply for asylum, not 237(a)(2).
        query = (
            "INA 237(a)(2) 8 U.S.C. 1227(a)(2) criminal grounds of deportability aggravated felony "
            "crimes involving moral turpitude controlled substance domestic violence firearms "
            "conviction removal deportation"
        )
        boost = compute_relevance_boost(
            query,
            citation="8 CFR § 208.3",
            topic="asylum",
            subtopic="application procedure",
            snippet="Applications for asylum must be filed on Form I-589 within one year of arrival.",
        )
        self.assertLess(boost, 0)

    def test_criminal_deportability_237a2_outranks_asylum_filing_chunk(self) -> None:
        query = (
            "INA 237(a)(2) 8 U.S.C. 1227(a)(2) criminal grounds of deportability aggravated felony "
            "crimes involving moral turpitude controlled substance domestic violence firearms "
            "conviction removal deportation"
        )
        deportability_boost = compute_relevance_boost(
            query,
            citation="8 U.S.C. § 1227(a)(2)",
            topic="criminal deportability",
            subtopic=None,
            snippet="An alien is deportable under 237(a)(2) if convicted of an aggravated felony.",
        )
        asylum_boost = compute_relevance_boost(
            query,
            citation="8 CFR § 208.3",
            topic="asylum",
            subtopic="application procedure",
            snippet="Applications for asylum must be filed on Form I-589 within one year.",
        )
        self.assertGreater(deportability_boost, asylum_boost)

    def test_unrelated_query_no_criminal_boost(self) -> None:
        # A non-criminal query should not get the criminal inadmissibility boost.
        boost = compute_relevance_boost(
            "How do I apply for an EAD as an asylum applicant?",
            citation="8 U.S.C. § 1182(a)(2)",
            topic="criminal inadmissibility",
            subtopic=None,
            snippet="Criminal grounds of inadmissibility under 212(a)(2).",
        )
        # Should not be substantially boosted — no criminal inadmissibility context in query.
        self.assertLess(boost, 0.015)


if __name__ == "__main__":
    unittest.main()
