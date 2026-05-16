# Retrieval Milestone Plan

**Status:** Planning — no retrieval code written yet
**Owner:** Backend track on `feature/backend-cloud-foundation`
**Scope:** Plan how we will test retrieval against the now-active embedded eCFR Title 8 sample `legal_chunks` before any backend retrieval service, `/api/retrieve` endpoint, `/api/chat/ask` endpoint, or LLM answer generation is built. This milestone is documentation-only and verification-only — it does not generate legal answers.

Related docs:
- [`docs/dataset-activation-milestone-plan.md`](./dataset-activation-milestone-plan.md) — how the active eCFR sample dataset reached its current state
- [`docs/local-embeddings-milestone-plan.md`](./local-embeddings-milestone-plan.md) — how the 768-dimensional embeddings on `legal_chunks` were generated
- [`docs/ecfr-ingestion-milestone-plan.md`](./ecfr-ingestion-milestone-plan.md) — how the eCFR Title 8 sample chunks were ingested
- [`database/migrations/001-initial-schema.sql`](../database/migrations/001-initial-schema.sql) — schema referenced below

---

## 1. Purpose

Before we build the backend retrieval service, the `/api/retrieve` endpoint, the `/api/chat/ask` endpoint, or any LLM answer-generation path, we need direct evidence that user-like legal questions actually retrieve the correct active public legal chunks from the database.

Retrieval testing is the checkpoint between "we have embedded chunks in the database" and "we are ready to wire chunks into an answer pipeline." It verifies that:

- A natural-language legal question, embedded locally, lands close (in vector space) to the right CFR section.
- Keyword search over `legal_chunks.search_vector` surfaces the correct citation when query terms appear directly in the regulation.
- The combination of vector and keyword retrieval is at least as good as either signal alone for the small MVP question set.

Retrieval testing **does not** generate answers. It does not call a chat LLM. It does not handle real user input. Its only job is to prove that the retrieval surface area is correct on public legal data so that later phases (citation checking, refusal logic, LLM answer generation) can be built on a known-good foundation.

---

## 2. Current State

Before this milestone runs, the database state is:

| Table | Column | State |
| --- | --- | --- |
| `dataset_versions` | `version_name` | `ecfr-title8-sample-2026-05-12` |
| `dataset_versions` | `status` | `active` |
| `dataset_versions` | `activated_at` | non-NULL |
| `legal_chunks` | row count (active) | 5 |
| `legal_chunks` | `is_active` | `TRUE` on all 5 rows |
| `legal_chunks` | `embedding` | `vector(768)` populated for all 5 active rows |
| `legal_chunks` | source | public eCFR Title 8 regulatory text |
| `privacy_safe_answer_logs` | (all) | 0 rows |

In short: the eCFR Title 8 sample dataset is active, all 5 active `legal_chunks` carry 768-dimensional embeddings generated locally, the underlying data is fully public, and no answer-log rows exist yet. This is exactly the state retrieval testing is designed to operate on.

---

## 3. Scope

This milestone is intentionally narrow.

