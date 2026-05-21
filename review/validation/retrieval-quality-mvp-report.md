# Retrieval Quality MVP Tuning Report

**Branch:** `feature/retrieval-quality-mvp-tuning`  
**Date:** May 20, 2026  
**Goal:** Expected citations in **top 3** for most MVP golden queries (rank 1 ideal).

---

## Summary

| Metric | Before tuning | After tuning |
|--------|---------------|--------------|
| Golden queries top-3 hit | 8 / 13 (62%) | **13 / 13 (100%)** |
| Golden queries top-1 hit | 6 / 13 (46%) | **11 / 13 (85%)** |
| Legacy 5-query exact citation in top-5 | NTA missing | All present (NTA § 239.1 at rank 3) |

Tuning stays **flexible** (substring / category matchers in `mvp-golden-retrieval-queries.json`), not hard-coded rank-1 strings only.

---

## Changes (backend only)

| Area | Change |
|------|--------|
| `retrieval_service.py` | Vector/keyword RRF weights (1.0 / 0.72), 15 candidates each, BIA filtered from keyword pool, supplemental `phraseto_tsquery` phrase pass (non-BIA), post-RRF relevance boosts, dedupe by citation |
| `retrieval_scoring.py` | Authority tiers, phrase/topic affinity, form-number match, BIA penalty, definitional tangential penalties |
| Golden set | `Review/validation/mvp-golden-retrieval-queries.json` (13 queries) |
| Validation | `Review/scripts/validate_mvp_golden_retrieval.py` |

**Not changed:** mobile UI, ingestion pipelines, unrelated docs.

---

## Golden query results (after)

| Query | Top-3 hit | Rank of first match | Top result |
|-------|-----------|---------------------|------------|
| Asylum applicants work authorization | Yes | 1 | 8 CFR § 208.7 |
| Notice to Appear | Yes | 3 | 8 CFR § 239.2 (239.1 in top 3) |
| Adjustment of status | Yes | 1 | 8 CFR § 1245.1 |
| Good moral character (naturalization) | Yes | 2 | Vol 12 + 8 CFR § 316.10 |
| How do I apply for EAD? (broad) | Yes | 1 | 8 CFR § 217.2 (+ I-765 #2); **guided intake** still applies in chat |
| STEM OPT | Yes | 1 | 8 CFR § 214.2 |
| Travel while I-485 pending | Yes | 2 | I-485 + 8 CFR § 1245.15 |
| Advance parole | Yes | 2 | 8 CFR § 1245.13 |
| RFE | Yes | 1 | Vol 2, Part L, Ch 9 |
| Change address with USCIS | Yes | 1 | USCIS Official Page |
| Form I-130 | Yes | 1 | USCIS Form I-130 |
| Form I-864 | Yes | 1 | USCIS Form I-864 |
| TPS work authorization | Yes | 1 | 8 CFR § 274a.12 |

---

## Notable before → after fixes

1. **NTA** — BIA decisions dominated keyword FTS on “appear”; now phrase retrieval excludes BIA and boosts 8 CFR § 239.x.
2. **Asylum EAD** — 8 CFR § 208.7 moved from rank 3 → **rank 1** (asylum topic affinity + dedupe).
3. **STEM OPT** — 8 CFR § 214.2 rank 1 (tangential § 324.1 demoted).
4. **RFE** — Vol 2, Part L rank 1 (phrase “request for evidence” signal).
5. **Broad EAD** — Form I-765 remains in top 3; chat `detect_broad_topic("ead")` unchanged for guided intake.

---

## Legacy hybrid validation (5 queries)

| Query | Expected | Rank after tuning |
|-------|----------|-------------------|
| Asylum EAD | 8 CFR § 208.7 | 1 |
| Asylum filing | 8 CFR § 208.4 | 2 |
| AOS eligibility | 8 CFR § 245.1 | 3 (1245.1 rank 1 — related AOS section) |
| Employment categories | 8 CFR § 274a.12 | 1 |
| NTA | 8 CFR § 239.1 | 3 |

Standalone `scripts/validate_hybrid_retrieval_results.py` still uses its **own** RRF copy; API/chat use `RetrievalService` with the new logic.

---

## How to re-run

```bash
uv run --project backend python Review/scripts/validate_mvp_golden_retrieval.py
uv run --project backend python Review/scripts/validate_mvp_golden_retrieval.py --output
uv run --project backend python -m unittest discover -s tests -p 'test_*.py'
```

---

## Acceptance

| Criterion | Status |
|-----------|--------|
| Expected source in top 3 for most golden queries | **13/13** |
| Broad EAD can still trigger guided intake | Unchanged (`guided_intake.py`) |
| No regression on strong queries (asylum EAD, forms, address) | Improved or stable |
| Backend tests pass | `test_retrieval_scoring.py` + existing suite |
