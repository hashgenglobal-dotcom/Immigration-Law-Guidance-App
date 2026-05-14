# Cloud / Shared Development Database — Plan

**Status:** Draft (planning only — no provider chosen, no resources created)
**Owner:** Backend track on `feature/backend-cloud-foundation`
**Applies to:** Immigration Law Guidance App, development environment only

---

## 1. Purpose

The shared cloud development database exists so the team can collaborate on the same set of **public legal source data** (USCIS / eCFR / INA / Federal Register / BIA) while building ingestion, retrieval, and UI features. It lets multiple developers query a consistent set of chunks, embeddings, and dataset versions without each person re-running the full ingestion pipeline locally.

This database is **explicitly not** a place to put real user questions, real user answers, or any private case facts. Its scope is intentionally narrow: public legal text and the metadata generated from it.

If we ever need to test against real user-style queries, those queries must be processed against a **local** PostgreSQL + local Ollama setup, never against the shared cloud instance.

---

## 2. What can go in the shared cloud dev DB

Allowed content (all of it is either public information, or operational metadata about public information):

- USCIS public source text (Policy Manual, public guidance documents)
- eCFR public regulations (Title 8)
- INA / U.S. Code public sections
- Federal Register public immigration updates
- BIA public decisions
- Citations (e.g., `8 CFR § 208.7(a)`)
- Source URLs for official documents
- Legal chunks derived from the above
- Embeddings of public legal text (vector columns on `legal_chunks`)
- Dataset versions (`dataset_versions`)
- Ingestion job metadata (`ingestion_jobs`)
- Scenario guide templates (generic, non-personal — e.g., "What to do if ICE comes to your door" written as general guidance, not tied to a real person)

All of the above is derived from publicly published sources and is safe to share among developers.

---

## 3. What must NOT go in the shared cloud dev DB

Not allowed — under any circumstances, including for "just testing":

- Real user immigration questions (raw question text)
- Full generated answers produced from real user facts
- Chat logs / conversation transcripts
- Asylum, credible fear, or persecution narratives
- ICE encounter details
- A-numbers (alien registration numbers)
- Passport numbers, visa numbers, I-94 numbers
- Home, work, or family addresses
- Criminal history (charges, convictions, dispositions)
- Uploaded user documents (NTAs, USCIS receipts, court filings, IDs)
- Private case facts (employer names, dates of entry, family member identities, etc.)

If a developer needs to test how a real-sounding query behaves end-to-end, they must do so on a **local** machine against a **local** PostgreSQL + local Ollama. The shared cloud DB never sees that traffic.

`privacy_safe_answer_logs` may exist as a table in the shared DB (it is part of the schema), but in shared-dev it should only ever contain rows generated from synthetic / test queries — never from real users.

---

## 4. Recommended environments

| Environment | Database name | What goes in it | Who connects |
| --- | --- | --- | --- |
| **Local dev** | `immigration_law_dev` | Public legal data + synthetic test traffic + any sensitive query a developer wants to experiment with privately | Single developer, on their machine, via `localhost` |
| **Shared cloud dev** | TBD (e.g., `immigration_law_shared_dev`) | Public legal data only (see §2). Synthetic test traffic allowed. **No real user data.** | All developers on the team via SSL, each with their own credentials |
| **Production** | TBD (separate cluster) | Public legal data + privacy-safe answer-log metadata only. Locked down. Separate VPC / network boundary. Separate credentials. **Not yet provisioned.** | Production app role only. No developer direct access without a documented break-glass process. |

Local and shared-dev share the **same migration**, so a developer can flip `DATABASE_URL` between local and shared-dev without code changes.

Production is intentionally out of scope for this document — it requires a separate privacy review before any data flows.

---

## 5. Provider requirements

This document does not choose a provider. Whichever managed PostgreSQL service we pick (e.g., Neon, Supabase, RDS, Aiven, Azure Database for PostgreSQL, etc.) must meet **all** of the following before we route any traffic at it:

