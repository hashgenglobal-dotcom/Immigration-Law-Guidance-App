# Final MVP Smoke Test Report

**Branch:** `test/final-mvp-smoke-pass`  
**Base:** `origin/main` after `0d5f757` (`fix: prevent duplicate structured chat sections`)  
**Date:** May 21, 2026  
**Scope:** Final MVP backend/API/mobile compile smoke validation. No raw data, no credentials, no screen captures.

---

## MVP readiness decision

**PASS for MVP demo smoke testing.**  
This is not a production security/legal sign-off.

The MVP backend, retrieval, guided intake, structured answers, source reporting, and mobile compile checks passed against the shared staging database.

---

## Final database state

The staging database was cleaned after BIA upload completed.

| Check | Final state | Result |
|---|---:|---|
| MVP active embedded chunks | 11,589 / 11,589 | PASS |
| eCFR full | 9,314 active embedded | PASS |
| INA / U.S. Code Title 8 | 1,387 active embedded | PASS |
| USCIS Policy Manual | 877 active embedded | PASS |
| USCIS official pages | 11 active embedded | PASS |
| eCFR sample active chunks | 0 | PASS |
| BIA active chunks | 0 | PASS |
| BIA embedded chunks | 0 | Post-MVP |
| privacy-safe answer logs | 0 | PASS |

BIA data remains stored for post-MVP work, but BIA chunks are inactive and BIA dataset versions are archived for MVP. BIA should not be enabled until embeddings are generated and BIA-specific retrieval evaluation passes.

---

## Code/test checks

| Area | Command / check | Result |
|---|---|---|
| Backend answer formatting tests | `tests.test_answer_formatting` | 11/11 PASS |
| Guided intake tests | `tests.test_guided_intake` | 9/9 PASS |
| Retrieval scoring tests | `tests.test_retrieval_scoring` | 7/7 PASS |
| Mobile TypeScript | `npm run type-check` | PASS |
| Expo dependency check | `npx expo install --check` | PASS |

---

## API smoke checks

| Check | Result | Evidence |
|---|---|---|
| Health endpoint | PASS | `status: ok`, `privacy_mode: local-first` |
| Broad EAD question | PASS | returns `needs_clarification` with category options |
| Selected F-1 OPT / STEM OPT answer | PASS | returns `status: ok`, citations, source reporting |
| Structured answer headers | PASS | each required header appears once |
| Retrieval for STEM OPT | PASS | returns non-empty results |
| BIA excluded from MVP sources | PASS | API source reporting does not include BIA |

---

## Final API source reporting

The final `/api/chat` and `/api/retrieve` smoke tests reported these MVP source families:

- eCFR Title 8
- INA / U.S. Code Title 8
- USCIS Policy Manual
- USCIS Official Pages

BIA was not included in active MVP source reporting.

---

## Known post-MVP items

1. BIA is available as stored data but remains post-MVP because BIA chunks currently have no embeddings.
2. BIA should be enabled only after embedding generation, BIA-specific golden retrieval testing, and citation UI validation.
3. Rotate the shared staging database credential before wider sharing or production use.
4. Perform a full manual mobile simulator pass before an external sponsor demo.
5. Production hardening is still post-MVP: authentication, rate limiting, audit logs, RLS/security policies, monitoring, backup plan, and legal review.

---

## Final conclusion

MVP smoke validation passes for demo readiness on the current `main`.

The app can now proceed to mobile manual testing and controlled demo preparation, while BIA and production security hardening remain post-MVP work.
