"""Plain-language summary generation for Official Updates (local LLM only)."""

from __future__ import annotations

import json
import re

from app.core.config import Settings
from app.services.ollama_chat_client import OllamaChatClient, OllamaChatClientError

_SUMMARY_SYSTEM = (
    "You summarize U.S. government immigration announcements for the public.\n"
    "Rules:\n"
    "- Use ONLY facts stated in the provided excerpt. Do not guess or add legal advice.\n"
    "- Write exactly 3 bullet points.\n"
    "- Use plain language at roughly a 6th-grade reading level.\n"
    "- Each bullet is one short sentence.\n"
    "- If the excerpt is too thin, say 'See the official release for full details.' in a bullet.\n"
    "- Do not use words like 'you should' or 'we recommend'.\n"
    "Respond with JSON only: {\"bullets\": [\"...\", \"...\", \"...\"]}"
)


def _fallback_bullets(title: str, publisher: str) -> list[str]:
    return [
        f"{publisher.replace('_', ' ').title()} posted an official announcement.",
        title[:200] + ("…" if len(title) > 200 else ""),
        "Open the official release link for complete details.",
    ]


def _parse_bullets_from_response(text: str) -> list[str] | None:
    text = text.strip()
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None
    try:
        data = json.loads(match.group())
        bullets = data.get("bullets")
        if isinstance(bullets, list) and len(bullets) >= 1:
            cleaned = [str(b).strip() for b in bullets if str(b).strip()][:3]
            while len(cleaned) < 3:
                cleaned.append("See the official release for full details.")
            return cleaned[:3]
    except json.JSONDecodeError:
        return None
    return None


async def generate_summary_bullets(
    *,
    settings: Settings,
    title: str,
    publisher: str,
    raw_excerpt: str | None,
    chat_client: OllamaChatClient | None = None,
) -> tuple[list[str], str | None]:
    """Return (bullets, model_name) or fallback on failure."""
    excerpt = (raw_excerpt or title).strip()[:4000]
    if len(excerpt) < 40:
        return _fallback_bullets(title, publisher), None

    client = chat_client or OllamaChatClient()
    user_msg = (
        f"Publisher: {publisher}\n"
        f"Title: {title}\n\n"
        f"Excerpt from official release:\n{excerpt}"
    )
    model = settings.ollama_chat_model
    try:
        raw = await client.generate_chat_response(
            messages=[
                {"role": "system", "content": _SUMMARY_SYSTEM},
                {"role": "user", "content": user_msg},
            ],
            model=model,
            ollama_base_url=settings.ollama_chat_base_url or settings.ollama_base_url,
            ollama_api_key=settings.ollama_api_key,
        )
        bullets = _parse_bullets_from_response(raw)
        if bullets:
            return bullets, model
    except OllamaChatClientError:
        pass
    return _fallback_bullets(title, publisher), None
