# eCFR Preview → Database Insert Mapping Plan

**Status:** Draft (planning only — no insertion code yet)
**Owner:** Backend track on `feature/backend-cloud-foundation` (handing off to a future ingestion PR)
**Scope:** How to load the validated JSON preview from `scripts/fetch_ecfr_title8_sample.py` into the existing database schema. This is a *mapping* document; it does not introduce SQL changes.

Related docs:
- [`docs/ecfr-ingestion-milestone-plan.md`](./ecfr-ingestion-milestone-plan.md) — overall ingestion milestone
- [`database/migrations/001-initial-schema.sql`](../database/migrations/001-initial-schema.sql) — the schema referenced below

---

## 1. Purpose

This document maps the validated eCFR Title 8 JSON preview into the existing database tables **before any insertion code is written**. It locks down which table receives which field, what gets hashed, what is left null on first pass, and how reruns stay idempotent. The goal is that the later "insert" PR is mechanical — every decision has already been made on paper.

It also makes explicit which tables are intentionally **not** touched by ingestion (the privacy-safe audit table and the admin-auth table).

---

## 2. Input file

The insertion script will consume the JSON preview produced by [`scripts/fetch_ecfr_title8_sample.py`](../scripts/fetch_ecfr_title8_sample.py):

```
data/ecfr_samples/title8_sample_preview_YYYY-MM-DD.json
```

Companion artifact (also referenced during insertion):

```
data/ecfr_samples/raw_title8_YYYY-MM-DD.xml
```

Both files are generated locally and live under `data/`, which is git-ignored by the root `.gitignore` (only `data/.gitkeep` is whitelisted). They must not be committed.

Before insertion, the script must pass [`scripts/validate_ecfr_title8_preview.py`](../scripts/validate_ecfr_title8_preview.py). The insertion script will refuse to run if validation fails.

---

## 3. Tables involved

| Table | Role during ingestion |
| --- | --- |
| `source_registry` | Look up existing seed row for `eCFR Title 8`. Read-only — no insert. |
| `dataset_versions` | Create (or reuse) a `building` → `ready` row that groups all chunks from this run. Never set to `active` automatically. |
| `ingestion_jobs` | One row per local ingestion run for observability. |
| `raw_documents` | Persist the raw Title 8 XML once per `content_hash`. |
| `legal_documents` | One document-level row pointing at the `raw_documents` row. |
| `legal_sections` | One row per parsed target section (5 for this first milestone). |
| `legal_chunks` | One chunk per section for now (`chunk_index = 0`), `embedding = NULL`, `is_active = FALSE`. |

**Explicitly NOT used by ingestion:**

- **`privacy_safe_answer_logs`** — that table is for privacy-safe Q&A metadata at retrieval time. It is **never** written to by ingestion code and must not be used as a sink for any data derived from this script.
- **`admin_users`** — this is a local developer script run from the CLI. It does not authenticate against `admin_users` and does not touch that table.

---

## 4. Mapping details

The JSON preview structure produced by the fetcher (per section) is:

```json
{
  "citation": "8 CFR § 208.7",
  "section_number": "208.7",
  "title": "Employment authorization.",
  "official_url": "https://www.ecfr.gov/current/title-8/section-208.7",
  "text_snippet": "...",
  "text_length": 12345,
  "source_date": "2026-05-12"
}
```

Plus a top-level `source_url` (the eCFR full-XML URL), `source_name = "eCFR Title 8"`, and `source_date`.

### 4.1 `source_registry`

| Action | Detail |
| --- | --- |
| Lookup | `SELECT id FROM source_registry WHERE source_name = 'eCFR Title 8'` |
| Insert? | **No.** The seed row was inserted by the initial migration. If the row is missing, the script fails with a clear error and exits non-zero. |

The resulting `source_registry.id` is used as the `source_id` foreign key on `raw_documents`.

### 4.2 `dataset_versions`

