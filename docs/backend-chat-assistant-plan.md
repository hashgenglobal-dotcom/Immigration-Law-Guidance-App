# Backend Chat Assistant Plan

**Status:** Planning — no chat endpoint code written yet
**Branch:** `feature/backend-chat-assistant`
**Scope:** Add a chat-style backend assistant on top of the existing retrieval API. This milestone does not integrate with the frontend or mobile app, does not store raw user questions or generated answers, and does not call any public AI API.

Related docs:

- [`docs/backend-retrieval-api-plan.md`](./backend-retrieval-api-plan.md) — retrieval API milestone plan
- [`docs/backend-retrieval-api-milestone-summary.md`](./backend-retrieval-api-milestone-summary.md) — retrieval API milestone summary and validation results

---

## Branch

`feature/backend-chat-assistant`

---

## Purpose

This milestone adds a `POST /api/chat` endpoint to the FastAPI backend. The endpoint accepts a single user message, retrieves the most relevant public legal chunks using the existing retrieval pipeline, and passes those chunks to a local Ollama chat model to generate a plain-language legal information response with citations.

The goal is to turn retrieved legal source text into a conversational, grounded answer — not to replace the retrieval endpoint, and not to provide legal advice. The retrieval endpoint (`POST /api/retrieve`) remains unchanged. The chat endpoint is an answer-generation layer built on top of it.

The response must be:

- Grounded exclusively in retrieved legal chunks. The model must not add information beyond what the chunks contain.
- Citation-backed. Every response includes the citations of the chunks that were used.
- Accompanied by a legal disclaimer. The response always states that this is general legal information, not advice from an attorney.
- Privacy-safe. Raw user questions are not stored. Generated answers are not stored. No public AI API is called.

This milestone does not connect the chat endpoint to any frontend or mobile client.

> **Important:** This plan does not claim that chatbot functionality is implemented. No chat endpoint exists yet. This document defines what will be built.

---

## Current Foundation

The following has been implemented, validated, and merged into `main` from the backend retrieval API milestone:

| Component | Details |
|---|---|
| Backend framework | FastAPI with async PostgreSQL via psycopg |
| Database | PostgreSQL with pgvector extension |
| Legal data table | `legal_chunks` — stores public eCFR text chunks with embeddings, citations, `topic`, `subtopic`, `risk_level`, `official_url`, and `search_vector` |
| Active dataset support | `dataset_versions.status = 'active'` controls which dataset is searched; only `is_active = TRUE` chunks are returned |
| Embedding model | Local Ollama `nomic-embed-text` (768-dimensional vectors); no public AI API |
| Embedding client | `backend/app/services/ollama_embedding_client.py` — async, `httpx`-based, validates 768 dimensions, never logs query text |
| Retrieval service | `backend/app/services/retrieval_service.py` — `RetrievalService.retrieve_hybrid()` runs pgvector cosine-distance search and `plainto_tsquery` full-text search, fuses results with Reciprocal Rank Fusion (`RRF_K = 60`) |
| Retrieval endpoint | `POST /api/retrieve` — accepts `query` and `top_k`, returns ranked `RetrievalResult` objects with citations, snippets, and metadata |
| Privacy logging | `privacy_safe_answer_logs` table exists in the schema and remains at 0 rows; it is metadata-only and is never written to by the retrieval path |
| Query privacy | Raw query text lives in memory only for the duration of a single request; only `query_hash` (SHA-256 of normalized query) appears in the response |
| Health endpoints | `/health`, `/health/dependencies`, `/health/schema` all passing |

The chat milestone builds on this foundation without modifying any of the files above.

---

## Planned Endpoint

> **This endpoint does not exist yet.** The following defines the intended design.

### `POST /api/chat`

**Planned request body:**

```json
{
  "message": "Can asylum applicants get work authorization?",
  "top_k": 5
}
```

| Field | Type | Constraints | Default |
|---|---|---|---|
| `message` | string | non-empty; max 1000 characters | required |
| `top_k` | integer | 1–10 | 5 |

**Planned response body (200 OK):**

