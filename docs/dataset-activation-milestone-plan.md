# Dataset Activation Milestone Plan

**Status:** Planning — no activation code written yet
**Owner:** Backend track on `feature/backend-cloud-foundation`
**Scope:** Transition the embedded eCFR Title 8 sample dataset from `ready` to `active`, making its chunks visible to the retrieval layer. This milestone does not include retrieval, answer generation, or any user-facing features.

Related docs:
- [`docs/local-embeddings-milestone-plan.md`](./local-embeddings-milestone-plan.md) — how embeddings were generated for the chunks
- [`docs/ecfr-ingestion-milestone-plan.md`](./ecfr-ingestion-milestone-plan.md) — overall ingestion milestone
- [`database/migrations/001-initial-schema.sql`](../database/migrations/001-initial-schema.sql) — schema referenced below

---

## 1. Purpose

After public eCFR legal chunks are inserted and embedded, they intentionally remain inactive (`is_active = FALSE`, `dataset_versions.status = 'ready'`). This is by design: a dataset that has been built and embedded but not yet reviewed or activated cannot be reached by the retrieval layer. No query can return results from it, and no answer can be generated from it.

This milestone defines the controlled step that promotes a `ready` dataset to `active`. Until this step is run deliberately, the chunks exist in the database but are invisible to retrieval — even if the embedding is present and correct.

---

## 2. Current State

Before this milestone runs, the database state is:

| Table | Column | State |
| --- | --- | --- |
| `dataset_versions` | `version_name` | `ecfr-title8-sample-2026-05-12` |
| `dataset_versions` | `status` | `ready` |
| `dataset_versions` | `activated_at` | `NULL` |
| `legal_chunks` | `embedding` | `vector(768)` — populated by `embed_legal_chunks.py` |
| `legal_chunks` | `is_active` | `FALSE` on all 5 rows |
| `privacy_safe_answer_logs` | (all) | 0 rows |

This means `search_legal_chunks(...)` returns no results because the retrieval filter requires `is_active = TRUE`. That is the expected and correct state before activation.

---

## 3. Why Activation Is Separate

Keeping activation as a distinct step — separate from ingestion and embedding — provides several guarantees:

**Prevents unreviewed data from reaching retrieval.** A dataset that is half-built, partially embedded, or has not been manually inspected cannot be served to users. Ingestion and embedding may succeed technically while still producing low-quality chunks; the activation step is the checkpoint where a human (or a gated admin workflow) decides the data is ready to serve.

**Supports an admin review workflow.** In a future release, the admin dashboard can show `ready` datasets alongside their chunk counts, citation coverage, and embedding completeness before offering an "Activate" button. This plan keeps the activation path clean enough for that workflow to be added without re-architecting the pipeline.

**Keeps pipeline stages independent.** Ingestion, embedding, and activation are three separate scripts with separate success criteria. A failure at activation does not corrupt the embedding work; re-running activation after fixing the issue is safe.

**Makes rollback straightforward.** If an activated dataset is found to be incorrect, it can be deactivated (set back to `ready` or `archived`) and a prior or corrected dataset can be activated in its place — without re-ingesting or re-embedding.

---

## 4. Tables Involved

### Read

| Table | Why |
| --- | --- |
| `dataset_versions` | Look up target dataset by `version_name`; verify `status = 'ready'` before activating |
| `legal_chunks` | Verify all chunks have non-NULL `embedding` and `vector_dims(embedding) = 768` |
| `privacy_safe_answer_logs` | Safety invariant check — count must be 0 before and after |

### Write (activation scripts only — not in dry-run or validation)

| Table | Column | What is written |
| --- | --- | --- |
| `dataset_versions` | `status` | `'active'` on the target; prior active dataset set to `'archived'` |
| `dataset_versions` | `activated_at` | `NOW()` on the target row |
| `legal_chunks` | `is_active` | `TRUE` on all chunks belonging to the target dataset version |

### Intentionally not written

| Table | Reason |
| --- | --- |
| `raw_documents` | Already inserted during ingestion; activation does not touch source data |
| `legal_documents` | Already inserted during ingestion; activation does not touch source data |
| `legal_sections` | Already inserted during ingestion; activation does not touch source data |
| `privacy_safe_answer_logs` | Retrieval-time metadata only; never written to by pipeline or activation scripts |
| `admin_users` | Authentication table; never written to by any data pipeline script |

