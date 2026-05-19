# Immigration Law Guidance App — Ingestion Master Plan

**Generated:** May 19, 2026  
**Status:** MVP sources ingested (eCFR, USCIS PM, INA) · BIA post-MVP

---

## MVP Source Readiness Summary

| Source | Status | Chunks (active) | Embeddings | URL type |
|--------|--------|-----------------|------------|----------|
| **eCFR Title 8** | MVP-ready | 9,314 | 9,314 | `https://www.ecfr.gov/current/title-8/section-*` |
| **USCIS Policy Manual** | MVP-ready | 877 | 877 | USCIS PM chapter citations; base `uscis.gov/policy-manual` |
| **INA / U.S. Code Title 8** | MVP-ready | 1,387 | 1,387 | `8 U.S.C. § …` (Cornell LII ingest) |
| **BIA Decisions** | Post-MVP (blocked) | 0 | 0 | Not required for MVP |

Details: `validation/mvp-source-validation-report.md`

---

## Source registry (10 planned sources)

| # | Source | Type | MVP status |
|---|--------|------|------------|
| 1 | eCFR Title 8 | Regulation | ✅ Ingested & active |
| 2 | USCIS Policy Manual | Policy | ✅ Ingested & active |
| 3 | U.S. Code Title 8 (INA) | Statute | ✅ Ingested & active |
| 4 | DOJ EOIR BIA Decisions | Case law | ❌ Post-MVP (blocked) |
| 5 | Federal Register Immigration | Regulation | Not ingested |
| 6 | USCIS Forms and Instructions | Form | Not ingested |

---

## eCFR Title 8 — complete

**Dataset:** `ecfr-title8-full-2026-05-11` (active)  
**Chunks:** 9,314 · **Embeddings:** 100%  
**Docs:** `01-ecfr-ingestion-status.md`

---

## USCIS Policy Manual — complete

**Dataset:** `uscis-pm-2026-05-19` (active)  
**Chunks:** 877 · **Embeddings:** 100%  
**Docs:** `02-uscis-policy-manual-plan.md`

---

## INA (U.S. Code Title 8) — complete

**Dataset:** `ina-2026-05-19` (active)  
**Chunks:** 1,387 · **Embeddings:** 100%  
**Docs:** `03-ina-ingestion-plan.md`  
**Ingest path:** `review/scripts/ingest_ina_cornell.py`

---

## BIA decisions — post-MVP (blocked)

**Chunks:** 0  
**Blocker:** Official DOJ/EOIR URLs return 404; no reliable public bulk source confirmed.  
**Docs:** `04-bia-decisions-challenge-report.md`, `04-bia-decisions-plan.md`

---

## Known limitations

- Three dataset versions are `active` simultaneously (multi-source MVP); legacy `validate_active_dataset.py` expects one.
- USCIS PM and INA chunks often lack per-chunk `official_url` (citations still present).
- BIA is out of scope until an official source is confirmed.

## Next post-MVP data tasks

1. BIA source acquisition (FOIA / EOIR)
2. Backfill official URLs for USCIS PM and INA
3. Optional: Federal Register, USCIS forms
4. Align dataset activation policy with validation scripts

---

**Last updated:** May 19, 2026
