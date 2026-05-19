# Immigration Law Guidance App — Ingestion Master Plan

**Generated:** May 19, 2026  
**Status:** eCFR ✅ Complete | USCIS 🔄 In Progress | INA 📋 Planned | BIA 📋 Planned

---

## Overview

This document tracks the ingestion of 10 official legal sources into the Immigration Law Guidance App's RAG system.

### Source Registry (All 10 Sources)

| # | Source Name | Type | Publisher | Status | Priority |
|---|-------------|------|-----------|--------|----------|
| 1 | eCFR Title 8 | Regulation | GPO | ✅ Active | Critical |
| 2 | USCIS Policy Manual | Policy | USCIS | 🔄 In Progress | High |
| 3 | U.S. Code Title 8 (INA) | Statute | GPO | 📋 Planned | Critical |
| 4 | DOJ EOIR BIA Decisions | Case Law | DOJ | 📋 Planned | Medium |
| 5 | Federal Register Immigration | Regulation | GPO | 📋 Planned | Low |
| 6 | USCIS Forms and Instructions | Form | USCIS | 📋 Planned | Medium |

---

## Current Status

### ✅ eCFR Title 8 — COMPLETE

**Dataset:** `ecfr-title8-full-2026-05-11`  
**Status:** Active  
**Records:**
- 9,319 legal chunks (with embeddings)
- 1,851 legal sections
- Full Title 8 coverage (all chapters, parts, sections)

**Documentation:**
- See `Review/01-ecfr-ingestion-status.md`

**Scripts:**
- `scripts/fetch_ecfr_title8_full.py`
- `scripts/embed_legal_chunks.py`
- `scripts/activate_dataset.py`

---

### 🔄 USCIS Policy Manual — IN PROGRESS

**Planned Dataset:** `uscis-pm-2026-05-19`  
**Estimated Records:**
- ~500-1,000 sections
- ~2,000-5,000 chunks

**Next Steps:**
1. Build URL discovery script
2. Test HTML parser on 10 sections
3. Run full crawl (15-30 minutes)
4. Insert into database
5. Generate embeddings and activate

**Documentation:**
- See `Review/02-uscis-policy-manual-plan.md`

**Blockers:** None — ready to start

---

### 📋 INA (U.S. Code Title 8) — PLANNED

**Planned Dataset:** `ina-title8-2026-05-19`  
**Estimated Records:**
- ~300-400 sections
- ~1,000-2,000 chunks

**Prerequisites:**
- GovInfo API key (free, 5-minute signup)

**Next Steps:**
1. Register for GovInfo API key
2. Build fetch script
3. Test on 10 sections
4. Run full ingestion
5. Generate embeddings and activate

**Documentation:**
- See `Review/03-ina-ingestion-plan.md`

---

### 📋 BIA Decisions — PLANNED

**Planned Dataset:** `bia-precedent-2026-05-19`  
**Scope:** Precedent decisions only (~500)  
**Estimated Records:**
- ~500 precedent decisions
- ~1,500-3,000 chunks

**Next Steps:**
1. Build precedent list scraper
2. Test parser on 10 decisions
3. Run full crawl (~10-15 minutes)
4. Insert into database
5. Generate embeddings and activate

**Documentation:**
- See `Review/04-bia-decisions-plan.md`

---

### 📋 Federal Register Immigration — PLANNED

**Priority:** Low (supplementary)  
**Source:** https://www.federalregister.gov/documents/immigration  
**Format:** API available

**Notes:**
- Proposed rules, final rules, notices
- Lower priority than core sources (CFR, INA, BIA)
- Defer until after USCIS/INA/BIA complete

---

### 📋 USCIS Forms — PLANNED

**Priority:** Medium (practical utility)  
**Source:** https://www.uscis.gov/forms  
**Format:** HTML scraping

**Notes:**
- Form instructions, filing fees, eligibility
- High user value (practical guidance)
- Can be ingested after core legal sources

---

## Technical Architecture

### Ingestion Pipeline (All Sources)

```
┌─────────────────┐
│ 1. FETCH        │  Download from official source
│    (raw)        │  Save to data/<source>/raw/
└────────┬────────┘
         │
         v
┌─────────────────┐
│ 2. PARSE        │  Extract metadata + text
│    (preview)    │  Generate JSON preview
└────────┬────────┘
         │
         v
┌─────────────────┐
│ 3. INSERT       │  legal_documents → legal_sections
│    (database)   │  → legal_chunks
└────────┬────────┘
         │
         v
┌─────────────────┐
│ 4. EMBED        │  Generate embeddings via Ollama
│    (vectors)    │  nomic-embed-text (768-dim)
└────────┬────────┘
         │
         v
┌─────────────────┐
│ 5. ACTIVATE     │  Set status='active'
│    (live)       │  Deactivate old versions
└─────────────────┘
```