```json
{
  "status": "ok",
  "privacy_mode": "local-first",
  "query_hash": "a3f2c1...",
  "answer": "Asylum applicants may apply for work authorization...",
  "citations": ["8 CFR § 208.7", "8 CFR § 274a.12"],
  "disclaimer": "This is general legal information only. It is not legal advice and does not create an attorney-client relationship. Consult a qualified immigration attorney for advice specific to your situation.",
  "active_dataset": "ecfr-title8-sample-2026-05-12",
  "used_chunks": [
    {
      "rank": 1,
      "chunk_id": 1,
      "citation": "8 CFR § 208.7",
      "official_url": "https://www.ecfr.gov/current/title-8/...",
      "topic": "asylum",
      "subtopic": "employment_authorization",
      "risk_level": "medium",
      "hybrid_score": 0.032787,
      "snippet": "An applicant for asylum..."
    }
  ]
}
```

`privacy_mode: "local-first"` is a static field present in every response — success and error — signaling that no query data was sent to a public API. The raw `message` is not returned in the response payload. `query_hash` is a one-way SHA-256 hash of the normalized message, computed in memory only and never written to any table.

**Planned error responses:**

| Status | Condition |
|---|---|
| 422 | Request body fails Pydantic validation (`message` empty or whitespace-only, `top_k` out of range) |
| 503 | Local Ollama service (embedding or chat) is unreachable |
| 500 | Database error or unexpected server fault |

---

## Chatbot Behavior

- **Single-turn only (first version).** The endpoint accepts one user message at a time. Persistent chat history across multiple turns is not supported in this milestone.
- **Retrieval-grounded.** The endpoint calls `RetrievalService.retrieve_hybrid()` using the user's message as the query. The same retrieval pipeline that powers `POST /api/retrieve` is reused unchanged.
- **Multiple chunks.** The answer must be generated using all retrieved chunks (up to `top_k`), not just the top result. The suggested default is `top_k = 5`.
- **Constrained generation.** The chat model is instructed to use only the provided retrieved chunks as its source of truth. It must not invent laws, deadlines, eligibility rules, or citations beyond what the chunks contain.
- **Safe uncertainty.** If the retrieved chunks do not answer the question — for example, because no relevant active chunks were returned or the hybrid scores are very low — the response must say that the assistant cannot answer confidently from the available sources. It must not fabricate an answer.
- **Always cited.** Every response includes a `citations` list populated from the retrieved chunks. A response without citations is a bug.
- **Always disclaimed.** Every response includes a plain-language disclaimer that this is general legal information, not legal advice, and that the user should consult a qualified immigration attorney for situation-specific guidance.
- **Conversational but careful.** The tone should be plain and accessible, but the assistant must not overstate its confidence or suggest definitive outcomes for specific cases.

---

## Local LLM Strategy

- **Local Ollama chat model only.** The answer-generation step contacts only the local Ollama daemon. No request is made to any public AI API at any point in the chat path.
- **Candidate model.** The intended model is `llama3.1:8b` or another local Ollama chat model already available on the development machine. The exact model selection will be confirmed during implementation.
- **Separate chat client.** A new `backend/app/services/ollama_chat_client.py` will be created for chat-completion requests. It will follow the same design principles as `ollama_embedding_client.py`: async, `httpx`-based, privacy-safe error messages, and no logging of raw query or response text.
- **Embedding and chat clients remain separate.** `ollama_embedding_client.py` handles only vector embedding and must not be extended to support chat. The two clients have different API endpoints, response shapes, and privacy properties.
- **No raw message to public services.** The user's message is embedded and retrieved against locally, and then passed only to the local Ollama chat model. It never leaves the local machine.

---

## Prompting Strategy

The following describes the intended system prompt structure for the local chat model. This is a plan — the exact wording will be finalized during implementation.

**Planned system prompt style:**

