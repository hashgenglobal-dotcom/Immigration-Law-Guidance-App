# SourcePath — Post-MVP Roadmap

**Product:** Immigration Law Guidance App (SourcePath)  
**Status:** Post-MVP execution started  
**MVP merge & QA:** Rishi (other contributor) — merges MVP branches 1–6 and runs full-stack testing  
**Post-MVP implementation:** Hash / agent branches — **one branch pushed at a time** for review  

**Base branch for all post-MVP work:** `feature/retrieval-quality-mvp-tuning` on branch **`feature/post-mvp`** (not `main`). Merge MVP → `main` first, then merge `feature/post-mvp`.

---

## Handoff to Rishi (MVP — not in this queue)

| Branch | Task | Action |
|--------|------|--------|
| `fix/mvp-data-readiness-cleanup` | MVP 1 | Merge → test |
| `fix/privacy-log-cleanup` | MVP 2 | Merge → test |
| `feature/common-immigration-source-coverage` | MVP 3 | Merge → test |
| `feature/chat-guided-intake-routing` | MVP 4 | Merge → test |
| `feature/chat-answer-formatting-v1` | MVP 5 | Merge → test |
| `feature/retrieval-quality-mvp-tuning` | MVP 6 | Merge → test (or merge tip once) |
| `test/final-mvp-smoke-pass` | MVP 7 | Re-run smoke on merged `main`; set `OLLAMA_CHAT_MODEL=llama3.2:latest` |

Do **not** start post-MVP product branches until MVP is on `main`, unless a doc-only branch is reviewed in parallel.

---

## Post-MVP principles

1. **Privacy-first** — no raw Q/A in DB/logs by default; extend only with explicit policy + config.
2. **Local-first AI** — no public LLM APIs on the answer path.
3. **Information, not advice** — disclaimers + guardrails + attorney referral for high-risk topics.
4. **One branch = one reviewable unit** — push, open PR, Rishi reviews; then next branch.
5. **Stack order** — respect dependencies below; do not skip rate limiting before production auth.

---

## Task queue (execution order)

| Order | ID | Branch | Doc § | Type | Depends on | Status |
|-------|-----|--------|-------|------|------------|--------|
| 0 | POST-00 | `docs/post-mvp-task-plan` | — | Plan | — | **In progress** |
| 1 | POST-01 | `docs/privacy-data-retention-policy` | 7.4 | Docs | POST-00 | Queued |
| 2 | POST-02 | `docs/legal-review-process` | 7.5 | Docs | POST-01 | Queued |
| 3 | POST-03 | `feature/rate-limiting-abuse-protection` | 7.2 | Backend | MVP on `main`, Redis | Queued |
| 4 | POST-04 | `feature/auth-production` | 7.1 | Backend + mobile | POST-03 | Queued |
| 5 | POST-05 | `feature/legal-safety-guardrails` | 7.6 | Backend | MVP on `main` | Queued |
| 6 | POST-06 | `feature/observability-safe-logs` | 7.10 | Backend | POST-03 | Queued |
| 7 | POST-07 | `infra/production-deployment` | 7.3 | Infra | POST-03, POST-04 | Queued |
| 8 | POST-08 | `feature/rag-evaluation-suite` | 7.8 | Review/scripts | MVP Task 6 merged | Queued |
| 9 | POST-09 | `feature/admin-source-dashboard` | 7.9 | Backend + UI | POST-08 (partial) | Queued |
| 10 | POST-10 | `feature/bia-decisions-v2` | 7.7 | Data pipeline | Official source found | **Blocked** |
| 11 | POST-11 | `feature/web-app-v2` | 7.11 | Web | MVP + auth stable | **Deferred** |

Update the **Status** column in PR descriptions as branches land.

---

## POST-00 — Plan (this document)

**Branch:** `docs/post-mvp-task-plan`  
**Deliverable:** `docs/post-mvp-roadmap.md` (this file)  
**Acceptance:** Rishi can use the table above as merge/review checklist.

