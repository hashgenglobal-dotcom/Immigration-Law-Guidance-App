# Backend Retrieval API Milestone Plan

**Status:** Planning — no retrieval API code written yet  
**Branch:** `feature/backend-retrieval-api`  
**Scope:** Move the validated hybrid retrieval logic from standalone scripts into FastAPI as a retrieval-only `POST /api/retrieve` endpoint. This milestone does not generate legal answers, does not call a chat LLM, and does not write to `privacy_safe_answer_logs`.

Related docs:
- [`docs/backend-cloud-foundation-milestone-summary.md`](./backend-cloud-foundation-milestone-summary.md) — what the prior milestone completed and verified
- [`docs/retrieval-milestone-plan.md`](./retrieval-milestone-plan.md) — how hybrid retrieval was validated at the script level
- [`database/migrations/001-initial-schema.sql`](../database/migrations/001-initial-schema.sql) — schema referenced below

---

## 1. Purpose

The previous milestone (`feature/backend-cloud-foundation`) proved that hybrid retrieval works against the active public eCFR dataset at the script level. All five synthetic test queries retrieved their expected CFR citations at hybrid rank 1.

This milestone exposes that same validated pipeline through FastAPI. The goal is a single `POST /api/retrieve` endpoint that:

- Accepts a synthetic or user-supplied query string.
- Embeds it locally via Ollama `nomic-embed-text` (no public AI API).
- Runs the same hybrid retrieval logic (vector + keyword + RRF) the scripts already proved out.
- Returns citation-backed chunks with metadata — no generated answer, no LLM chat call.

This endpoint becomes the stable retrieval contract that the frontend, mobile clients, and the future `/api/ask` answer-generation path will build on.

---

## 2. Current Baseline

Before this milestone begins, the following has been merged to `main` and verified locally:

| Item | State |
|---|---|
| Branch merged | `feature/backend-cloud-foundation` → `main` |
| Active dataset | `ecfr-title8-sample-2026-05-12` |
| `dataset_versions.status` | `active` |
| Active `legal_chunks` | 5 rows |
| All active chunk `embedding` | `vector(768)`, non-NULL |
| Hybrid retrieval validation | 5/5 queries, expected citation at rank 1 |
| `privacy_safe_answer_logs` row count | 0 |
| FastAPI health endpoints | `/health`, `/health/dependencies`, `/health/schema` all passing |

The retrieval logic in `scripts/hybrid_retrieve_legal_chunks.py` and `scripts/validate_hybrid_retrieval_results.py` is the reference implementation this milestone ports into the app layer.

---

## 3. Scope

**In scope:**
- Pydantic request and response models for the retrieval endpoint.
- A local-only Ollama embedding client (no public AI APIs).
- A retrieval service encapsulating vector search, keyword search, and RRF fusion.
- A `POST /api/retrieve` FastAPI route.
- Wiring the new router into `backend/app/main.py`.
- Manual testing with the five synthetic test queries from the prior milestone.

**Out of scope:**
- Generating a legal answer in any form.
- Calling `llama3.1:8b` or any chat LLM.
- Storing full user query text in any table.
- Writing to `privacy_safe_answer_logs` (reserved for the answer-generation milestone).
- Using any public AI API (OpenAI, Anthropic, Cohere, Gemini, etc.).
- Any frontend or mobile code changes.
- Database migration changes.
- A `/api/ask` endpoint.

---

## 4. Planned Backend Files

### `backend/app/schemas/retrieval.py`

Pydantic models for the `POST /api/retrieve` request and response.

- `RetrieveRequest` — validated request body: `query` (str, non-empty, max 1000 chars), `top_k` (int, 1–10, default 5).
- `RetrievedChunk` — one result item: `rank`, `chunk_id`, `citation`, `official_url`, `topic`, `subtopic`, `risk_level`, `hybrid_score`, `vector_rank`, `keyword_rank`, `snippet`.
- `RetrieveResponse` — full response: `status`, `privacy_mode`, `query_hash`, `top_k`, `results` (list of `RetrievedChunk`).

`query_hash` is a SHA-256 hash of the lowercased, stripped query — never the raw query text. It is included in the response for client-side deduplication and future privacy-safe logging, but is not written to any table in this milestone.

---

### `backend/app/services/ollama_embedding_client.py`

A thin, local-only client for the Ollama `/api/embed` endpoint.

