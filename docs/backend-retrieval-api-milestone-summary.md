# Backend Retrieval API Milestone Summary

**Status:** Complete  
**Branch:** `feature/backend-retrieval-api`  
**Merged into:** Not yet merged

---

## Branch

`feature/backend-retrieval-api`

---

## Purpose

This milestone moves the validated script-based hybrid retrieval pipeline into the FastAPI backend as a production-ready `POST /api/retrieve` endpoint.

The prior milestone (`feature/backend-cloud-foundation`) proved that hybrid vector+keyword retrieval works against the active public eCFR dataset at the script level — all five synthetic test queries retrieved their expected CFR citations at rank 1. This milestone exposes that same validated pipeline through FastAPI, establishing the stable retrieval contract that the frontend, mobile clients, and the future answer-generation path will build on.

This milestone does **not** generate legal answers, does **not** call a chat LLM, and does **not** write to `privacy_safe_answer_logs`.

---

## Completed Files

### `docs/backend-retrieval-api-plan.md`
Milestone planning document. Defined the purpose, scope, planned backend files, API endpoint design, privacy rules, retrieval rules, safety limits, testing plan, and success criteria. Written before any implementation code.

### `backend/app/schemas/retrieval.py`
Pydantic v2 request and response models for `POST /api/retrieve`. Defines four models:
- `RetrievalRequest` — validates `query` (non-empty string, max 1000 chars) and `top_k` (int 1–10, default 5); strips whitespace before validation via `@field_validator(mode="before")`.
- `RetrievalResult` — one ranked result item: `rank`, `chunk_id`, `citation`, `official_url`, `topic`, `subtopic`, `risk_level`, `hybrid_score`, `vector_rank`, `keyword_rank`, `vector_distance`, `keyword_score`, `snippet`.
- `RetrievalResponse` — full 200 OK response: `status`, `privacy_mode`, `query_hash`, `top_k`, `active_dataset`, `results`.
- `RetrievalErrorResponse` — error response shape: `status`, `error_code`, `message`, `privacy_mode`.

Raw query text is never stored. `query_hash` (SHA-256 of the lowercased, stripped query) is included in the response for potential future hash-only audit use — not written to any table.

### `backend/app/services/ollama_embedding_client.py`
Async local-only Ollama embedding client. Contacts only the local Ollama daemon at `OLLAMA_BASE_URL` (default `http://localhost:11434`) — never any public AI API. Key elements:
- `DEFAULT_EMBEDDING_MODEL = "nomic-embed-text"`, `EXPECTED_EMBEDDING_DIMENSIONS = 768`.
- `EmbeddingClientError` — all error messages are privacy-safe; never include raw query text, URL credentials, HTTP response bodies, or stack traces.
- `async def embed_query(query, *, model, ollama_base_url, timeout_seconds) -> list[float]` — POSTs to `/api/embed`, parses `embeddings[0]`, validates numeric values and exactly 768 dimensions.
- `def format_pgvector_literal(vector) -> str` — formats a `list[float]` as `"[f1,f2,...]"` for use with psycopg `::vector` casts.

Uses `httpx.AsyncClient` to avoid blocking the FastAPI async event loop.

### `backend/app/services/retrieval_service.py`
Retrieval business logic ported from `scripts/hybrid_retrieve_legal_chunks.py`. Operates exclusively on `legal_chunks WHERE is_active = TRUE`. Key elements:
- `RetrievalService` class — stateless between calls; accepts `Settings` via constructor.
- `async def retrieve_hybrid(query, top_k=5) -> tuple[list[RetrievalResult], str | None]` — embeds the query locally, runs vector search and keyword search in parallel via a single DB connection, fuses results with RRF, and returns ranked results with the active dataset name.
- `_vector_search` — pgvector cosine-distance search filtered to `is_active = TRUE AND embedding IS NOT NULL`; ordered ascending by distance.
- `_keyword_search` — PostgreSQL `plainto_tsquery` full-text search against `search_vector`; ordered by `ts_rank_cd` descending.
- `_fuse_rrf` — Reciprocal Rank Fusion with `RRF_K = 60`, kept in sync with `scripts/validate_hybrid_retrieval_results.py`.
- All SQL queries are fully parameterized — no string interpolation of query text or vectors.
- The `app.db.connection` import is deferred inside `retrieve_hybrid()` to avoid a hard psycopg dependency at module import time.

### `backend/app/api/routes/retrieval.py`
FastAPI route layer for `POST /api/retrieve`. Follows the project's existing `health.py` route style. Key elements:
- `router = APIRouter(tags=["retrieval"])`.
- Endpoint accepts `RetrievalRequest`, injects `Settings` via `Depends(get_settings)`.
- Computes `query_hash = sha256(query.lower().strip().encode()).hexdigest()` in memory — never persisted.
- Instantiates `RetrievalService(settings)` inline per request.
- Maps `EmbeddingClientError` → HTTP 503 (`OLLAMA_UNAVAILABLE`); any other exception → HTTP 500 (`RETRIEVAL_ERROR`).
- Error messages never echo the raw query, the database DSN, or stack traces.
- Returns `RetrievalResponse` with `privacy_mode: "local-first"` in every response.

### `backend/app/main.py`
Router registration. The retrieval router was added alongside the existing health router:

```python
from app.api.routes import health, retrieval
...
app.include_router(health.router)
app.include_router(retrieval.router)
```

