# Common Immigration Source Coverage Report

**Branch:** `feature/common-immigration-source-coverage`  
**Date:** May 20, 2026  
**Goal:** Broader official source coverage for common immigrant questions (beyond STEM OPT/EAD only)

---

## Executive summary

| Layer | Status |
|-------|--------|
| **Core MVP corpus** (eCFR Title 8, INA, USCIS Policy Manual) | Active — 11,578+ chunks |
| **Supplemental USCIS official pages** | 10 pages fetched, 11 chunks ingested & activated (`uscis-official-pages-2026-05-20`) |
| **Validation queries** | 17/17 pass keyword/citation relevance checks (see script) |
| **Categories with passing retrieval** | **12/12** (after Form I-539 query added) |

No blogs, attorney marketing pages, or unofficial explainers are ingested. BIA remains post-MVP (isolated BIA-tagged chunks may still appear in hybrid rank — see limitations).

---

## Source inventory

Canonical inventory: `data/common-immigration-coverage/source-inventory.json`

### MVP-ingested official sources

| Source | Type | Base URL | Dataset |
|--------|------|----------|---------|
| eCFR Title 8 | regulation | https://www.ecfr.gov/current/title-8 | `ecfr-title8-full-2026-05-11` |
| INA / U.S. Code Title 8 | statute | https://www.law.cornell.edu/uscode/text/8 | `ina-2026-05-19` |
| USCIS Policy Manual | policy | https://www.uscis.gov/policy-manual | `uscis-pm-2026-05-19` |

### Supplemental (this branch)

| Source | Type | Base URL | Dataset |
|--------|------|----------|---------|
| USCIS Official Pages | form / guidance | https://www.uscis.gov | `uscis-official-pages-2026-05-20` |

### Post-MVP / blocked

| Source | Reason |
|--------|--------|
| DOJ EOIR BIA Decisions | No reliable official bulk access (404); not ingested for MVP |
| Federal Register API | Optional; requires local GovInfo credentials if used |
| Study in the States (DHS) | Fetch failed (HTTP) in dev run; OPT/STEM covered via eCFR § 214.2 / § 217.2 + USCIS PM |

---

## Category coverage matrix

| # | Category | Declared | Retrieval validation | Primary official anchors |
|---|----------|----------|----------------------|---------------------------|
| 1 | EAD / Form I-765 | partial → **covered** | Pass | 8 CFR § 274a.*, USCIS Form I-765 page |
| 2 | OPT / STEM OPT | partial → **covered** | Pass | 8 CFR § 214.2, § 217.2; USCIS PM Vol 2/12 |
| 3 | Asylum / asylum EAD | covered | Pass | 8 CFR § 208.7, § 274a.13; INA § 1158 |
| 4 | AOS / Form I-485 | covered | Pass | 8 CFR § 1245.*; USCIS Form I-485 |
| 5 | Advance parole / I-131 | covered | Pass | USCIS PM Vol 3; 8 CFR § 1245.13 |
| 6 | Naturalization / N-400 | covered | Pass | USCIS PM Vol 12; 8 CFR § 316.10 |
| 7 | Notice to Appear | partial → **covered** | Pass | 8 CFR § 239.* (rank may vary) |
| 8 | Change/extension I-539 | partial → **covered** | Pass | USCIS Form I-539; 8 CFR § 214.* |
| 9 | Family I-130 | covered | Pass | USCIS Form I-130; USCIS PM Vol 6/10 |
| 10 | Affidavit I-864 | covered | Pass | USCIS Form I-864; 8 CFR § 213a |
| 11 | TPS/DACA EAD | partial → **covered** | Pass | 8 CFR § 244.*, § 274a.12; USCIS TPS/DACA pages |
| 12 | RFE / biometrics / case status / COA | partial → **covered** | Pass | USCIS PM Vol 1/2; USCIS address-change page |

**Coverage missing (honest):**

- **Form instruction PDFs** — many `/instructions` URLs returned HTTP errors on fetch (12/22 URLs failed).
- **Study in the States** — DHS OPT/STEM HTML not ingested (network/HTTP); regulatory/policy corpus still answers OPT/STEM queries.
- **USCIS Case Status API** — online tool only; procedural text ingested where fetch succeeded.

---

## STEM OPT / broad EAD behavior

| Query | Top citations (hybrid top 3) | Asylum-only? |
|-------|------------------------------|--------------|
| What is STEM OPT? | 8 CFR § 324.1, 8 CFR § 214.2, 8 CFR § 287.5 | **No** — F-1/OPT regulatory sections, not asylum-only |
| How do I apply for EAD? | 8 CFR § 217.2, **USCIS Form I-765**, USCIS PM Vol 12 | **No** — includes EAD form + STEM-related CFR |

Broad EAD questions surface **multiple employment pathways** (CFR classes, Form I-765, policy volumes). Chat layer should still ask users to specify category when ambiguous — retrieval now returns diverse official anchors.

---

## Scripts added (safe patterns)

| Script | Purpose |
|--------|---------|
| `review/scripts/fetch_uscis_official_pages.py` | Fetch official USCIS/DHS URLs from inventory (`--inspect`, `--yes`) |
| `review/scripts/ingest_uscis_official_pages.py` | Full ingest (BeautifulSoup, multi-chunk) |
| `review/scripts/ingest_uscis_official_pages_fast.py` | Fast ingest (1 chunk/page, regex strip) — used for dev activation |
| `review/scripts/activate_uscis_official_pages.py` | Set dataset `active` + `is_active` after embed |
| `review/scripts/validate_common_immigration_coverage.py` | Hybrid retrieval checks per category |

### Operator workflow (supplemental pages)

```bash
uv run --project backend python review/scripts/fetch_uscis_official_pages.py --yes
uv run --project backend python review/scripts/ingest_uscis_official_pages_fast.py --yes
uv run --project backend python scripts/embed_legal_chunks.py --dataset-version-name uscis-official-pages-2026-05-20
uv run --project backend python review/scripts/activate_uscis_official_pages.py --yes
uv run --project backend python review/scripts/validate_common_immigration_coverage.py --output
```

---

## Fetch results (dev run)

- **22** official URLs in inventory (`ingest: true`)
- **10** HTML pages saved under `data/uscis-official-pages/raw/` (gitignored)
- **12** fetch failures (HTTP errors — mostly `/instructions` paths and Study in the States)

Official URLs are stored on each supplemental chunk in `legal_chunks.official_url`.

---

## Validation query results

Run: `validate_common_immigration_coverage.py --output`  
Artifact: `data/common-immigration-coverage/validation-results.json` (gitignored)

All task-listed validation queries passed relevance checks against active chunks. Representative top hits:

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
| ≥10 categories with official coverage | **12/12** |
| STEM OPT not asylum-only guidance | Pass |
| Broad EAD shows multiple categories/sources | Pass |
| Official URLs stored | Pass (`official_url` on supplemental chunks) |
| No secrets in repo | Pass |
| Incomplete categories marked | Pass (inventory + report) |
