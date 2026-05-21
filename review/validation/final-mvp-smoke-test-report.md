# Final MVP Smoke Test Report

**Branch:** `test/final-mvp-smoke-pass`  
**Base:** `origin/main` @ `56af442` (`fix(mobile): polish final MVP UI layout`)  
**Date:** May 20, 2026  
**Scope:** Validation only — no feature changes, no screenshots, no new scaffold.

---

## MVP readiness decision

**Conditional PASS for local MVP demo** — core backend retrieval, mobile shell, guest limits, and privacy posture are sound. **Not a production sign-off.**

Blockers / follow-ups before calling MVP “complete” on `main`:

1. Set `OLLAMA_CHAT_MODEL=llama3.2:latest` (or install `llama3.1:8b`) in `backend/.env` so **HTTP** `POST /api/chat` succeeds without 503.
2. Merge open feature branches (guided intake, answer formatting, retrieval tuning, source coverage) — several smoke items are **implemented on branches but absent on `main`**.
3. Reconcile **multiple active datasets** (including BIA in dev DB) with MVP source policy.
4. Add backend unit tests on `main` (no `backend/tests/` on this revision).

---

## Tested environment

| Item | Value |
|------|--------|
| OS | macOS (darwin 25.4.0) |
| Repo | `Immigration-Law-Guidance-App` @ `56af442` |
| Backend | `uvicorn` @ `http://127.0.0.1:8000` (already running) |
| PostgreSQL | Local dev via `backend/.env` |
| Redis | Connected (`/health/dependencies`) |
| Ollama | `nomic-embed-text:latest`, `llama3.2:latest` (no `llama3.1:8b`) |
| Mobile | `npx tsc --noEmit` (compile-only; Expo UI not launched in this pass) |

**Note:** The live backend on port 8000 may have been started from a **newer working tree** than `main` (e.g. retrieve JSON included `active_datasets` / `mvp_sources`, which are not in `main`’s `RetrievalResponse` schema). API results below describe **observed runtime**; **code review** reflects **`main`** only.

---

## Pass / fail summary

| # | Check | Result | Notes |
|---|--------|--------|-------|
| 1 | Backend health `GET /health` | **PASS** | `status: ok`, `privacy_mode: local-first` |
| 2 | Backend dependencies `GET /health/dependencies` | **PASS** | postgres, redis, ollama `ok` |
| 3 | `POST /api/retrieve` | **PASS** | 200, `query_hash` present, raw query not echoed |
| 4 | `POST /api/chat` (HTTP) | **FAIL** | 503 `CHAT_MODEL_UNAVAILABLE` — default model `llama3.1:8b` not installed |
| 4b | Chat via `ChatService` + `llama3.2:latest` | **PASS** | All 12 MVP queries returned answer, disclaimer, citations |
| 5 | Mobile Ask (code + tsc) | **PASS** | Ask screen, composer, citations UI, error box; `tsc` clean |
| 6 | Guided intake routing | **FAIL** | Not present on `main` (no `guided_intake`, `needs_clarification`, clarification UI) |
| 7 | Common question coverage | **PARTIAL** | All 12 retrieve with ≥1 result; several top-1 citations tangential (see below) |
| 8 | Guest mode | **PASS** | Guest session + limit in `AuthContext`; only `guestChatsUsed` persisted |
| 9 | Privacy storage (mobile) | **PASS** | No raw chat in AsyncStorage; Ask `turns` in React state only |
| 10 | Privacy logs (DB) | **PASS** | `privacy_safe_answer_logs` count **0**; columns hash/metadata only |
| 11 | Source readiness | **PASS** | 11,594 active embedded chunks; eCFR, USCIS PM, INA, official pages active |
| 12 | No screenshots committed | **PASS** | Only known assets under `mobile/assets/images/` (6 PNGs) |
| 13 | No secrets / PII in repo | **PASS** | Scan found README business address/EIN only; no API keys |

### Mobile manual checklist (not run in Expo this pass)

