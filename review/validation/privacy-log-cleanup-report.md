# Privacy Log Cleanup Report

**Branch:** `fix/privacy-log-cleanup`  
**Date:** May 20, 2026  
**Scope:** Inspect and clear `privacy_safe_answer_logs` before MVP demo

---

## Executive summary

The table stores **metadata only** (SHA-256 hashes, chunk IDs, citations JSON, model/latency fields). It has **no columns** for raw user questions or generated answers. **27 dev/test rows** from May 15–16, 2026 were truncated. The table is **empty** (0 rows). Current `POST /api/chat` does **not** write to this table.

---

## Schema inspection

| Column | Type | Purpose |
|--------|------|---------|
| `id` | uuid | Row primary key |
| `request_id` | uuid | Per-request correlation id |
| `question_hash` | varchar | SHA-256 of normalized question (64 hex chars) |
| `answer_hash` | varchar | SHA-256 of generated answer (64 hex chars) |
| `retrieved_chunk_ids` | integer[] | Chunk IDs used for grounding |
| `citations_used` | jsonb | Citation metadata (not full chunk text) |
| `dataset_version_id` | integer | Active dataset at answer time |
| `risk_level` | varchar | Optional risk label |
| `user_language` | varchar | e.g. `en` |
| `refusal_triggered` | boolean | Safety refusal flag |
| `safety_flags` | jsonb | Structured safety metadata |
| `model_name` | varchar | Chat model (e.g. `llama3.2`) |
| `embedding_model` | varchar | e.g. `nomic-embed-text` |
| `latency_ms` | integer | End-to-end latency |
| `created_at` | timestamptz | Insert time |

**Not present:** `question_text`, `answer_text`, `raw_question`, `raw_answer`, or any free-text Q&A fields.

Legacy `answer_logs` (full-text design) **does not exist** in this database.

---

## What was stored (before cleanup)

| Data type | Stored? | Evidence |
|-----------|---------|----------|
| Raw user question | **No** | No text column; only `question_hash` (64-char hex on all 27 rows) |
| Raw generated answer | **No** | No text column; only `answer_hash` (64-char hex on all 27 rows) |
| Query hash | **Yes** | `question_hash` |
| Answer hash | **Yes** | `answer_hash` |
| Metadata | **Yes** | chunk IDs, citations JSON, model names, latency, flags |
| Timestamps | **Yes** | `created_at` between 2026-05-15 and 2026-05-16 (dev window) |

**Row count before cleanup:** 27  
**Origin:** Dev chat/answer logging from an earlier prototype path (`llama3.2` + `nomic-embed-text`). Not production user data. No raw text was ever persisted in this table’s schema.

---

## Backend logging behavior (current)

| Component | Writes to `privacy_safe_answer_logs`? |
|-----------|--------------------------------------|
| `POST /api/chat` (`chat_service.py`, `chat.py`) | **No** |
| `POST /api/retrieve` | **No** |
| Ingestion / embedding scripts | **No** (excluded explicitly) |
| `STORE_USER_QUESTIONS` config flag | Defined, default `False`, **unused** in code |

MVP demo policy: table may stay at **0 rows** until a future milestone adds **hash-only** logging. No logging code changes were required for this cleanup because the schema and current chat path already avoid raw text.

---

## Cleanup performed

```bash
# Inspect (no writes, no sensitive text printed)
uv run --project backend python review/scripts/clear_privacy_safe_answer_logs.py --inspect

# Clear all dev rows
uv run --project backend python review/scripts/clear_privacy_safe_answer_logs.py --execute
```

**Result:** `TRUNCATE` removed 27 rows; post-check `row_count = 0`.

The script refuses to run `--execute` if forbidden raw-text column names appear in the schema.

---

## Post-cleanup verification

| Check | Result |
|-------|--------|
| `privacy_safe_answer_logs` row count | **0** |
| Raw text columns | **None** |
| `POST /api/retrieve` | **OK** (hybrid results returned) |
| `POST /api/chat` | **OK** when `OLLAMA_CHAT_MODEL` matches an installed model (e.g. `llama3.2:latest`); default `llama3.1:8b` may 503 if not installed — unrelated to log cleanup |

---

## Privacy behavior for MVP

1. **Never store** raw user messages or full generated answers in Postgres.
2. **If logging is added later**, only: `question_hash`, `answer_hash`, retrieval metadata, model/latency, safety flags — same columns as today’s schema.
3. **`STORE_USER_QUESTIONS`** must remain off unless explicitly reviewed; even when on, application code must not persist raw text (config documents intent only).
4. **Pre-demo:** run `clear_privacy_safe_answer_logs.py --inspect` and confirm `row_count = 0`.

---

## Acceptance checklist

| Criterion | Status |
|-----------|--------|
| No raw questions stored | Pass (schema + inspection) |
| No raw answers stored | Pass (schema + inspection) |
| Dev/test rows cleared | Pass (27 → 0) |
| `/api/chat` works after cleanup | Pass (retrieve + chat verified) |
| Privacy behavior documented | Pass (this report + cleanup script) |
