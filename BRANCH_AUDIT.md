# Unmerged Branch Inventory Report

**Repository:** Immigration-Law-Guidance-App  
**Audit date:** 2026-05-26  
**Baseline:** `origin/main` @ `f8e499bd` — *style(web): use navy for landing top nav and chat headers* (2026-05-25)  
**Method:** Read-only `git` analysis (`git branch`, `git log -1`, `git diff --stat origin/main...<branch>`). No branches were checked out or modified.

---

## Executive summary

| Metric | Count |
|--------|------:|
| Local branches (excluding `main`) | 27 |
| Branches with **unique commits** vs `origin/main` (`ahead > 0`) | 13 |
| Branches with **no diff** vs `origin/main` (`ahead = 0`) | 14 |
| Branches flagged **High** merge risk | 6 |
| Branches flagged **Medium** merge risk | 5 |
| Branches flagged **Low** merge risk | 16 |

**Architectural themes across active branches:**

1. **Two web stacks** — `web/` (Vite, on `main` + `feature/updated-web`) vs `frontend/` (Next.js on `feature/frontend-foundation`, `feature/web-full-stack`). Merging both without a product decision creates duplicate UIs and deployment confusion.
2. **Official Updates** — Overlapping work on `feature/official-updates`, `feature/official-updates-mvp`, and `local/test-ask-and-updates` (shared migration `003-official-updates.sql` and `backend/app/schemas/official_updates.py`).
3. **Ask / chat evolution** — `feature/ask-UIupdate`, `feature/ask-memory-simple-rework`, and `local/test-ask-and-updates` all touch `chat_service.py` / `backend/app/schemas/chat.py` and mobile Ask screens.
4. **Stale / already-integrated branches** — Many `feature/*` branches show **0 commits ahead** of `main` (content likely merged via other PRs); safe to archive after verification.

**Suggested merge attention order (active branches only):**

1. `feature/updated-web` — aligned with current `main` web stack (0 behind `main`).
2. `features/more-guide` — small, mobile-only scenario library.
3. `feature/ask-memory-simple-rework` — coordinate with Ask UI branches; **High** schema/chat risk.
4. `feature/official-updates-mvp` — pick **one** official-updates line (`mvp` vs `feature/official-updates` vs local test branch).
5. Defer or reject duplicate `frontend/` mega-branches unless Next.js is the chosen web target.

---

## Merge risk criteria (used in this report)

| Level | Criteria |
|-------|----------|
| **High** | Touches `database/migrations/`, `backend/app/services/retrieval_service.py`, or core schemas (`backend/app/schemas/*`), or heavily modifies `chat_service.py` |
| **Medium** | Multi-surface (backend + mobile + docs), large diff (>1k LOC), or conflicts with another active feature branch |
| **Low** | Docs-only, small scoped change, mobile-only UI, or **no unique commits** vs `main` |

---

## Active branches (unique commits vs `origin/main`)

### `feature/updated-web`

- **Branch Name:** `feature/updated-web`
- **Last Commit:** 2026-05-26 — `ux(web): shift messaging to verifiable navigation`
- **Commits vs main:** 2 ahead · 0 behind
- **Diff summary:** 31 files · +3,866 / −761 lines
- **Architectural Scope:** Web (Vite) / Full-Stack (web-only)
- **Key Files Touched:**
  - `web/src/pages/AboutPage.module.css`
  - `web/src/pages/AboutPage.tsx`
  - `web/src/lib/sourceCatalog.ts`
  - `web/src/pages/SourcesPage.tsx`
  - `web/src/lib/productMessaging.ts`
- **Inferred Feature/Purpose:** SourcePath-branded Vite web app: About trust center, source library catalog, scenarios page, landing/chat UX, and “verifiable navigation” product copy. This is the branch intended for Vercel `web/` deploys on `main`.
- **Merge Risk Level:** **Medium** (large UI surface; does not touch DB/retrieval/schemas; low conflict with `main` timing)

---

### `feature/web-full-stack`

