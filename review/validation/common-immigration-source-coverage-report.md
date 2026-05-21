# Common Immigration Source Coverage Report

**Branch:** `feature/common-immigration-source-coverage`
**Date:** May 21, 2026
**Author:** Rishi Raj Kanukuntla

---

> **Reviewer note — local DB state:**
> During Rishi's local review, the scripts compiled and the source inventory was structurally valid, but
> full coverage endpoint validation could not be completed because Rishi's local PostgreSQL still
> contains only the sample eCFR dataset (`ecfr-title8-sample-2026-05-11`, 5 chunks).
> The query validation results claimed in this report (17/17 pass, 12/12 categories) were produced in
> a teammate's full-data environment and have not been reproduced locally. This branch should be treated
> as **source coverage tooling and source inventory** — not final proof that coverage is active locally.
> To reproduce locally: follow the MVP DB rebuild guide (`scripts/mvp_data/README.md`) to import the
> full corpus, then re-run `validate_common_immigration_coverage.py --output`.

---

## Executive summary

| Layer | Status |
|-------|--------|
| **Core MVP corpus** (eCFR Title 8, INA, USCIS Policy Manual) | Prepared — pending local DB rebuild/import |
| **Supplemental USCIS official pages** | Scripts added; ingestion prepared; pending full DB rebuild |
| **Source inventory** | Validated (12 categories, official-only URLs) |
| **Retrieval validation queries** | Validated after import in teammate environment (17/17); **pending local DB rebuild on Rishi's machine** |
| **Categories with passing retrieval** | Validated after import in teammate environment (12/12); **pending local DB rebuild on Rishi's machine** |

No blogs, attorney marketing pages, or unofficial explainers are ingested. BIA remains post-MVP.

---

## Source inventory

Canonical inventory: `data/common-immigration-coverage/source-inventory.json`

### MVP-ingested official sources (teammate / full-data environment)

| Source | Type | Base URL | Dataset |
|--------|------|----------|---------|
| eCFR Title 8 | regulation | https://www.ecfr.gov/current/title-8 | `ecfr-title8-full-2026-05-11` |
| INA / U.S. Code Title 8 | statute | https://www.law.cornell.edu/uscode/text/8 | `ina-2026-05-19` |
| USCIS Policy Manual | policy | https://www.uscis.gov/policy-manual | `uscis-pm-2026-05-19` |

### Supplemental (this branch — scripts added, activation pending full DB rebuild)

| Source | Type | Base URL | Dataset |
|--------|------|----------|---------|
| USCIS Official Pages | form / guidance | https://www.uscis.gov | `uscis-official-pages-YYYY-MM-DD` |

### Post-MVP / blocked

| Source | Reason |
|--------|--------|
| DOJ EOIR BIA Decisions | No reliable official bulk access (404); not ingested for MVP |
| Federal Register API | Optional; requires local GovInfo credentials if used |
| Study in the States (DHS) | Fetch failed (HTTP) in dev run; OPT/STEM covered via eCFR § 214.2 / § 217.2 + USCIS PM |

---

## Category coverage matrix

Declared coverage below reflects the source inventory and teammate-environment validation.
**All "Retrieval validation" entries below are pending local DB rebuild on Rishi's machine.**

| # | Category | Declared | Retrieval validation | Primary official anchors |
|---|----------|----------|----------------------|---------------------------|
| 1 | EAD / Form I-765 | partial → covered | Validated after import | 8 CFR § 274a.*, USCIS Form I-765 page |
| 2 | OPT / STEM OPT | partial → covered | Validated after import | 8 CFR § 214.2, § 217.2; USCIS PM Vol 2/12 |
| 3 | Asylum / asylum EAD | covered | Validated after import | 8 CFR § 208.7, § 274a.13; INA § 1158 |
| 4 | AOS / Form I-485 | covered | Validated after import | 8 CFR § 1245.*; USCIS Form I-485 |
| 5 | Advance parole / I-131 | covered | Validated after import | USCIS PM Vol 3; 8 CFR § 1245.13 |
| 6 | Naturalization / N-400 | covered | Validated after import | USCIS PM Vol 12; 8 CFR § 316.10 |
| 7 | Notice to Appear | partial → covered | Validated after import | 8 CFR § 239.* (rank may vary) |
| 8 | Change/extension I-539 | partial → covered | Validated after import | USCIS Form I-539; 8 CFR § 214.* |
| 9 | Family I-130 | covered | Validated after import | USCIS Form I-130; USCIS PM Vol 6/10 |
| 10 | Affidavit I-864 | covered | Validated after import | USCIS Form I-864; 8 CFR § 213a |
| 11 | TPS/DACA EAD | partial → covered | Validated after import | 8 CFR § 244.*, § 274a.12; USCIS TPS/DACA pages |
| 12 | RFE / biometrics / case status / COA | partial → covered | Validated after import | USCIS PM Vol 1/2; USCIS address-change page |

