# Post-MVP integration branch

All post-MVP tasks (POST-00 … POST-11) are developed on the **`post-mvp`** git branch.

| ID | Task | Path / branch artifact |
|----|------|------------------------|
| POST-00 | Roadmap | `docs/post-mvp-roadmap.md` |
| POST-01 | Privacy policy | `docs/privacy-data-retention-policy.md` |
| POST-02 | Legal review process | `docs/legal-review-process.md` |
| POST-03 | Rate limiting | `backend/app/services/rate_limit_service.py` |
| POST-04 | Production auth | `backend/app/api/routes/auth.py`, `database/migrations/002-app-users.sql` |
| POST-05 | Legal guardrails | `backend/app/services/legal_guardrails.py` |
| POST-06 | Observability | `backend/app/middleware/request_context.py` |
| POST-07 | Production deploy | `infra/`, `docs/production-deployment.md` |
| POST-08 | RAG eval suite | `review/scripts/run_rag_eval.py` |
| POST-09 | Admin API | `backend/app/api/routes/admin.py` |
| POST-10 | BIA v2 (blocked) | `post-mvp/tasks/10-bia/` |
| POST-11 | Web v2 (deferred) | `post-mvp/tasks/11-web/` |

**Review:** Rishi merges to `main` after MVP stack is integrated and tests pass.

**Status:** See `post-mvp/STATUS.md`.