---

## 5. Activation Rules

These rules must all be satisfied before activation proceeds. The activation script must enforce them in order and abort (rollback) if any check fails.

1. **Exactly one target dataset.** The `--dataset-version-name` argument (or the auto-detected newest `ready` dataset) must resolve to exactly one `dataset_versions` row.

2. **Target status must be `ready`.** A dataset with `status = 'building'`, `'active'`, or `'archived'` must not be activated by this script. Attempting to activate an already-active dataset is a no-op error.

3. **All target chunks must have non-NULL embeddings.** If any chunk in the target dataset has `embedding IS NULL`, the script must refuse and exit non-zero. Run `embed_legal_chunks.py` first.

4. **All target chunk embeddings must be 768-dimensional.** The script verifies `vector_dims(embedding) = 768` for every chunk before committing. A dimension mismatch causes a rollback.

5. **`privacy_safe_answer_logs` must be 0 at this milestone.** The count is checked as a safety invariant before activation proceeds.

6. **At most one active dataset at a time.** Before setting the target to `active`, any currently-active dataset version is set to `archived`. This is done in the same transaction so there is never a window where zero or two datasets are active simultaneously.

7. **One transaction.** All writes — deactivating the old dataset, writing `activated_at`, promoting the target, and flipping `is_active` on chunks — happen in a single PostgreSQL transaction. Any failure rolls back the entire operation.

8. **No embedding generation.** The activation script does not call Ollama or any external AI service. It only reads existing embeddings to verify them.

9. **No user data.** The activation script reads and writes only public legal-source tables. It does not read or write `privacy_safe_answer_logs` beyond the row-count safety check.

---

## 6. Planned Scripts

Three scripts are planned for this milestone, following the same dry-run → real-run → validate pattern used for ingestion and embedding.

---

### `scripts/dry_run_activate_dataset.py`

**Purpose:** Preview what activation would do without writing to the database.

**Behavior:**
- Connect to PostgreSQL (read-only)
- Resolve the target dataset version (CLI arg or newest `ready` ecfr-title8-sample-*)
- Verify target status is `ready`
- Count target chunks; verify all have non-NULL embeddings and dimension 768
- Identify any currently-active dataset that would be archived
- Print a clear dry-run report: target dataset, chunks that would become active, dataset that would be archived
- Print a compact JSON summary
- Do **not** write to any table

**Exit codes:** 0 if dry-run completes and preconditions are satisfied; 1 if any precondition fails or connection error.

---

### `scripts/activate_dataset.py`

**Purpose:** Transactionally activate the target dataset and its chunks.

**Behavior:**
- Accept `--database-url`, `--dataset-version-name` CLI arguments
- Connect to PostgreSQL
- Verify all preconditions (§5) inside the transaction
- In one transaction:
  - Set any currently-active `dataset_versions.status` to `'archived'`
  - Set target `dataset_versions.status = 'active'`
  - Set target `dataset_versions.activated_at = NOW()`
  - Set `legal_chunks.is_active = TRUE` for all chunks in the target dataset
- Keep `privacy_safe_answer_logs` untouched
- Print a per-step progress report and a final summary
- On any precondition failure or DB error: rollback and exit non-zero

**Exit codes:** 0 if activation committed successfully; 1 if any precondition failed, rollback occurred, or connection error.

---

### `scripts/validate_active_dataset.py`

**Purpose:** Confirm the activation completed correctly (read-only).

**Checks:**
- Exactly one `dataset_versions` row has `status = 'active'`
- That active dataset is the expected one
- `activated_at` is non-NULL on the active dataset
- All expected citations have `is_active = TRUE` in `legal_chunks`
- All active chunks have non-NULL embeddings with dimension 768
- No other dataset's chunks have `is_active = TRUE`
- `privacy_safe_answer_logs` count is still 0

**Exit codes:** 0 on PASS; 1 on any FAIL.

---

## 7. Safety and Privacy Rules