- Reads `OLLAMA_BASE_URL` from app settings (default: `http://localhost:11434`).
- `async def embed(query: str, model: str = "nomic-embed-text") -> list[float]` — POSTs to `/api/embed`, parses `embeddings[0]`, and raises a typed exception if the call fails or the response is malformed.
- Validates that the returned vector is exactly 768-dimensional; raises if not.
- Uses `httpx.AsyncClient` (already a FastAPI ecosystem standard) rather than `urllib.request` so the async FastAPI event loop is not blocked.
- No text is sent to any public AI API. The Ollama URL must resolve to a local or private endpoint.

---

### `backend/app/services/retrieval_service.py`

Database retrieval logic ported from `scripts/hybrid_retrieve_legal_chunks.py`. Operates only on `legal_chunks WHERE is_active = TRUE`.

- `async def vector_search(conn, query_vector: list[float], n_candidates: int) -> list[dict]` — pgvector cosine-distance search; returns `chunk_id`, `citation`, `distance`, and result metadata.
- `async def keyword_search(conn, query: str, n_candidates: int) -> list[dict]` — `plainto_tsquery` full-text search against `legal_chunks.search_vector`; returns `chunk_id`, `citation`, `kw_score`, and result metadata.
- `def fuse_rrf(vector_results, keyword_results, top_k: int, rrf_k: int = 60) -> list[dict]` — identical RRF logic to the script: `hybrid_score = 1/(rrf_k + vector_rank) + 1/(rrf_k + keyword_rank)`; chunks in only one list still receive that signal's contribution; sorted by `hybrid_score` DESC, truncated to `top_k`.
- `async def retrieve(conn, query_vector, query_text, top_k, vector_candidates, keyword_candidates) -> list[dict]` — orchestrates the three steps above and returns the merged ranking.

All queries filter to `is_active = TRUE AND embedding IS NOT NULL`. No answer generation. No question text written to any table.

---

### `backend/app/api/routes/retrieval.py`

The `POST /api/retrieve` FastAPI route.

- Validates the request body against `RetrieveRequest` (empty query → 400, `top_k` out of range → 422).
- Computes `query_hash = sha256(query.lower().strip())` — stored in response only, not in the database.
- Calls `OllamaEmbeddingClient.embed(query)` — local only; raises HTTP 503 if Ollama is unreachable.
- Calls `retrieval_service.retrieve(...)` against the PostgreSQL connection pool.
- Returns a `RetrieveResponse`. Does not write to any table. Does not call any public AI API.

---

### `backend/app/main.py`

Add the retrieval router:

```python
from app.api.routes import retrieval
app.include_router(retrieval.router, prefix="/api")
```

No other changes to `main.py` beyond the router registration.

---

## 5. API Endpoint Design

### `POST /api/retrieve`

**Request body:**

```json
{
  "query": "Can asylum applicants get work authorization?",
  "top_k": 5
}
```

| Field | Type | Constraints | Default |
|---|---|---|---|
| `query` | string | non-empty; max 1000 characters | required |
| `top_k` | integer | 1–10 | 5 |

**Response body (200 OK):**

```json
{
  "status": "ok",
  "privacy_mode": "local-first",
  "query_hash": "a3f2c1...",
  "top_k": 5,
  "results": [
    {
      "rank": 1,
      "chunk_id": 1,
      "citation": "8 CFR § 208.7",
      "official_url": "https://www.ecfr.gov/current/title-8/chapter-I/subchapter-B/part-208/section-208.7",
      "topic": "asylum",
      "subtopic": "employment_authorization",
      "risk_level": "medium",
      "hybrid_score": 0.032787,
      "vector_rank": 1,
      "keyword_rank": null,
      "snippet": "An applicant for asylum..."
    }
  ]
}
```

**Error responses:**

| Status | Condition |
|---|---|
| 400 | `query` is empty or whitespace-only |
| 422 | Request body fails Pydantic validation (e.g. `top_k` out of range) |
| 503 | Ollama embedding service is unreachable |
| 500 | Database error or unexpected server fault |

`privacy_mode: "local-first"` is a static field in every response that signals to clients that no query data was sent to a public API.

---

## 6. Privacy Rules

These rules apply to every file added in this milestone. They are non-negotiable.