- **Branch Name:** `feature/web-full-stack`
- **Last Commit:** 2026-05-23 — `feat: add Next.js web app with live Ask API proxy for local and Vercel`
- **Commits vs main:** 1 ahead · 22 behind
- **Diff summary:** 36 files · +9,454 / −1 lines
- **Architectural Scope:** Frontend (Next.js) / Scripts
- **Key Files Touched:**
  - `frontend/src/components/ui/bolt-style-chat.tsx`
  - `frontend/src/components/ui/about-us-section.tsx`
  - `frontend/src/app/scenarios/page.tsx`
  - `frontend/src/lib/parseChatAnswer.ts`
  - `scripts/start-web-local.sh`
- **Inferred Feature/Purpose:** Parallel **Next.js** web stack with Ask proxy, scenarios UI, and local start script—overlaps conceptually with `web/` on `main` but different framework and deploy path.
- **Merge Risk Level:** **Medium** (architectural fork vs Vite `web/`; not schema/retrieval, but high product/process risk)

---

### `feature/frontend-foundation`

- **Branch Name:** `feature/frontend-foundation`
- **Last Commit:** 2026-05-16 — `feat(frontend): enhance UI, About section, and risk badge colors`
- **Commits vs main:** 5 ahead · 115 behind
- **Diff summary:** 29 files · +9,302 lines
- **Architectural Scope:** Frontend (Next.js)
- **Key Files Touched:**
  - `frontend/src/components/ui/bolt-style-chat.tsx`
  - `frontend/src/components/ui/about-us-section.tsx`
  - `frontend/src/app/scenarios/page.tsx`
  - `frontend/src/app/page.tsx`
  - `frontend/package-lock.json`
- **Inferred Feature/Purpose:** Early Next.js marketing/chat/scenarios scaffold; largely superseded by `main`’s `web/` direction unless team standardizes on `frontend/`.
- **Merge Risk Level:** **Medium** (duplicate web stack; very stale vs `main`)

---

### `feature/post-mvp`

- **Branch Name:** `feature/post-mvp`
- **Last Commit:** 2026-05-21 — `merge: integrate origin/main into feature/post-mvp`
- **Commits vs main:** 17 ahead · 29 behind
- **Diff summary:** 51 files · +2,376 / −82 lines
- **Architectural Scope:** Full-Stack (Docs / Review / Backend auth / Mobile)
- **Key Files Touched:**
  - `review/validation/mvp-database-handoff.md`
  - `docs/post-mvp-roadmap.md`
  - `backend/app/services/auth_service.py`
  - `backend/app/schemas/auth.py`
  - `database/migrations/002-app-users.sql`
- **Inferred Feature/Purpose:** Post-MVP planning docs, BIA/RAG eval scaffolding, mobile auth API wiring, and **app-users** DB migration—broader than a single feature.
- **Merge Risk Level:** **High** (`database/migrations/002-app-users.sql`, `backend/app/schemas/auth.py`)

---

### `feature/official-updates`

- **Branch Name:** `feature/official-updates`
- **Last Commit:** 2026-05-22 — `fix(mobile): remove preview wording from auth choice and sign-in flows`
- **Commits vs main:** 2 ahead · 29 behind
- **Diff summary:** 31 files · +2,377 / −37 lines
- **Architectural Scope:** Full-Stack (Backend / Database / Mobile / Docs / Scripts)
- **Key Files Touched:**
  - `database/migrations/003-official-updates.sql`
  - `backend/app/services/official_updates_service.py`
  - `backend/app/schemas/official_updates.py`
  - `mobile/app/(main)/updates.tsx`
  - `docs/official-updates.md`
- **Inferred Feature/Purpose:** End-to-end **Official Updates** feed: DB tables, FastAPI routes/services, mobile list/detail screens, ingest/seed scripts. Superset of MVP branch plus auth copy fixes.
- **Merge Risk Level:** **High** (migration + new schemas; overlaps `feature/official-updates-mvp`)

---

### `feature/official-updates-mvp`

- **Branch Name:** `feature/official-updates-mvp`
- **Last Commit:** 2026-05-23 — `feat: add Official Updates MVP from government feeds`
- **Commits vs main:** 1 ahead · 22 behind
- **Diff summary:** 24 files · +2,248 / −5 lines
- **Architectural Scope:** Full-Stack (Backend / Database / Mobile / Docs / Scripts)
- **Key Files Touched:**
  - `database/migrations/003-official-updates.sql`
  - `docs/official-updates.md`
  - `backend/app/services/official_updates_service.py`
  - `mobile/app/(main)/updates/[id].tsx`
  - `review/scripts/ingest_official_updates.py`
