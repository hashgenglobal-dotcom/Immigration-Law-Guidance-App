# eCFR Title 8 Ingestion — Status Report

**Generated:** May 19, 2026  
**Status:** ✅ COMPLETE & ACTIVE

---

## Summary

eCFR Title 8 (Aliens and Nationality) has been fully ingested into the database with embeddings generated and dataset activated for production retrieval.

---

## Database Statistics

| Table | Count | Notes |
|-------|-------|-------|
| `legal_chunks` | 9,319 | All with embeddings (768-dim nomic-embed-text) |
| `legal_sections` | 1,851 | Parsed from eCFR Title 8 XML |
| `dataset_versions` | 2 | 1 active, 1 ready (sample) |
| `source_registry` | 6 | All 10 planned sources registered |

### Active Dataset

```
version_name: ecfr-title8-full-2026-05-11
status: active
activated_at: 2026-05-16 07:30:11 EDT
notes: Full Title 8 ingestion
```

---

## Source Coverage

### eCFR Title 8 Structure

| Component | Count | Description |
|-----------|-------|-------------|
| Chapters | Multiple | Chapter I (USCIS), Chapter II (EOIR), Chapter III (DHS), Chapter V (DOS) |
| Parts | ~100+ | All parts within Title 8 |
| Sections | 1,851 | Individual CFR sections (e.g., 8 CFR § 208.7) |
| Chunks | 9,319 | Retrieval-ready segments with embeddings |

### Key Sections Ingested (MVP Coverage)

| Citation | Topic | Subtopic | Risk Level |
|----------|-------|----------|------------|
| 8 CFR § 208.7 | asylum | employment_authorization | medium |
| 8 CFR § 208.4 | asylum | filing_deadline | high |
| 8 CFR § 245.1 | adjustment_of_status | eligibility | medium |
| 8 CFR § 274a.12 | employment_authorization | categories | medium |
| 8 CFR § 239.1 | removal_proceedings | notice_to_appear | high |

---

## Technical Implementation

### Ingestion Pipeline

1. **Fetch:** `scripts/fetch_ecfr_title8_full.py`
   - Downloads full Title 8 XML from eCFR API
   - Auto-detects latest issue date
   - Saves raw XML to `data/ecfr/raw/` (git-ignored)

2. **Parse:** XML parsing with ElementTree
   - Extracts section-level metadata
   - Cleans text (removes XML tags, normalizes whitespace)
   - Maps to schema: `legal_documents` → `legal_sections` → `legal_chunks`

3. **Chunk:** Strategic text segmentation
   - Chunk size: ~1,500 characters
   - Overlap: 200 characters
   - Preserves citation context in each chunk

4. **Embed:** `scripts/embed_legal_chunks.py`
   - Model: `nomic-embed-text` (768 dimensions)
   - Local Ollama inference (no external API calls)
   - Stored in `legal_chunks.embedding` (pgvector)

5. **Activate:** `scripts/activate_dataset.py`
   - Sets `status = 'active'` on dataset version
   - Deactivates previous versions
   - Only active chunks are retrievable

### Retrieval Service

**Endpoint:** `POST /api/retrieve`

- Hybrid search: vector (pgvector cosine) + keyword (PostgreSQL full-text)
- Reciprocal Rank Fusion (RRF_K=60)
- Returns ranked citations with snippets
- Privacy-safe: query never stored, only hashed

**Endpoint:** `POST /api/chat/ask`

- RAG pipeline: retrieve → generate answer
- Model: `llama3.2` (local Ollama)
- Structured JSON response with citations
- Metadata logging only (no raw Q&A text)

---

## Privacy & Security

✅ **All processing is local:**
- Ollama embeddings (localhost:11434)
- Ollama LLM (llama3.2)
- PostgreSQL database (localhost:54329)

✅ **No external API calls:**
- No OpenAI, Anthropic, or cloud LLMs
- No user data leaves the machine

✅ **Privacy-safe logging:**
- `privacy_safe_answer_logs` stores only:
  - Question/answer hashes (SHA-256)
  - Retrieved chunk IDs
  - Citations used
  - Risk level, latency, model info
- **Never stores:** raw questions, answers, or personal facts

---

## Files & Scripts

### Core Scripts

| Script | Purpose |
|--------|---------|
| `scripts/fetch_ecfr_title8_full.py` | Full Title 8 ingestion |
| `scripts/fetch_ecfr_title8_sample.py` | 5-section sample (testing) |
| `scripts/embed_legal_chunks.py` | Generate embeddings |
| `scripts/activate_dataset.py` | Activate dataset version |
| `scripts/validate_ecfr_title8_preview.py` | Preview validation |
| `scripts/validate_hybrid_retrieval_results.py` | Retrieval quality checks |

### Database Schema

- `database/migrations/001-initial-schema.sql`
- 10 tables with pgvector, full-text search, and audit trails

### API Routes

- `backend/app/api/routes/retrieval.py` — Hybrid search
- `backend/app/api/routes/chat.py` — RAG Q&A
- `backend/app/services/retrieval_service.py` — Core logic
- `backend/app/services/ollama_embedding_client.py` — Local embeddings

---

## Next Steps

### Phase 2: USCIS Policy Manual

- **Source:** https://www.uscis.gov/policy-manual
- **Format:** HTML scraping (no bulk API)
- **Challenge:** Hierarchical navigation (Volume → Part → Chapter → Section)
- **Priority:** High (policy guidance complements CFR regulations)

### Phase 3: INA (Immigration and Nationality Act)

- **Source:** U.S. Code Title 8 (https://uscode.house.gov/)
- **Format:** XML/JSON via API
- **Priority:** Critical (statutory foundation)

### Phase 4: BIA Decisions

- **Source:** DOJ EOIR (https://www.justice.gov/eoir/bia-decisions)
- **Format:** HTML case law
- **Challenge:** Case-level parsing, precedent identification
- **Priority:** Medium (case law interpretation)

---

## Developer Notes

### Running the Backend

```bash
cd ~/projects/immigration-law-app-official/backend
uv sync
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Testing Retrieval

```bash
curl -X POST http://localhost:8000/api/retrieve \
  -H "Content-Type: application/json" \
  -d '{"query": "Can I work while my asylum case is pending?", "top_k": 5}'
```

### Database Access

```bash
psql -h localhost -p 54329 -U hash -d immigration_law_dev
```

### Environment Variables

See `backend/.env.example`:
- `DATABASE_URL`
- `OLLAMA_BASE_URL`
- `SECRET_KEY`

---

## Contact

**Project:** Immigration Law Guidance App  
**Company:** HashGen Global LLC  
**Developer:** Hash (@hashgen.global)  
**Repo:** https://github.com/hashgenglobal-dotcom/Immigration-Law-Guidance-App