---

## POST-01 — Privacy & data retention policy (§7.4)

**Branch:** `docs/privacy-data-retention-policy`

**Goal:** Formal, user- and operator-facing policy aligned with current architecture (no raw chat storage, hash-only logs, guest limits).

**Deliverables:**
- `docs/privacy-data-retention-policy.md` — full policy (collection, use, retention, deletion, subprocessors, local AI)
- `docs/privacy-summary-for-users.md` — short in-app–ready summary

**Acceptance criteria:**
- [ ] States what is **never** stored (full questions, full answers, chat history in DB)
- [ ] Describes `privacy_safe_answer_logs` fields at a high level
- [ ] Describes mobile storage (guest counter only; no user PII in AsyncStorage)
- [ ] Retention periods and deletion process documented (even if “manual until admin UI”)
- [ ] Matches `STORE_USER_QUESTIONS=false` default in backend config

**Out of scope:** Legal sign-off (POST-02); implementation of automated deletion jobs (POST-06/09).

---

## POST-02 — Legal review process (§7.5)

**Branch:** `docs/legal-review-process`

**Goal:** Repeatable process for attorney review of disclaimers, high-risk routing, and sample answers.

**Deliverables:**
- `docs/legal-review-process.md` — roles, cadence, checklist, sign-off template
- `docs/legal-review-sample-questions.md` — fixed set for periodic re-review

**Acceptance criteria:**
- [ ] Defines who approves disclaimer/caution text changes
- [ ] Ties to POST-05 guardrail categories when that branch merges
- [ ] Explicit “not legal advice” review items

---

## POST-03 — Rate limiting & abuse protection (§7.2)

**Branch:** `feature/rate-limiting-abuse-protection`

**Goal:** Server-side limits on expensive endpoints; complement mobile guest cap.

**Deliverables:**
- Redis-backed rate limiter (IP + optional `X-Client-Id` / future auth subject)
- Limits on `POST /api/chat` and `POST /api/retrieve`
- Config via env (`RATE_LIMIT_*`); documented in `.env.example`
- `429` responses with stable error code; no user message in body
- Unit tests for limiter logic

**Acceptance criteria:**
- [ ] Default limits suitable for demo (e.g. chat 10/min/IP, retrieve 30/min/IP)
- [ ] Disabled or relaxed in `APP_ENV=development` via config flag
- [ ] Health routes exempt
- [ ] Privacy: rate-limit keys are hashes or opaque IDs, not raw questions

**Subtasks:**
1. `app/services/rate_limit_service.py`
2. FastAPI dependency / middleware registration in `main.py`
3. Wire into `chat.py` and `retrieval.py`
4. `.env.example` + short `docs/rate-limiting.md`

---

## POST-04 — Production authentication (§7.1)

**Branch:** `feature/auth-production`

**Goal:** Replace mock mobile login with real accounts backed by the API.

**Deliverables:**
- DB migration: `users` (id, email hash or email, password hash, created_at)
- Routes: `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me`
- JWT or signed session tokens; refresh strategy documented
- Mobile: secure token storage (expo-secure-store), attach `Authorization` to chat
- Guest mode retained with stricter server limits

**Acceptance criteria:**
- [ ] Passwords hashed (bcrypt/argon2); never logged
- [ ] No full chat content in auth tables
- [ ] Rate limits apply per user id after login (POST-03)
- [ ] Sign-up/login screens call real API (remove “preview only” comment)

**Subtasks:** schema → auth service → routes → mobile AuthContext → tests

---

## POST-05 — Legal safety guardrails (§7.6)

**Branch:** `feature/legal-safety-guardrails`

**Goal:** Structured pre- and post-generation checks beyond prompt text.

**Deliverables:**
- `app/services/legal_guardrails.py` — classifiers: fraud, criminal evasion, impersonation, explicit advice-seeking
- Refusal templates aligned with POST-05 answer formatting (when MVP merged)
- Log refusals to `privacy_safe_answer_logs` (refusal flag only)
- Tests for known bad prompts