**In scope:**
- Embedding short, synthetic, public test questions locally with Ollama `nomic-embed-text` (768-dim).
- Running pgvector similarity search against `legal_chunks.embedding` filtered to `is_active = TRUE`.
- Running PostgreSQL full-text search against `legal_chunks.search_vector` (auto-populated by the schema's trigger) filtered to `is_active = TRUE`.
- Combining the two signals into a hybrid ranking and inspecting which chunks surface.
- Reporting citations, official URLs, topic, subtopic, risk level, and snippets for the retrieved chunks.

**Out of scope:**
- Generating legal answers in any form.
- Calling a chat LLM (e.g. `llama3.1:8b`) or any cloud LLM.
- Storing user questions or any portion of them.
- Writing to `privacy_safe_answer_logs`.
- Building a FastAPI endpoint, route, or service.
- Modifying `backend/app` code or database migrations.
- Handling real user immigration questions.

---

## 4. Retrieval Types

Three retrieval modes are planned. All three operate over `legal_chunks WHERE is_active = TRUE` only.

### A. Vector retrieval

- Embed the synthetic query locally with Ollama `nomic-embed-text` to produce a 768-dim vector.
- Compare the query vector against `legal_chunks.embedding` using pgvector cosine distance (`<=>`).
- Filter to `is_active = TRUE` so that only chunks belonging to the active dataset are eligible.
- Return the top-k chunks ordered by ascending cosine distance, along with citation, distance, snippet, and metadata.

### B. Keyword retrieval

- Build a `tsquery` from the synthetic question (using `plainto_tsquery('english', ...)` or equivalent).
- Match against `legal_chunks.search_vector`, which the schema trigger keeps populated from `chunk_text`.
- Filter to `is_active = TRUE`.
- Return chunks ordered by `ts_rank` / `ts_rank_cd`, including the citation and snippet so we can see *why* a chunk matched.

### C. Hybrid retrieval

- Run both vector retrieval and keyword retrieval for the same query.
- Combine the two ranked lists. Chunks that appear in both lists rank higher than chunks that appear in only one (a simple normalize-and-add or reciprocal-rank-fusion approach is acceptable for this milestone — the exact weighting is an open question; see §10).
- Return the merged ranking together with per-signal scores so it is clear which signal pushed each chunk up.
- Always include `citation`, `official_url`, `topic`, `subtopic`, `risk_level`, and a short `snippet` for every returned chunk so the result is human-reviewable.

---

## 5. First Test Queries

Only safe, synthetic, public test questions are used in this milestone. None of them describe a real person, a real case, or any user-supplied facts. Each is intentionally close in topic to one of the 20 MVP questions and is expected to retrieve a specific public eCFR Title 8 chunk.

| # | Synthetic test query | Expected target citation |
| --- | --- | --- |
| 1 | Can asylum applicants get work authorization? | 8 CFR § 208.7 |
| 2 | When can someone file for asylum? | 8 CFR § 208.4 |
| 3 | Who is eligible for adjustment of status? | 8 CFR § 245.1 |
| 4 | What categories are authorized for employment? | 8 CFR § 274a.12 |
| 5 | What is a Notice to Appear? | 8 CFR § 239.1 |

These queries are paraphrases of public regulatory topics, not user case facts. A query is considered correctly answered if its expected citation appears in the top-k retrieved chunks (the exact value of *k* is an open question; see §10).

---

## 6. Planned Scripts

Four scripts are planned for this milestone, following the same dry-run → real-run → validate pattern used for ingestion, embedding, and activation. They are described here so the plan can be reviewed before any code is written.

> **`scripts/dry_run_retrieve_legal_chunks.py` now exists.** Run with `uv run --project backend python scripts/dry_run_retrieve_legal_chunks.py`. Connects to PostgreSQL (read-only), inspects the active dataset and its 5 active `legal_chunks` (citation, topic, subtopic, risk level, official URL, embedding dimension, snippet), prints the five planned synthetic test queries with their expected target citations, verifies `privacy_safe_answer_logs` is still 0, and prints a compact JSON summary — no Ollama calls, no embedding generation, no answer generation, no database writes.

### `scripts/dry_run_retrieve_legal_chunks.py`

**Purpose:** Show what retrieval *will* operate on, without doing any retrieval work.

**Behavior:**
- Connect to PostgreSQL (read-only).
- List active `legal_chunks` (citation, title, topic, subtopic, risk level, embedding presence/dimension).
- Print the five synthetic test queries from §5 and their expected citations.
- Confirm the active dataset version and chunk count.
- Do **not** embed anything. Do **not** call Ollama. Do **not** write to any table.

**Exit codes:** 0 if dataset state matches §2; 1 otherwise.

---

> **`scripts/retrieve_legal_chunks.py` now exists.** Run with `uv run --project backend python scripts/retrieve_legal_chunks.py`. Embeds a synthetic test query locally via Ollama `nomic-embed-text`, verifies the resulting vector is exactly 768-dimensional, then runs a pgvector cosine-distance search over `legal_chunks WHERE is_active = TRUE`. Prints rank, citation, topic, subtopic, risk level, official URL, distance, and a 500-character snippet for each result — no answer generation, no question storage, no database writes, no public AI APIs.

### `scripts/retrieve_legal_chunks.py`

**Purpose:** Run vector retrieval against the active chunks for one synthetic query at a time.

**Behavior:**
- Accept a synthetic query string and a top-k value as CLI arguments.
- Embed the query locally using Ollama `nomic-embed-text` (768-dim). Refuse to run if the resulting vector is not exactly 768-dim.
- Run a pgvector cosine-distance search against `legal_chunks.embedding` filtered to `is_active = TRUE`.
- Return the top-k results with: `citation`, cosine `distance`, `topic`, `subtopic`, `risk_level`, `official_url`, and a short `snippet` of `chunk_text`.
- Do **not** generate an answer. Do **not** write to any table. Do **not** log the query text.

**Exit codes:** 0 if retrieval succeeds; 1 on any embedding, dimension, or DB error.

---

### `scripts/hybrid_retrieve_legal_chunks.py`

**Purpose:** Run combined vector + keyword retrieval for one synthetic query at a time.

**Behavior:**
- Accept a synthetic query string and a top-k value.
- Embed the query locally with Ollama `nomic-embed-text` (768-dim).
- Run vector retrieval (as in `retrieve_legal_chunks.py`).
- Run keyword retrieval over `legal_chunks.search_vector` for the same query.
- Combine results, preferring chunks that appear in both lists.
- Print a merged ranking with citation, official URL, both scores (vector distance and full-text rank), topic, subtopic, risk level, and snippet.
- Do **not** generate an answer. Do **not** write to any table. Do **not** log the query text.

**Exit codes:** 0 if both retrievals succeed; 1 on any error.

---

### `scripts/validate_retrieval_results.py`

**Purpose:** Confirm that the five synthetic queries from §5 each retrieve their expected citation, and confirm safety invariants are preserved.

**Behavior:**
- Iterate over the five `(query, expected_citation)` pairs from §5.
- For each pair, embed the query locally and run vector retrieval (or hybrid retrieval, if so configured) with the agreed-upon top-k.
- PASS the query if `expected_citation` appears anywhere in the top-k results; FAIL otherwise.
- Confirm the active chunk count is still 5 and `dataset_versions.status = 'active'` for the expected version.
- Confirm `privacy_safe_answer_logs` row count is still 0.
- Print a per-query PASS/FAIL line and a final summary.

**Exit codes:** 0 if all five queries PASS and `privacy_safe_answer_logs` count is still 0; 1 on any FAIL.

---

## 7. Safety and Privacy Rules

These rules apply to every script and every test in this milestone. They are non-negotiable.

- **Only synthetic test questions are used.** The five queries in §5 are paraphrases of public regulatory topics. They contain no names, A-numbers, dates of birth, addresses, case facts, or other identifying information.
- **No real user immigration facts are used.** This milestone does not accept input from end users. The scripts run only the curated synthetic queries.
- **No questions are stored.** Neither the synthetic test queries nor any future query text is persisted to any table by these scripts. Print-to-stdout is acceptable for development; database writes are not.
- **No answer generation happens.** No script in this milestone calls a chat LLM. No script composes a natural-language answer. The only outputs are retrieved chunks, citations, and metadata.
- **No public AI APIs are used.** OpenAI, Anthropic, Cohere, Gemini, and all other cloud AI APIs are prohibited. This is a Protocol 2 hard rule and applies to every script in the project.
- **Ollama must stay local.** All embedding work runs against the local Ollama daemon (`http://localhost:11434` or the agreed local endpoint). No remote embedding service is used.
- **Retrieval results must include citations and official URLs.** Every chunk surfaced by a retrieval script must carry its `citation` (e.g. `8 CFR § 208.7`) and its `official_url` so a reviewer can verify the source. A retrieval result without a citation is a bug.
- **`privacy_safe_answer_logs` is not written.** This table is reserved for answer-time metadata and is not touched until the LLM answer-generation milestone — which is not this one.

---

## 8. Success Criteria

This milestone is complete when **all** of the following are true:

- [ ] All 5 active chunks are discoverable from `legal_chunks` with `is_active = TRUE` and 768-dim embeddings.
- [ ] Query embeddings produced by Ollama `nomic-embed-text` are exactly 768-dimensional.
- [ ] Each of the five synthetic queries from §5 retrieves its expected citation in the agreed top-k.
- [ ] Every retrieval result carries `citation`, `official_url`, `topic`, `subtopic`, `risk_level`, and a snippet of `chunk_text`.
- [ ] `privacy_safe_answer_logs` row count is still 0 after every script in this milestone has run.
- [ ] No script in this milestone performs any database write — verified by inspecting the scripts and by the unchanged row counts on every table.
- [ ] `scripts/validate_retrieval_results.py` exits 0.

---

## 9. Later Phases

These follow once §8 is satisfied. Each is its own feature branch / PR:

1. **Backend retrieval service.** A small `backend/app/retrieval/` module that wraps the same embed-and-search logic the milestone scripts proved out, with proper dependency injection, connection pooling, and error handling.
2. **`/api/retrieve` endpoint.** A FastAPI route that accepts a synthetic test query, returns retrieved chunks (citation, official URL, snippet, scores), and does **not** generate an answer or store the question.
3. **`/api/chat/ask` retrieval-only skeleton.** The eventual chat endpoint, initially wired to return only citations and snippets — no LLM call yet — so the frontend can integrate against a stable contract before answer generation lands.
4. **Citation checker.** Verify every chunk surfaced by retrieval has a citation string; add a refusal path for out-of-scope queries that return no active chunks above a configured score threshold.
5. **Local LLM answer generation.** Pass retrieved active chunks to a local Ollama LLM (e.g. `llama3.1:8b`) as context; generate a plain-language answer with citations. Log metadata only (no raw Q&A text) to `privacy_safe_answer_logs`.
6. **Frontend integration.** Wire the React chat UI to `/api/chat/ask`, render citations and disclaimers, and surface attorney-referral CTAs for high-risk topics.

---

## 10. Open Questions

To resolve before or during the retrieval scripts PR:

- **What top-k should the MVP use?** Candidate values are 3, 5, and 10. Smaller k tightens precision and reduces LLM context cost later; larger k gives the eventual LLM more material to ground in but increases the chance of off-topic chunks. A starting value of `k = 5` is reasonable for the 5-chunk active dataset, but the value should be reconsidered once the dataset grows.
- **How should vector and keyword scores be weighted in hybrid retrieval?** Options include simple normalize-and-add, weighted sum (e.g. `0.6 * vector + 0.4 * keyword`), and reciprocal rank fusion. The chosen scheme should be inspectable in script output so a reviewer can see *why* a chunk ranked where it did.
- **Should retrieval filter by topic or risk level?** Filtering can improve precision (e.g. an asylum question should not surface naturalization chunks) but also risks suppressing genuinely relevant cross-topic results. Decide whether topic/risk filtering is a hard filter, a soft re-rank signal, or off by default for MVP.
- **Should high-risk topics trigger disclaimers before answer generation?** Even though this milestone does not generate answers, the retrieval layer should probably tag results whose `risk_level` is high so the later LLM phase can attach a stronger disclaimer or attorney-referral CTA without re-querying the database.
- **How much source text should be returned to the LLM later?** Full `chunk_text`, a fixed-length snippet, or the chunk plus its surrounding section heading? This is a context-budget and quality decision that the LLM-generation milestone will need to make, but the retrieval scripts in this milestone should expose enough fields (full text + snippet + section metadata) that either choice is supported without changing the retrieval contract.