- **Inferred Feature/Purpose:** MVP slice of Official Updates (feeds, topics, mobile UI, migration). **Do not merge both this and `feature/official-updates`** without reconciling duplicate migration/schema.
- **Merge Risk Level:** **High**

---

### `local/test-ask-and-updates`

- **Branch Name:** `local/test-ask-and-updates`
- **Last Commit:** 2026-05-23 — `Merge remote-tracking branch 'origin/feature/official-updates-mvp' into local/test-ask-and-updates`
- **Commits vs main:** 3 ahead · 22 behind
- **Diff summary:** 33 files · +2,679 / −116 lines
- **Architectural Scope:** Full-Stack (combines Ask memory + Official Updates)
- **Key Files Touched:**
  - `database/migrations/003-official-updates.sql`
  - `backend/app/services/ask_memory_context.py`
  - `backend/app/schemas/chat.py`
  - `mobile/app/(main)/ask.tsx`
  - `mobile/app/(main)/updates.tsx`
- **Inferred Feature/Purpose:** Local integration branch merging **Ask conversation memory** with **Official Updates MVP** for simulator testing—not ideal as a direct `main` merge without splitting.
- **Merge Risk Level:** **High** (migration + `chat` schema + composite features)

---

### `feature/ask-memory-simple-rework`

- **Branch Name:** `feature/ask-memory-simple-rework`
- **Last Commit:** 2026-05-23 — `feat: add simple in-session Ask conversation memory`
- **Commits vs main:** 1 ahead · 22 behind
- **Diff summary:** 9 files · +431 / −111 lines
- **Architectural Scope:** Backend / Mobile
- **Key Files Touched:**
  - `backend/app/services/ask_memory_context.py`
  - `backend/app/schemas/chat.py`
  - `backend/app/services/chat_service.py`
  - `mobile/app/(main)/ask.tsx`
  - `backend/tests/test_ask_memory_context.py`
- **Inferred Feature/Purpose:** In-session conversation memory for Ask: extends chat request/response schema and threads prior turns into `chat_service` without persistent user storage.
- **Merge Risk Level:** **High** (`backend/app/schemas/chat.py`, `chat_service.py`)

---

### `feature/ask-UIupdate`

- **Branch Name:** `feature/ask-UIupdate`
- **Last Commit:** 2026-05-22 — `chore: drop unrelated screenshot and validation JSON from ask-UIupdate`
- **Commits vs main:** 2 ahead · 26 behind
- **Diff summary:** 10 files · +675 / −58 lines
- **Architectural Scope:** Full-Stack (Backend chat path / Mobile Ask UI / Docs)
- **Key Files Touched:**
  - `backend/app/services/chat_service.py`
  - `backend/app/api/routes/chat.py`
  - `mobile/src/lib/chatApi.ts`
  - `mobile/src/components/AssistantAnswerContent.tsx`
  - `docs/ask-handoff-for-rishi.md`
- **Inferred Feature/Purpose:** Ask UX refresh: streaming/source detail components, expanded mobile chat client, and backend chat route/service updates for richer answers.
- **Merge Risk Level:** **High** (`chat_service.py`, `chat.py` route—coordinate with memory branch)

---

### `feature/mvp-smoke-test-docs`

- **Branch Name:** `feature/mvp-smoke-test-docs`
- **Last Commit:** 2026-05-19 — `MVP smoke test docs: complete frontend scaffold, mobile screenshots, eCFR/INA ingestion scripts`
- **Commits vs main:** 2 ahead · 56 behind
- **Diff summary:** 91 files · +13,570 lines
- **Architectural Scope:** Full-Stack (Scripts / Docs / Frontend artifacts / Mobile screenshots)
- **Key Files Touched:**
  - `scripts/fetch_ecfr_title8_full.py`
  - `scripts/ingest_ina_cornell.py`
  - `scripts/ingest_uscis_pm.py`
  - `review/validation/mvp-smoke-test-checklist.md`
  - `mobile/screenshots/` (binaries)
