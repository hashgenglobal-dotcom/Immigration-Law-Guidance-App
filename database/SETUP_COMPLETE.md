# Database Setup Complete

**Date:** 2026-05-14  
**PostgreSQL:** 17.9 (Homebrew)  
**pgvector:** 0.8.2  
**Database:** `immigration_law`

---

## Installation Summary

### PostgreSQL Upgrade
- **Uninstalled:** PostgreSQL 14.22 (old version, incompatible with pgvector)
- **Installed:** PostgreSQL 17.9 (latest, pgvector 0.8.2 compatible)
- **Data Directory:** `/opt/homebrew/var/postgresql@17`
- **Service:** Running via `brew services start postgresql@17`

### pgvector Installation
- **Version:** 0.8.2
- **Extension:** `CREATE EXTENSION vector` ✓
- **Vector Dimensions:** 768 (nomic-embed-text compatible)

---

## Schema Tables (10 total)

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `source_registry` | Track official legal sources | source_name, source_type, publisher, access_method |
| `raw_documents` | Audit trail of fetched content | raw_content, content_hash, fetched_at |
| `legal_documents` | Cleaned document metadata | citation, effective_date, version_date |
| `legal_sections` | Specific legal sections | section_number, official_text, topic, subtopic |
| `legal_chunks` | **Retrieval-ready chunks** | chunk_text, embedding, search_vector, is_active |
| `scenario_guides` | User-friendly guides | user_situation, plain_language_guidance, risk_level |
| `dataset_versions` | Version control for legal data | status (building/ready/active/failed/archived) |
| `ingestion_jobs` | Track admin update jobs | source_name, status, records_added, error_message |
| `answer_logs` | Audit user Q&A | question_text, answer_text, citations_used |
| `admin_users` | Dashboard authentication | username, password_hash, is_active |

---

## Key Features

### 1. Hybrid Search Ready
- **Vector search:** HNSW index on `embedding` column (768 dimensions)
- **Keyword search:** GIN index on `search_vector` (PostgreSQL full-text)
- **Combined retrieval:** `search_legal_chunks()` function merges both approaches

### 2. Dataset Versioning
- Only chunks with `is_active = TRUE` are retrieved
- `dataset_versions` table tracks which version is active
- Users always query from stable, published datasets
- Admins can build new versions without disrupting live users

### 3. Full-Text Search Trigger
- Automatic `tsvector` generation on INSERT/UPDATE
- Weights: chunk_text (A), summary (B), citation (C), topic/subtopic (D)
- No manual index maintenance needed

### 4. Audit Trail
- `raw_documents.content_hash` detects content changes
- `answer_logs` tracks all user questions and citations used
- `ingestion_jobs` logs every admin update attempt

### 5. Risk Classification
- `legal_chunks.risk_level`: low, medium, high, critical
- `scenario_guides.risk_level`: same scale
- Enables safety layer: high-risk answers trigger attorney referrals

---

## Seed Data

**6 Official Sources Pre-loaded:**

```sql
source_name          | source_type | publisher
---------------------+-------------+----------
eCFR Title 8         | regulation  | GPO
USCIS Policy Manual  | policy      | USCIS
U.S. Code Title 8    | statute     | GPO
DOJ EOIR BIA         | case_law    | DOJ
Federal Register     | regulation  | GPO
USCIS Forms          | form        | USCIS
```

---

## Connection String

```bash
# Local development
postgresql://hash@localhost:5432/immigration_law

# With pgvector
psql immigration_law -c "SELECT '[1,2,3]'::vector(3);"
```

---

## Next Steps

### Phase 1: Database Foundation ✅ COMPLETE

### Phase 2: First Legal Source Ingestion
1. Build eCFR Title 8 scraper (bulk XML API)
2. Parse sections: 8 CFR § 208.7, 208.4, 245.1-245.2, etc.
3. Store in `raw_documents` → `legal_documents` → `legal_sections`
4. Chunk text (500-1000 tokens with 50-100 overlap)
5. Generate embeddings (nomic-embed-text via Ollama)
6. Create first `dataset_version` with status='active'

### Phase 3: Retrieval MVP
1. Build FastAPI backend
2. Implement `POST /api/chat/ask` endpoint
3. Call `search_legal_chunks()` with query embedding + text
4. Send retrieved chunks to LLM for answer generation
5. Return answer with citations

---

## Files Created

- `~/projects/immigration-app/database/migrations/001-initial-schema.sql` (15KB)
- `~/projects/immigration-app/docs/01-mvp-questions-source-mapping.md` (16KB)
- `~/projects/immigration-app/database/SETUP_COMPLETE.md` (this file)

---

## Commands Reference

```bash
# Start PostgreSQL
brew services start postgresql@17

# Connect to database
psql immigration_law

# Check tables
\dt

# Check pgvector
SELECT '[1,2,3]'::vector(3);

# Test hybrid search function (after data ingestion)
SELECT * FROM search_legal_chunks(
  '[0.1,0.2,...]'::vector(768),  -- query embedding
  'Can I work while asylum pending?',
  10  -- limit
);

# Check active dataset
SELECT * FROM dataset_versions WHERE status = 'active';

# Check ingestion jobs
SELECT * FROM ingestion_jobs ORDER BY created_at DESC LIMIT 5;
```

---

## pgvector Notes

**HNSW Index Configuration:**
- Default: `m=16`, `ef_construction=64`
- For production: `m=32`, `ef_construction=128` (better recall, slower build)
- Query time: `ef_search=40` (balance speed/accuracy)

**Embedding Dimensions:**
- Schema uses 768 (nomic-embed-text, mxbai-embed-large)
- To use OpenAI: Change to 1536 (text-embedding-3-small)
- To use local alternatives: Keep 768 or use 1024 (e5-mistral)

**Index Build Time:**
- 10K chunks: ~30 seconds
- 100K chunks: ~5 minutes
- 1M chunks: ~50 minutes

---

**Status:** ✅ Database ready for ingestion pipeline development
