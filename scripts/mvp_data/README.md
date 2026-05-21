# MVP Data Pipeline — Local Rebuild Guide

This folder contains scripts to build or rebuild the MVP legal corpus locally.
Use this when your local PostgreSQL only has the sample eCFR dataset and you
need the full three-source MVP set.

---

## 1. Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| PostgreSQL | 14+ | Must be running locally with pgvector extension |
| pgvector | 0.5+ | `CREATE EXTENSION IF NOT EXISTS vector;` |
| Python | 3.11+ | Used via `uv run --project backend` |
| psycopg | v3 | Installed in backend venv via `uv sync` |
| Ollama | latest | Running at `http://localhost:11434` |
| nomic-embed-text | — | `ollama pull nomic-embed-text` |
| uv | latest | `pip install uv` or `brew install uv` |

Verify prerequisites:

```bash
# PostgreSQL
psql -c "SELECT version();"

# pgvector
psql -c "SELECT * FROM pg_extension WHERE extname = 'vector';"

# Ollama + nomic-embed-text
curl http://localhost:11434/api/tags | grep nomic-embed-text
```

---

## 2. Setting DATABASE_URL Locally

**Never commit `backend/.env`.**

Option A — set in your shell session (recommended for CI):
```bash
export DATABASE_URL="postgresql://youruser:yourpassword@localhost:5432/immigration_law_dev"
```

Option B — add to `backend/.env` (git-ignored locally):
```
# backend/.env  (already in .gitignore — never commit this file)
DATABASE_URL=postgresql://youruser:yourpassword@localhost:5432/immigration_law_dev
```

All scripts in this folder read `DATABASE_URL` from:
1. `--database-url` CLI flag
2. `DATABASE_URL` environment variable
3. `backend/.env` file

None of these scripts will print the URL or password.

---

## 3. MVP Source Set

The MVP corpus is **three co-active dataset versions** (no single combined row):

| Dataset prefix | Source | Approx. chunks |
|----------------|--------|----------------|
| `ecfr-title8-full-YYYY-MM-DD` | eCFR Title 8 — Aliens and Nationality | ~9,300 |
| `ina-YYYY-MM-DD` | INA / U.S. Code Title 8 | ~1,400 |
| `uscis-pm-YYYY-MM-DD` | USCIS Policy Manual | ~900 |

BIA decisions are **post-MVP** and not included.

The sample dataset (`ecfr-title8-sample-*`, 5 chunks, status `ready`) must
NOT be active after the rebuild.

---

## 4. Pipeline Stages

### Stage overview

```
fetch → insert → embed → activate → validate
```

Run everything with `--dry-run` first to see what will happen:

```bash
uv run --project backend python scripts/mvp_data/rebuild_mvp_database.py --dry-run
```

---

### Stage 1 — Fetch source data

**Status: partially automated. Full-corpus fetch requires manual steps.**

#### eCFR Title 8 (sample — automated)

The existing fetch script downloads a small 5-section preview:

```bash
uv run --project backend python scripts/fetch_ecfr_title8_sample.py
```

#### eCFR Title 8 (full corpus — manual)

Download the full Title 8 XML using the eCFR Versioner API:

```bash
# Get the latest available date
DATE=$(curl -s "https://www.ecfr.gov/api/versioner/v1/titles" \
    | python3 -c "import sys,json; d=json.load(sys.stdin); \
      t=[t for t in d['titles'] if t['number']==8][0]; \
      print(t['latest_issue_date'])")

echo "Latest eCFR Title 8 date: $DATE"

# Download full XML (~30 MB)
mkdir -p data/ecfr_full
curl -o "data/ecfr_full/title-8-${DATE}.xml" \
    "https://www.ecfr.gov/api/versioner/v1/full/${DATE}/title-8.xml"
```

#### INA / U.S. Code Title 8 (manual)

```bash
mkdir -p data/ina
# Download from USLM (United States Legislative Markup) — public domain
curl -L -o data/ina/usc-title8.xml \
    "https://uscode.house.gov/download/releasepoints/us/pl/119/usc08.xml"
```