- **Inferred Feature/Purpose:** MVP validation package: large ingestion scripts, smoke-test checklist, screenshots, and frontend scaffold snapshots—not a single runtime feature.
- **Merge Risk Level:** **Medium** (mostly scripts/docs/binaries; avoid merging duplicate `frontend/` unless intended)

---

### `feature/mobile-final-polish`

- **Branch Name:** `feature/mobile-final-polish`
- **Last Commit:** 2026-05-20 — `merge: local full-stack simulator test (chat + polish)`
- **Commits vs main:** 1 ahead · 52 behind
- **Diff summary:** 7 files · +360 / −31 lines
- **Architectural Scope:** Mobile
- **Key Files Touched:**
  - `mobile/src/lib/chatApi.ts`
  - `mobile/app/(main)/ask.tsx`
  - `mobile/src/components/AssistantAnswerContent.tsx`
  - `mobile/src/components/CitationCard.tsx`
  - `mobile/src/types/chat.ts`
- **Inferred Feature/Purpose:** Mobile Ask polish: citation cards, typed chat API responses, and simulator-tested chat integration.
- **Merge Risk Level:** **Medium** (overlaps other Ask branches; mobile-only)

---

### `features/more-guide`

- **Branch Name:** `features/more-guide`
- **Last Commit:** 2026-05-23 — `feat: add 12 step-by-step scenario guides for common immigration paths`
- **Commits vs main:** 1 ahead · 22 behind
- **Diff summary:** 3 files · +378 / −109 lines
- **Architectural Scope:** Mobile (content library)
- **Key Files Touched:**
  - `mobile/src/lib/scenarioGuides.ts`
  - `mobile/src/lib/mockData.ts`
  - `mobile/app/(main)/scenarios.tsx`
- **Inferred Feature/Purpose:** Replaces thin mock scenarios with a **12-guide** library (same content later mirrored on web `scenarioGuides.ts` in `feature/updated-web`).
- **Merge Risk Level:** **Low**

---

### `docs/post-mvp-task-plan`

- **Branch Name:** `docs/post-mvp-task-plan`
- **Last Commit:** 2026-05-21 — `docs: add post-MVP roadmap and branch queue`
- **Commits vs main:** 1 ahead · 47 behind
- **Diff summary:** 1 file · +293 lines
- **Architectural Scope:** Docs / Review
- **Key Files Touched:**
  - `docs/post-mvp-roadmap.md`
- **Inferred Feature/Purpose:** Planning document for post-MVP work queue and branch sequencing.
- **Merge Risk Level:** **Low**

---

## Branches with no unique commits vs `origin/main`

These branches have **0 commits ahead** of `origin/main` (no `git diff` vs main). Content likely already on `main` via squash merge or equivalent. **No merge required** unless you need the branch pointer for history.

### `docs/privacy-data-retention-policy`

- **Branch Name:** `docs/privacy-data-retention-policy`
- **Last Commit:** 2026-05-21 — `docs: add privacy and data retention policy (post-MVP §7.4)`
- **Architectural Scope:** Docs
- **Key Files Touched:** `docs/privacy-and-data-retention.md` (on branch tip; verify on `main`)
- **Inferred Feature/Purpose:** Privacy and data-retention policy documentation for the product.
- **Merge Risk Level:** **Low** (no unique commits vs `main`)

### `feature/ask-conversation`

- **Branch Name:** `feature/ask-conversation`
- **Last Commit:** 2026-05-22 — `feat(ask): Phase 2 grounded follow-up suggestion chips`
- **Architectural Scope:** Mobile
- **Key Files Touched:** `mobile/app/(main)/ask.tsx`, `mobile/src/lib/chatApi.ts`
- **Inferred Feature/Purpose:** Follow-up suggestion chips on Ask answers to drive continued exploration.
- **Merge Risk Level:** **Low** (no unique commits vs `main`)

### `feature/backend-cloud-foundation`

