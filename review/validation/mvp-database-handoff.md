# MVP Database Handoff (Task 1)

**Prepared:** May 21, 2026  
**Branch:** `feature/post-mvp` (documentation only — **do not merge to `main` until Rishi approves**)  
**Handoff method:** **Option 3** (source artifacts + import commands) is canonical. **Option 1** (sanitized dump) is optional for faster restore.

**No secrets in this doc.** Use your own `backend/.env` for `DATABASE_URL`. Do not commit `.env`, dumps, or `data/` to Git.

---

## Executive summary

| Item | Status |
|------|--------|
| MVP sources in dev DB | **Present** — eCFR full, INA, USCIS PM, USCIS official pages (11 chunks) |
| Embeddings (768-dim, nomic-embed-text) | **11,589** active embedded chunks for MVP datasets |
| eCFR sample (`ecfr-title8-sample-2026-05-11`) | Dataset `status=ready` but **5 chunks still `is_active=TRUE`** — **deactivate before MVP handoff** |
| BIA in dev DB | **25,412** active chunks, **0 embeddings** — **not MVP**; exclude from handoff |
| Sanitized dump on disk | `review/database/data-inserts.sql` (~161 MB, May 19) — **stale** vs current DB; regenerate before use |
| Schema in git | `review/database/schema-only.sql` (27 KB) |

---

## Recommended handoff path (Option 3)

Rishi recreates the DB locally from public sources using scripts below, then runs validation SQL.

### Prerequisites

```bash
# PostgreSQL 16+ with pgvector
# Ollama: nomic-embed-text
brew install postgresql@18   # or your PG install
export PATH="/opt/homebrew/opt/postgresql@18/bin:$PATH"

cd ~/projects/immigration-law-app-official
cp backend/.env.example backend/.env
# Edit DATABASE_URL, REDIS_URL, OLLAMA_* — never commit .env

# Apply schema
psql "$DATABASE_URL" -f database/migrations/001-initial-schema.sql
```

Use a libpq URL: `postgresql://USER@HOST:PORT/immigration_law_dev` (strip `+psycopg` if copied from `.env`).

### 1. eCFR Title 8 (full)

```bash
cd ~/projects/immigration-law-app-official
uv run --project backend python review/scripts/fetch_ecfr_title8_full.py --yes
# Or: scripts/fetch_ecfr_title8_full.py (duplicate under scripts/)
```

**Expected:** dataset `ecfr-title8-full-2026-05-11`, ~9,314 chunks, embedded, `status=active`.

**Raw XML (gitignored):** `data/ecfr/raw/`

**Do not activate sample:** `ecfr-title8-sample-2026-05-11` is for milestone tests only (5 sections).

### 2. INA / U.S. Code Title 8

```bash
uv run --project backend python review/scripts/ingest_ina_cornell.py --yes
uv run --project backend python scripts/embed_legal_chunks.py \
  --dataset-version-name ina-2026-05-19 --yes
```

**Expected:** ~1,387 chunks, dataset `ina-2026-05-19`, `status=active`.

**Raw (gitignored):** `data/ina/raw/`, `data/ina/preview/`

### 3. USCIS Policy Manual

```bash
uv run --project backend python review/scripts/ingest_uscis_pm.py --yes
uv run --project backend python scripts/embed_legal_chunks.py \
  --dataset-version-name uscis-pm-2026-05-19 --yes
```

**Expected:** ~877 chunks, dataset `uscis-pm-2026-05-19`, `status=active`.

**Raw (gitignored):** `data/uscis-pm/raw/`

### 4. USCIS / common immigrant official pages (optional MVP supplement)

```bash
uv run --project backend python review/scripts/fetch_uscis_official_pages.py --yes
uv run --project backend python review/scripts/ingest_uscis_official_pages.py --yes
uv run --project backend python scripts/embed_legal_chunks.py \
  --dataset-version-name uscis-official-pages-2026-05-20 --yes
```

