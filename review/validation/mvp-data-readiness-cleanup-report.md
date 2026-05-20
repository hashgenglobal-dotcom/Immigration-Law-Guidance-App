# MVP Data Readiness Cleanup Report

**Branch:** `fix/mvp-data-readiness-cleanup`  
**Date:** May 20, 2026  
**Scope:** Backend retrieval/chat source selection and API source reporting (read-only DB validation)

---

## Executive summary

The backend was searching all `legal_chunks` with `is_active = TRUE`, which included five chunks from the non-MVP preview dataset `ecfr-title8-sample-2026-05-11` (`status = ready`). API `active_dataset` used `SELECT … LIMIT 1`, so responses could misleadingly show only the sample name.

**Fix:** Retrieval and keyword search now require `dataset_versions.status = 'active'`. Responses expose `active_datasets`, `mvp_sources`, and a backward-compatible `active_dataset` summary (`mvp-multi-source: …`). Per-chunk `dataset_version` and `source_family` are returned on retrieve and chat `used_chunks`.

There is **no combined MVP dataset row** — the design is **three co-active dataset versions**. Sample eCFR is excluded without any DB migration.

---

## Active dataset findings

### All dataset versions

| `version_name` | `status` | Total chunks | Embedded | `is_active` chunks |
|----------------|----------|--------------|----------|-------------------|
| `ecfr-title8-full-2026-05-11` | **active** | 9,314 | 9,314 | 9,314 |
| `ina-2026-05-19` | **active** | 1,387 | 1,387 | 1,387 |
| `uscis-pm-2026-05-19` | **active** | 877 | 877 | 877 |
| `ecfr-title8-sample-2026-05-11` | ready | 5 | 5 | 5 |

### Active MVP set (search scope after fix)

- **Active dataset count:** 3 (not one combined dataset)
- **Searchable active chunks:** 11,578 (`status = 'active'` AND `is_active = TRUE`)
- **Prior `is_active`-only count:** 11,583 (included 5 sample chunks — now excluded)

### Backend design

| Question | Answer |
|----------|--------|
| One active combined dataset? | **No** — gap documented; three co-active versions |
| Multiple active datasets? | **Yes** — retrieval queries all `status = 'active'` versions |
| BIA in MVP? | **No** — post-MVP; 0 chunks ingested |

### Source registry (read-only)

| `source_name` | `source_type` | MVP status |
|---------------|---------------|------------|
| eCFR Title 8 | regulation | Active via `ecfr-title8-full-*` |
| U.S. Code Title 8 (INA) / Immigration and Nationality Act | statute | Active via `ina-*` |
| USCIS Policy Manual | policy | Active via `uscis-pm-*` |
| DOJ EOIR BIA Decisions | case_law | **Post-MVP** — registry only |
| USCIS Forms and Instructions | form | Not ingested |
| Federal Register Immigration | regulation | Not ingested |

`dataset_versions` has no `source_registry_id` column; source family is inferred from `version_name` prefixes in `backend/app/services/mvp_source_scope.py`.

---

## Source coverage findings

| MVP source | Dataset version | Retrievable in hybrid tests |
|------------|-----------------|----------------------------|
| eCFR Title 8 | `ecfr-title8-full-2026-05-11` | Yes — appears in all seven query top-5 sets |
| INA / U.S. Code Title 8 | `ina-2026-05-19` | Yes — e.g. asylum/work auth query rank 4 |
| USCIS Policy Manual | `uscis-pm-2026-05-19` | Yes — GMC, STEM OPT, advance parole queries |
| eCFR sample (non-MVP) | `ecfr-title8-sample-2026-05-11` | **Excluded** from search (`ready` only) |
| BIA | — | **0 chunks** — post-MVP |

**API reporting (after fix):**

```json
{
  "active_dataset": "mvp-multi-source: ecfr-title8-full-2026-05-11, ina-2026-05-19, uscis-pm-2026-05-19",
  "active_datasets": ["ecfr-title8-full-2026-05-11", "ina-2026-05-19", "uscis-pm-2026-05-19"],
  "mvp_sources": ["eCFR Title 8", "INA / U.S. Code Title 8", "USCIS Policy Manual"]
}
```

---

## Query test results

Environment: local Postgres, Ollama `nomic-embed-text`, backend `POST /api/retrieve` (`top_k=5`). Chat source fields verified via `ChatService` with `OLLAMA_CHAT_MODEL=llama3.2:latest` (default `llama3.1:8b` is not installed locally → HTTP 503 on `/api/chat` until model env is set).

**Reported source set (all queries):** same `active_dataset` / `active_datasets` / `mvp_sources` as above.

### 1. Can asylum applicants get work authorization?

| Rank | Citation | Source family |
|------|----------|---------------|
| 1 | 8 CFR § 274a.13 | eCFR Title 8 |
| 2 | 8 CFR § 208.7 | eCFR Title 8 |
| 3 | 8 CFR § 208.7 | eCFR Title 8 |
| 4 | 8 U.S.C. § 1158 | INA / U.S. Code Title 8 |
| 5 | 8 CFR § 274a.13 | eCFR Title 8 |

**Useful:** Yes (asylum EAD / employment rules). **Coverage:** eCFR + INA in top 5; no USCIS PM in top 5 for this query.

