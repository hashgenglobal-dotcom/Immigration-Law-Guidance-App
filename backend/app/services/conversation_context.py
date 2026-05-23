"""In-memory conversation context for multi-turn Ask (never persisted).

Privacy: conversation turns are accepted per request only, trimmed, and passed
to the local Ollama client in memory. They are not logged or written to the DB.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_MAX_TURNS = 6
_MAX_TURN_CHARS = 500
_MAX_TOTAL_CHARS = 2400

_SHORT_ANSWER_HEADER = re.compile(
    r"(?is)short answer:\s*(.*?)(?=\n\s*(?:what this means|typical next steps|official sources|important caution)\s*:|$)"
)


@dataclass(frozen=True)
class ConversationTurn:
    role: str
    content: str


def sanitize_conversation(
    turns: list[dict[str, str]] | None,
) -> list[ConversationTurn]:
    """Normalize and cap client-supplied conversation history."""
    if not turns:
        return []

    out: list[ConversationTurn] = []
    total = 0
    for raw in turns[-_MAX_TURNS:]:
        role = (raw.get("role") or "").strip().lower()
        if role not in ("user", "assistant"):
            continue
        content = (raw.get("content") or "").strip()
        if not content:
            continue
        content = content[:_MAX_TURN_CHARS]
        if total + len(content) > _MAX_TOTAL_CHARS:
            remaining = _MAX_TOTAL_CHARS - total
            if remaining <= 0:
                break
            content = content[:remaining]
        out.append(ConversationTurn(role=role, content=content))
        total += len(content)
    return out


def extract_short_answer_section(answer: str) -> str:
    """Pull the Short answer section for compact assistant context."""
    text = answer.strip()
    if not text:
        return ""
    match = _SHORT_ANSWER_HEADER.search(text)
    if match:
        snippet = match.group(1).strip()
        return snippet[:400] if snippet else text[:400]
    return text[:400]


def format_conversation_block(turns: list[ConversationTurn]) -> str:
    """Plain-text block for the chat model (not for retrieval)."""
    if not turns:
        return ""
    lines: list[str] = []
    for t in turns:
        label = "User" if t.role == "user" else "Assistant"
        lines.append(f"{label}: {t.content}")
    return "\n".join(lines)


def build_retrieval_query(
    message: str,
    conversation: list[ConversationTurn],
    *,
    selected_category: str | None = None,
    category_resolver,
) -> str:
    """Merge thread context into the hybrid retrieval query.

    When a guided-intake category is known, the category template wins.
    """
    if selected_category:
        return category_resolver(message, selected_category)

    message = message.strip()
    if not conversation:
        return message

    prior_user: list[str] = []
    prior_assistant: list[str] = []
    for turn in conversation[:-1] if len(conversation) > 1 else conversation:
        if turn.role == "user":
            prior_user.append(turn.content)
        else:
            prior_assistant.append(turn.content)

    context_bits: list[str] = []
    if prior_user:
        context_bits.append(prior_user[-1])
    if prior_assistant:
        context_bits.append(prior_assistant[-1])
    if context_bits:
        context_bits.append(message)
        combined = " ".join(context_bits)
        return combined[:1200]
    return message