- **Query is accepted in memory only.** The raw query string lives only in the FastAPI request scope. It is embedded locally, used to construct a pgvector query string, and then discarded. It is never persisted to any table.
- **Do not store raw query text.** Neither the full query nor any truncated form of it may be written to `legal_chunks`, `privacy_safe_answer_logs`, or any other table. The only derivative of the query that may appear in the response is `query_hash` (SHA-256 of the normalized query).
- **If logging is needed later, hash only.** If a future milestone needs to audit query patterns, it must log only the normalized SHA-256 hash — never the plaintext query, never a fuzzy fingerprint that could reconstruct the original.
- **Do not store generated answers.** No answer is generated in this milestone. This rule is stated explicitly so it is not accidentally violated when the endpoint is extended.
- **Do not write to `privacy_safe_answer_logs` in this milestone.** This table is reserved for answer-generation metadata. It must remain at 0 rows after every run of this endpoint during development and testing.
- **No OpenAI, Anthropic, Cohere, Gemini, or any public AI API calls.** This is a HashGen Protocol 2 hard rule. Any code path that would call a remote AI API must be refused at the architecture level, not just guarded by a flag.
- **Ollama must remain local.** The `OLLAMA_BASE_URL` setting must resolve to a local or private network address. The embedding client must not be configured to point at a public Ollama-compatible proxy.

---

## 7. Retrieval Rules

These rules govern the behavior of `retrieval_service.py` and the route handler.

- **Only `legal_chunks WHERE is_active = TRUE`.** Every query that touches `legal_chunks` must include `is_active = TRUE` in the WHERE clause. Inactive chunks — from datasets in `ready`, `building`, or `archived` status — must never be returned to callers.
- **Require `embedding IS NOT NULL`.** Vector search must filter to chunks with a populated embedding. A chunk without an embedding is not eligible for retrieval.
- **Query embedding must be 768-dimensional.** The embedding client must verify `len(vector) == 768` before the vector is used in a SQL query. A dimension mismatch must raise an exception that surfaces as HTTP 503, not silently return wrong results.
- **Use pgvector for vector search.** The cosine-distance operator (`<->`) over `legal_chunks.embedding` is the vector signal. Results are ordered by ascending distance (lower = more similar).
- **Use `search_vector` for keyword search.** The `plainto_tsquery('english', query)` match against `legal_chunks.search_vector` is the keyword signal. Results are ordered by `ts_rank_cd` descending. If no chunks match the keyword query, keyword results are empty and the fusion step still runs on the vector results alone.
- **Fuse using RRF with `rrf_k = 60`.** The fusion formula is identical to `scripts/hybrid_retrieve_legal_chunks.py`: `hybrid_score = 1/(60 + vector_rank) + 1/(60 + keyword_rank)`. This constant must not be changed without re-running the hybrid validation script to confirm retrieval quality is maintained.
- **Every returned chunk must include `citation` and `official_url`.** A retrieval result without a citation is a bug. The response schema enforces these fields as non-nullable.

---

## 8. Safety Limits

Input validation enforced by `RetrieveRequest` and the route handler:

| Limit | Value | Enforcement |
|---|---|---|
| Max query length | 1000 characters | Pydantic `max_length=1000` on `query` field |
| Min `top_k` | 1 | Pydantic `ge=1` on `top_k` field |
| Max `top_k` | 10 | Pydantic `le=10` on `top_k` field |
| Empty query | rejected | Pydantic `min_length=1`; route returns HTTP 400 for whitespace-only input after `.strip()` |

Additional behavioral constraints:

- The endpoint must not include any language in its response that could be interpreted as legal advice. Response fields are citations, metadata, and text snippets — not interpreted guidance.
- The endpoint description in OpenAPI (`/docs`) must state: "Retrieval only. Returns public legal text citations and snippets. Does not generate legal advice."
- The `privacy_mode: "local-first"` field in every response communicates to the client that no user data was sent to a public API.

---

## 9. Testing Plan

Manual testing steps after implementation is complete. All steps use the five synthetic test queries from the prior milestone — no real user immigration facts.

**Step 1 — Start the backend:**

```bash
cd backend
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Step 2 — Confirm health endpoints still pass:**

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/health/dependencies
curl http://127.0.0.1:8000/health/schema
```

Expected: all return `"ok"` / all dependencies healthy / all 10 tables present.

**Step 3 — Run the five synthetic test queries:**

```bash
curl -s -X POST http://127.0.0.1:8000/api/retrieve \
  -H "Content-Type: application/json" \
  -d '{"query": "Can asylum applicants get work authorization?", "top_k": 5}' | python3 -m json.tool

curl -s -X POST http://127.0.0.1:8000/api/retrieve \
  -H "Content-Type: application/json" \
  -d '{"query": "When can someone file for asylum?", "top_k": 5}' | python3 -m json.tool

curl -s -X POST http://127.0.0.1:8000/api/retrieve \
  -H "Content-Type: application/json" \
  -d '{"query": "Who is eligible for adjustment of status?", "top_k": 5}' | python3 -m json.tool

curl -s -X POST http://127.0.0.1:8000/api/retrieve \
  -H "Content-Type: application/json" \
  -d '{"query": "What categories are authorized for employment?", "top_k": 5}' | python3 -m json.tool

curl -s -X POST http://127.0.0.1:8000/api/retrieve \
  -H "Content-Type: application/json" \
  -d '{"query": "What is a Notice to Appear?", "top_k": 5}' | python3 -m json.tool
```