### 2. What is a Notice to Appear?

| Rank | Citation | Source family |
|------|----------|---------------|
| 1–5 | 8 CFR § 287.5, 239.2, 324.1, 239.2, 292.3 | eCFR Title 8 only |

**Useful:** Partial — CFR removal/hearing provisions; may not be the canonical NTA definition users expect. **Coverage gap:** INA/USCIS PM not in top 5; rank fusion favored eCFR keyword matches.

### 3. What is adjustment of status?

| Rank | Citation | Source family |
|------|----------|---------------|
| 1–5 | 8 CFR § 1245.20, 1245.1, 106.3, 245a.22, 106.3 | eCFR Title 8 only |

**Useful:** Yes for regulatory AOS framework. **Coverage gap:** USCIS PM (common for practitioner AOS guidance) not in top 5 for this phrasing.

### 4. What is USCIS policy on naturalization good moral character?

| Rank | Citation | Source family |
|------|----------|---------------|
| 1 | Vol 12, Part D, Ch 9 | USCIS Policy Manual |
| 2 | Vol 12, Part F, Ch 1 | USCIS Policy Manual |
| 3 | 8 CFR § 316.10 | eCFR Title 8 |
| 4 | Vol 12, Part F, Ch 5 | USCIS Policy Manual |
| 5 | Vol 12, Part D, Ch 7 | USCIS Policy Manual |

**Useful:** Yes — strong USCIS PM hits. **Coverage:** USCIS PM + eCFR.

### 5. How do I apply for STEM OPT EAD?

| Rank | Citation | Source family |
|------|----------|---------------|
| 1 | 8 CFR § 217.2 | eCFR Title 8 |
| 2 | 8 CFR § 244.6 | eCFR Title 8 |
| 3 | Vol 12, Part K, Ch 3 | USCIS Policy Manual |
| 4 | Vol 2, Part P, Ch 5 | USCIS Policy Manual |
| 5 | Vol 3, Part B, Ch 3 | USCIS Policy Manual |

**Useful:** Yes — STEM OPT / EAD policy mix. **Coverage:** eCFR + USCIS PM; no INA in top 5.

### 6. What is Form I-765?

| Rank | Citation | Source family |
|------|----------|---------------|
| 1–5 | 8 CFR § 1208.4, 214.2, 1240.11, 214.2, 204.5 | eCFR Title 8 only |

**Useful:** Partial — regulatory references to EAD eligibility, not form instructions. **Coverage gap:** USCIS Forms source not ingested; no form-specific chunks.

### 7. What is advance parole?

| Rank | Citation | Source family |
|------|----------|---------------|
| 1 | Vol 3, Part F, Ch 1 | USCIS Policy Manual |
| 2 | Vol 3, Part B, Ch 12 | USCIS Policy Manual |
| 3 | 8 CFR § 1245.13 | eCFR Title 8 |
| 4 | 8 CFR § 244.15 | eCFR Title 8 |
| 5 | 8 CFR § 240.21 | eCFR Title 8 |

**Useful:** Yes. **Coverage:** USCIS PM + eCFR.

---

## Cleanup actions taken

| Change | File(s) |
|--------|---------|
| Restrict vector + keyword search to `dataset_versions.status = 'active'` | `backend/app/services/retrieval_service.py` |
| Return all active version names + multi-source summary | `retrieval_service.py`, `mvp_source_scope.py` |
| Add `active_datasets`, `mvp_sources`, per-chunk `dataset_version` / `source_family` | `schemas/retrieval.py`, `schemas/chat.py` |
| Wire routes and chat service to new fields | `api/routes/retrieval.py`, `services/chat_service.py` |

**Not done (by design):**

- No DB migrations or dataset activation scripts run
- No combined MVP dataset fabricated
- No mobile/frontend/ingestion changes

---

## Remaining limitations

1. **Multi-active policy** — Three simultaneous `active` rows; legacy `validate_active_dataset.py` still expects one active dataset.
2. **Rank fusion bias** — Top-5 results may be single-source for some queries even though all three corpora are searchable.
3. **USCIS Forms** — Not ingested; Form I-765 queries hit CFR, not form instructions.
4. **`official_url`** — Sparse on INA/USCIS PM chunks (see prior validation report).
5. **Local `/api/chat` LLM** — Default `OLLAMA_CHAT_MODEL=llama3.1:8b` may 503 if only `llama3.2` is installed; retrieval/source reporting is independent.
6. **BIA** — Post-MVP; `DOJ EOIR BIA Decisions` in registry with zero chunks.

---

## BIA post-MVP note

BIA decisions remain **out of scope** for MVP retrieval. The `source_registry` row exists for future case-law ingestion; no chunks are embedded or activated. Users should not expect BIA citations until a separate ingestion milestone resolves official source access (see `04-bia-decisions-challenge-report.md`).

---

## Acceptance checklist

| Criterion | Status |
|-----------|--------|
| eCFR retrievable | Pass |
| INA retrievable | Pass |
| USCIS Policy Manual retrievable | Pass |
| `/api/chat` / `/api/retrieve` do not imply sample-only dataset | Pass (multi-source summary) |
| BIA post-MVP | Pass (excluded) |
| No destructive DB changes | Pass |
| No secrets in repo/docs | Pass (validation used local `.env` only) |
