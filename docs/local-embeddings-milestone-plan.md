# Local Embeddings Milestone Plan

**Status:** Planning — no embedding code written yet
**Owner:** Backend track on `feature/backend-cloud-foundation`
**Scope:** Generate local vector embeddings for public eCFR `legal_chunks` using Ollama `nomic-embed-text` and store them in pgvector. This milestone does not include retrieval, answer generation, or any user-facing features.

Related docs:
- [`docs/ecfr-preview-to-db-mapping-plan.md`](./ecfr-preview-to-db-mapping-plan.md) — how eCFR data was mapped into the schema
- [`docs/ecfr-ingestion-milestone-plan.md`](./ecfr-ingestion-milestone-plan.md) — overall ingestion milestone
- [`database/migrations/001-initial-schema.sql`](../database/migrations/001-initial-schema.sql) — schema referenced below

---

## 1. Purpose

This milestone turns the already-inserted public `legal_chunks` into vector-searchable chunks by generating local embeddings for each chunk's `chunk_text` and storing the resulting vector in `legal_chunks.embedding`.

After this milestone, the five eCFR Title 8 sample chunks will each have a 768-dimensional embedding stored in pgvector, making them ready for the later vector-retrieval and hybrid-search milestones. The chunks remain inactive (`is_active = FALSE`) until a deliberate publish step is taken.

---

## 2. Scope

This milestone applies **only** to public legal-source data already inserted into `legal_chunks` by [`scripts/insert_ecfr_preview_to_db.py`](../scripts/insert_ecfr_preview_to_db.py).

**In scope:**
- Generating embeddings for `legal_chunks` rows where `embedding IS NULL`
- Storing the resulting `vector(768)` back into `legal_chunks.embedding`
- Verifying the stored dimension after write

**Out of scope:**
- Real user questions — this milestone embeds only public regulatory text
- Answer generation of any kind
- Activating the dataset or setting `is_active = TRUE`
- Any public AI API (OpenAI, Anthropic, Cohere, etc.)
- Chunk splitting or improving the text used for embedding (that is §8.2 of the ingestion plan)

---

## 3. Current Starting Point

Before this milestone runs, the database state is:

| Table | State |
| --- | --- |
| `legal_sections` | 5 rows for eCFR Title 8 MVP sections (`208.7`, `208.4`, `245.1`, `274a.12`, `239.1`) |
| `legal_chunks` | 5 rows, one per section, `chunk_index = 0` |
| `legal_chunks.embedding` | `NULL` on all 5 rows — pgvector slot is reserved but not yet filled |
| `legal_chunks.is_active` | `FALSE` on all 5 rows |
| `dataset_versions.status` | `ready` — inserted and verified, but not yet activated |

This means `search_legal_chunks(...)` returns no results because the HNSW index requires non-NULL embeddings and `is_active = FALSE` rows are excluded by the retrieval filter. That is the expected state at this point.

---

## 4. Embedding Model

| Property | Value |
| --- | --- |
| Runtime | Ollama (local, no network calls to any external AI service) |
| Model | `nomic-embed-text` |
| Output dimension | 768 |
| Schema column | `legal_chunks.embedding vector(768)` |

The `vector(768)` type in the schema was chosen to match `nomic-embed-text` exactly. The HNSW index `idx_legal_chunks_embedding` uses `vector_cosine_ops`, which is the correct operator class for cosine similarity with this model.

Ollama must be running locally before the embedding script is called:

```bash
ollama pull nomic-embed-text   # one-time download
ollama serve                   # keep running in a separate terminal
```

The embedding script will call Ollama over localhost only and will never send chunk text to any external service.

---

## 5. Tables Involved

### Read
| Table | Why |
| --- | --- |
| `dataset_versions` | Look up the target `dataset_version_id` for chunks to embed |
| `legal_chunks` | Select rows where `embedding IS NULL` and `dataset_version_id` matches |

### Write
| Table | Column | What is written |
| --- | --- | --- |
| `legal_chunks` | `embedding` | `vector(768)` returned by Ollama `nomic-embed-text` |

### Intentionally not written

| Table | Reason |
| --- | --- |
| `privacy_safe_answer_logs` | Retrieval-time metadata only; never written to by ingestion or embedding scripts |
| `admin_users` | Authentication table; never written to by any data pipeline script |
| `raw_documents` | Already inserted; embedding operates only on derived `chunk_text` |
| `legal_documents` | Already inserted; not modified by the embedding phase |
| `legal_sections` | Already inserted; `legal_sections` has no embedding column |
| Any user data table | No user data exists at this milestone |

---

## 6. Planned Scripts

Three scripts are planned for this milestone, following the same dry-run → real-run → validate pattern used for ingestion.

---

### `scripts/dry_run_embed_legal_chunks.py`

**Purpose:** Preview which chunks would be embedded without calling Ollama or writing to the database.

**Behavior:**
- Connect to PostgreSQL (read-only)
- Find all `legal_chunks` rows where `embedding IS NULL` for the target `dataset_version_id`
- Print chunk IDs, citations, `chunk_text` length, and the model name that would be used
- Print a compact JSON summary: chunk count, dataset version, model name
- Do **not** call Ollama
- Do **not** write to the database

**Exit codes:** 0 if chunks are found and the report printed cleanly; 1 if no chunks need embedding or on connection error.

---

### `scripts/embed_legal_chunks.py`

