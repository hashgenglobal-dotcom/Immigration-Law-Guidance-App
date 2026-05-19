# Full Ingestion Pipeline — MVP Status

**Date:** May 19, 2026  
**Status:** 3 MVP sources dev-validated · BIA post-MVP

---

## MVP Source Readiness Summary

| Source | Status | Chunks (active) | Embeddings | Source URL type |
|--------|--------|-----------------|------------|-----------------|
| **eCFR Title 8** | MVP-ready | 9,314 | 9,314 (100%) | `ecfr.gov` per-section URLs |
| **USCIS Policy Manual** | MVP-ready | 877 | 877 (100%) | Chapter-level citations; `uscis.gov/policy-manual` |
| **INA / U.S. Code Title 8** | MVP-ready | 1,387 | 1,387 (100%) | `8 U.S.C. § …`; Cornell LII |
| **BIA Decisions** | Post-MVP (blocked) | 0 | 0 | Not required for MVP |

**Total:** 11,583 chunks · 11,583 embedded · **3 active datasets** (`ecfr-title8-full-2026-05-11`, `uscis-pm-2026-05-19`, `ina-2026-05-19`)

Validation report: `validation/mvp-source-validation-report.md`

---

## Completed MVP sources

### 1. eCFR Title 8
- Dataset `ecfr-title8-full-2026-05-11` — 9,314 chunks, all embedded
- Official links on every active chunk (`ecfr.gov`)

### 2. INA (8 U.S.C.)
- Dataset `ina-2026-05-19` — 1,387 chunks, all embedded
- 273 sections via Cornell LII

### 3. USCIS Policy Manual
- Dataset `uscis-pm-2026-05-19` — 877 chunks, all embedded
- 451 chapters across 12 volumes

---

## Post-MVP: BIA decisions

**Status:** Blocked — 0 chunks. Official EOIR URLs unavailable. See `04-bia-decisions-challenge-report.md`.

The three MVP sources cover regulations, agency policy, and statutes for typical user questions.

---

## Known limitations

1. Legacy validators (`validate_active_dataset.py`, `validate_hybrid_retrieval_results.py`) target the 5-chunk sample milestone — they fail on full MVP data (documented in validation report).
2. Three co-active datasets — intentional for multi-source retrieval; may show “leaked active chunks” in strict single-dataset checks.
3. USCIS / INA chunks often missing `official_url` field (text + citation still present).

## Next post-MVP data tasks

- BIA ingestion when source is confirmed
- URL backfill for USCIS PM and INA
- Optional additional sources in `source_registry`

---

**Not production-ready.** MVP data pipeline only.
