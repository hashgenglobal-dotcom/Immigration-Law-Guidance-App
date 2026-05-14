# eCFR Title 8 Ingestion — First Milestone Plan

**Status:** Draft — first script implemented as [`scripts/fetch_ecfr_title8_sample.py`](../scripts/fetch_ecfr_title8_sample.py); when `--date` is not provided, the script now auto-detects Title 8's latest available eCFR issue date via the [titles metadata endpoint](https://www.ecfr.gov/api/versioner/v1/titles). A JSON-preview validator has also been added at [`scripts/validate_ecfr_title8_preview.py`](../scripts/validate_ecfr_title8_preview.py) to sanity-check the generated preview before any database insertion is implemented. Database / chunking / embeddings phases still pending.
**Owner:** Backend track on `feature/backend-cloud-foundation` (handing off to a future `feature/ecfr-ingestion`)
**Scope:** Smallest possible, testable slice of eCFR Title 8 ingestion. Not the full pipeline.

---

## 1. Goal

Fetch a **small public sample** of eCFR Title 8 (Aliens and Nationality), parse a handful of section-level records, and produce a JSON preview that can be inspected by hand. The output of this milestone is a verified parser and a saved local sample — **not** a populated database.

This milestone is intentionally separable from the full ingestion pipeline. We want to be confident that:

- We can reach the official eCFR endpoint.
- We can extract `citation`, `title`, `official_url`, and a clean `text` snippet for at least one real section.
- The parsed shape matches what `legal_documents` / `legal_sections` / `legal_chunks` in `database/migrations/001-initial-schema.sql` expect, **before** we wire up any database writes.

---

## 2. Why eCFR first

- **Directly relevant.** eCFR Title 8 is the federal regulation source for nearly every MVP question (asylum work authorization, asylum filing deadline, adjustment of status, employment authorization classes, Notice to Appear, etc.). See `docs/01-mvp-questions-source-mapping.md`.
- **Public legal-source data.** Published by the U.S. Government Publishing Office. No copyright or licensing concerns, and nothing in it is user data. It is the canonical example of "safe to commit / safe to share."
- **Structured.** eCFR exposes both bulk XML and per-section endpoints, with stable hierarchy (title → chapter → part → section). That is far easier to parse reliably than scraping arbitrary policy pages.
- **Good fit for our schema.** eCFR maps cleanly onto the existing tables we will eventually write to: `source_registry` (already seeded with `eCFR Title 8`), `raw_documents` (the fetched XML), `legal_documents` (the parsed document-level record), `legal_sections` (per-section text), and later `legal_chunks` (retrieval-ready chunks with embeddings).

Starting with eCFR de-risks the whole ingestion design before we attempt harder sources (USCIS Policy Manual scraping, BIA decisions, etc.).

---

## 3. Milestone boundary — what this milestone does and does NOT do

**This milestone WILL:**

- Fetch a small eCFR Title 8 sample from an official public endpoint.
- Save the raw source response to a local, git-ignored folder for inspection.
- Parse basic metadata (title, citation, official URL, effective/version date if available).
- Extract section-level `citation`, `section_title`, and `text` for a small number of target sections.
- Write a JSON preview file describing the parsed sample.

**This milestone will NOT:**

- Build the full ingestion pipeline.
- Write to PostgreSQL (no inserts into `raw_documents`, `legal_documents`, `legal_sections`, `legal_chunks`, `ingestion_jobs`, or `dataset_versions`).
- Chunk the text for retrieval.
- Generate embeddings (no Ollama, no `nomic-embed-text`).
- Generate or store any answer text.
- Call any LLM, local or remote.

If a future PR starts doing any of the "will not" items in this same milestone, that PR is too large and should be split.

---

## 4. First target sections

These five sections cover a high fraction of MVP questions and exercise different shapes of regulatory text (definitional, deadline-driven, list-of-classes, procedural):

| Citation | Subject | Why it matters for MVP |
| --- | --- | --- |
| **8 CFR § 208.7** | Employment authorization for asylum applicants | Q1: "Can I work while my asylum case is pending?" |
| **8 CFR § 208.4** | Asylum filing deadlines and exceptions | Q3: "Can I apply for asylum after one year?" |
| **8 CFR § 245.1** | Adjustment of status eligibility | Q4: "What is adjustment of status?" |
| **8 CFR § 274a.12** | Employment authorization classes | Q11: "What is a work permit?" |
| **8 CFR § 239.1** | Notice to Appear (initiation of removal proceedings) | Q8: "What happens if I receive a Notice to Appear?" |

If the parser handles these five reliably, it is very likely to handle the rest of Title 8 Chapter I with minimal changes.

---

## 5. Expected script later

A future PR will add (this milestone does **not** create it yet):

```
scripts/fetch_ecfr_title8_sample.py
```

Expected behavior of that script:

- Use **only official public eCFR / GovInfo source URLs** (e.g., `https://www.ecfr.gov/api/...` and/or the bulk Title 8 XML download). No third-party mirrors, no scrapers of unofficial copies.
- Use `httpx` (already a backend dependency) or `requests`. Synchronous is fine — this is an offline data-prep script, not part of the request path.
- Save the raw XML/JSON response to a **git-ignored** local folder, e.g. `data/ecfr/raw/title8/<date>/`. The root `.gitignore` already ignores `data/*` except for `data/.gitkeep`, so no accidental commits.
- Parse only the small sample described in §4. Do not attempt to ingest the full title in this milestone.
- Write a JSON preview file (e.g., `data/ecfr/preview/title8-sample.json`) with one record per target section containing:
  - `citation`
  - `section_number`
  - `section_title`
  - `official_url`
  - `effective_date` (if available)
  - `version_date` (if available)
  - `text_snippet` (first ~500 chars — for human inspection only; full text stays in the raw file)
  - `source_name` (always `"eCFR Title 8"`, matching the seed in `source_registry`)
