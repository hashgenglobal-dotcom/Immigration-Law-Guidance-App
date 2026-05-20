# MVP Source Validation Report

**Branch:** `feature/mvp-source-validation`  
**Validated:** May 19, 2026 (dev environment, read-only checks)  
**Validator:** Automated SQL + existing read-only scripts under `review/scripts/`

---

## MVP Source Readiness Summary

| Source | Status | Chunks (active) | Embeddings (768-dim) | Source URL type |
|--------|--------|-----------------|----------------------|-----------------|
| **eCFR Title 8** | MVP-ready (dev-validated) | 9,314 | 9,314 (100%) | `https://www.ecfr.gov/current/title-8/section-*` on all active chunks |
| **USCIS Policy Manual** | MVP-ready (dev-validated) | 877 | 877 (100%) | Policy Manual chapter citations (`Vol N, Part …`); `official_url` not populated on chunks — canonical base `https://www.uscis.gov/policy-manual` |
| **INA / U.S. Code Title 8** | MVP-ready (dev-validated) | 1,387 | 1,387 (100%) | `8 U.S.C. § …` citations; `official_url` not populated on chunks — ingest via Cornell LII (`https://www.law.cornell.edu/uscode/text/8`) |
| **BIA Decisions** | **Post-MVP — blocked** | **0** | **0** | Registry row exists; no chunks ingested. Official DOJ/EOIR URLs return 404 — see `04-bia-decisions-challenge-report.md` |

**Database totals (all dataset versions):** 11,583 `legal_chunks` · 11,583 with embeddings · 11,578 `is_active = TRUE` (includes 5 sample eCFR chunks in `ready` dataset)

**Active dataset versions (3 simultaneous):**

| ID | `version_name` | `status` | Active chunks |
|----|----------------|----------|---------------|
| 3 | `ecfr-title8-full-2026-05-11` | active | 9,314 |
| 4 | `uscis-pm-2026-05-19` | active | 877 |
| 5 | `ina-2026-05-19` | active | 1,387 |

**Retrieval (dev-validated):** `search_legal_chunks()` returns results for all five MVP smoke queries below. Top hits are primarily INA (`8 U.S.C. § …`) for tested questions; eCFR and USCIS PM chunks are present in the index and appear in hybrid tests (e.g. USCIS PM volumes for adjustment-of-status queries).

**BIA:** Zero chunks · source blocked · **not required for MVP**.

---

### Known limitations

1. **Three active datasets** — `validate_active_dataset.py` expects exactly one `active` row (milestone-era). Current MVP uses three co-active sources; `leaked active chunks` warning (10,196) is expected until a single-activation policy is chosen.
2. **USCIS PM / INA `official_url`** — Chunks have citations and text but often lack per-chunk `official_url`; eCFR chunks have full eCFR deep links.
3. **Legacy validation scripts** — `validate_active_dataset.py` and `validate_hybrid_retrieval_results.py` target the 5-chunk eCFR sample milestone; they **FAIL** against full MVP data (documented below).
4. **`privacy_safe_answer_logs`** — 27 rows (dev Q&A activity); milestone scripts expect 0.
5. **Hybrid rank strictness** — Synthetic hybrid tests did not rank exact `8 CFR § …` strings first for all five legacy test cases; MVP smoke queries still return on-topic statute/regulation citations.

### Next post-MVP data tasks

1. Resolve BIA official source (FOIA / EOIR relocation) before any case-law ingestion.
2. Backfill `official_url` on USCIS PM and INA chunks where possible.
3. Decide dataset activation policy (one active vs multi-active) and align validation scripts.
4. Optional: Federal Register, USCIS forms (registered in `source_registry`, not ingested).

---

## Validation commands and results

### 1. Active dataset / chunk counts (read-only SQL)

```bash
cd <repo-root>
uv run --project backend python -c "..."  # see commit; queries dataset_versions + legal_chunks
```

**Results:** 3 active datasets; 11,583 total chunks; 100% embedding coverage on MVP sources listed above.

### 2. `validate_active_dataset.py`

```bash
uv run --project backend python review/scripts/validate_active_dataset.py
```

**Exit code:** 1 (FAIL)  
**Reasons:** 3 active datasets (expected 1); 1,387 chunks on newest active INA set (expected 5 sample); missing sample CFR citations on INA-only check; 10,196 cross-dataset active chunks; `privacy_safe_answer_logs` count 27.

### 3. `validate_hybrid_retrieval_results.py`

```bash
uv run --project backend python review/scripts/validate_hybrid_retrieval_results.py --top-k 5
```

**Exit code:** 1 (FAIL)  
**Reasons:** 0/5 legacy synthetic tests passed strict `expected_rank_1` CFR checks (multi-source index returns USCIS PM and related CFR sections).

### 4. MVP smoke queries (`search_legal_chunks`, read-only)

| Query | Top citations returned (types) |
|-------|--------------------------------|
| Can asylum applicants get work authorization? | `8 U.S.C. § 1158`, `§ 1225` (INA) |
| What is a Notice to Appear? | `8 U.S.C. § …` (INA; NTA-specific CFR not in top 5) |
| What is adjustment of status? | `8 U.S.C. § 1255` (INA) |
| What is asylum eligibility? | `8 U.S.C. § 1158`, `§ 1182` (INA) |
| What is USCIS policy on naturalization good moral character? | `8 U.S.C. § 1443`, `§ 1427` (INA; USCIS PM not in top 5) |

**Interpretation:** INA retrieval is strong. eCFR is verified present (e.g. `8 CFR § 208.7` with eCFR URL). USCIS PM is in the corpus (877 chunks); ranking may prefer statutes for some queries until hybrid tuning or URL backfill.

### 5. Safety grep

```bash
A staged documentation safety scan was run against the review folder and returned no unsafe credential or private-identity matches.
```

**Result:** No matches in `review/*.{md,txt}`.

---

## Source registry

| `source_name` | `source_type` | `base_url` | MVP chunks |
|---------------|---------------|------------|------------|
| eCFR Title 8 | regulation | https://www.ecfr.gov/current/title-8 | 9,314 (+ 5 sample) |
| USCIS Policy Manual | policy | https://www.uscis.gov/policy-manual | 877 |
| U.S. Code Title 8 (INA) | statute | https://uscode.house.gov/browse.xhtml | 1,387 |
| DOJ EOIR BIA Decisions | case_law | https://www.justice.gov/eoir/bia-decisions | **0 (blocked)** |
| Federal Register Immigration | regulation | federalregister.gov | 0 (not ingested) |
| USCIS Forms and Instructions | form | uscis.gov/forms | 0 (not ingested) |
| Immigration and Nationality Act | statute | law.cornell.edu | (duplicate registry label; data in `ina-2026-05-19`) |

---

**Not production-ready.** This report describes **MVP data pipeline** state for developer review only.
