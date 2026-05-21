# MVP Supabase Handoff Controls

**Branch:** `fix/mvp-supabase-handoff-controls`
**Date:** May 21, 2026

---

> **Credential safety notice:**
> A teammate's migration summary document contained a plaintext temporary Supabase database
> password. That document must **not** be committed to this repository. Rotate the Supabase
> database password before any production use or before sharing access more broadly.
>
> Rules:
> - Never commit `.env` or any file containing `DATABASE_URL` with credentials.
> - Never paste database passwords into Claude, GitHub issues, PR descriptions,
>   screen captures, Slack, or documentation.
> - Treat Supabase connection strings as secrets — even temporary ones.

---

## Purpose

This set of scripts and controls validates that the Supabase staging database is in the
correct state before MVP smoke testing begins. Validation is read-only. Cleanup requires an
explicit `--apply` flag and never deletes rows.

---

## MVP corpus definition

| Source | Dataset version prefix | Supabase alias prefix | Status in DB |
|--------|------------------------|----------------------|--------------|
| eCFR Title 8 (regulations) | `ecfr-title8-full-*` | `eCFR-v*` / `ecfr-v*` | `active` |
| INA / U.S. Code Title 8 (statutes) | `ina-*` | `ina-v*` | `active` |
| USCIS Policy Manual (policy) | `uscis-pm-*` | `uscis-pm-v*` | `active` |
| USCIS Official Pages (guidance) | `uscis-official-pages-*` | — | `active` |
| eCFR Title 8 sample (non-MVP) | `ecfr-title8-sample-*` | — | `ready` (is_active=FALSE) |
| BIA Precedent Decisions (post-MVP) | `bia-*` | — | must be `archived` / is_active=FALSE |

**MVP target:** 11,589 active embedded chunks across all four active sources.

---

## BIA exclusion policy

BIA decisions are **post-MVP**. They must remain inactive until:
1. Embeddings have been generated and quality-checked.
2. Retrieval evaluation passes for BIA-specific queries.
3. The team explicitly enables BIA as an active source.

For MVP: `bia_active_chunks` must be 0. The validation script exits non-zero if any BIA
chunks are active (unless `--allow-bia` is passed for post-MVP testing).

---

## eCFR sample deactivation

The eCFR sample dataset (`ecfr-title8-sample-*`, 5 chunks) was the initial preview corpus.
It must have `is_active = FALSE` before smoke testing. If any sample chunks are active,
run `cleanup_mvp_handoff_state.py --apply`.

---

## Scripts

### `review/scripts/validate_mvp_supabase_handoff.py`

Read-only validation. Checks:
- Dataset versions present
- Chunk counts per dataset (total / embedded / active / active+embedded)
- MVP active embedded count ≥ 10,000 (target: 11,589)
- eCFR sample active count = 0
- BIA active count = 0 (unless `--allow-bia`)
- `privacy_safe_answer_logs` count = 0

```bash
# Validate (expects full Supabase corpus)
uv run --project backend python review/scripts/validate_mvp_supabase_handoff.py

# On sample-only local DB (exits 0 regardless)
uv run --project backend python review/scripts/validate_mvp_supabase_handoff.py --relaxed

# Post-MVP BIA testing (bypasses BIA active check only)
uv run --project backend python review/scripts/validate_mvp_supabase_handoff.py --allow-bia
```

### `review/scripts/cleanup_mvp_handoff_state.py`

Deactivates sample and BIA chunks. Dry-run by default.

```bash
# Preview what would change (no writes)
uv run --project backend python review/scripts/cleanup_mvp_handoff_state.py

# Apply deactivations (single atomic transaction, rolls back on error)
uv run --project backend python review/scripts/cleanup_mvp_handoff_state.py --apply
```

Changes applied with `--apply`:
- `legal_chunks.is_active = FALSE` for `ecfr-title8-sample%` datasets
- `legal_chunks.is_active = FALSE` for `bia%` datasets
- `dataset_versions.status = 'archived'` for `bia%` datasets

---

## Smoke testing checklist

Final smoke testing must not begin until all of these pass:

| Check | Required state |
|-------|---------------|
| `validate_mvp_supabase_handoff.py` exits 0 | All checks pass |
| MVP active embedded chunks | ≥ 10,000 (target 11,589) |
| eCFR sample active chunks | 0 |
| BIA active chunks | 0 |
| `privacy_safe_answer_logs` rows | 0 |
| `.env` not committed | Verified in git history |
| Supabase password rotated | Before production access |

---

## Reference SQL

See `review/validation/mvp-database-snapshot-queries.sql` for read-only SQL to inspect
the database state directly.

---

## What must not be committed

- `backend/.env` or any file containing a `DATABASE_URL` with credentials
- Supabase connection strings (even temporary ones)
- Raw PDFs, JSONL exports, CSV dumps, SQL dumps, or database backups
- Files under `data/` (gitignored)
- Screen captures containing connection details
- Migration summary documents with plaintext passwords
