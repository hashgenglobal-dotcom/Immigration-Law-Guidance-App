# Reproducible MVP Database Pipeline — Branch Report

**Branch:** `feature/reproducible-mvp-database-pipeline`
**Date:** May 21, 2026
**Author:** Rishi Raj Kanukuntla

---

## Why This Branch Exists

Rishi's local PostgreSQL only had the sample eCFR dataset:

| Dataset | Status | Chunks |
|---------|--------|--------|
| `ecfr-title8-sample-2026-05-11` | ready | 5 |

The three MVP production datasets (`ecfr-title8-full-*`, `ina-*`, `uscis-pm-*`)
existed only in a teammate's local environment. There was no documented,
repeatable way to rebuild the MVP corpus from scratch.

This means:
- Local backend queries returned at most 5 chunks.
- The sample dataset could become `active` accidentally and appear in API responses.
- A fresh developer environment had no clear path to a working local DB.

This branch adds a reproducible pipeline so any developer can rebuild the MVP
corpus locally without depending on a hidden teammate environment.

---

## What Was Added

### `scripts/mvp_data/` — new folder

| File | Purpose |
|------|---------|
| `README.md` | Full local rebuild guide: prerequisites, DATABASE_URL setup, all pipeline stages, expected final state, validation commands |
| `source_inventory.json` | Official source URLs covering 12 immigration topic areas (EAD, OPT/STEM OPT, asylum, AOS, advance parole, naturalization, NTA/removal, change of status, family petition, affidavit of support, TPS/DACA, RFE/biometrics) |
| `validate_mvp_database.py` | Read-only validation script: lists all dataset_versions, checks active datasets, counts chunks and embeddings per dataset, confirms sample is not active, checks MVP prefix coverage, exits non-zero on FAIL |
| `set_mvp_active_datasets.py` | Dry-run by default; `--apply` to activate MVP datasets and demote sample to `ready`; no deletes; transaction-safe |
| `rebuild_mvp_database.py` | Orchestrator with `--dry-run`, `--skip-fetch`, `--skip-insert`, `--skip-embed`, `--reset` (guarded with interactive confirmation) |

No changes to mobile, frontend, ingestion scripts, migrations, or the backend
application code. No secrets committed.

---

## How This Solves the Problem

### Before this branch

1. Fresh clone → local DB has only the 5-chunk sample.
2. No script existed that validated whether all three MVP sources were active.
3. No script existed to atomically activate all three MVP datasets and demote the sample.
4. No source inventory documented which official URLs backed each topic.

### After this branch

```bash
# 1. Check current state
uv run --project backend python scripts/mvp_data/validate_mvp_database.py

# 2. If datasets exist but are not active:
uv run --project backend python scripts/mvp_data/set_mvp_active_datasets.py --apply

# 3. Verify
uv run --project backend python scripts/mvp_data/validate_mvp_database.py
```

Or for a full rebuild:

```bash
uv run --project backend python scripts/mvp_data/rebuild_mvp_database.py --dry-run
# Review the plan, then:
uv run --project backend python scripts/mvp_data/rebuild_mvp_database.py --skip-fetch --skip-insert
```

---

## What Remains Manual

Full pipeline automation requires two steps not yet scripted:

### 1. Full eCFR Title 8 fetch and insert

The existing `scripts/fetch_ecfr_title8_sample.py` fetches only 5 sections.
A full-corpus fetcher (all ~9,300 chunks) is needed.

**Workaround until automated:**
```bash
DATE=$(curl -s "https://www.ecfr.gov/api/versioner/v1/titles" \
    | python3 -c "import sys,json; d=json.load(sys.stdin); \
      t=[t for t in d['titles'] if t['number']==8][0]; print(t['latest_issue_date'])")

curl -o "data/ecfr_full/title-8-${DATE}.xml" \
    "https://www.ecfr.gov/api/versioner/v1/full/${DATE}/title-8.xml"
```

Then a full-corpus insert script is needed to parse and chunk this XML.

### 2. INA and USCIS PM fetch and insert

No fetch or insert scripts exist yet for:
- INA / U.S. Code Title 8 (XML available from uscode.house.gov)
- USCIS Policy Manual (no public bulk API; requires web scraping or export)

**Workaround until automated:**
Export a `pg_dump` from a correctly-loaded environment (excluding user data
tables) and import locally. Full instructions in
`scripts/mvp_data/README.md §7`.

---

## BIA Exclusion Note

BIA (Board of Immigration Appeals) decisions remain **post-MVP**. No BIA
ingestion scripts, dataset versions, or chunk data exist. The
`source_registry` table contains a `DOJ EOIR BIA Decisions` row for future
use with zero chunks attached. BIA citations will not appear in retrieval
results until a separate ingestion milestone is completed.

