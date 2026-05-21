# Privacy & Data Retention Policy (Technical)

**App:** Immigration Law Guidance App (SourcePath)  
**Operator:** HashGen Global LLC  
**Version:** 1.0 (Post-MVP draft)  
**Effective:** Upon production launch (draft for engineering and legal review)

This document describes how the product **is designed to handle data**. It is a technical privacy policy for engineering, operations, and legal review—not a substitute for a final user-facing privacy notice published in the app store or website.

---

## 1. Purpose

SourcePath provides immigration **legal information** from official public sources. Privacy is a core requirement: users may ask sensitive immigration questions. The system is built **local-first** and **minimal-collection** by default.

---

## 2. What we do not collect or store (default)

The following are **not** written to PostgreSQL, Redis (except transient rate-limit counters), application logs, or mobile persistent storage by default:

| Data | Default handling |
|------|------------------|
| Full text of user questions | Processed in memory only for the request |
| Full text of generated answers | Returned to client only; not persisted |
| Chat conversation history (server) | Stateless API — no server-side thread storage |
| Chat conversation history (mobile) | In-memory UI state only for the session |
| User email / password (guest mode) | Not collected |
| Raw user questions in `privacy_safe_answer_logs` | Prohibited by schema design |

Backend configuration enforces this default:

- `STORE_USER_QUESTIONS=false` (see `backend/app/core/config.py`)

---

## 3. What may be processed (transient)

For each `POST /api/chat` or `POST /api/retrieve` request:

- Question text is held in server memory for retrieval and (for chat) local LLM generation.
- Embeddings are computed in memory via local Ollama; not stored per user.
- Retrieved legal chunks come from pre-ingested public sources, not from user data.

No public cloud LLM APIs (OpenAI, Anthropic, etc.) are used on the answer path.

---

## 4. What may be stored (privacy-safe metadata)

When logging is enabled, the `privacy_safe_answer_logs` table may store **only**:

- Cryptographic hash of the question (not reversible to full text from hash alone)
- Topic / category labels (coarse)
- Citation identifiers used in the response
- Retrieved chunk IDs
- Risk level and refusal flags
- Latency and timestamp
- Optional session or user **opaque IDs** (no email in this table)

Operators must not add columns for raw question or answer text without a formal policy change and legal review.

---

## 5. Mobile client storage

| Storage | Content | Purpose |
|---------|---------|---------|
| AsyncStorage: onboarding flag | Boolean | Skip welcome on return |
| AsyncStorage: guest session | `{ mode: "guest", guestChatsUsed: number }` | Enforce guest chat limit (default 5) |
| React state (Ask screen) | Current conversation turns | Display only; cleared on reload |
| Secure storage (post-MVP auth) | Auth tokens only | Planned in `feature/auth-production` — no chat text |

Legacy keys that stored user email or display name are purged on load.

**Guest limit** is also enforced in the UI; server-side rate limits are planned (post-MVP §7.2).

---

## 6. Legal corpus (not user data)

PostgreSQL holds ingested **public** legal text (eCFR, INA, USCIS Policy Manual, supplemental official pages). This is shared corpus data, not personal data about users.

---

## 7. Retention periods (target)

| Data class | Retention (target) | Deletion |
|------------|-------------------|----------|
| `privacy_safe_answer_logs` | 90 days rolling (production target) | Automated purge job (post-MVP observability/admin) or manual SQL per runbook |
| Rate-limit Redis keys | Minutes to hours (TTL) | Automatic expiry |
| User accounts (post-MVP) | Until account deletion request | Delete user row; revoke tokens; no chat history to delete on server |
| Ingested legal chunks | Until dataset version superseded | Operator deactivates dataset version; optional archive |
| Application logs | 30 days (production target) | Log rotation; must not contain raw questions |

Until automated purge exists, operators follow `docs/ops-runbook-privacy.md` (to be added in POST-06).

---

## 8. User rights & deletion (target)

For production with registered accounts (post-MVP):

- **Access:** Profile metadata only (email, account created date)—not chat history, because it is not stored.
- **Deletion:** Account deletion removes auth record and tokens; no chat export is possible server-side by design.
- **Correction:** Profile fields only.

Guest users have no account; clearing app data removes guest counter and onboarding flags.

---

## 9. Third parties & subprocessors

| Component | Role | User PII sent? |
|-----------|------|----------------|
| Self-hosted or VPC PostgreSQL | Legal corpus + metadata logs | No raw chat by default |
| Redis | Rate limiting, caching | Opaque keys only (post-MVP) |
| Ollama (local/private) | Embeddings + chat generation | Question text in memory to local model only |
| Expo / app stores | Distribution | Per store policies |

No advertising or analytics SDKs are in the MVP mobile app.

---

## 10. Security measures (baseline)

- TLS in production for all API traffic
- Secrets via environment variables, not committed to git
- Generic API errors (no echo of user message, DSN, or stack traces to clients)
- Password hashing for real auth (post-MVP; bcrypt/argon2)

---

## 11. Children

The service is not directed at children under 13. Do not knowingly collect data from children.

---

## 12. Changes to this policy

Material changes require:

1. Engineering update to this document and config defaults  
2. Legal review per `docs/legal-review-process.md` (POST-02)  
3. User-facing notice update before production deploy  

---

## 13. Contact

**Privacy inquiries:** privacy@hashgenglobal.com (placeholder — confirm before production)

**Operator:** HashGen Global LLC — see root `README.md` for business contact.

---

## 14. Related documents

- User summary: `docs/privacy-summary-for-users.md`
- Post-MVP roadmap: `docs/post-mvp-roadmap.md`
- MVP smoke privacy checks: `review/validation/final-mvp-smoke-test-report.md`

---

*Draft v1.0 — May 20, 2026. Requires attorney review before publication as a consumer privacy notice.*
