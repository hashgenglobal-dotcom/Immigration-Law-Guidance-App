# Legal safety guardrails (POST-05)

`legal_guardrails.py` runs **before** retrieval/LLM on `POST /api/chat`.

## Blocked categories

- Fraud or misrepresentation on applications
- Evasion of immigration law, fake documents, avoiding court

## Privacy

- Refusal responses do not log raw message text
- `query_hash` only in API response

## Review

Update patterns after attorney review per `docs/legal-review-process.md`.