| Column | Value |
| --- | --- |
| `version_name` | `ecfr-title8-sample-{source_date}` (e.g., `ecfr-title8-sample-2026-05-12`) |
| `status` | Start as `'building'`; on successful insertion of all chunks, update to `'ready'` |
| `started_at` | `NOW()` at insertion start |
| `completed_at` | `NOW()` once `status = 'ready'` |
| `activated_at` | **NULL** for now |
| `notes` | `"First eCFR Title 8 sample (5 MVP sections) from scripts/fetch_ecfr_title8_sample.py"` |
| `created_by` | local username (e.g., `whoami`); used for traceability only |

`version_name` carries a `UNIQUE` constraint, so reruns for the same `source_date` will reuse the existing row instead of creating a duplicate.

**Do not** set `status = 'active'` automatically. Activation is a separate, deliberate step described in §8.

### 4.3 `ingestion_jobs`

One row per local ingestion run.

| Column | Value |
| --- | --- |
| `source_name` | `'eCFR Title 8'` |
| `status` | `'running'` at start; updated to `'success'` or `'failed'` |
| `triggered_by` | local username (or `'cli'`) |
| `started_at` | `NOW()` at start |
| `finished_at` | `NOW()` at end |
| `records_added` | total inserted across `raw_documents` + `legal_documents` + `legal_sections` + `legal_chunks` |
| `records_updated` | total rows updated (e.g., dataset_version status flip from `building` → `ready`) |
| `error_message` | NULL on success; on failure store a short, scrubbed message (no DSN, no stack trace) |
| `dataset_version_id` | the `dataset_versions.id` from §4.2 |

### 4.4 `raw_documents`

The full Title 8 XML is stored once per `content_hash`.

| Column | Value |
| --- | --- |
| `source_id` | `source_registry.id` from §4.1 |
| `external_id` | `'title-8-full'` (placeholder until we ingest at part/section granularity) |
| `title` | `'eCFR Title 8 — Aliens and Nationality (full XML)'` |
| `citation` | `'8 CFR Title 8'` |
| `official_url` | eCFR full-XML URL, e.g., `https://www.ecfr.gov/api/versioner/v1/full/{source_date}/title-8.xml` |
| `raw_format` | `'xml'` |
| `raw_content` | full XML text from `raw_title8_{source_date}.xml` |
| `content_hash` | `sha256(raw_content)` as hex |
| `fetched_at` | `NOW()` |
| `effective_date` | `source_date` (best available proxy; refined in §9) |
| `version_date` | `source_date` |

Idempotency: before insert, `SELECT id FROM raw_documents WHERE content_hash = $hash`. If a row exists, reuse it (do not insert a duplicate).

### 4.5 `legal_documents`

One row per Title 8 raw document for now.