`set_mvp_active_datasets.py` only activates datasets matching
`ecfr-title8-full-*`, `ina-*`, and `uscis-pm-*`. It will never accidentally
activate a BIA dataset even if one is inserted later.

---

## Dataset Activation Safety

`set_mvp_active_datasets.py` design decisions:

- **No deletes.** Only `UPDATE dataset_versions.status` and
  `UPDATE legal_chunks.is_active`. Rows are never removed.
- **Dry-run by default.** Requires `--apply` to write. Without `--apply`
  the script prints the plan and exits 1.
- **Transaction-safe.** All updates for one run are in a single transaction.
  On any failure the transaction rolls back; no partial state.
- **Scoped to known prefixes.** Only `ecfr-title8-full-*`, `ina-*`, `uscis-pm-*`
  are activated. Everything else is left unchanged.
- **No credential exposure.** DATABASE_URL is never printed.

---

## Source Inventory Coverage

`source_inventory.json` covers 12 MVP topic areas with official government URLs:

| Topic | eCFR | INA | USCIS PM | Form page |
|-------|------|-----|----------|-----------|
| EAD / I-765 | § 274a.12, § 274a.13 | § 1324a | Vol 10 | I-765 |
| OPT / STEM OPT | § 214.2(f) | — | Vol 2 Part F | — |
| Asylum / Asylum EAD | Part 208, § 208.7 | § 1158 | Vol 1 Part E | I-589 |
| Adjustment of Status / I-485 | Part 245, § 245.1 | § 1255 | Vol 7 | I-485 |
| Advance Parole / I-131 | § 223.2, § 212.5 | § 1182(d)(5) | Vol 3 Part F | I-131 |
| Naturalization / N-400 | Part 316, § 316.10 | § 1427, § 1430 | Vol 12 | N-400 |
| NTA / Removal | Part 239, Part 1240 | § 1229, § 1229a | — | — |
| Change/Extension of Status / I-539 | § 214.1, § 248.1 | § 1258 | Vol 2 Part F | I-539 |
| Family Petition / I-130 | Part 204 | § 1151, § 1153 | Vol 6 Part B | I-130 |
| Affidavit of Support / I-864 | Part 213a | § 1183a | — | I-864 |
| TPS / DACA Work Auth | Part 244, § 274a.12(c)(14) | § 1254a | — | — |
| RFE / Biometrics / CoA | § 103.2, § 103.16, § 265.1 | § 1305 | Vol 1 Part A Ch 6 | AR-11 |

All URLs point to uscis.gov, ecfr.gov, uscode.house.gov, or
studyinthestates.dhs.gov. No blogs or law firm pages.

---

## Expected Next Validation Commands

After importing or rebuilding the full corpus:

```bash
# 1. Validate database state
uv run --project backend python scripts/mvp_data/validate_mvp_database.py
# Expected: RESULT: PASS

# 2. Confirm retrieval returns all three source families
curl -s -X POST http://localhost:8000/api/retrieve \
    -H "Content-Type: application/json" \
    -d '{"query": "naturalization good moral character", "top_k": 5}' \
    | python3 -c "
import sys, json; d = json.load(sys.stdin)
print('active_datasets:', d.get('active_datasets'))
print('mvp_sources:', d.get('mvp_sources'))
for r in d.get('results',[]): print(' -', r.get('source_family'), r.get('citation'))
"

# 3. Confirm no sample chunks in retrieval
curl -s -X POST http://localhost:8000/api/retrieve \
    -H "Content-Type: application/json" \
    -d '{"query": "immigration", "top_k": 20}' \
    | python3 -c "
import sys, json; d = json.load(sys.stdin)
sample = [r for r in d.get('results',[]) if 'sample' in (r.get('dataset_version') or '')]
print(f'Sample chunks in top-20: {len(sample)} (expected 0)')
"

# 4. Confirm chat response has correct source fields
curl -s -X POST http://localhost:8000/api/chat \
    -H "Content-Type: application/json" \
    -d '{"message": "What is advance parole?"}' \
    | python3 -c "
import sys, json; d = json.load(sys.stdin)
print('mvp_sources:', d.get('mvp_sources'))
print('active_datasets:', d.get('active_datasets'))
"
```

---

## Files Changed in This Branch

```
A  scripts/mvp_data/README.md
A  scripts/mvp_data/source_inventory.json
A  scripts/mvp_data/validate_mvp_database.py
A  scripts/mvp_data/set_mvp_active_datasets.py
A  scripts/mvp_data/rebuild_mvp_database.py
A  review/validation/reproducible-mvp-database-pipeline-report.md
```

No backend application code, mobile, or frontend files were modified.
No secrets, credentials, or raw data artifacts were committed.