**Acceptance criteria:**
- [ ] Blocks or redirects high-risk categories before LLM call when possible
- [ ] Never stores blocked user message text in DB
- [ ] Documented in `docs/legal-guardrails.md`

---

## POST-06 — Observability & safe logs (§7.10)

**Branch:** `feature/observability-safe-logs`

**Goal:** Operability without PII leakage.

**Deliverables:**
- Request ID middleware; structured JSON logs (level, route, latency, status, `query_hash` only)
- Optional metrics hooks (Prometheus-friendly counters) behind config
- `docs/observability.md` — what is logged vs forbidden

**Acceptance criteria:**
- [ ] No raw `message` or `answer` in application logs
- [ ] Correlation id returned in response header for support

---

## POST-07 — Production deployment (§7.3)

**Branch:** `infra/production-deployment`

**Goal:** Repeatable deploy path for backend + DB + Redis + Ollama guidance.

**Deliverables:**
- `infra/docker-compose.prod.yml` or `deploy/` templates
- `docs/production-deployment.md` — env checklist, secrets, TLS, backups
- Health check probes for orchestrator

**Acceptance criteria:**
- [ ] Documented secret management (no keys in repo)
- [ ] Postgres backup / restore notes
- [ ] Ollama colocated or private network only

---

## POST-08 — RAG evaluation suite (§7.8)

**Branch:** `feature/rag-evaluation-suite`

**Goal:** Expand MVP golden retrieval into broader eval (citation match, refusal, faithfulness sampling).

**Deliverables:**
- `review/validation/rag-eval-queries.json` — expanded set
- `review/scripts/run_rag_eval.py` — report JSON + markdown
- CI-friendly exit codes

**Acceptance criteria:**
- [ ] Builds on `validate_mvp_golden_retrieval.py` (requires MVP Task 6 on `main`)
- [ ] Reports precision@k and refusal rate without storing raw answers in git

---

## POST-09 — Admin source dashboard (§7.9)

**Branch:** `feature/admin-source-dashboard`

**Goal:** Operator UI to see dataset health, chunk counts, last ingest — no end-user PII.

**Deliverables:**
- Protected admin routes (`/api/admin/sources`, `/api/admin/datasets`)
- Simple admin web or mobile-internal screen (read-only v1)
- Auth gate: admin role from POST-04

**Acceptance criteria:**
- [ ] No user chat data in admin API
- [ ] Reuses existing schema health / table counts patterns

---

## POST-10 — BIA decisions v2 (§7.7) — BLOCKED

**Branch:** `feature/bia-decisions-v2`

**Blocker:** No official bulk source; see `review/04-bia-decisions-challenge-report.md`.

**When unblocked:**
- Source adapter + ingest script
- Separate dataset version; MVP scope filter excludes until explicitly enabled
- Re-run POST-08 eval with case-law queries

**Early scaffold (optional):** registry placeholder + ingest dry-run script only — no fake data.

---

## POST-11 — Web app v2 (§7.11) — DEFERRED

**Branch:** `feature/web-app-v2` (new; do not merge stale `feature/frontend-foundation` as-is)

**Goal:** Production web client sharing backend with mobile — after auth and rate limits.

**Defer until:** POST-04, POST-03, MVP merged.

---

## Suggested PR workflow (Rishi)

1. Review POST-00 plan PR → approve direction.
2. For each subsequent branch: pull branch → local smoke → comment → merge to `main` when green.
3. After MVP merge: rebase open post-MVP branches if conflicts appear.
4. Track blockers in this file’s Status column.

---

## Environment reminders (all post-MVP branches)

```bash
# Backend
cd backend && uvicorn app.main:app --reload

# After MVP merge on main
OLLAMA_CHAT_MODEL=llama3.2:latest

# Redis required for POST-03+
REDIS_URL=redis://localhost:6379/0
```

---

**Last updated:** May 20, 2026  
**Maintainer:** Update Status column when each branch is pushed.