| Column | Value |
| --- | --- |
| `raw_document_id` | `raw_documents.id` from §4.4 |
| `source_type` | `'regulation'` |
| `title` | `'eCFR Title 8 Sample'` |
| `citation` | `'8 CFR Title 8'` |
| `jurisdiction` | `'federal'` (note: the schema's default is `'United States'`; we use `'federal'` per this plan — the column accepts either) |
| `publisher` | `'eCFR'` |
| `official_url` | same eCFR full-XML URL as `raw_documents.official_url` |
| `effective_date` | `source_date` |
| `version_date` | `source_date` |

Idempotency: keyed on `(raw_document_id, source_type)` for now — if a `legal_documents` row already references the reused `raw_document_id`, reuse it instead of inserting again.

### 4.6 `legal_sections`

One row per parsed target section. For this first milestone, five rows.

| Column | Source |
| --- | --- |
| `document_id` | `legal_documents.id` from §4.5 |
| `section_number` | JSON `section_number` (e.g., `"208.7"`) |
| `section_title` | JSON `title` |
| `citation` | JSON `citation` (e.g., `"8 CFR § 208.7"`) |
| `official_text` | Full parsed section text (deferred — see §9). For this first milestone, may be `text_snippet` if full text is not yet extracted. |
| `cleaned_text` | Cleaned version of `official_text` (whitespace normalized). |
| `topic` | From the deterministic mapping in §5 |
| `subtopic` | From the deterministic mapping in §5 |
| `audience` | NULL for now |
| `official_url` | JSON `official_url` |
| `effective_date` | `source_date` |
| `version_date` | `source_date` |

Idempotency: keyed on `(document_id, section_number)`. If a row exists, update mutable fields (`section_title`, `cleaned_text`, etc.) instead of inserting a duplicate. A formal unique index is listed as an open question in §9.

### 4.7 `legal_chunks`

For the **first insert milestone**, one chunk per section (no splitting yet). The future chunking phase will add multiple chunks per section.

| Column | Source |
| --- | --- |
| `section_id` | `legal_sections.id` from §4.6 |
| `chunk_index` | `0` |
| `chunk_text` | `legal_sections.cleaned_text` (or `text_snippet` if full text isn't yet extracted) |
| `plain_language_summary` | NULL |
| `citation` | copied from `legal_sections.citation` |
| `topic` | copied from `legal_sections.topic` |
| `subtopic` | copied from `legal_sections.subtopic` |
| `risk_level` | from the deterministic mapping in §5 |
| `official_url` | copied from `legal_sections.official_url` |
| `embedding` | **NULL** for now (embeddings are a later phase) |
| `dataset_version_id` | `dataset_versions.id` from §4.2 |
| `is_active` | **FALSE** unless we explicitly publish the dataset later |

Idempotency: keyed on `(section_id, chunk_index, dataset_version_id)`. Reruns for the same section/dataset version update the existing row in place.

---

## 5. Deterministic topic mapping (first MVP sample)

The five target sections are mapped by hand for this first milestone so the inserts are reproducible and we don't depend on any AI classifier:

| section_number | topic | subtopic | risk_level |
| --- | --- | --- | --- |
| `208.7` | `asylum` | `employment_authorization` | `medium` |
| `208.4` | `asylum` | `filing_deadline` | `high` |
| `245.1` | `adjustment_of_status` | `eligibility` | `medium` |
| `274a.12` | `employment_authorization` | `categories` | `medium` |
| `239.1` | `removal_proceedings` | `notice_to_appear` | `high` |

All five `risk_level` values use only the lower three buckets (`medium` / `high`). `critical` is reserved for sections that warrant an immediate attorney-referral flag in answer generation and will be assigned in a later, reviewed pass.

---

## 6. Insert rules

> **First local insert script exists.** [`scripts/insert_ecfr_preview_to_db.py`](../scripts/insert_ecfr_preview_to_db.py)
> is the first real ingestion script. It reads the validated preview JSON and companion
> raw XML, inserts all rows in one transaction, and prints a per-table inserted/reused
> summary. Run it with `uv run --project backend python scripts/insert_ecfr_preview_to_db.py`.

> **Dry-run available.** Before running the real insertion script, use
> [`scripts/dry_run_insert_ecfr_preview.py`](../scripts/dry_run_insert_ecfr_preview.py)
> to simulate all planned inserts without writing to PostgreSQL. The dry-run
> script reads the same preview JSON, resolves the companion raw XML, computes
> its SHA-256, applies the §5 topic mapping, and prints a human-readable report
> plus a compact JSON summary — exit 0 on success, exit 1 on missing/invalid input.

The future insertion script (likely `scripts/insert_ecfr_title8_sample.py`) must:

- **Validate first.** Run `scripts/validate_ecfr_title8_preview.py` on the target preview file before opening any DB transaction. Refuse to insert if validation fails.
- **Fail safely on missing schema.** Before any insert, confirm every table in §3 exists (equivalent to the `/health/schema` probe). If any table is missing, exit non-zero with a clear, credential-free message.
- **No duplicate rows on rerun.** Each table has an idempotency key documented in §4 (`content_hash` for raw_documents; `(raw_document_id, source_type)` for legal_documents; `(document_id, section_number)` for legal_sections; `(section_id, chunk_index, dataset_version_id)` for legal_chunks; `version_name` for dataset_versions).
- **Use `content_hash` for raw XML.** Compute SHA-256 of the raw XML bytes; if a `raw_documents` row already has that hash, reuse it rather than inserting again. This makes daily reruns cheap.
- **Do NOT mark the dataset active automatically.** The dataset stays at `building` → `ready`. Activation is a deliberate later step (§8).
- **Do NOT store user questions, full answers, or any personal data.** This script ingests public legal-source content only.
- **Do NOT write to `privacy_safe_answer_logs`.** That table is for retrieval-time metadata only.
- **Wrap inserts in a transaction.** A partial failure should not leave half-ingested rows. `ingestion_jobs.status = 'failed'` should be recorded in a separate, committed transaction so the failure is auditable.
- **Log only privacy-safe operational info to stdout.** Counts, IDs, and durations are fine. Section text, raw XML, DSNs, and stack traces are not.

---

## 7. Success criteria

The insertion milestone is done when **all** of the following are true:

- [ ] `source_registry` row for `eCFR Title 8` is found (not re-inserted).
- [ ] `dataset_versions` row `ecfr-title8-sample-{source_date}` is created (or reused) and ends at `status = 'ready'`.
- [ ] One `ingestion_jobs` row exists for the run with `status = 'success'` and a non-NULL `dataset_version_id`.
- [ ] Exactly one `raw_documents` row exists for the run's `content_hash`.
- [ ] Exactly one `legal_documents` row exists pointing at that `raw_documents` row.
- [ ] Exactly five `legal_sections` rows exist for the five target sections in §5.
- [ ] Exactly five `legal_chunks` rows exist with `chunk_index = 0`, `embedding IS NULL`, `is_active = FALSE`, and `dataset_version_id` pointing at the §4.2 row.
- [ ] Rerunning the script against the same preview produces zero new rows (idempotent).
- [ ] `GET /health/schema` continues to report `"status": "ok"` after ingestion (no schema regressions).
- [ ] `git status` shows no new tracked files under `data/`.

---

## 8. Later phases

These follow once §7 is satisfied. Each is its own feature branch / PR:

1. **Improve full section text extraction** so `legal_sections.official_text` / `cleaned_text` contain the entire section, not just the 1200-char snippet from the preview.
2. **Add chunk splitting** (≈ 500–1000 token chunks with 50–100 token overlap), populating multiple `legal_chunks` rows per section. `chunk_index` will then matter.
3. **Add local embeddings** via Ollama (`nomic-embed-text`, 768 dims) and backfill `legal_chunks.embedding`. First time Ollama is required.
4. **Set the dataset `active` through a controlled publish step** (separate script / admin action), flipping `legal_chunks.is_active = TRUE` and `dataset_versions.status = 'active' / activated_at = NOW()` only for the chosen dataset.
5. **Add retrieval tests** using `search_legal_chunks(...)` against a small set of canned MVP questions.
6. **Add citation-based answer generation later**, with logging confined to `privacy_safe_answer_logs` (metadata only, never raw Q&A text).

---

## 9. Open questions

To resolve before / during the insertion PR:

- **Granularity of `raw_documents`.** Should `raw_documents` store the full Title 8 XML once, or one row per CFR part (208, 245, 274a, 239)? Single full XML is simpler and matches the current preview; per-part rows make change detection finer-grained.
- **Granularity of `legal_documents`.** One `legal_documents` row for "Title 8" total, or one per CFR part? This affects how we compute `effective_date` and how a UI surface groups citations.
- **`legal_chunks` source text.** Use the 1200-char `text_snippet` now (fast, lossy) or block on §8.1 (full-text extraction) before doing any chunk inserts at all?
- **Effective dates and amendments.** eCFR sections each have their own amendment history. Should `effective_date` / `version_date` come from per-section eCFR metadata (when available) instead of the title-level snapshot date?
- **Uniqueness constraints.** The migration does not enforce uniqueness on `(legal_documents.raw_document_id, source_type)`, `(legal_sections.document_id, section_number)`, or `(legal_chunks.section_id, chunk_index, dataset_version_id)`. Idempotency in this plan is enforced in application code. Should a follow-up migration add real unique indexes on those keys?
- **`jurisdiction` value.** The schema default is `'United States'`, while this plan proposes `'federal'`. Pick one and use it consistently across seeds and inserts so later filters work as expected.
- **`audience` field.** Defaulting to NULL for now. Do we want to populate it (`'general'` / `'attorney'` / `'student'`) during ingestion, or assign it later?
