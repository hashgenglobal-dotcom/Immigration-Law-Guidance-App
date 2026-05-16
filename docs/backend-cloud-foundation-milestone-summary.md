# Backend Cloud Foundation + Public Legal Retrieval Foundation

**Milestone:** Backend Cloud Foundation + Public Legal Retrieval Foundation  
**Branch:** `feature/backend-cloud-foundation`  
**Status:** Complete — ready for pre-merge verification

---

## 1. Purpose

This milestone creates the local backend and data foundation for a privacy-first immigration legal guidance app. All AI processing runs on-device using local Ollama; no user data is sent to any public AI API.

Specifically, this milestone establishes:

- A **FastAPI backend** with health endpoints and a PostgreSQL/pgvector/Redis dependency check.
- A **PostgreSQL + pgvector database** schema with 10 tables, source registry seeding, and full-text search triggers.
- An **eCFR Title 8 ingestion pipeline** that fetches, validates, previews, inserts, and verifies public regulatory text from the official eCFR API.
- **Local Ollama embeddings** (768-dimensional, `nomic-embed-text`) for all inserted public legal chunks.
- A **controlled dataset activation** workflow that promotes a reviewed, fully-embedded dataset from `ready` to `active` so it becomes visible to retrieval.
- **Vector retrieval** (pgvector cosine distance) and **hybrid retrieval** (vector + PostgreSQL full-text + Reciprocal Rank Fusion) against the active public dataset.
- **Retrieval validation** confirming that all five synthetic test queries retrieve their expected eCFR citation at rank 1.

No user questions are processed. No answers are generated. No public AI APIs are called. `privacy_safe_answer_logs` remains at 0 throughout.

---

## 2. What Was Completed

### FastAPI backend foundation

- `backend/app/main.py` — FastAPI application entry point with CORS, lifespan, and router registration.
- `backend/app/core/config.py` — Pydantic settings loading `DATABASE_URL`, `REDIS_URL`, and other environment variables from `backend/.env`.
- Database session factory, SQLAlchemy models, and Alembic migration wiring.

### Health endpoints

- `GET /health` — liveness check; returns `{"status": "ok"}`.
- `GET /health/dependencies` — checks PostgreSQL connectivity, pgvector extension presence, and Redis ping; reports each dependency as `ok` or `error`.
- `GET /health/schema` — verifies that the 10 expected database tables exist in the public schema.

### Backend environment template