For each query, confirm:
- HTTP 200.
- `results[0].citation` matches the expected citation from the hybrid validation script.
- Every result includes `citation`, `official_url`, `topic`, `risk_level`, `hybrid_score`, and `snippet`.
- `privacy_mode` is `"local-first"` in every response.

**Step 4 — Confirm input validation:**

```bash
# Empty query → 400
curl -s -X POST http://127.0.0.1:8000/api/retrieve \
  -H "Content-Type: application/json" \
  -d '{"query": "", "top_k": 5}'

# top_k out of range → 422
curl -s -X POST http://127.0.0.1:8000/api/retrieve \
  -H "Content-Type: application/json" \
  -d '{"query": "What is asylum?", "top_k": 99}'
```

**Step 5 — Confirm privacy invariant:**

```bash
psql -d immigration_law_dev -c \
  "SELECT COUNT(*) AS privacy_safe_answer_logs_count FROM privacy_safe_answer_logs;"
```

Expected: `0`.

**Step 6 — Confirm no frontend or mobile files changed:**

```bash
git diff --name-only main | grep -E '^(frontend|mobile)/' || echo "no frontend/mobile changes"
```

Expected: no matches.

---

## 10. Success Criteria

This milestone is complete when **all** of the following are true:

- [ ] `POST /api/retrieve` returns HTTP 200 with a valid `RetrieveResponse` for all five synthetic test queries.
- [ ] The top hybrid result (`results[0].citation`) matches the expected citation for each of the five queries, consistent with `scripts/validate_hybrid_retrieval_results.py`.
- [ ] The embedding client uses local Ollama only — no public AI API is called.
- [ ] Only `legal_chunks WHERE is_active = TRUE AND embedding IS NOT NULL` are returned.
- [ ] Every result in the response includes `citation` and `official_url` (non-null, non-empty).
- [ ] Raw query text is not written to any database table.
- [ ] `privacy_safe_answer_logs` row count is still 0 after all test queries are run.
- [ ] `/health`, `/health/dependencies`, and `/health/schema` all still pass.
- [ ] Empty query returns HTTP 400; `top_k` outside 1–10 returns HTTP 422.
- [ ] No frontend or mobile files are modified.
- [ ] No database migration files are modified.

---

## 11. Not Included Yet

The following are explicitly out of scope for this milestone. Each will be its own feature branch:

- **`/api/ask` endpoint** — the answer-generation chat endpoint is not implemented here.
- **Answer generation** — no script or route calls a chat LLM or generates a natural-language answer.
- **Local LLM chat** — `llama3.1:8b` and all chat models are out of scope.
- **Citation checker** — no logic verifies citation integrity at the API layer or applies a score threshold for out-of-scope queries.
- **Safety / refusal classifier** — no high-risk topic detection or attorney-referral CTA logic is implemented.
- **User accounts and authentication** — `admin_users` table exists in the schema but no auth is wired to this endpoint.
- **Frontend integration** — no React or Next.js components are added or modified.
- **Mobile integration** — no mobile code is added or modified.

---

## 12. Next Milestone After This

Recommended sequence once `feature/backend-retrieval-api` is merged:

1. **Retrieval-only `/api/ask` skeleton** — a `POST /api/ask` endpoint that calls `/api/retrieve` internally and returns citations and snippets without generating an answer. Establishes the stable contract that frontend and mobile will integrate against.
2. **Frontend / mobile integration** — wire the React chat UI and (if applicable) the mobile client to `/api/ask` using the retrieval-only response; render citations and snippets before LLM generation is available.
3. **Local LLM answer generation** — pass retrieved active chunks to `llama3.1:8b` via local Ollama as context; generate a plain-language answer with citations; log metadata only (no raw Q&A text) to `privacy_safe_answer_logs`.
4. **Citation and safety checker** — verify every chunk surfaced by retrieval has a citation string; add a refusal path for out-of-scope queries that return no active chunks above a configured score threshold; attach stronger disclaimers or attorney-referral CTAs for high-risk `risk_level` values.