- **Branch Name:** `feature/backend-cloud-foundation`
- **Last Commit:** 2026-05-14 — `feat(backend): add retrieval readiness and cloud foundation`
- **Architectural Scope:** Backend / Scripts
- **Key Files Touched:** `backend/app/services/retrieval_service.py`, `scripts/ingest_*.py`
- **Inferred Feature/Purpose:** Early backend retrieval and cloud-readiness groundwork.
- **Merge Risk Level:** **Low** (no unique commits vs `main`; superseded by later `main`)

### `feature/chat-answer-formatting-v1`

- **Branch Name:** `feature/chat-answer-formatting-v1`
- **Last Commit:** 2026-05-21 — `feat(chat): structured answer formatting v1`
- **Architectural Scope:** Backend / Mobile
- **Key Files Touched:** `backend/app/services/chat_service.py`, `mobile/src/components/AssistantAnswerContent.tsx`
- **Inferred Feature/Purpose:** Structured chat answer formatting for citations and readability.
- **Merge Risk Level:** **Low** (no unique commits vs `main`)

### `feature/chat-guided-intake-routing`

- **Branch Name:** `feature/chat-guided-intake-routing`
- **Last Commit:** 2026-05-21 — `feat: add guided intake routing for broad immigration questions`
- **Architectural Scope:** Backend
- **Key Files Touched:** `backend/app/services/chat_service.py`, `backend/app/services/intake_routing.py`
- **Inferred Feature/Purpose:** Routes Ask queries through guided intake when facts are insufficient.
- **Merge Risk Level:** **Low** (no unique commits vs `main`)

### `feature/common-immigration-source-coverage`

- **Branch Name:** `feature/common-immigration-source-coverage`
- **Last Commit:** 2026-05-20 — `feat(sources): expand common immigration source coverage`
- **Architectural Scope:** Scripts / Database
- **Key Files Touched:** `scripts/ingest_*.py`, `review/validation/`
- **Inferred Feature/Purpose:** Broader corpus ingestion for common immigration sources.
- **Merge Risk Level:** **Low** (no unique commits vs `main`)

### `feature/mobile-chat-backend-integration`

- **Branch Name:** `feature/mobile-chat-backend-integration`
- **Last Commit:** 2026-05-19 — `fix(mobile): guest quota and live chat backend integration`
- **Architectural Scope:** Mobile / Backend
- **Key Files Touched:** `mobile/src/lib/chatApi.ts`, `backend/app/api/routes/chat.py`
- **Inferred Feature/Purpose:** Wires mobile Ask to live FastAPI chat with guest limits.
- **Merge Risk Level:** **Low** (no unique commits vs `main`)

### `feature/mobile-foundation`

- **Branch Name:** `feature/mobile-foundation`
- **Last Commit:** 2026-05-16 — `feat(mobile): foundation UI and navigation`
- **Architectural Scope:** Mobile
- **Key Files Touched:** `mobile/app/(main)/_layout.tsx`, `mobile/app/(auth)/`
- **Inferred Feature/Purpose:** Core Expo Router shell, auth flows, and tab navigation.
- **Merge Risk Level:** **Low** (no unique commits vs `main`)

### `feature/mobile-ui-ux-polish`

- **Branch Name:** `feature/mobile-ui-ux-polish`
- **Last Commit:** 2026-05-19 — `chore: mobile UI/UX polish and review package`
- **Architectural Scope:** Mobile / Review
- **Key Files Touched:** `mobile/src/components/`, `review/validation/`
- **Inferred Feature/Purpose:** Visual polish and review artifacts for mobile MVP.
- **Merge Risk Level:** **Low** (no unique commits vs `main`)

### `feature/mvp-source-validation`

- **Branch Name:** `feature/mvp-source-validation`
- **Last Commit:** 2026-05-19 — `docs: MVP source validation summary`
- **Architectural Scope:** Docs / Review
- **Key Files Touched:** `review/validation/mvp-source-validation-summary.md`
- **Inferred Feature/Purpose:** Documents which sources passed MVP validation gates.
- **Merge Risk Level:** **Low** (no unique commits vs `main`)

### `feature/retrieval-quality-mvp-tuning`