- **Public data only.** Activation operates entirely on public eCFR regulatory data already stored in `dataset_versions` and `legal_chunks`. No user questions, no personal data, and no information from `privacy_safe_answer_logs` is read or modified.
- **No LLM calls.** The activation script does not call Ollama or any language model. It only reads existing embedding vectors to verify their dimension.
- **No embedding generation.** Embeddings must already exist in `legal_chunks.embedding` before activation is attempted. If any are missing, the script aborts.
- **No public AI APIs.** OpenAI, Anthropic, Cohere, and all other cloud AI APIs are prohibited for this milestone and for all pipeline scripts in this project.
- **No answer logs written.** The activation pipeline never writes to `privacy_safe_answer_logs`. That table is written only at answer-generation time, which is a later milestone.
- **Fail loudly on precondition violations.** Missing embeddings, wrong dimensions, wrong dataset status, or any unexpected state causes an immediate rollback and non-zero exit rather than a silent partial activation.

---

## 8. Success Criteria

This milestone is complete when **all** of the following are true:

- [ ] Dry-run script identifies the target dataset, its 5 chunks, and any dataset that would be archived, then exits 0.
- [ ] Activation script commits successfully and exits 0.
- [ ] `dataset_versions.status = 'active'` on the target row.
- [ ] `dataset_versions.activated_at` is non-NULL on the target row.
- [ ] `legal_chunks.is_active = TRUE` on all 5 target chunks.
- [ ] No other `legal_chunks` rows have `is_active = TRUE`.
- [ ] All 5 active chunks have non-NULL `embedding` with `vector_dims(embedding) = 768`.
- [ ] `privacy_safe_answer_logs` count is still 0.
- [ ] Validation script (`validate_active_dataset.py`) exits 0 (PASS).

---

## 9. Later Phases

These follow once §8 is satisfied. Each is its own feature branch / PR:

1. **Vector retrieval test** — run `search_legal_chunks(embedding, query_text, 5)` against a small set of canned public-domain test queries against the now-active chunks; verify top-1 citation is correct.
2. **Hybrid retrieval test** — combine the pgvector cosine score with the `search_vector` full-text rank (auto-populated by the DB trigger); verify combined scoring outperforms either signal alone.
3. **`POST /api/chat/ask` retrieval-only skeleton** — implement the FastAPI endpoint that accepts a question, retrieves active chunks, and returns citations — without LLM generation yet.
4. **Citation checker** — verify retrieved chunks always surface a citation string; add a refusal path for out-of-scope queries that return no active chunks above a score threshold.
5. **Local LLM answer generation** — pass retrieved active chunks to a local Ollama LLM (e.g. `llama3.1:8b`) as context; generate a plain-language answer with citations. Log metadata only (no raw Q&A text) to `privacy_safe_answer_logs`.
6. **Admin dashboard publish workflow** — build a React admin interface that shows `ready` datasets with their chunk and embedding counts and offers a one-click activation path backed by `activate_dataset.py`.

---

## 10. Open Questions

To resolve before or during the activation PR:

- **Archiving vs. reverting old active datasets.** When a new dataset is activated, should the previously-active one become `'archived'` (permanent, reviewable history) or `'ready'` (re-activatable without re-ingestion)? `'archived'` is safer and avoids accidental re-activation; `'ready'` is more flexible for rollback. Pick one and enforce it in the schema or activation script.

- **Human approval flag.** Should `activate_dataset.py` accept a `--confirm` flag (or require the user to type the dataset version name) to prevent accidental activation from scripts or CI? A lightweight guard here could prevent costly mistakes before the admin dashboard exists.

- **Database constraint for one active dataset.** Currently, nothing in the schema prevents two `dataset_versions` rows from having `status = 'active'` simultaneously. A partial unique index (`WHERE status = 'active'`) on `dataset_versions` would make the one-active-at-a-time rule enforceable at the database level rather than only in application code.

- **Rollback mechanism.** If an activated dataset is found to produce incorrect answers, what is the supported rollback path? Options: (a) run a deactivate script that sets the active dataset back to `'ready'` and flips `is_active = FALSE` on its chunks; (b) activate a prior dataset version if one exists. The rollback script should be planned alongside the activation script, not added as an afterthought.