- You are a legal information assistant. You are not a lawyer, and you do not provide legal advice.
- Use only the retrieved legal source chunks provided to you. Do not use any knowledge beyond these sources.
- Do not invent laws, deadlines, eligibility rules, form numbers, processing times, or citations. If a detail is not in the provided sources, do not state it.
- If the provided sources do not answer the question, say clearly that you cannot answer this question from the available sources, and recommend consulting a qualified immigration attorney.
- Explain in plain language that a non-expert can understand. Avoid legal jargon where possible, or explain it when used.
- When the topic involves significant personal risk — such as removal, detention, asylum denial, or criminal consequences — mention that risk explicitly and strongly recommend consulting a qualified immigration attorney.
- Always cite the specific CFR section or legal source that supports each statement. Use the citation strings from the retrieved chunks.
- Never state or imply that this is legal advice. Never state or imply that this creates an attorney-client relationship.
- Do not provide guidance on how to evade immigration law, misrepresent facts on applications, avoid court, commit fraud, or otherwise circumvent legal obligations. Decline these requests clearly.

---

## Privacy and Security Rules

These rules apply to every file added in this milestone. They are non-negotiable.

- **No raw user questions stored.** The `message` field lives in memory only for the duration of a single request. It must not be written to `privacy_safe_answer_logs`, `legal_chunks`, or any other table.
- **No generated answers stored.** The LLM-generated answer text must not be written to any database table.
- **No persistent chat history in first version.** The endpoint is stateless between requests. No session, conversation, or turn history is stored.
- **No public AI APIs.** The embedding step uses local Ollama `nomic-embed-text`. The chat step uses a local Ollama chat model. No request is made to any external AI service.
- **No frontend or mobile integration in this milestone.** The `POST /api/chat` endpoint is backend-only. No React, Next.js, React Native, or mobile code is modified.
- **No credentials in code.** Runtime configuration values must be loaded through the existing `Settings` / `get_settings()` pattern. Credentials, raw DSNs, and private local paths must not be hardcoded.
- **No `.env` commits.** `.env` and `.env.*` files must not be committed to version control.
- **`privacy_safe_answer_logs` remains metadata-only.** This table must not receive raw query text or raw answer text. If logging is added in a future milestone, only metadata may be recorded — specifically: `query_hash`, retrieval result count, latency in milliseconds, model name, and error code. The following must never be logged: raw prompt, raw response, full retrieved chunk text, or raw user message.
- **Error messages are privacy-safe.** Error responses from the chat route, chat client, and chat service must never echo the user's message, the database DSN, URL credentials, or Python stack traces.

---

## Legal Safety Rules

- **General legal information only.** This application provides general legal information sourced from public regulatory text. It does not provide legal advice.
- **No attorney-client relationship.** The application does not create an attorney-client relationship between the user and any person or entity.
- **Attorney consultation recommended for high-stakes situations.** The assistant should recommend consulting a qualified immigration attorney for any situation involving urgent deadlines, removal proceedings, detention, criminal consequences, or case-specific eligibility questions.
- **No final eligibility decisions.** The assistant must not tell a user that they are eligible or ineligible for a specific immigration benefit. It may explain what the regulations say about eligibility criteria.
- **No filing instructions without source support.** The assistant must not tell a user what to file, when to file, or how to file unless the instruction is directly supported by a retrieved legal chunk with a citation.
- **No assistance with misrepresentation, fraud, or evasion.** The assistant must not help users misrepresent facts on applications, avoid court appearances, evade immigration law, or commit fraud. Requests of this type must be declined clearly.

---

## Planned Backend Files

The following files will be created during implementation of this milestone. **None of these files exist yet and none should be created as part of writing this plan.**

- `backend/app/schemas/chat.py` — Pydantic v2 request and response models for `POST /api/chat` (`ChatRequest`, `ChatResponse`, `ChatErrorResponse`).
- `backend/app/services/ollama_chat_client.py` — Async local-only Ollama chat completion client. Contacts only the local Ollama daemon. Separate from `ollama_embedding_client.py`. Never logs raw prompt or response.
- `backend/app/services/chat_service.py` — Chat business logic. Calls `RetrievalService.retrieve_hybrid()` to fetch chunks, builds the system prompt with retrieved chunk text and citations, calls `OllamaChatClient` for answer generation, and assembles the `ChatResponse`.
- `backend/app/api/routes/chat.py` — FastAPI route for `POST /api/chat`. Follows the same structure as `retrieval.py`. Maps `OllamaChatClientError` → HTTP 503; other exceptions → HTTP 500. Never echoes the raw message in error responses.
- `backend/app/main.py` — Router registration for the chat router will be added in this milestone, alongside the existing health and retrieval routers. No other changes to `main.py`.