Alternatively, download the ZIP from https://uscode.house.gov/download/download.shtml
(Title 8 → XML format).

#### USCIS Policy Manual (manual)

The USCIS Policy Manual is accessible via the USCIS website. A full automated
download is not available via a public API. Options:

1. Use an existing ingestion export if available from another team member.
2. Use the USCIS website scraper (not yet automated — see
   `scripts/fetch_ecfr_title8_sample.py` as a pattern reference for writing one).

> **Note:** A full USCIS PM ingestion script is the primary remaining gap in
> pipeline automation. Until automated, you can import a known-good exported
> JSON from a teammate's environment (see §7 for import instructions).

---

### Stage 2 — Insert to PostgreSQL

**Status: partially automated.**

#### Sample eCFR (automated)

```bash
uv run --project backend python scripts/insert_ecfr_preview_to_db.py
```

#### Full corpus insert (requires ingestion scripts)

When full-corpus ingestion scripts are available, run them here. Until then,
import a database dump (see §7).

---

### Stage 3 — Embed

Generates 768-dim vectors for all `embedding IS NULL` chunks using
Ollama `nomic-embed-text`. Safe to re-run; skips already-embedded chunks.

```bash
# Embed all datasets
uv run --project backend python scripts/embed_legal_chunks.py

# Embed a specific dataset version
uv run --project backend python scripts/embed_legal_chunks.py \
    --dataset-version-name ecfr-title8-full-2026-05-11
```

Requires Ollama running: `ollama serve` (if not already running).

---

### Stage 4 — Activate

Sets the three MVP datasets to `active` and demotes the sample to `ready`.

Always dry-run first:

```bash
uv run --project backend python scripts/mvp_data/set_mvp_active_datasets.py
```

Apply:

```bash
uv run --project backend python scripts/mvp_data/set_mvp_active_datasets.py --apply
```

---

### Stage 5 — Validate

```bash
uv run --project backend python scripts/mvp_data/validate_mvp_database.py
```

Expected output:
```
RESULT: PASS
```

---

## 5. Expected Final State

After a successful rebuild:

### dataset_versions

| version_name | status | total chunks | embedded |
|---|---|---|---|
| `ecfr-title8-full-YYYY-MM-DD` | **active** | ~9,300 | ~9,300 |
| `ina-YYYY-MM-DD` | **active** | ~1,400 | ~1,400 |
| `uscis-pm-YYYY-MM-DD` | **active** | ~900 | ~900 |
| `ecfr-title8-sample-2026-05-11` | ready | 5 | 5 |

Total searchable chunks: ~11,600 (`status = 'active'` AND `is_active = TRUE`).

### API response fields

```json
{
  "active_dataset": "mvp-multi-source: ecfr-title8-full-YYYY-MM-DD, ina-YYYY-MM-DD, uscis-pm-YYYY-MM-DD",
  "active_datasets": ["ecfr-title8-full-YYYY-MM-DD", "ina-YYYY-MM-DD", "uscis-pm-YYYY-MM-DD"],
  "mvp_sources": ["eCFR Title 8", "INA / U.S. Code Title 8", "USCIS Policy Manual"]
}
```

---

## 6. How to Reset and Rebuild Safely

> **Warning:** Reset truncates `legal_chunks` and deletes all `dataset_versions`
> rows. This cannot be undone without a backup.

```bash
# See what will happen (dry-run)
uv run --project backend python scripts/mvp_data/rebuild_mvp_database.py --dry-run --reset

# Execute with reset (you will be asked to type 'yes' before any rows are deleted)
uv run --project backend python scripts/mvp_data/rebuild_mvp_database.py --reset
```

To reset without the full pipeline:

```bash
psql -c "TRUNCATE TABLE legal_chunks RESTART IDENTITY CASCADE;"
psql -c "DELETE FROM dataset_versions;"
```