- **Branch Name:** `feature/retrieval-quality-mvp-tuning`
- **Last Commit:** 2026-05-21 — `feat: tune retrieval quality for MVP queries`
- **Architectural Scope:** Backend
- **Key Files Touched:** `backend/app/services/retrieval_scoring.py`, `backend/app/services/retrieval_service.py`
- **Inferred Feature/Purpose:** Hybrid retrieval scoring and tuning for MVP answer quality.
- **Merge Risk Level:** **Low** (no unique commits vs `main`; logic present on `main`)

### `fix/mvp-data-readiness-cleanup`

- **Branch Name:** `fix/mvp-data-readiness-cleanup`
- **Last Commit:** 2026-05-20 — `fix: MVP data readiness cleanup`
- **Architectural Scope:** Scripts / Database
- **Key Files Touched:** `scripts/`, `database/`
- **Inferred Feature/Purpose:** Cleans ingestion/seed paths so MVP demo data is consistent.
- **Merge Risk Level:** **Low** (no unique commits vs `main`)

### `fix/privacy-log-cleanup`

- **Branch Name:** `fix/privacy-log-cleanup`
- **Last Commit:** 2026-05-20 — `fix: remove PII from logs`
- **Architectural Scope:** Backend
- **Key Files Touched:** `backend/app/services/chat_service.py`, `backend/app/core/logging.py`
- **Inferred Feature/Purpose:** Redacts or avoids logging user content and identifiers.
- **Merge Risk Level:** **Low** (no unique commits vs `main`)

### `test/final-mvp-smoke-pass`

- **Branch Name:** `test/final-mvp-smoke-pass`
- **Last Commit:** 2026-05-21 — `test: final MVP smoke pass report`
- **Architectural Scope:** Review / Docs
- **Key Files Touched:** `review/validation/final-mvp-smoke-pass.md`
- **Inferred Feature/Purpose:** Records final smoke-test pass/fail for MVP release gate.
- **Merge Risk Level:** **Low** (no unique commits vs `main`)

---

## Dependency & conflict matrix (active branches)

| Area | Branches involved | Risk |
|------|-------------------|------|
| **Official Updates DB** | `feature/official-updates`, `feature/official-updates-mvp`, `local/test-ask-and-updates` | Duplicate `003-official-updates.sql` — merge **one** line only |
| **Ask / Chat backend** | `feature/ask-UIupdate`, `feature/ask-memory-simple-rework`, `local/test-ask-and-updates` | Conflicts in `chat_service.py`, `schemas/chat.py` |
| **Web UI stack** | `feature/updated-web` (Vite) vs `feature/web-full-stack` / `feature/frontend-foundation` (Next) | Product decision required before any merge |
| **Scenario guides** | `features/more-guide` (mobile) vs `feature/updated-web` (`web/src/lib/scenarioGuides.ts`) | Content parity, not necessarily conflict |
| **Post-MVP auth** | `feature/post-mvp` | New migration `002-app-users.sql` — run only with migration plan |

---

## Remote-only branches (not local)

| Remote branch | Note |
|---------------|------|
| `origin/BIA` | BIA corpus work; not checked out locally in this audit |

---

## Commands used (reproducibility)

```bash
git fetch origin main
git branch --format='%(refname:short)'
git log -1 --format='%ci|%s' <branch>
git rev-list --count origin/main..<branch>    # commits ahead
git rev-list --count <branch>..origin/main>    # commits behind
git diff --stat origin/main...<branch>
git diff --name-only origin/main...<branch>
```

---

## Reviewer checklist before merging to `main`

- [ ] Confirm **canonical web app**: `web/` (Vite) vs `frontend/` (Next.js)
- [ ] Pick **one** Official Updates branch; drop or rebase duplicates
- [ ] Sequence **Ask** merges: memory schema → UI update → integration test branch
- [ ] Run DB migrations in order (`002-app-users` only if auth scope approved; `003-official-updates` once)
- [ ] After web merge: `cd web && npm run build` and smoke-test `/`, `/chat`, `/about`, `/sources`
- [ ] After backend merges: `cd backend && pytest -q` and hit `/health/dependencies`
- [ ] Prune or delete branches with **0 commits ahead** after verification

---

*Generated by read-only branch audit. No branches were checked out.*
