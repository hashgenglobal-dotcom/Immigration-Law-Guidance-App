"""Simple in-session Ask memory helpers (request-scoped only; never persisted)."""

from __future__ import annotations

import re
from dataclasses import dataclass

_MAX_TURNS = 4
_MAX_TURN_CHARS = 400
_MAX_TOTAL_CHARS = 1600

_STANDALONE_QUESTION_START = re.compile(
    r"^(how do i|how can i|what is|what are|can i|do i|am i|should i)\b",
    re.I,
)

_FOLLOW_UP_START = re.compile(
    r"^("
    r"what about|what if|how about|and what|also[, ]|"
    r"what is next|what's next|what happens next|"
    r"what documents|which documents|which forms|what form|"
    r"can i travel|what about travel"
    r")\b",
    re.I,
)

_TOPIC_HINTS: tuple[tuple[str, frozenset[str]], ...] = (
    ("opt", frozenset({"opt", "f-1", "f1", "stem", "214.2", "practical training"})),
    ("naturalization", frozenset({"naturalization", "n-400", "n400", "citizen", "citizenship"})),
    ("asylum", frozenset({"asylum", "refugee", "208.7", "i-589"})),
    ("ead", frozenset({"ead", "i-765", "765", "employment authorization", "work authorization"})),
    ("green_card", frozenset({"green card", "i-485", "adjustment of status", "permanent resident"})),
    ("nta", frozenset({"notice to appear", "nta", "removal", "immigration court"})),
)

_SHORT_ANSWER_HEADER = re.compile(
    r"(?is)short answer:\s*(.*?)(?=\n\s*(?:what this means|typical next steps|official sources|important caution)\s*:|$)"
)


@dataclass(frozen=True)
class ConversationTurn:
    role: str
    content: str


def sanitize_conversation(turns: list[dict[str, str]] | None) -> list[ConversationTurn]:
    """Normalize and cap client-supplied visible turns."""
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


def extract_short_answer_snippet(answer: str) -> str:
    text = answer.strip()
    if not text:
        return ""
    match = _SHORT_ANSWER_HEADER.search(text)
    if match:
        return match.group(1).strip()[:300]
    return text[:300]


def _last_user_turn(turns: list[ConversationTurn]) -> str | None:
    for turn in reversed(turns):
        if turn.role == "user":
            return turn.content
    return None


def _topic_keys(text: str) -> set[str]:
    lower = text.lower()
    keys: set[str] = set()
    for key, words in _TOPIC_HINTS:
        if any(w in lower for w in words):
            keys.add(key)
    return keys


def is_likely_follow_up(message: str) -> bool:
    """Short or referential messages that may need prior visible context."""
    text = message.strip()
    if not text:
        return False
    if len(text) > 120:
        return False
    if _FOLLOW_UP_START.search(text):
        return True
    if _STANDALONE_QUESTION_START.search(text):
        return False
    word_count = len(text.split())
    if word_count <= 5 and len(text) < 40:
        return True
    return False


def is_new_topic_shift(current_message: str, prior_user_message: str | None) -> bool:
    """True when the current message should not inherit the prior thread topic."""
    current = current_message.strip()
    if not prior_user_message:
        return True
    if len(current) > 100:
        return True
    current_topics = _topic_keys(current)
    prior_topics = _topic_keys(prior_user_message)
    if current_topics and prior_topics and not current_topics.intersection(prior_topics):
        return True
    return False


def should_use_conversation_context(
    message: str,
    turns: list[ConversationTurn],
) -> bool:
    if not turns:
        return False
    if not is_likely_follow_up(message):
        return False
    prior = _last_user_turn(turns)
    if is_new_topic_shift(message, prior):
        return False
    return True


def build_retrieval_query(
    message: str,
    turns: list[ConversationTurn],
    *,
    category_query: str | None = None,
) -> str:
    """Build hybrid retrieval query; current message always leads."""
    message = message.strip()
    if category_query:
        return category_query
    if not should_use_conversation_context(message, turns):
        return message
    prior = _last_user_turn(turns)
    if not prior:
        return message
    return f"{message} (brief context from prior question: {prior[:150]})"[:1200]


def format_conversation_for_prompt(turns: list[ConversationTurn]) -> str:
    if not turns:
        return ""
    lines: list[str] = []
    for t in turns:
        label = "User" if t.role == "user" else "Assistant"
        lines.append(f"{label}: {t.content}")
    return "\n".join(lines)