### Database Schema

**Core Tables:**
- `source_registry` — Source metadata (6 sources registered)
- `raw_documents` — Original fetched content (audit trail)
- `legal_documents` — Document-level metadata
- `legal_sections` — Section-level text (e.g., 8 CFR § 208.7)
- `legal_chunks` — Retrieval-ready segments with embeddings
- `dataset_versions` — Version tracking (one active at a time)
- `ingestion_jobs` — Job tracking
- `privacy_safe_answer_logs` — Privacy-safe Q&A audit trail

**Indexes:**
- pgvector HNSW index on `legal_chunks.embedding`
- PostgreSQL GIN index on `legal_chunks.search_vector` (full-text)
- B-tree indexes on topic, subtopic, citation, dataset_version_id

---

## Retrieval System

### Hybrid Search

**Vector Search:**
- pgvector cosine distance
- HNSW index for fast approximate nearest neighbors
- 768-dimensional embeddings (nomic-embed-text)

**Keyword Search:**
- PostgreSQL `plainto_tsquery` + `ts_rank_cd`
- English language stemming
- Full-text search vector (chunk_text + summary + citation + topic)

**Fusion:**
- Reciprocal Rank Fusion (RRF_K=60)
- Combines vector + keyword rankings
- Returns unified hybrid score

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/retrieve` | POST | Hybrid search (citations only) |
| `/api/chat/ask` | POST | RAG Q&A with structured answer |

---

## Privacy & Security

### Data Classification

| Data Type | Classification | Storage |
|-----------|----------------|---------|
| eCFR/INA/BIA text | Public legal source | ✅ Stored in database |
| User questions | Sensitive PII | ❌ Never stored (hash only) |
| Generated answers | Sensitive | ❌ Never stored (hash only) |
| Retrieval metadata | Audit trail | ✅ Logged (chunk IDs, citations) |

### Processing Rules

✅ **Local-first:**
- Ollama embeddings (localhost:11434)
- Ollama LLM (llama3.2)
- PostgreSQL (localhost:54329)

✅ **No external APIs:**
- No OpenAI, Anthropic, or cloud LLMs
- No user data leaves the machine

✅ **Privacy-safe logging:**
- Only hashes, IDs, citations logged
- No raw Q&A text in `privacy_safe_answer_logs`

---

## Developer Quickstart

### Prerequisites

```bash
# Install Ollama models
ollama pull nomic-embed-text
ollama pull llama3.2

# Start PostgreSQL (if not running)
brew services start postgresql@17

# Navigate to backend
cd ~/projects/immigration-law-app-official/backend
uv sync
```

### Run Backend

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Test Retrieval

```bash
curl -X POST http://localhost:8000/api/retrieve \
  -H "Content-Type: application/json" \
  -d '{"query": "Can I work while my asylum case is pending?", "top_k": 5}' | jq
```

### Test Chat

```bash
curl -X POST http://localhost:8000/api/chat/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Can I work while my asylum case is pending?", "language": "en"}' | jq
```

### Database Access

```bash
psql -h localhost -p 54329 -U hash -d immigration_law_dev
```

---

## Timeline

| Phase | Source | Status | Est. Time |
|-------|--------|--------|-----------|
| 1 | eCFR Title 8 | ✅ Complete | Done |
| 2 | USCIS Policy Manual | 🔄 In Progress | 2-3 days |
| 3 | INA (Title 8) | 📋 Planned | 2-3 days |
| 4 | BIA Decisions | 📋 Planned | 2-3 days |
| 5 | Federal Register | 📋 Planned | 1 day |
| 6 | USCIS Forms | 📋 Planned | 1 day |

**Total Estimated Time:** 8-10 days (all sources)

---

## Next Actions

1. **Start USCIS Policy Manual ingestion** (today)
   - Build discovery script
   - Test parser
   - Run full crawl

2. **Parallel: Register for GovInfo API key** (5 minutes)
   - https://api.govinfo.gov/

3. **After USCIS complete: Start INA ingestion**
   - Use API key
   - Fetch all Title 8 sections

4. **After INA complete: Start BIA decisions**
   - Crawl precedent decisions
   - Parse and ingest

---

## Contact

**Project:** Immigration Law Guidance App  
**Company:** HashGen Global LLC (EIN: 41-4374777)  
**Developer:** Hash (@hashgen.global)  
**Repo:** https://github.com/hashgenglobal-dotcom/Immigration-Law-Guidance-App
