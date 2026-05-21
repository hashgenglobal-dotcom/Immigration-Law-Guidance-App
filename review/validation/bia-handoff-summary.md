# BIA Handoff Summary (Task 2)

**Prepared:** May 21, 2026  
**Branch:** `feature/post-mvp` (docs only)  
**BIA code branch:** `origin/BIA` (not merged to `main`)

---

## Short answer

| Question | Answer |
|----------|--------|
| Raw PDFs in Git? | **No** — `data/*` is gitignored |
| PDFs on disk (this repo path)? | **0** under `data/` in `immigration-law-app-official` |
| BIA active in Postgres (dev)? | **Yes — partial** — 25,412 active chunks, **0 embeddings** |
| BIA ready for MVP retrieval? | **No** — exclude from MVP handoff |
| BIA pipeline in Git? | **Yes** on branch `BIA` under `scripts/bia/` |

---

## Git: `origin/BIA`

**Latest commits:**

- `bf7b81d0` — feat: Complete BIA acquisition pipeline with auto-trigger  
- `893c98eb` — feat: BIA precedent decisions acquisition pipeline  

**Pipeline scripts (committed):**

| Script | Purpose |
|--------|---------|
| `scripts/bia/01_discover_volumes.py` | Discover EOIR volumes |
| `scripts/bia/02_extract_decision_manifest.py` | Build decision manifest |
| `scripts/bia/03_download_pdfs.py` | Download PDFs → `data/raw/bia/bia/pdfs` |
| `scripts/bia/04_extract_pdf_text.py` | PDF → text/JSON |
| `scripts/bia/05_create_rag_chunks.py` | Chunk for RAG |
| `scripts/bia/06_validate_bia_dataset.py` | Validation report |
| `scripts/bia/ingest_bia_decisions.py` | Load JSON into Postgres |
| `scripts/bia/pipeline_orchestrator.py` | Full pipeline |
| `scripts/bia/watch_download_complete.py` | Watch downloads |
| `scripts/bia/config.py` | Paths, delays, URLs |

**Reports in Git:**

- `reports/bia_acquisition_report.md` (template output; run had 0 volumes on that machine)
- `review/04-bia-decisions-challenge-report.md`
- `review/04-bia-decisions-plan.md`

**Not in Git (`.gitignore`):**

```
data/*
*.pdf
*.sql
*.dump
```

No PDF, JSONL, or manifest files are tracked on `origin/BIA`.

---

## External / local artifacts (gitignored paths)

From `scripts/bia/config.py` on `BIA` branch:

| Artifact | Path |
|----------|------|
| Volume manifest | `data/raw/bia/volume_manifest.json` |
| Decision manifest | `data/raw/bia/bia_decision_manifest.json` |
| PDFs | `data/raw/bia/bia/pdfs/` |
| Extracted text | `data/processed/bia/text/` |
| Extracted JSON | `data/processed/bia/json/` |
| Chunk JSONL | `data/final/bia_precedent_chunks.jsonl` |
| Acquisition report | `reports/bia_acquisition_report.md` |
| Logs | `logs/` |

**This workspace (`immigration-law-app-official`):** `data/raw/bia` **not present** — no local PDF tree in this clone.

**Alternate path in generated report:** an older run referenced `Immigration-Law-Guidance-App/data/raw/bia` (sibling repo name) with **0** volumes/PDFs at generation time.

---

## Volume / file metrics

### From `reports/bia_acquisition_report.md` on `BIA` branch (automated run)

| Metric | Count |
|--------|------:|
| Volumes discovered | 0 |
| Decisions discovered | 0 |
| PDFs downloaded | 0 |
| PDF download failures | 0 |
| Text extraction failures | 0 |
| Duplicate decision IDs | 0 |
| RAG chunks created (JSONL) | 0 |

### From **dev Postgres** (May 21, 2026 — this operator DB)

| Metric | Count |
|--------|------:|
| `dataset_versions` (BIA) | 3 rows (`bia-2026-05-20`, `bia-2026-05-21`, `bia-2026-05-21-final`) |
| Active BIA chunks (`bia-2026-05-21`) | **25,412** |
| BIA chunks with embeddings | **0** |
| Sample citation | `S-S-, 21 I&N Dec. 121 (BIA 1995)` |

**Interpretation:** Text/chunks were loaded into Postgres (likely from JSON under `data/processed/bia/json` on another machine) **without** running `embed_legal_chunks.py` for BIA. **Not safe for hybrid retrieval** until embedded or deactivated.

---

## Postgres vs artifacts

| Layer | Status |
|-------|--------|
| **Artifacts only** | Pipeline can produce JSONL/PDFs under `data/` (external) |
| **Postgres** | Dev DB has **25,412** active BIA rows; other BIA dataset rows empty |
| **MVP retrieval** | Should **deactivate** BIA chunks (see `mvp-database-handoff.md` cleanup SQL) |

`source_registry` includes:

- `DOJ EOIR BIA Decisions` (id 4)  
- `BIA Precedent Decisions` (id 13) — `https://www.justice.gov/eoir/ag-bia-decisions`

---

## Commands used (BIA branch)

```bash
# Full pipeline (from repo root on BIA branch)
python3 scripts/bia/pipeline_orchestrator.py

# Or stepwise:
python3 scripts/bia/01_discover_volumes.py
python3 scripts/bia/02_extract_decision_manifest.py
python3 scripts/bia/03_download_pdfs.py
python3 scripts/bia/04_extract_pdf_text.py
python3 scripts/bia/05_create_rag_chunks.py
python3 scripts/bia/06_validate_bia_dataset.py

# Database ingest
python3 scripts/bia/ingest_bia_decisions.py --dataset-version-name bia-2026-05-21

# Embeddings (required before retrieval — NOT run in dev)
uv run --project backend python scripts/embed_legal_chunks.py \
  --dataset-version-name bia-2026-05-21 --yes
```

**Source URL:** `https://www.justice.gov/eoir/ag-bia-decisions`  
**User-Agent:** `BIA-RAG-Bot/1.0` (see `config.py`)

---

## Known blockers (official source)

See `review/04-bia-decisions-challenge-report.md`:

- Historical EOIR URLs returned **404**
- No public bulk Git/Hugging Face dataset confirmed
- Automated discovery run returned **0** volumes without browser/session

---

## Post-MVP placeholder on `feature/post-mvp`

- `review/scripts/bia_v2_placeholder.py` — exits 2, no ingest  
- `post-mvp/tasks/10-bia/README.md` — blocked notice  

---

## Rishi / data handoff actions

1. **Do not** include BIA in MVP database dump.  
2. Run cleanup SQL in `mvp-database-handoff.md` to set `is_active=FALSE` on BIA chunks.  
3. For BIA work later: checkout `BIA`, run pipeline on a machine with EOIR access, store artifacts **off-repo**, embed, then activate only after legal/product sign-off.  
4. Do **not** merge `BIA` to `main` until embeddings + eval pass and MVP policy allows case law.

---

## File sizes

| Item | Size |
|------|------|
| BIA scripts in Git | ~tens of KB (code only) |
| `data-inserts.sql` (MVP May 19, no BIA) | ~161 MB |
| Local `data/` (this clone) | No `data/raw/bia`; eCFR/INA/PM dirs only |
| BIA in Postgres | 25k rows text — dump size depends on pg_dump scope |

Do not commit generated PDFs, JSONL, or full dumps to GitHub.