| Check | Result | Evidence |
|--------|--------|----------|
| Home loads | **Code PASS** | `(main)/index.tsx`, `SessionBanner`, `HomeHero` |
| Guest mode works | **Code PASS** | `signInAsGuest`, guest badge |
| Ask question works | **Code PASS** | `POST /api/chat` via `chatApi.ts` |
| Clarification options | **FAIL on main** | Feature not merged |
| Citations show | **Code PASS** | `AssistantChatContent` + `CitationCard` |
| Disclaimer shows | **Code PASS** | Backend disclaimer + UI fallback |
| Backend offline friendly error | **Code PASS** | `ChatApiError` → `OFFLINE_MESSAGE` in `ask.tsx` |
| Guest limit works | **Code PASS** | `GUEST_CHAT_LIMIT = 5`, `GuestLimitModal` |
| Reload does not restore raw chat | **PASS** | No chat persistence keys; `turns` not in AsyncStorage |

---

## Commands run

```bash
# Branch
git fetch origin main && git checkout main && git pull && git checkout -b test/final-mvp-smoke-pass

# Health
curl -sS http://127.0.0.1:8000/health
curl -sS http://127.0.0.1:8000/health/dependencies
curl -sS http://127.0.0.1:8000/health/schema

# Retrieve (12 MVP queries)
curl -sS -X POST http://127.0.0.1:8000/api/retrieve \
  -H "Content-Type: application/json" \
  -d '{"query":"<query>","top_k":3}'

# Chat HTTP (failed on default model)
curl -sS -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Can asylum applicants get work authorization?","top_k":5}'

# Chat programmatic (pass) — llama3.2
cd backend && OLLAMA_CHAT_MODEL=llama3.2:latest uv run python -c "..."  # ChatService, 12 queries

# Mobile compile
cd mobile && npx tsc --noEmit

# Backend tests on main
cd backend && uv run python -m unittest discover -s tests -p 'test_*.py'
# → 0 tests (no test modules on main)

# Privacy / sources (read-only SQL)
# psal count, active chunks, dataset_versions

# Repo scans
git status --short
git grep -n -E 'password=|OPENAI_API_KEY|sk-|...' -- .
find . -path ./.git -prune -o -path ./node_modules -prune -o \
  -type f \( -name '*.png' -o -name '*.jpg' \) -print
```

---

## Sample query results

### `POST /api/retrieve` (top citation, `top_k=3`)

| Query | Top citation | Assessment |
|-------|----------------|------------|
| How do I apply for EAD? | 8 CFR § 217.2 | Partial — Form I-765 also in top 3 |
| Can asylum applicants get work authorization? | 8 CFR § 274a.13 | Partial — 208.7 not rank 1 on runtime |
| What is STEM OPT? | 8 CFR § 324.1 | Weak — OPT § 214.2 lower in list |
| What is a Notice to Appear? | 8 CFR § 287.5 | Weak — § 239.x not in top 3 |
| What is adjustment of status? | 8 CFR § 1245.20 | OK — AOS family |
| Can I travel while I-485 is pending? | Vol 3, Part B, Ch 12 | OK — travel / AOS policy |
| How do I become a citizen? | Vol 12, Part H, Ch 1 | OK — naturalization PM |
| What is good moral character? | 8 CFR § 316.10 | OK |
| What is an RFE? | 8 CFR § 324.1 | Weak — PM RFE chapters lower |
| How do I change my address with USCIS? | USCIS Official Page | OK |
| What is Form I-130? | USCIS Form I-130 | OK |
| What is TPS? | 8 CFR § 324.1 | Weak — TPS § 244.x lower |

### `ChatService` + `llama3.2:latest` (`top_k=5`, May 20, 2026)