- Be **idempotent and re-runnable**. Running it twice should produce the same files (modulo the date in the folder name).
- Print a short summary to stdout: how many sections were targeted, how many parsed successfully, where the raw file and the preview file were written.
- **Do not call any LLM**, local or remote.
- **Do not generate embeddings.**
- **Do not write to PostgreSQL** — no `psycopg` connection at all in this script.

The script's only purpose is: "show me what eCFR Title 8 actually looks like once parsed, on disk, in a form the database schema will accept later."

---

## 6. Privacy rules

eCFR ingestion is the easiest part of the system from a privacy standpoint, because none of it touches user data:

- **eCFR data is public legal-source data and is safe to ingest and (eventually) commit** via seed scripts and migrations.
- **No real user questions are used** anywhere in this milestone — there is no `/chat` endpoint involved, and the script does not take a user query as input.
- **No private immigration facts are processed.** The only inputs are official regulation URLs.
- **No public AI API is called.** No OpenAI / Anthropic / etc.
- **Local LLM / Ollama is not needed for this milestone.** Ollama only becomes relevant in a later phase, when we chunk + embed. This milestone is purely fetch + parse + preview.
- The eventual database writes (later phase) go into `raw_documents`, `legal_documents`, `legal_sections`, `legal_chunks`, `ingestion_jobs`, and `dataset_versions` — never into `privacy_safe_answer_logs` and never into any user-facing logging table.

---

## 7. Success criteria

The milestone is done when **all** of the following are true:

- [ ] Fetch succeeds from the official eCFR endpoint (HTTP 200, expected content type, non-empty body).
- [ ] Raw response is saved locally under `data/ecfr/raw/...` and is **not committed** (verified by `git status`).
- [ ] JSON preview file is produced, containing at minimum: `citation`, `section_title`, `official_url`, and a `text_snippet`.
- [ ] At least one target section from §4 is parsed cleanly — `citation` and `section_title` are correctly extracted and `text_snippet` is human-readable text (no XML tags, no boilerplate header).
- [ ] No private data is created, written, or committed. The diff for the PR that adds the script should contain code only, plus `data/.gitkeep` if it doesn't already exist — never raw downloads.
- [ ] The script can be re-run safely (idempotent — re-running does not corrupt prior runs or require manual cleanup).
- [ ] `git status` after a clean run shows no new tracked files under `data/`.

---

## 8. Later phases (NOT part of this milestone)

These follow once §7 is satisfied. Each is its own feature branch / PR:

1. **Database insertion.** Persist the parsed sample into `raw_documents` → `legal_documents` → `legal_sections`, gated behind an `ingestion_jobs` row.
2. **Chunking.** Break section text into ~500–1000 token chunks with 50–100 token overlap, populate `legal_chunks` (no embeddings yet).
3. **Local embeddings.** Generate 768-dim embeddings via Ollama `nomic-embed-text` and backfill `legal_chunks.embedding`. First time Ollama is required.
4. **Retrieval tests.** Use `search_legal_chunks(...)` (already defined in the migration) against a small set of canned MVP questions to validate hybrid search quality.
5. **Citation-based answer generation.** Wire a local LLM (Ollama `llama3.1:8b` first) to produce answers strictly from retrieved chunks, with citations. Logging into `privacy_safe_answer_logs` — metadata only, no raw Q&A text.
6. **Activate first `dataset_versions` row** with `status = 'active'` so the retrieval endpoint can rely on it.

Each later phase is gated by its own privacy review.

---

## 9. Open questions

To resolve before / during the script PR:

- **Endpoint choice:** What is the best official endpoint for section-level fetch — `https://www.ecfr.gov/api/versioner/v1/full/<date>/title-8.xml` (full title, large), the `structure` endpoint, the per-section content endpoint, or the GovInfo bulk download? Tradeoff: one-big-XML is simpler to cache but heavier per run.
- **Parse strategy:** Do we parse the full title XML once and slice out target sections, or hit a per-section endpoint per target? Probably full XML once (cheaper, more deterministic), but worth confirming the response size and rate limits.
- **Versioning:** How do we track `effective_date` and `version_date` per section reliably? eCFR is amended frequently and our schema (`legal_documents`, `legal_sections`, `legal_chunks`) carries both `effective_date` and `version_date` columns — we need to decide which eCFR field maps to which.
- **Updates / changed sections:** When a section text changes upstream, how do we detect it (content hash on `raw_documents.content_hash` works for the raw payload, but section-level diffs need a strategy), and how do we tie that to a new `dataset_versions` row instead of mutating existing chunks?
- **Hierarchy depth:** Do we ingest section-level only (e.g., `§ 208.7`) or also subsection-level (`§ 208.7(a)(1)(ii)`)? The schema's `legal_sections.section_number` supports both, but chunking strategy and citation display change depending on the answer.
- **Rate limiting / etiquette:** What rate limits does ecfr.gov publish, and should we add a polite `User-Agent` header identifying the project?