- **PostgreSQL 17 or 18** preferred (matches `database/SETUP_COMPLETE.md`).
- **pgvector** extension available and installable (`CREATE EXTENSION IF NOT EXISTS vector`). The current schema uses `vector(768)` and HNSW indexes, so vector ops must be supported.
- **TLS / SSL required** for all connections. `sslmode=require` (or stricter) in the DSN.
- **Separate database user for the app.** The app role must not be the cluster owner / superuser. A separate admin role handles migrations.
- **Automated backups** enabled, with at least a 7-day point-in-time recovery window for dev.
- **Connection string stored only in `backend/.env` (locally) or in a deployment secret manager** (later, for any hosted backend). Never in source control. Never in chat / tickets / screenshots.
- **No secrets committed to GitHub.** Root `.gitignore` already ignores `.env` and `backend/.env`. Anyone adding a new service must extend the ignore list rather than work around it.
- **Network controls:** allow-listed IPs or a private connection when possible. Public unrestricted access is not acceptable even for dev.

---

## 6. Team workflow

- `main` contains the migration (`database/migrations/001-initial-schema.sql`) and any seed scripts for **public** legal data. `main` is the source of truth for schema.
- Each developer works on feature branches off `main` (e.g., `feature/backend-cloud-foundation`, `feature/ecfr-ingestion`).
- The **shared dev DB schema is created by running the migration**, not by hand-editing tables in a GUI. If a column needs to change, write a new migration file.
- Data should come from **ingestion / seed scripts**, not from manual `INSERT`s in a GUI. This keeps the dataset reproducible.
- **Frontend branches do not modify DB schema.** UI work consumes the API, not the database. If a UI change needs a new column, the backend track adds it via a migration first.
- **Backend branches own schema, ingestion, retrieval, and answer-logging changes.** Any change that touches what data is stored (especially anything that could persist user text) requires a privacy review, not just a code review.

---

## 7. Setup checklist (placeholder)

Concrete steps to fill in once a provider is selected:

- [ ] Create hosted PostgreSQL instance (PG 17 or 18, smallest viable size for dev).
- [ ] Enable the `vector` extension (`CREATE EXTENSION IF NOT EXISTS vector;`).
- [ ] Create the database (e.g., `immigration_law_shared_dev`).
- [ ] Create the application role with least-privilege grants on that database only.
- [ ] Apply the initial migration: `psql "$SHARED_DEV_DSN" -f database/migrations/001-initial-schema.sql`.
- [ ] From a developer machine pointed at the shared DB, run `GET /health/dependencies` and confirm Postgres reports `"status": "ok"`.
- [ ] Run `GET /health/schema` and confirm all 10 required tables are present, including `privacy_safe_answer_logs`.
- [ ] Manually confirm the DB contains **no real user data**: spot-check `privacy_safe_answer_logs` is empty (or contains only synthetic rows), and that no ad-hoc tables holding raw question/answer text exist.
- [ ] Distribute the DSN via the team's secret manager (never via chat, screenshot, or git).

---

## 8. Security notes

- **Rotate credentials immediately if exposed.** If a DSN, password, or service-account credential ends up in chat, a screenshot, a public PR, or a public log, rotate it before anything else. Treat exposure as a security incident, not a paperwork incident.
- **Use a read-only DB user later** for public-facing frontend/testing if we ever need direct DB reads. The application role should write; analytics or read-only clients should not.
- **Do not expose the local Ollama instance to the public internet.** Ollama listens on `localhost:11434` by default and that is where it must stay. The shared DB also must not be reachable from arbitrary IPs.
- **Local / private LLM remains separate from the shared DB.** The Ollama (or future vLLM) host that processes real user questions is not the same machine as the shared dev DB and never connects to it.
- **Real user query processing remains private/local until a production privacy review.** Even when a hosted backend is stood up, real user questions are processed by local/private model infrastructure, and only privacy-safe metadata (hashes, citations used, retrieved chunk IDs, risk level, refusal flag, latency, etc.) is ever persisted — into `privacy_safe_answer_logs`, not into raw-text tables. Full question text and full answer text are not stored by default.

---

## 9. Decision log

| Date | Decision | Reason | Owner |
| --- | --- | --- | --- |
|  |  |  |  |

(Add a new row per decision; do not edit existing rows.)
