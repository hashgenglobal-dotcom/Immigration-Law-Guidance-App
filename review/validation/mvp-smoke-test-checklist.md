# MVP Smoke Test Checklist

**Purpose:** Quick pass/fail checks before handoff or merge review.  
**Environment:** Local dev only — not a production sign-off.  
**Time:** ~15–25 minutes if backend, Ollama, and Postgres are already running.

---

## Prerequisites

- [ ] `backend/.env` exists locally (never commit). `DATABASE_URL` and `OLLAMA_BASE_URL` set.
- [ ] PostgreSQL has MVP sources loaded (eCFR, USCIS PM, INA). See `validation/mvp-source-validation-report.md`.
- [ ] Ollama running locally (`ollama serve`) with chat + embedding models available.
- [ ] Backend: `cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- [ ] Mobile (optional): `cd mobile && npx expo start` — set `EXPO_PUBLIC_API_BASE_URL` in `mobile/.env` if not using simulator defaults (see `mobile/src/constants/api.ts`).

**Base URL for curls below:** `http://127.0.0.1:8000` (change if your port differs).

---

## 1. Backend health

| # | Check | Command / action | Pass criteria |
|---|--------|------------------|---------------|
| 1.1 | Liveness | `curl -sS http://127.0.0.1:8000/health` | HTTP 200; JSON includes `"status"` and `"privacy_mode":"local-first"` |
| 1.2 | Dependencies | `curl -sS http://127.0.0.1:8000/health/dependencies` | HTTP 200; `postgresql` and `ollama` reported reachable (redis may vary) |
| 1.3 | Schema | `curl -sS http://127.0.0.1:8000/health/schema` | HTTP 200; `"status":"ok"` or documented known gaps |

---

## 2. Retrieval (`POST /api/retrieve`)

| # | Check | Command / action | Pass criteria |
|---|--------|------------------|---------------|
| 2.1 | Hybrid retrieve | See curl below | HTTP 200; `status` ok; `results` array non-empty with `citation` fields |
| 2.2 | Query hash only | Inspect JSON response | `query_hash` present; response does **not** echo full query in error payloads |

```bash
curl -sS -X POST http://127.0.0.1:8000/api/retrieve \
  -H "Content-Type: application/json" \
  -d '{"query":"Can asylum applicants get work authorization?","top_k":5}'
```

**Second query (optional):** `"What is a Notice to Appear?"`

---

## 3. Chat (`POST /api/chat`)

| # | Check | Command / action | Pass criteria |
|---|--------|------------------|---------------|
| 3.1 | Grounded answer | See curl below | HTTP 200; non-empty `answer`; `disclaimer` present |
| 3.2 | Citations | Inspect JSON | `citations` array present (may be empty only if backend explicitly allows — note in results) |
| 3.3 | Privacy fields | Inspect JSON | `privacy_mode` present (e.g. `local-first`); `query_hash` present; no raw question in body |

```bash
curl -sS -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What is adjustment of status?","top_k":5}'
```

**Allow 30–90s** for local LLM. Timeout → check Ollama and backend logs (do not paste logs containing user text into tickets).

**Offline test (optional):** Stop backend → curl should fail; mobile should show connection error (see §4).

---

## 4. Mobile Ask (manual)

Run on iOS Simulator or device with backend reachable.

| # | Screen / flow | Pass criteria |
|---|----------------|---------------|
| 4.1 | Home | No confusing **Back** on Home; guest banner readable |
| 4.2 | Ask → submit | User message appears; loading state; answer appears |
| 4.3 | Citations | Citation cards or “no citations” note visible |
| 4.4 | Disclaimer | Backend or UI disclaimer visible; not presented as legal advice |
| 4.5 | Guest limit | Guest mode: limit enforced; count not stored as PII |
| 4.6 | Backend down | Stop backend → friendly error (no crash) |

**Sample questions:**

1. Can asylum applicants get work authorization?
2. What is a Notice to Appear?

**Mobile type-check:** `cd mobile && npm run type-check`

---

## 5. Privacy checks (no secrets)

| # | Check | Command / action | Pass criteria |
|---|--------|------------------|---------------|
| 5.1 | Mobile grep | `grep -rE 'OPENAI_API_KEY|OLLAMA_API_KEY|sk-|API_KEY|password=' mobile/src \|\| true` | No matches in app source |
| 5.2 | Mobile storage | `grep -r 'AsyncStorage.setItem' mobile/src` | Only `AuthContext` / onboarding + guest count keys |
| 5.3 | Review docs grep | `grep -rE 'password=\|OPENAI_API_KEY\|sk-\|Production-Ready' Review \|\| true` | No real secrets (pattern in this checklist line is OK) |
| 5.4 | Chat persistence | Use Ask, reload app | Questions/answers **not** restored from storage |
| 5.5 | Mock auth | Sign in preview → inspect storage | No email, displayName, or password in AsyncStorage |

**Allowed AsyncStorage keys:** `@sourcepath/onboarding_complete`, `@sourcepath/session` (guest `{ mode, guestChatsUsed }` only).

---

## 6. Source readiness (data layer)

| # | Check | Command / action | Pass criteria |
|---|--------|------------------|---------------|
| 6.1 | Readiness doc | Open `validation/mvp-source-validation-report.md` | eCFR, USCIS PM, INA MVP-ready; BIA post-MVP / 0 chunks |
| 6.2 | Active data (optional) | `uv run --project backend python Review/scripts/validate_active_dataset.py` | Note: milestone script may **FAIL** on multi-active MVP datasets — use report § SQL counts instead |
| 6.3 | Embeddings (optional) | `uv run --project backend python Review/scripts/validate_legal_chunk_embeddings.py` | Run if validating a specific dataset version |

**MVP sources in scope:** eCFR Title 8 · USCIS Policy Manual · INA / U.S. Code Title 8.  
**Out of scope:** BIA decisions (blocked).

---

## Sign-off block

| Area | Tester | Date | Pass / Fail | Notes |
|------|--------|------|-------------|-------|
| Backend health | | | | |
| Retrieve | | | | |
| Chat | | | | |
| Mobile Ask | | | | |
| Privacy | | | | |
| Source readiness | | | | |

**Overall MVP smoke test:** ☐ Pass ☐ Fail

---

**Not production-ready.** Pass here means **dev-validated MVP** only — auth, rate limiting, deployment hardening, and security review are separate.
