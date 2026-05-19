# Complete Ingestion Report

**Generated:** May 19, 2026  
**Status:** MVP data pipeline — 3 sources operational · BIA post-MVP

---

## MVP Source Readiness Summary

| Source | Status | Chunks (active) | Embeddings | Source URL type |
|--------|--------|-----------------|------------|-----------------|
| **eCFR Title 8** | MVP-ready (dev-validated) | 9,314 | 9,314 | `https://www.ecfr.gov/current/title-8/section-*` |
| **USCIS Policy Manual** | MVP-ready (dev-validated) | 877 | 877 | USCIS PM volume/chapter citations; base `https://www.uscis.gov/policy-manual` |
| **INA / U.S. Code Title 8** | MVP-ready (dev-validated) | 1,387 | 1,387 | `8 U.S.C. § …`; Cornell LII (`law.cornell.edu/uscode/text/8`) |
| **BIA Decisions** | **Post-MVP — blocked** | **0** | **0** | Registry only; no working ingestion |

**Validation:** `validation/mvp-source-validation-report.md`

---

## Executive summary

| Source | Type | Chunks | Embedded | Dataset | Status |
|--------|------|--------|----------|---------|--------|
| eCFR Title 8 | Regulations | 9,314 | 9,314 | `ecfr-title8-full-2026-05-11` | Active |
| INA (8 U.S.C.) | Statutes | 1,387 | 1,387 | `ina-2026-05-19` | Active |
| USCIS Policy Manual | Policy | 877 | 877 | `uscis-pm-2026-05-19` | Active |
| BIA Decisions | Case law | 0 | 0 | — | Post-MVP |
| **Total** | | **11,583** | **11,583** | | |

Plus 5 sample eCFR chunks in `ecfr-title8-sample-2026-05-11` (`ready` status).

---

## Source 1: eCFR Title 8

- **Ingestion:** May 11–16, 2026
- **Chunks:** 9,314 active (full Title 8)
- **Embeddings:** nomic-embed-text (768-dim, local Ollama)
- **URLs:** All active chunks have `ecfr.gov` section links

---

## Source 2: USCIS Policy Manual

- **Ingestion:** May 19, 2026
- **Chunks:** 877 (451 chapters)
- **Embeddings:** 100%
- **URLs:** Chapter citations; per-chunk `official_url` often null (limitation)

---

## Source 3: INA (U.S. Code Title 8)

- **Ingestion:** May 19, 2026 via Cornell LII
- **Chunks:** 1,387
- **Embeddings:** 100%
- **URLs:** Statute citations (`8 U.S.C. § …`); per-chunk `official_url` often null (limitation)

---

## BIA decisions — post-MVP

- **Chunks:** 0
- **Reason:** Official DOJ/EOIR precedent URLs return 404; no confirmed bulk source
- **MVP impact:** None — eCFR + USCIS PM + INA cover MVP retrieval needs
- **Details:** `04-bia-decisions-challenge-report.md`

---

## Retrieval (dev-validated)

- Hybrid search: vector + keyword + RRF via `search_legal_chunks()`
- Smoke queries (May 19 validation) return relevant INA citations; eCFR and USCIS PM present in corpus
- Strict legacy hybrid tests (`validate_hybrid_retrieval_results.py`) fail rank-1 CFR expectations — see validation report

---

## Known limitations

1. Three simultaneous `active` dataset versions (multi-source MVP).
2. USCIS PM / INA lack per-chunk official URLs in many rows.
3. Milestone validation scripts do not pass against full corpus without updates.
4. `privacy_safe_answer_logs`: 27 rows in dev (milestone scripts expect 0).

## Next post-MVP data tasks

1. BIA source resolution and ingestion
2. Official URL backfill
3. Dataset activation policy + validator alignment
4. Optional: Federal Register, USCIS forms

---

## Quality assurance (read-only)

```bash
uv run --project backend python review/scripts/validate_active_dataset.py
uv run --project backend python review/scripts/validate_legal_chunk_embeddings.py
uv run --project backend python review/scripts/validate_hybrid_retrieval_results.py
```

See `validation/mvp-source-validation-report.md` for interpreted results.

---

**Last updated:** May 19, 2026