**Expected:** ~10–11 chunks (dev had 11 after ingest), dataset `uscis-official-pages-2026-05-20`, `status=active`.

**Raw (gitignored):** `data/uscis-official-pages/raw/`

Fast path (MVP branch): `review/scripts/ingest_uscis_official_pages_fast.py`

---

## Option 1 — Sanitized PostgreSQL dump (off-repo transfer)

**Do not commit dumps to Git.** Share via secure drive or staging bucket.

### Generate MVP-only dump (recommended)

Run cleanup SQL first (see [Pre-export cleanup](#pre-export-cleanup)), then:

```bash
export PATH="/opt/homebrew/opt/postgresql@18/bin:$PATH"
cd ~/projects/immigration-law-app-official

# Schema (safe to keep in repo)
pg_dump "$DATABASE_URL" --schema-only \
  -f review/database/schema-only.sql

# Data — MVP corpus tables only (adjust -h/-p/-U from your .env)
pg_dump "$DATABASE_URL" --data-only --inserts \
  --table=source_registry \
  --table=raw_documents \
  --table=legal_documents \
  --table=legal_sections \
  --table=legal_chunks \
  --table=dataset_versions \
  --table=ingestion_jobs \
  -f review/database/mvp-data-inserts.sql
```

**Exclude from dump:** `privacy_safe_answer_logs`, `app_users`, `admin_users`, `scenario_guides` (no user PII; logs empty in current dev).

### Restore

```bash
createdb immigration_law_restore
psql immigration_law_restore -f review/database/schema-only.sql
psql immigration_law_restore -f review/database/mvp-data-inserts.sql
psql immigration_law_restore -f review/validation/mvp-database-snapshot-queries.sql
```

---

## Option 2 — Staging Postgres (not provisioned in repo)

If HashGen provides a shared staging instance:

- PostgreSQL **16+** with **pgvector** extension
- Ollama reachable from app network (or embed locally, upload vectors only)
- Load using Option 1 restore or Option 3 scripts
- Share connection string with Rishi via **1Password / vault** — not Git

---

## Live validation snapshot (May 21, 2026)

Environment: local dev, `immigration_law_dev`, port **54329** (from operator `.env`).

### `dataset_versions`

| id | version_name | status | total_chunks | embedded | active_chunks |
|----|----------------|--------|--------------|----------|---------------|
| 1 | ecfr-title8-sample-2026-05-11 | ready | 5 | 5 | **5** ⚠️ |
| 3 | ecfr-title8-full-2026-05-11 | active | 9,314 | 9,314 | 9,314 |
| 4 | uscis-pm-2026-05-19 | active | 877 | 877 | 877 |
| 5 | ina-2026-05-19 | active | 1,387 | 1,387 | 1,387 |
| 7 | uscis-official-pages-2026-05-20 | active | 11 | 11 | 11 |
| 10 | bia-2026-05-20 | active | 0 | 0 | 0 |
| 11 | bia-2026-05-21 | active | 25,412 | **0** | 25,412 |
| 12 | bia-2026-05-21-final | active | 0 | 0 | 0 |

### MVP-only totals (for handoff)

| Metric | Count |
|--------|------:|
| Active + embedded (MVP datasets only) | **11,589** |
| eCFR full | 9,314 |
| INA | 1,387 |
| USCIS PM | 877 |
| USCIS official pages | 11 |

### Which datasets are “active” for retrieval?

Retrieval uses `legal_chunks.is_active = TRUE` (not only `dataset_versions.status`).  
**MVP-intended active embedded sets:** rows tied to version names above (full eCFR, PM, INA, official pages).

**Not MVP-ready in current dev DB:**

- **eCFR sample:** 5 chunks with `is_active=TRUE` (dataset `ready`) — pollutes hybrid search
- **BIA:** 25,412 active chunks, **no embeddings** — breaks or skews retrieval

### eCFR sample confirmation

| Check | Result |
|-------|--------|
| `dataset_versions.status` for sample | `ready` (not `active`) |
| Sample chunks `is_active` | **TRUE (5)** — **should be FALSE for MVP handoff** |
| Sample in MVP embedded count if not cleaned | Included in leaked active set |

**Action:** run [Pre-export cleanup](#pre-export-cleanup) before sharing a dump or declaring MVP-ready.

### `source_registry` (public sources)

| source_name | source_type |
|-------------|-------------|
| eCFR Title 8 | regulation |
| USCIS Policy Manual | policy |
| U.S. Code Title 8 (INA) | statute |
| Immigration and Nationality Act | statute |
| USCIS Official Pages | form |
| DOJ EOIR BIA Decisions / BIA Precedent Decisions | case_law |
| Federal Register Immigration | regulation |
| USCIS Forms and Instructions | form |

### Privacy

| Table | Rows (dev) |
|-------|------------|
| `privacy_safe_answer_logs` | 0 |

---

## Pre-export cleanup

Run on the **source** database before pg_dump or handoff to Rishi:

```sql
-- Deactivate eCFR sample chunks (retrieval uses is_active, not dataset status)
UPDATE legal_chunks SET is_active = FALSE
WHERE dataset_version_id = (
  SELECT id FROM dataset_versions WHERE version_name = 'ecfr-title8-sample-2026-05-11'
);

-- Deactivate all BIA chunks (post-MVP; no embeddings in dev)
UPDATE legal_chunks SET is_active = FALSE
WHERE dataset_version_id IN (
  SELECT id FROM dataset_versions WHERE version_name LIKE 'bia%'
);

-- Optional: archive BIA dataset version rows
UPDATE dataset_versions SET status = 'archived'
WHERE version_name LIKE 'bia%';
```

Re-validate:

```bash
psql "$DATABASE_URL" -f review/validation/mvp-database-snapshot-queries.sql
```

---

## Validation commands (run after restore or ingest)

```bash
cd ~/projects/immigration-law-app-official

# 1. SQL snapshot
psql "$DATABASE_URL" -f review/validation/mvp-database-snapshot-queries.sql

# 2. Embedding coverage
uv run --project backend python review/scripts/validate_legal_chunk_embeddings.py

# 3. Common immigration retrieval (17 queries) — requires Ollama
uv run --project backend python review/scripts/validate_common_immigration_coverage.py

# 4. Golden retrieval (after MVP code merged)
uv run --project backend python review/scripts/validate_mvp_golden_retrieval.py
```

### Validation output (May 21, 2026 — this environment)

**`validate_common_immigration_coverage.py`:** **17/17** queries passed, **12/12** categories.

Sample top citations:

- EAD → `8 CFR § 217.2`, USCIS Form I-765  
- STEM OPT → `8 CFR § 214.2`, Vol 2 Part F  
- Asylum work → `8 CFR § 208.7`  
- Address change → USCIS Official Page chunk  

---

## Git artifacts (safe to commit)

| Path | Purpose |
|------|---------|
| `database/migrations/001-initial-schema.sql` | Schema (if present; else `review/database/schema-only.sql`) |
| `review/database/schema-only.sql` | Schema snapshot |
| `review/database/table-row-counts.txt` | Historical counts (regenerate) |
| `review/scripts/*.py` | Ingest / embed / validate |
| `data/**` | **Gitignored** — raw source files |

---

## Rishi checklist

- [ ] Use **Option 3** or fresh **Option 1** dump after cleanup SQL  
- [ ] Confirm **11,589** MVP active embedded chunks (after cleanup)  
- [ ] Confirm **eCFR sample chunks inactive**  
- [ ] Confirm **no BIA active chunks** in MVP DB  
- [ ] Set `OLLAMA_CHAT_MODEL` and run golden retrieval after MVP merge  
- [ ] Do **not** commit `.env`, dumps, or `data/`  

---

**Contact:** Update this file after staging dump is generated or shared DB is provisioned.
