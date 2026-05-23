# Ask conversation — Phase 1 (`feature/ask-conversation`)

## What shipped

- **In-session thread:** Mobile sends up to 6 prior turns on `POST /api/chat` (`conversation[]`). Not stored in the database.
- **Retrieval rewrite:** Follow-up questions merge recent user/assistant context into the hybrid search query.
- **Model context:** Prior turns appear in the prompt under “Conversation so far”; legal facts still come only from retrieved chunks.
- **Typed clarification:** Users can type e.g. “F-1 OPT” instead of tapping chips; maps to `selected_category` server-side.
- **Softer clarification copy:** Natural lead-in question on broad topics.
- **New conversation:** Clears thread on device only.

## API

```json
{
  "message": "Can I travel?",
  "top_k": 5,
  "selected_category": null,
  "conversation": [
    { "role": "user", "content": "I'm on F-1 OPT" },
    { "role": "assistant", "content": "Optional Practical Training allows..." }
  ]
}
```

## Privacy

Unchanged: no full Q&A persistence; context is request-scoped + mobile memory only.

## Phase 2 (same branch)

- **`suggested_followups`** on `ChatResponse` (max 3), derived from retrieved chunk metadata only.
- Mobile **Continue the conversation** chips under the latest answer; tap sends the next message with thread context.

## Next (Phase 3–4)

Streaming, collapse technical metadata in UI, optional warmer bubble layout.