No prefix added — `retrieval.py` already declares the full path `/api/retrieve`. No other changes to `main.py`.

---

## API Endpoint

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
  "active_dataset": "ecfr-title8-sample-2026-05-12",
  "results": [
    {
      "rank": 1,
      "chunk_id": 1,
      "citation": "8 CFR § 208.7",
      "official_url": "https://www.ecfr.gov/current/title-8/...",
      "topic": "asylum",
      "subtopic": "employment_authorization",
      "risk_level": "medium",
      "hybrid_score": 0.032787,
      "vector_rank": 1,
      "keyword_rank": null,
      "vector_distance": 0.21,
      "keyword_score": null,
      "snippet": "An applicant for asylum..."
    }
  ]
}
```

**Error responses:**

| Status | Condition |
|---|---|
| 422 | Request body fails Pydantic validation (`query` empty or whitespace-only, `top_k` out of range) |
| 503 | Ollama embedding service is unreachable |
| 500 | Database error or unexpected server fault |

The raw query is **not** returned in the response payload. `query_hash` is a one-way SHA-256 hash of `query.lower().strip()`, computed in memory only and never written to any table. `privacy_mode: "local-first"` is a static field present in every response — success and error — signaling that no query data was sent to a public API.

---

## Retrieval Behavior

- Searches only `legal_chunks WHERE is_active = TRUE`.
- Vector search additionally requires `embedding IS NOT NULL`.
- Query is embedded locally using Ollama `nomic-embed-text` (768 dimensions). No public AI API is contacted.
- **Vector search:** pgvector cosine-distance operator (`embedding <-> %s::vector`) ordered ascending; lower distance = more similar.
- **Keyword search:** PostgreSQL `plainto_tsquery('english', query)` match against `search_vector`, ordered by `ts_rank_cd` descending. If no chunks match, keyword results are empty and fusion runs on vector results alone.
- **Reciprocal Rank Fusion (RRF_K = 60):**

  ```
  vector_score  = 1 / (60 + vector_rank)
  keyword_score = 1 / (60 + keyword_rank)
  hybrid_score  = vector_score + keyword_score
  ```

  Chunks present in only one list still receive that signal's contribution. Results are sorted by `hybrid_score` descending and truncated to `top_k`. `RRF_K = 60` is kept in sync with `scripts/validate_hybrid_retrieval_results.py`.

- Candidate pool: 10 vector candidates + 10 keyword candidates fed into fusion before truncation to `top_k` (capped at 10 by schema).

---

## Active Dataset Used in Validation

`ecfr-title8-sample-2026-05-12`

---

## Validation Results

The following were verified after `POST /api/retrieve` was wired into the live FastAPI app:

| Test query | Expected rank-1 citation | Result |
|---|---|---|
| "Can asylum applicants get work authorization?" | `8 CFR § 208.7` | Passed |
| "What is a Notice to Appear?" | `8 CFR § 239.1` | Passed |

Additional checks:

- Real app `TestClient` confirmed `POST /api/retrieve` returns HTTP 200 with a valid `RetrievalResponse`.
- `/health` continued to return `"ok"` after router registration.
- `privacy_safe_answer_logs` row count remained **0** throughout all test runs.
- The raw query string did not appear anywhere in the response payload.
- Every result included `citation`, `official_url`, `topic`, `hybrid_score`, and `snippet`.

---

## Privacy and Security Guarantees

- No legal answers are generated in this milestone.
- No `llama3.1` or other chat LLM call is made.
- No public AI API is called at any point in the retrieval path.
- Raw user query text is never written to `privacy_safe_answer_logs`.
- No generated answers are written to `privacy_safe_answer_logs`.
- `privacy_safe_answer_logs` remains metadata-only and was at 0 rows after all validation runs.
- All embedding is performed locally via Ollama. The embedding client contacts only the local daemon at `OLLAMA_BASE_URL`.
- All SQL queries are fully parameterized — query text and vectors are never string-interpolated into SQL.
- Error messages at every layer (embedding client, service, route) are privacy-safe: they never include raw query text, the database DSN, URL credentials, or Python stack traces.
- Retrieval is local-first end-to-end.

---

## Current Limitations

- The retrieval endpoint returns legal source chunks and citations only. It does not generate a final legal guidance response.
- This is **not legal advice**. Returned content is raw public legal text with citations.
- The endpoint has not yet been connected to the frontend or mobile clients.
- The endpoint currently depends on a local PostgreSQL + pgvector database and a locally running Ollama daemon. It is not yet wired to a shared cloud database or remote embedding service.
- Only the active `ecfr-title8-sample-2026-05-12` dataset (5 chunks) was available during validation. Retrieval quality at scale has not been evaluated.

---

## Next Recommended Steps

1. **Add a lightweight backend API smoke test or test script** — automate the two verified synthetic queries against a test database fixture so retrieval quality regressions are caught in CI.
2. **Add an answer-generation layer** — future milestone using a local-only reasoning model (e.g., `llama3.1:8b` via Ollama) to synthesize a plain-language answer from retrieved chunks; log metadata only (no raw Q&A text) to `privacy_safe_answer_logs`.
3. **Add frontend and mobile integration** — wire the React chat UI and mobile client to the retrieval endpoint; render citations and snippets before LLM generation is available.
4. **Keep privacy-safe logging metadata-only** — if query auditing is needed, log only the normalized SHA-256 hash; never the plaintext query or any derivative that could reconstruct the original.