**Coverage missing (honest):**

- **Form instruction PDFs** — many `/instructions` URLs returned HTTP errors on fetch (12/22 URLs failed).
- **Study in the States** — DHS OPT/STEM HTML not ingested (network/HTTP); regulatory/policy corpus still answers OPT/STEM queries.
- **USCIS Case Status API** — online tool only; procedural text ingested where fetch succeeded.

---

## Scripts added (safe patterns)

| Script | Purpose |
|--------|---------|
| `review/scripts/fetch_uscis_official_pages.py` | Fetch official USCIS/DHS URLs from inventory (`--inspect`, `--yes`); bs4 is a lazy import (only needed for `--yes`) |
| `review/scripts/ingest_uscis_official_pages.py` | Full ingest (BeautifulSoup, multi-chunk) |
| `review/scripts/ingest_uscis_official_pages_fast.py` | Fast ingest (1 chunk/page, regex strip) — used for dev activation |
| `review/scripts/activate_uscis_official_pages.py` | Set dataset `active` + `is_active` after embed |
| `review/scripts/validate_common_immigration_coverage.py` | Hybrid retrieval checks per category |

### Operator workflow (after full MVP DB rebuild)

```bash
uv run --project backend python review/scripts/fetch_uscis_official_pages.py --yes
uv run --project backend python review/scripts/ingest_uscis_official_pages_fast.py --yes
uv run --project backend python scripts/embed_legal_chunks.py --dataset-version-name uscis-official-pages-$(date +%Y-%m-%d)
uv run --project backend python review/scripts/activate_uscis_official_pages.py --yes
uv run --project backend python review/scripts/validate_common_immigration_coverage.py --output
```

---

## Fetch results (teammate dev run)

- **22** official URLs in inventory (`ingest: true`)
- **10** HTML pages saved under `data/uscis-official-pages/raw/` (gitignored)
- **12** fetch failures (HTTP errors — mostly `/instructions` paths and Study in the States)

Official URLs are stored on each supplemental chunk in `legal_chunks.official_url`.

---

## Validation query results

Environment: teammate's full-data local DB (eCFR full + INA + USCIS PM + supplemental pages active).
**Not yet reproduced on Rishi's local DB** (sample-only as of 2026-05-21).

Run after full DB rebuild:
```bash
uv run --project backend python review/scripts/validate_common_immigration_coverage.py --output
```
Artifact: `data/common-immigration-coverage/validation-results.json` (gitignored)

Representative top hits (teammate environment):

- **Form I-765** → `USCIS Form I-765` (official page chunk) + 8 CFR § 214.2
- **Asylum EAD** → 8 CFR § 208.7 + USCIS Form I-765 (EAD filing context)
- **STEM OPT** → 8 CFR § 214.2 (not asylum-only top 3)
- **Advance parole** → USCIS PM Vol 3 + 8 CFR § 1245.13
- **Change of address** → `USCIS Official Page` (addresschange) + Vol 1 Part A

---

## Known limitations

1. **Hybrid ranking** — Top-5 order may include tangential CFR sections; citations remain official.
2. **Single chunk per supplemental page** — Fast ingest trades depth for stability; expand with full ingest when local DB has headroom.
3. **BIA snippets** — If legacy BIA-tagged chunks remain `is_active`, they may appear in results; BIA is not an MVP authoritative source.
4. **Multi-active datasets** — Four active datasets (eCFR, INA, USCIS PM, official pages) unless activation policy is consolidated.
5. **No secrets committed** — `data/*` gitignored; scripts read `backend/.env` locally only.

---

## Acceptance checklist

| Criterion | Status |
|-----------|--------|
| Source inventory complete (12 categories, official-only URLs) | Prepared |
| Scripts compile without errors | Prepared |
| `--inspect` works without bs4 | Prepared |
| STEM OPT not asylum-only guidance | Validated after import (teammate env) |
| Broad EAD shows multiple categories/sources | Validated after import (teammate env) |
| Official URLs stored on supplemental chunks | Validated after import (teammate env) |
| No secrets in repo | Prepared |
| Incomplete categories marked | Prepared (inventory + report) |
| Full endpoint validation on Rishi's local DB | **Pending local DB rebuild** |