---

## Testing Plan

The following validation steps are planned for after implementation is complete. All test queries use synthetic legal questions — no real personal immigration facts.

1. **Import check.** Confirm that `schemas/chat.py`, `services/ollama_chat_client.py`, `services/chat_service.py`, and `api/routes/chat.py` all import without error.
2. **Asylum work authorization query.** Send `POST /api/chat` with `"message": "Can asylum applicants get work authorization?"` and confirm HTTP 200, a non-empty `answer`, and `citations` containing `8 CFR § 208.7`.
3. **Notice to Appear query.** Send `POST /api/chat` with `"message": "What is a Notice to Appear?"` and confirm HTTP 200, a non-empty `answer`, and `citations` containing `8 CFR § 239.1`.
4. **Citations present.** For every test response, confirm that the `citations` list is non-empty and that each entry is a non-empty string matching the `citation` field of a returned chunk in `used_chunks`.
5. **Raw query not returned.** Confirm that the raw `message` value does not appear anywhere in the response payload.
6. **`privacy_safe_answer_logs` remains metadata-only.** After running all test queries, confirm the row count in `privacy_safe_answer_logs` has not increased and that no raw query text or answer text appears in any row.
7. **No public API calls.** Confirm that the chat path contacts only `OLLAMA_BASE_URL` (local daemon). No network calls to external AI services should occur.
8. **Top-k chunks used.** Confirm that `used_chunks` in the response contains up to `top_k` entries and that `top_k` defaults to 5 when not specified.
9. **Safe uncertainty response.** Send a query that is unlikely to match any active chunk (e.g., a question unrelated to immigration law) and confirm the response acknowledges it cannot answer confidently from available sources, rather than fabricating an answer.
10. **Existing endpoints unchanged.** After wiring the chat router, confirm `/health` returns `"ok"` and `POST /api/retrieve` returns a valid `RetrievalResponse` for the five synthetic test queries from the prior milestone.

---

## Success Criteria

This milestone is complete when **all** of the following are true:

- [ ] `POST /api/chat` returns HTTP 200 with a valid `ChatResponse` for the asylum work authorization and Notice to Appear test queries.
- [ ] Every response includes a non-empty `answer` field.
- [ ] Every response includes a non-empty `citations` list populated from retrieved chunks.
- [ ] Every response includes a plain-language legal disclaimer.
- [ ] Answer generation uses a local Ollama chat model only — no public AI API is called.
- [ ] Raw user questions are not written to any database table.
- [ ] Generated answers are not written to any database table.
- [ ] `privacy_safe_answer_logs` remains metadata-only and is not written to by the chat path.
- [ ] `POST /api/retrieve` continues to return valid results for all five synthetic test queries.
- [ ] `/health`, `/health/dependencies`, and `/health/schema` all still pass.
- [ ] No frontend or mobile files are modified.
- [ ] No database migration files are modified.
- [ ] No dependency files (`pyproject.toml`, `uv.lock`, `package.json`, lock files) are modified.

---

## Out of Scope for This Milestone

The following are explicitly deferred to future milestones:

- **Mobile integration** — no mobile code is modified.
- **Web / frontend integration** — no React or Next.js code is modified.
- **Real user accounts** — no authentication is wired to the chat endpoint.
- **Persistent chat history** — multi-turn conversation memory is not implemented in the first version.
- **Production authentication** — bearer credentials, JWT, or OAuth are not implemented in this milestone.
- **Cloud deployment** — this milestone targets the local development environment only.
- **Full legal dataset expansion** — the active dataset used during development is the existing `ecfr-title8-sample-2026-05-12` sample.
- **Attorney marketplace or lawyer referral features** — the assistant recommends consulting an attorney but does not connect users with attorneys.
- **Lawyer replacement claims** — the assistant is not a lawyer and must not be described as one.