- `backend/.env.example` — documents all required environment variables (`DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `OLLAMA_BASE_URL`, etc.) without secrets.

### Shared cloud DB safety plan

- `docs/shared-dev-database-plan.md` — documents the rules and risks for any future shared development database, establishing that the local PostgreSQL instance is the canonical dev environment for this milestone.

### eCFR public data fetch and validation

- Fetched 5 public eCFR Title 8 sections from the official eCFR API (no scraping; structured JSON from `api.ecfr.gov`).
- Validated the JSON preview: citation format, content length, source URL presence, and absence of PII.
- Preview-to-database field mapping documented in `docs/ecfr-preview-database-mapping-plan.md`.

### Local PostgreSQL insertion and validation

- Inserted 5 eCFR Title 8 chunks into `raw_documents`, `legal_documents`, `legal_sections`, and `legal_chunks` inside a single transaction using dataset versioning (`ecfr-title8-sample-2026-05-12`, status `ready`).
- Validated insertion: row counts, citation coverage, `search_vector` population by trigger, and absence of PII fields.

### Local Ollama embeddings

- Generated 768-dimensional embeddings for all 5 active `legal_chunks` using `nomic-embed-text` via the local Ollama daemon.
- Dry-run script previewed what would be embedded before any writes.
- Validation script confirmed all 5 chunks carry non-NULL `embedding` with `vector_dims(embedding) = 768`.

### Controlled dataset activation

- Dry-run script showed what activation would do (target dataset, chunks to flip, any dataset to archive) without writing.
- Activation script transactionally promoted `ecfr-title8-sample-2026-05-12` from `ready` to `active`, set `activated_at = NOW()`, and flipped `legal_chunks.is_active = TRUE` on all 5 chunks — rolling back on any precondition failure.
- Validation script confirmed: exactly one active dataset, all 5 citations present with `is_active = TRUE` and 768-dim embeddings, no leaked active chunks from other versions, `privacy_safe_answer_logs = 0`.

### Vector retrieval

- Dry-run script listed active chunks (citation, topic, subtopic, risk level, embedding presence) and the five planned synthetic test queries — no Ollama calls, no DB writes.
- Vector retrieval script embeds a synthetic query locally, verifies 768-dim, runs pgvector cosine-distance search over `legal_chunks WHERE is_active = TRUE`, and prints ranked results with citation, topic, subtopic, risk level, official URL, distance, and 500-character snippet.

### Hybrid retrieval

- Hybrid retrieval script runs both pgvector cosine-distance search and PostgreSQL `plainto_tsquery` full-text search for a synthetic query, then merges the two ranked lists using **Reciprocal Rank Fusion** (RRF_K=60).
- Output shows per-signal candidate summaries (vector distance, `ts_rank_cd`) and a merged hybrid ranking with all signal details (vector rank, keyword rank, RRF contributions, hybrid score).

### Retrieval validation

- **Vector validation** (`validate_retrieval_results.py`): embeds all 5 synthetic queries, runs vector search, checks each expected citation appears in top-k. Exits 0 only when all 5 pass and `privacy_safe_answer_logs = 0`.
- **Hybrid validation** (`validate_hybrid_retrieval_results.py`): embeds all 5 synthetic queries, runs hybrid retrieval (vector + keyword + RRF), checks each expected citation is the **top hybrid result (rank 1)**. Exits 0 only when all 5 pass rank-1 check and `privacy_safe_answer_logs = 0`.

---

## 3. Key Scripts Added

### Setup / health

- `backend/app/api/routes/health.py` — `/health`, `/health/dependencies`, `/health/schema` endpoints

### eCFR ingestion

| Script | Purpose |
|---|---|
| `scripts/fetch_ecfr_title8_sample.py` | Fetch 5 eCFR Title 8 sections from `api.ecfr.gov` and save as JSON preview |
| `scripts/validate_ecfr_title8_preview.py` | Validate the JSON preview (citation format, content length, source URL, no PII) |
| `scripts/dry_run_insert_ecfr_preview.py` | Preview what the insertion script would write, without any DB writes |
| `scripts/insert_ecfr_preview_to_db.py` | Insert preview into `raw_documents`, `legal_documents`, `legal_sections`, `legal_chunks` in one transaction |
| `scripts/validate_ecfr_db_insert.py` | Verify row counts, citation coverage, `search_vector` presence, no PII in DB |

### Embeddings

| Script | Purpose |
|---|---|
| `scripts/dry_run_embed_legal_chunks.py` | Show which chunks would be embedded and their current state, without calling Ollama |
| `scripts/embed_legal_chunks.py` | Generate 768-dim Ollama embeddings for all unembed active-dataset chunks; writes to `legal_chunks.embedding` |
| `scripts/validate_legal_chunk_embeddings.py` | Confirm all 5 chunks have non-NULL embeddings with `vector_dims = 768` |

### Activation

| Script | Purpose |
|---|---|
| `scripts/dry_run_activate_dataset.py` | Preview activation (target dataset, chunks to flip, dataset to archive) — no DB writes |
| `scripts/activate_dataset.py` | Transactionally activate target dataset: archive prior active, set `activated_at`, flip `is_active = TRUE` on chunks |
| `scripts/validate_active_dataset.py` | Confirm exactly one active dataset with 5 active, 768-dim embedded chunks; no leaked active chunks; `psal = 0` |

### Retrieval

| Script | Purpose |
|---|---|
| `scripts/dry_run_retrieve_legal_chunks.py` | List active chunks and planned test queries — no Ollama calls, no DB writes |
| `scripts/retrieve_legal_chunks.py` | Embed one synthetic query locally, run pgvector search, print ranked results with citations and snippets |
| `scripts/validate_retrieval_results.py` | Embed all 5 synthetic queries, run vector search, verify each expected citation in top-k |
| `scripts/hybrid_retrieve_legal_chunks.py` | Embed one synthetic query, run vector + keyword search, fuse with RRF, print hybrid ranking |
| `scripts/validate_hybrid_retrieval_results.py` | Embed all 5 synthetic queries, run hybrid retrieval, verify each expected citation at hybrid rank 1 |

---

## 4. Current Validated Local DB State

After this milestone runs cleanly on the local development machine:

| Item | State |
|---|---|
| Active dataset | `ecfr-title8-sample-2026-05-12` |
| `dataset_versions.status` | `active` |
| `dataset_versions.activated_at` | non-NULL |
| Active `legal_chunks` | 5 rows |
| All active chunks `is_active` | `TRUE` |
| All active chunk `embedding` | `vector(768)`, non-NULL |
| Vector validation (5/5 queries) | PASS |
| Hybrid validation (5/5 queries at rank 1) | PASS |
| `privacy_safe_answer_logs` row count | 0 |

---

## 5. Privacy Guarantees

These guarantees apply to every script and every endpoint delivered in this milestone:

- **No full user questions stored.** No script or endpoint in this milestone accepts real user immigration questions. Only synthetic, public test queries are used in validation scripts, and they are never persisted to any table.
- **No full generated answers stored.** No script in this milestone calls a chat LLM or generates a natural-language answer.
- **`privacy_safe_answer_logs` is metadata-only.** This table is reserved for answer-time metadata (hashes, citations used, chunk IDs, risk level, refusal flag, latency) and is written only during the LLM answer-generation milestone — which is not this one. Its count is verified to be 0 by every validation script.
- **Ingestion uses public legal-source data only.** All inserted text comes from the official eCFR API (`api.ecfr.gov`). This is public regulatory data with no PII.
- **Embeddings generated only for public eCFR text.** The embedding scripts call local Ollama with public regulatory chunk text — never user input, never case facts.
- **Retrieval tests use synthetic questions only.** The five test queries are paraphrases of public regulatory topics. They contain no names, A-numbers, dates of birth, addresses, or case facts.
- **No OpenAI, Anthropic, or any public AI API is called.** This is a HashGen Protocol 2 hard rule enforced in every script and endpoint.
- **All AI processing runs through local Ollama.** Embedding (`nomic-embed-text`) runs against the local Ollama daemon (`http://localhost:11434`). No text leaves the machine.

---

## 6. Pre-Merge Verification Checklist

Run all steps below on the current developer machine before opening a PR to `main`. Every command must exit cleanly (exit code 0) and match the expected output described.

### Step 1 — Git state

```bash
git status
git log --oneline --max-count=10
```

Expected: clean working tree on `feature/backend-cloud-foundation`.

---

### Step 2 — Backend health endpoints

In one terminal:

```bash
cd backend
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In a second terminal:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/health/dependencies
curl http://127.0.0.1:8000/health/schema
```

Expected:
- `/health` → `{"status": "ok"}`
- `/health/dependencies` → all three dependencies (`postgresql`, `pgvector`, `redis`) report `"ok"`
- `/health/schema` → all 10 expected tables present

---

### Step 3 — Data pipeline validation

From the repository root, in a separate terminal (backend server does not need to be running for these):

```bash
# Confirm eCFR insertion: 5 chunks, all citations present, search_vector populated
uv run --project backend python scripts/validate_ecfr_db_insert.py

# Confirm embeddings: all 5 active chunks have 768-dim embeddings
uv run --project backend python scripts/validate_legal_chunk_embeddings.py

# Confirm activation: exactly one active dataset, no leaked is_active rows, psal=0
uv run --project backend python scripts/validate_active_dataset.py

# Confirm vector retrieval: all 5 synthetic queries find expected citation in top-5
uv run --project backend python scripts/validate_retrieval_results.py --top-k 5

# Confirm hybrid retrieval: all 5 synthetic queries find expected citation at rank 1
uv run --project backend python scripts/validate_hybrid_retrieval_results.py --top-k 5
```

Expected: all five commands exit 0. The hybrid validation script prints `final status: PASS` with `5/5` rank-1 passes.

---

### Step 4 — Privacy invariant check

```bash
psql -d immigration_law_dev -c "SELECT COUNT(*) AS privacy_safe_answer_logs_count FROM privacy_safe_answer_logs;"
```

Expected: `privacy_safe_answer_logs_count = 0`.

---

This branch is ready to merge to `main` only after **all four steps above pass cleanly** on the current developer machine.

---

## 7. What Is Not Included Yet

The following are explicitly out of scope for this milestone. Each will be its own feature branch and PR:

- **Production cloud database** — all work in this milestone runs against the local PostgreSQL instance only.
- **Frontend integration** — no React components or Next.js pages are added or modified.
- **`POST /api/retrieve` endpoint** — the retrieval logic is validated via standalone scripts; no FastAPI route wraps it yet.
- **`POST /api/chat/ask` endpoint** — the chat endpoint is not implemented; the route file is a placeholder only.
- **Local LLM answer generation** — no script calls `llama3.1:8b` or any chat model to generate an answer.
- **Citation checker** — no logic verifies citation presence at the API layer or applies a score threshold for out-of-scope queries.
- **Safety / refusal classifier** — no high-risk topic detection or attorney-referral CTA logic is implemented.
- **Admin dashboard** — no React admin interface for dataset management exists yet.
- **User authentication** — `admin_users` table exists in the schema but no auth logic is wired up.

---

## 8. Next Milestone After Merge

Recommended sequence for the next feature branch (`feature/backend-retrieval-service`):

1. **Backend retrieval service** — a `backend/app/retrieval/` module that wraps the embed-and-search logic the milestone scripts proved out, with dependency injection, connection pooling, and error handling.
2. **`POST /api/retrieve` endpoint** — a FastAPI route that accepts a synthetic test query, runs hybrid retrieval, and returns citations and snippets (no LLM call, no question storage).
3. **Frontend integration** — wire the React chat UI to `/api/retrieve` with a mock-to-real API swap; render citations and snippets before LLM generation is available.
4. **Retrieval-only answer skeleton** — a `POST /api/chat/ask` stub that returns cited chunks without calling a chat LLM, so the frontend can integrate against a stable contract.
5. **Local LLM answer generation** — pass retrieved active chunks to `llama3.1:8b` via local Ollama as context; generate a plain-language answer with citations; log metadata only (no raw Q&A text) to `privacy_safe_answer_logs`.