**Purpose:** Generate embeddings for all `legal_chunks` rows with `embedding IS NULL` and store them in PostgreSQL.

**Behavior:**
- Accept `--database-url`, `--ollama-url` (default `http://localhost:11434`), and `--dataset-version` (default: newest `ecfr-title8-sample-*`) CLI arguments
- Connect to PostgreSQL; select chunks where `embedding IS NULL` for the target dataset version
- For each chunk, POST `chunk_text` to the local Ollama embeddings endpoint
- Verify the returned vector has exactly 768 dimensions before writing
- UPDATE `legal_chunks SET embedding = %s WHERE id = %s` — one row at a time for the MVP
- Keep `is_active = FALSE` — do not activate the dataset
- Never send user questions or any private data to Ollama
- Print a per-chunk progress line and a final summary (IDs updated, any failures)

**Exit codes:** 0 if all NULL embeddings were filled; 1 if any chunk failed or dimension mismatch detected.

---

### `scripts/validate_legal_chunk_embeddings.py`

**Purpose:** Confirm the embedding phase completed correctly (read-only).

**Checks:**
- Expected 5 chunks have non-NULL `embedding` values
- Each stored vector has dimension 768 (via `vector_dims(embedding)`)
- `legal_chunks.is_active` remains `FALSE` on all 5 rows
- `dataset_versions.status` is `ready` (not yet `active`)
- `privacy_safe_answer_logs` row count is still 0

**Exit codes:** 0 on PASS; 1 on any FAIL.

---

## 7. Safety and Privacy Rules

- **Public text only.** Only public eCFR regulatory text from `legal_chunks.chunk_text` is sent to Ollama. No real user questions, no personal data, and no information from `privacy_safe_answer_logs` is embedded.
- **Local Ollama only.** All embedding calls go to `http://localhost:11434` (or a configurable local URL). Ollama must not be exposed to the internet.
- **No public AI APIs.** OpenAI, Anthropic, Cohere, and all other cloud AI APIs are prohibited for this milestone and for all ingestion-phase scripts in this project.
- **Minimal logging.** Scripts log chunk IDs and citation strings for observability. Full `chunk_text` is not printed to stdout unless in an explicit debug mode.
- **No side effects on user tables.** The embedding script touches only `legal_chunks.embedding`. It does not read or write `privacy_safe_answer_logs`, `admin_users`, or any future user-data tables.
- **Fail loudly on dimension mismatch.** If Ollama returns a vector with dimension ≠ 768, the script must reject it and exit non-zero rather than storing a malformed vector.

---

## 8. Success Criteria

This milestone is complete when **all** of the following are true:

- [ ] Dry-run script identifies exactly 5 eCFR chunks needing embeddings and exits 0.
- [ ] Real embed script updates all 5 chunks with non-NULL `embedding` values and exits 0.
- [ ] Every stored embedding has dimension 768 (confirmed by `vector_dims(embedding)`).
- [ ] `legal_chunks.is_active` remains `FALSE` on all 5 rows after the embed script runs.
- [ ] `dataset_versions.status` remains `ready` (not `active`) after the embed script runs.
- [ ] `privacy_safe_answer_logs` row count is still 0.
- [ ] Validation script (`validate_legal_chunk_embeddings.py`) exits 0 (PASS).
- [ ] `git status` shows no new tracked files under `data/`.

---

## 9. Later Phases

These follow once §8 is satisfied. Each is its own feature branch / PR:

1. **Controlled dataset activation** — a separate script or admin action that sets `legal_chunks.is_active = TRUE` and `dataset_versions.status = 'active'` for a chosen dataset version. Must not activate automatically.
2. **Vector retrieval test** — run `search_legal_chunks(embedding, query_text, 5)` against a small set of canned public-domain test queries; verify top-1 citation is correct.
3. **Hybrid retrieval test** — combine the pgvector cosine score with the `search_vector` full-text rank (already populated by the DB trigger); verify combined scoring outperforms either signal alone.
4. **Cited answer generation with local LLM** — pass retrieved chunks to a local Ollama LLM (e.g. `llama3`) as context; generate a plain-language answer with citations. Logging is confined to `privacy_safe_answer_logs` (metadata only — no raw Q&A text).
5. **Safety and citation checker** — verify generated answers always include source citations; add a refusal path for out-of-scope queries.

---

## 10. Open Questions

To resolve before or during the embedding PR:

- **Which Ollama endpoint to standardize on?** Ollama offers both `/api/embeddings` (older, single-input) and `/api/embed` (newer, supports batching). Pick one and document it so the insert script and any future tooling agree.
- **Batch vs. one-at-a-time for MVP?** Calling Ollama once per chunk is simpler but slower if the section count grows. For 5 chunks the difference is negligible; but should the script already accept a `--batch-size` argument to make batching easy to add later?
- **Full section text vs. current snippet?** The current `chunk_text` is the whitespace-normalized `text_snippet` (~1200 chars). Embedding a truncated snippet produces a different vector than embedding the full section. Should we block this milestone on first improving full-text extraction (ingestion plan §8.1), or proceed with snippets and re-embed later?
- **Embedding model versioning in `dataset_versions`?** If we change models (e.g. from `nomic-embed-text` to a future model), stored embeddings become incompatible. Should the `dataset_versions` row carry a `notes` field entry or a dedicated metadata column recording which embedding model was used?