---

## 7. Importing from a Teammate's Environment

If a teammate has a correctly-loaded database, export and import as a pg_dump:

```bash
# On their machine (exclude user data tables)
pg_dump \
    --no-owner --no-acl \
    --table=source_registry \
    --table=dataset_versions \
    --table=legal_chunks \
    --table=legal_documents \
    --table=legal_sections \
    --table=raw_documents \
    immigration_law_dev > mvp_corpus_$(date +%Y%m%d).sql

# Do NOT include: privacy_safe_answer_logs, admin_users
```

Import on your machine:

```bash
psql immigration_law_dev < mvp_corpus_YYYYMMDD.sql
```

Then run activation and validation:

```bash
uv run --project backend python scripts/mvp_data/set_mvp_active_datasets.py --apply
uv run --project backend python scripts/mvp_data/validate_mvp_database.py
```

> The exported dump must NOT include `privacy_safe_answer_logs` or `admin_users`.
> Do not commit the dump file to git.

---

## 8. Validating Retrieval and Chat After Rebuild

### API smoke tests

```bash
# Retrieval — expect 3 active datasets, no sample in source families
curl -s -X POST http://localhost:8000/api/retrieve \
    -H "Content-Type: application/json" \
    -d '{"query": "adjustment of status eligibility", "top_k": 5}' \
    | python3 -m json.tool | grep -A5 '"active_datasets"'

# Chat — expect mvp_sources list, no sample citation
curl -s -X POST http://localhost:8000/api/chat \
    -H "Content-Type: application/json" \
    -d '{"message": "What is advance parole?"}' \
    | python3 -m json.tool | grep -E '"mvp_sources"|"active_datasets"|"source_family"'
```

### Validate retrieval covers all three sources

Run at least these seven queries and confirm results come from eCFR, INA,
and USCIS PM across the set (no single-source monopoly):

```bash
QUERIES=(
    "Can asylum applicants get work authorization"
    "What is a Notice to Appear"
    "What is adjustment of status"
    "What is USCIS policy on naturalization good moral character"
    "How do I apply for STEM OPT EAD"
    "What is Form I-765"
    "What is advance parole"
)
for q in "${QUERIES[@]}"; do
    echo "=== $q ==="
    curl -s -X POST http://localhost:8000/api/retrieve \
        -H "Content-Type: application/json" \
        -d "{\"query\": \"$q\", \"top_k\": 5}" \
        | python3 -c "
import sys, json
d=json.load(sys.stdin)
for r in d.get('results', []):
    print(f\"  [{r.get('source_family','?')}] {r.get('citation','?')}\")
"
done
```

### Confirm sample is excluded

```bash
curl -s -X POST http://localhost:8000/api/retrieve \
    -H "Content-Type: application/json" \
    -d '{"query": "immigration", "top_k": 20}' \
    | python3 -c "
import sys, json
d = json.load(sys.stdin)
sample = [r for r in d.get('results',[]) if 'sample' in (r.get('dataset_version') or '')]
print(f'Sample chunks in results: {len(sample)} (expected 0)')
"
```

---

## 9. BIA Exclusion Note

Board of Immigration Appeals (BIA) decisions are **post-MVP**. No BIA chunks
are ingested or activated. The `source_registry` table contains a `DOJ EOIR
BIA Decisions` row for future use; it has zero chunks. BIA will not appear
in `mvp_sources` or retrieval results until a separate ingestion milestone
is completed (see `review/validation/04-bia-decisions-challenge-report.md`).

---

## 10. Files in This Folder

| File | Purpose |
|------|---------|
| `README.md` | This file |
| `source_inventory.json` | Official source URLs for all MVP topic areas |
| `validate_mvp_database.py` | Read-only validation: dataset status, chunk counts, embedding completeness |
| `set_mvp_active_datasets.py` | Activate MVP datasets; demote sample to ready |
| `rebuild_mvp_database.py` | Orchestrator: runs embed → activate → validate |
