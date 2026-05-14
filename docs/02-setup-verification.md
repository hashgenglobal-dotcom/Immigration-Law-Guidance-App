# Setup Verification Checklist

**Date:** May 14, 2026  
**Developer:** Hash  
**Sync Target:** Rishi Raj's Mac Setup

---

## ✅ Installed & Verified

| Tool | My Version | Rishi's Version | Status |
|------|-----------|-----------------|--------|
| **macOS** | Apple Silicon | macOS 26.2 / ARM64 | ✅ |
| **Git** | 2.54.0 | 2.50.1 | ✅ |
| **Node.js** | v22.22.1 | v22.22.1 | ✅ Match |
| **npm** | 10.9.4 | 10.9.4 | ✅ Match |
| **uv** | 0.11.11 | 0.11.14 | ✅ (minor diff) |
| **PostgreSQL** | 18.3 | 18.3 | ✅ Match |
| **pgvector** | 0.8.2 | 0.8.2 | ✅ Match |
| **Redis** | 8.x (running) | 8.6.3 | ✅ |
| **Docker** | 29.2.1 | 29.4.1 | ✅ (minor diff) |
| **Ollama** | 0.23.3 | 0.23.4 | ✅ (minor diff) |

---

## ✅ Services Running

```bash
# PostgreSQL 18
brew services start postgresql@18
# Status: started ✓

# Redis
brew services start redis
# Status: started ✓

# Ollama
brew services start ollama
# Status: started ✓
```

---

## ✅ Database Created

```bash
# Database
createdb immigration_law_dev
# Status: created ✓

# pgvector extension
psql -d immigration_law_dev -c "CREATE EXTENSION IF NOT EXISTS vector;"
# Status: CREATE EXTENSION ✓

# Vector test
psql -d immigration_law_dev -c "SELECT '[1,2,3]'::vector(3);"
# Result: [1,2,3] ✓

# Redis ping
redis-cli ping
# Result: PONG ✓
```

---

## ✅ Ollama Models

```bash
ollama list
# nomic-embed-text:latest (274 MB) ✓
# llama3.2:latest (2.0 GB) ✓
```

**Note:** Rishi has no models pulled yet. I have:
- `nomic-embed-text` (for embeddings - 768 dims)
- `llama3.2` (can use for testing, but MVP will use `llama3.1:8b`)

---

## 📦 Repository Pushed

**URL:** https://github.com/hashgenglobal-dotcom/Immigration-Law-Guidance-App

**Initial Commit:** `2e3fe4a`
```
feat: initial project setup - database schema, docs, MVP question mapping

- PostgreSQL 18 + pgvector 0.8.2 schema (10 tables)
- 20 MVP questions with source mapping (eCFR, USCIS, INA, BIA)
- Tech stack documented (FastAPI, React, Ollama, Redis)
- Hybrid search design (vector + full-text)
- Dataset versioning for safe updates
- Local-first AI architecture (Ollama embeddings + LLM)
```

**Files Pushed:**
1. `README.md` - Full project overview
2. `database/SETUP_COMPLETE.md` - DB setup docs
3. `database/migrations/001-initial-schema.sql` - 10 tables
4. `docs/01-mvp-questions-source-mapping.md` - Question→Source mapping
5. `docs/TECH_STACK.md` - Versioned tech stack
6. `scripts/test-ollama-embeddings.py` - Test script

---

## 🔧 Next Steps for Both Devs

### Hash (Me)
- [ ] Pull `llama3.1:8b` for answer generation
- [ ] Create backend FastAPI skeleton
- [ ] Build eCFR ingestion pipeline

### Rishi Raj
- [ ] Clone repo: `git clone https://github.com/hashgenglobal-dotcom/Immigration-Law-Guidance-App.git`
- [ ] Pull Ollama models:
  ```bash
  ollama pull nomic-embed-text
  ollama pull llama3.1:8b
  ```
- [ ] Run database migration:
  ```bash
  psql -d immigration_law_dev -f database/migrations/001-initial-schema.sql
  ```
- [ ] Verify setup:
  ```bash
  python3 scripts/test-ollama-embeddings.py
  ```

---

## 🚀 Phase 2 Kickoff (eCFR Ingestion)

**Goal:** Fetch Title 8 CFR, parse, chunk, embed, store

**Files to Create:**
```
backend/
├── app/
│   ├── ingestion/
│   │   ├── sources/ecfr.py      # eCFR XML fetcher
│   │   ├── chunking.py          # 500-1000 token chunks
│   │   ├── embeddings.py        # Ollama integration
│   │   └── pipeline.py          # Full orchestration
│   └── db/
│       └── models.py            # SQLAlchemy models
```

**Priority Sections (from source mapping):**
- 8 CFR § 208.7 (asylum work authorization)
- 8 CFR § 208.4 (asylum application)
- 8 CFR § 245.1-245.2 (adjustment of status)
- 8 CFR § 214.2 (F-1 student status)
- 8 CFR § 235 (inspection)

---

## 📋 Command Reference

```bash
# Clone repo
git clone https://github.com/hashgenglobal-dotcom/Immigration-Law-Guidance-App.git

# Start services
brew services start postgresql@18
brew services start redis
brew services start ollama

# Create DB + extension
createdb immigration_law_dev
psql -d immigration_law_dev -c "CREATE EXTENSION vector;"

# Run migrations
psql -d immigration_law_dev -f database/migrations/001-initial-schema.sql

# Pull Ollama models
ollama pull nomic-embed-text
ollama pull llama3.1:8b

# Test embeddings
python3 scripts/test-ollama-embeddings.py

# Verify Redis
redis-cli ping  # PONG

# Verify PostgreSQL
psql -d immigration_law_dev -c "SELECT '[1,2,3]'::vector(3);"
```

---

**Status:** ✅ Both devs synced, repo initialized, ready for Phase 2
