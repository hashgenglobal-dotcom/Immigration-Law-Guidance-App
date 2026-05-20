# Immigration Law App — Review Package

**Generated:** May 19, 2026  
**Branch:** `feature/mvp-source-validation`  
**Status:** MVP data pipeline — 3 sources dev-validated; BIA post-MVP

---

## MVP Source Readiness Summary

| Source | Status | Chunks (active) | Embeddings | URL type |
|--------|--------|-----------------|------------|----------|
| **eCFR Title 8** | MVP-ready | 9,314 | 9,314 (100%) | `ecfr.gov` section links on chunks |
| **USCIS Policy Manual** | MVP-ready | 877 | 877 (100%) | Chapter citations; base `uscis.gov/policy-manual` |
| **INA / U.S. Code Title 8** | MVP-ready | 1,387 | 1,387 (100%) | `8 U.S.C. § …`; Cornell LII ingest |
| **BIA Decisions** | Post-MVP (blocked) | 0 | 0 | Not required for MVP |

**Full validation:** `validation/mvp-source-validation-report.md` (commands, SQL outputs, limitations).

**MVP scope:** Regulations (eCFR) + policy (USCIS PM) + statutes (INA). Case law (BIA) is **post-MVP** — official source blocked; see `04-bia-decisions-challenge-report.md`.

---

## Package contents

```
review/
├── README.md
├── validation/
│   └── mvp-source-validation-report.md
├── 00-master-plan.md
├── 00-complete-ingestion-report.md
├── 00-full-ingestion-complete.md
├── 01-ecfr-ingestion-status.md
├── 02-uscis-policy-manual-plan.md
├── 03-ina-ingestion-plan.md
├── 04-bia-decisions-challenge-report.md
├── scripts/          # Ingestion + read-only validators
└── database/         # Schema reference + row counts (no secrets)
```

---

## Current system state

### Data coverage (MVP)

| Source | Chunks | Embeddings | Dataset version |
|--------|--------|------------|-----------------|
| eCFR Title 8 | 9,314 | 9,314 | `ecfr-title8-full-2026-05-11` |
| USCIS Policy Manual | 877 | 877 | `uscis-pm-2026-05-19` |
| INA (8 U.S.C.) | 1,387 | 1,387 | `ina-2026-05-19` |
| BIA Decisions | 0 | 0 | — |
| **Total** | **11,583** | **11,583** | 3 active + 1 sample (`ready`) |

### Database tables

See `database/table-row-counts.txt`.

---

## Read-only validation scripts

Run from repo root (requires `backend/.env` with `DATABASE_URL`; never commit `.env`):

```bash
uv run --project backend python review/scripts/validate_active_dataset.py
uv run --project backend python review/scripts/validate_legal_chunk_embeddings.py
uv run --project backend python review/scripts/validate_hybrid_retrieval_results.py
uv run --project backend python review/scripts/validate_retrieval_results.py
```

**Note:** `validate_active_dataset.py` and `validate_hybrid_retrieval_results.py` were written for the 5-chunk eCFR sample milestone. They **fail** against the full 3-source MVP corpus (expected). Use `validation/mvp-source-validation-report.md` for current MVP status.

---

## API (backend)

- `POST /api/chat` — grounded answer from active legal chunks (local Ollama only)
- `GET /health` — service health
- `POST /api/retrieve` — retrieval-only (if enabled in deployment)

No cloud LLM API keys are used. Configure `DATABASE_URL` and `OLLAMA_BASE_URL` in `backend/.env` (not in this folder).

---

## Legal disclaimer

General legal information only — not legal advice. Users should consult qualified immigration attorneys for case-specific guidance.

**Last updated:** May 19, 2026
