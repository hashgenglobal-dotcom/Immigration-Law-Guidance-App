"""
Local-only Ollama chat client for answer generation.

PRIVACY / SECURITY RULES (must not be loosened without team review):
    * This client only contacts the LOCAL Ollama daemon. It must never be
      pointed at any public AI API endpoint.
    * Message content is used only to construct the HTTP payload for a
      single request. It is never logged, printed, persisted, or included
      in error messages.
    * This client is CHAT-ONLY. It does not perform retrieval, does not
      build legal prompts, and has no connection to privacy_safe_answer_logs.
    * Error messages are intentionally generic. They never include raw
      message content, model response bodies, credentials, or local paths.
"""

from __future__ import annotations

import httpx

from app.core.config import get_settings

DEFAULT_CHAT_MODEL = "llama3.1:8b"
DEFAULT_CHAT_TIMEOUT_SECONDS = 60

_VALID_ROLES = frozenset({"system", "user", "assistant"})


class OllamaChatClientError(Exception):
    """Raised when the Ollama chat client cannot produce a valid response.

    Error messages are intentionally safe: they never include raw message
    content, model response bodies, credentials, local paths, or stack traces.
    """


class OllamaChatClient:
    """Local-only async Ollama chat completion client.

    Contacts only the local Ollama daemon at OLLAMA_BASE_URL. Does not
    perform retrieval, does not build legal prompts, and does not write
    to any database table.

    Parameters
    ----------
    ollama_base_url:
        Base URL of the local Ollama daemon. Defaults to
        ``settings.ollama_base_url`` (``http://localhost:11434``) when
        neither this argument nor the per-call override is provided.
    """

    def __init__(self, ollama_base_url: str | None = None) -> None:
        self._ollama_base_url = ollama_base_url

    async def generate_chat_response(
        self,
        *,
        messages: list[dict[str, str]],
        model: str = DEFAULT_CHAT_MODEL,
        ollama_base_url: str | None = None,
        timeout_seconds: int = DEFAULT_CHAT_TIMEOUT_SECONDS,
        temperature: float = 0.2,
    ) -> str:
        """Send a chat completion request to the local Ollama daemon.

        Parameters
        ----------
        messages:
            Ordered list of message dicts. Each must have ``role``
            (one of ``system``, ``user``, ``assistant``) and ``content``
            (non-empty string). Content is never logged or persisted.
        model:
            Local Ollama model name. Defaults to ``llama3.1:8b``.
        ollama_base_url:
            Per-call override for the Ollama base URL. Takes priority over
            the instance value and ``settings.ollama_base_url``.
        timeout_seconds:
            Total request timeout in seconds.
        temperature:
            Sampling temperature forwarded to Ollama options
            (lower = more deterministic output).

        Returns
        -------
        str
            Stripped assistant reply content from the Ollama response.

        Raises
        ------
        OllamaChatClientError
            On invalid messages, network failure, unexpected response shape,
            or empty model reply. The message is always privacy-safe.
        """
        self._validate_messages(messages)

        base_url = ollama_base_url or self._ollama_base_url or get_settings().ollama_base_url
        endpoint = f"{base_url.rstrip('/')}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }

        try:
            async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                response = await client.post(endpoint, json=payload)
                response.raise_for_status()
        except httpx.TimeoutException:
            raise OllamaChatClientError(
                f"Ollama chat request timed out after {timeout_seconds}s"
            )
        except httpx.HTTPStatusError as exc:
            raise OllamaChatClientError(
                f"Ollama returned HTTP {exc.response.status_code}"
            )
        except httpx.RequestError:
            raise OllamaChatClientError(
                "Ollama is not reachable — ensure the local Ollama daemon is running"
            )

        try:
            data = response.json()
        except Exception:
            raise OllamaChatClientError("Ollama response was not valid JSON")

        try:
            content = data["message"]["content"]
        except (KeyError, TypeError):
            raise OllamaChatClientError(
                "Ollama response missing expected 'message.content' field"
            )

        if not isinstance(content, str) or not content.strip():
            raise OllamaChatClientError(
                "Ollama returned an empty or non-string response content"
            )

        return content.strip()

    @staticmethod
    def _validate_messages(messages: list[dict[str, str]]) -> None:
        """Validate the messages list structure before sending to Ollama.

        Raises OllamaChatClientError for structural problems only.
        Message content is never included in error text.
        """
        if not isinstance(messages, list) or len(messages) == 0:
            raise OllamaChatClientError("messages must be a non-empty list")

        for index, item in enumerate(messages):
            if not isinstance(item, dict):
                raise OllamaChatClientError(
                    f"messages[{index}] must be a dict with 'role' and 'content'"
                )
            role = item.get("role")
            if role not in _VALID_ROLES:
                raise OllamaChatClientError(
                    f"messages[{index}].role must be one of: system, user, assistant"
                )
            content = item.get("content")
            if not isinstance(content, str) or not content.strip():
                raise OllamaChatClientError(
                    f"messages[{index}].content must be a non-empty string"
                )
