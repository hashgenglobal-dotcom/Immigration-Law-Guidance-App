# POST-10 — BIA decisions v2 (blocked)

Official DOJ/EOIR bulk source is not available. See:

- `review/04-bia-decisions-challenge-report.md`

**Do not ingest synthetic case law.**

When a source is confirmed:

1. Add ingest script under `review/scripts/`
2. Register dataset in `source_registry`
3. Re-run `review/scripts/run_rag_eval.py` with case-law queries

Placeholder script: `review/scripts/bia_v2_placeholder.py`