| Query | Citations | Top citation used |
|-------|-----------|-------------------|
| How do I apply for EAD? | 5 | 8 CFR § 217.2 |
| Can asylum applicants get work authorization? | 3 | 8 CFR § 274a.13 |
| What is STEM OPT? | 4 | 8 CFR § 324.1 |
| What is a Notice to Appear? | 5 | 8 CFR § 287.5 |
| What is adjustment of status? | 5 | 8 CFR § 1245.20 |
| Can I travel while I-485 is pending? | 4 | Vol 3, Part B, Ch 12 |
| How do I become a citizen? | 5 | Vol 12, Part H, Ch 1 |
| What is good moral character? | 4 | 8 CFR § 316.10 |
| What is an RFE? | 5 | 8 CFR § 324.1 |
| How do I change my address with USCIS? | 4 | USCIS Official Page |
| What is Form I-130? | 4 | USCIS Form I-130 |
| What is TPS? | 5 | 8 CFR § 324.1 |

All chat answers included **disclaimer** text and did not echo the raw question in the response body. Responses are grounded in retrieved chunks (not evaluated for legal accuracy in this pass).

### HTTP `POST /api/chat`

```json
{
  "detail": {
    "status": "error",
    "error_code": "CHAT_MODEL_UNAVAILABLE",
    "message": "Local chat model is not available. Ensure Ollama is running: ollama serve",
    "privacy_mode": "local-first"
  }
}
```

**Fix:** `OLLAMA_CHAT_MODEL=llama3.2:latest` in `backend/.env` and restart uvicorn.

---

## Privacy and storage

| Area | Finding |
|------|---------|
| `privacy_safe_answer_logs` | **0 rows** in dev DB at test time |
| Table columns | `question_hash`, `answer_hash`, chunk IDs, metadata — **no raw Q/A text** |
| `/api/chat` route | Documented stateless; no chat history persistence |
| Mobile AsyncStorage | `onboarding_complete`, guest `{ mode, guestChatsUsed }` only |
| Ask screen | Messages in component state; **cleared on reload** |

---

## Source readiness

| Metric | Value |
|--------|--------|
| Active embedded chunks | 11,594 |
| Active datasets (dev) | eCFR full, USCIS PM, INA, USCIS official pages, BIA variants |
| `GET /health/schema` | `status: ok`, 10/10 required tables |

See also: `Review/validation/mvp-source-validation-report.md`, `Review/validation/mvp-smoke-test-checklist.md`.

---

## Security / repo hygiene scans

### `git status --short` (before report commit)

```
?? Review/validation/retrieval-quality-mvp-results.json
```

Untracked generated JSON from a prior branch — **not committed** in this smoke pass.

### Secret / PII grep

No matches for `OPENAI_API_KEY`, `sk-`, `rawQuestion`, `rawMessage`, or `chatHistory` in application code. README contains public business **EIN/address** only.

### Images

Committed app assets only (6 files under `mobile/assets/images/`). No new screenshots added.

---

## Remaining known limitations

1. **`main` lags feature branches** — guided intake, structured answers, retrieval tuning, and extended MVP reporting are on open branches, not merged.
2. **Chat HTTP 503** — default `OLLAMA_CHAT_MODEL=llama3.1:8b` vs installed `llama3.2:latest`.
3. **Hybrid rank quality** — several definitional queries surface tangential CFR sections at rank 1 (STEM OPT, NTA, RFE, TPS); tuning branch addresses golden-set top-3.
4. **Multiple active datasets** — dev DB has 7 active versions including BIA; MVP policy prefers official regulatory/policy sources.
5. **No automated backend tests on `main`** — regression risk until test suite is merged.
6. **Mobile UI** — manual Expo pass recommended before external demo.
7. **Answer formatting** — `main` answers are not yet section-structured (Short answer / caution blocks).

---

## References

- Checklist: `Review/validation/mvp-smoke-test-checklist.md`
- Source validation: `Review/validation/mvp-source-validation-report.md`
- Open PR branches (not on `main`): `feature/chat-guided-intake-routing`, `feature/chat-answer-formatting-v1`, `feature/retrieval-quality-mvp-tuning`, `feature/common-immigration-source-coverage`
