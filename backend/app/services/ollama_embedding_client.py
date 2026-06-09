"""
Ollama embedding client for retrieval use (local daemon or Ollama Cloud).

PRIVACY / SECURITY RULES (must not be loosened without team review):
    * This client contacts the Ollama endpoint configured via OLLAMA_BASE_URL.
      It must never be pointed at OpenAI, Anthropic, or any other public AI
      API endpoint.
    * Query text is used only to construct the HTTP payload for a single
      request. It is never logged, printed, persisted, or included in
      error messages.
    * The API key (when present) is sent only in the Authorization header.
      It is never logged, printed, or included in error messages.
    * This client is RETRIEVAL-ONLY. It embeds queries so that pgvector
      cosine-distance search can be run against pre-embedded public legal
      chunks. It does not generate answers and has no connection to the
      privacy_safe_answer_logs table.
"""

from __future__ import annotations

import httpx

from app.core.config import get_settings

DEFAULT_EMBEDDING_MODEL = "mxbai-embed-large"
EXPECTED_EMBEDDING_DIMENSIONS = 1024


class EmbeddingClientError(Exception):
    """Raised when the Ollama embedding client cannot produce a valid vector.

    Error messages are intentionally safe: they never include raw query text,
    URL credentials, HTTP response bodies, or Python stack traces.
    """


async def embed_query(
    query: str,
    *,
    model: str | None = None,
    ollama_base_url: str | None = None,
    ollama_api_key: str | None = None,
    timeout_seconds: float = 120.0,
) -> list[float]:
    """Embed a single query string using Ollama (local daemon or Ollama Cloud).

    Parameters
    ----------
    query:
        The text to embed. Whitespace is stripped before the request is
        sent. The raw text is never logged or persisted.
    model:
        Ollama model name. Defaults to ``settings.ollama_embed_model``
        (``mxbai-embed-large``, 1024 dims). Pass an explicit value to
        override the settings default.
    ollama_base_url:
        Ollama endpoint. Defaults to ``settings.ollama_base_url``.
        Set ``OLLAMA_BASE_URL=https://ollama.com`` for Ollama Cloud.
    ollama_api_key:
        Optional bearer credential for Ollama Cloud or private
        authenticated endpoints. When provided, sent as
        ``Authorization: Bearer <key>``. Never logged or included in
        error messages.
    timeout_seconds:
        Total request timeout in seconds.

    Returns
    -------
    list[float]
        A 1024-dimensional embedding vector.

    Raises
    ------
    EmbeddingClientError
        On empty input, network failure, unexpected response shape, or
        wrong embedding dimensions. The message is always privacy-safe.
    """
    stripped = query.strip()
    if not stripped:
        raise EmbeddingClientError("query must not be empty")

    settings = get_settings()
    base_url = ollama_base_url or settings.ollama_base_url
    resolved_model = model or settings.ollama_embed_model
    endpoint = f"{base_url.rstrip('/')}/api/embed"
    payload = {"model": resolved_model, "input": stripped}

    headers: dict[str, str] = {}
    if ollama_api_key:
        headers["Authorization"] = f"Bearer {ollama_api_key}"

    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            response = await client.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()
    except httpx.TimeoutException:
        raise EmbeddingClientError(
            f"Embedding request timed out after {timeout_seconds}s"
        )
    except httpx.HTTPStatusError as exc:
        raise EmbeddingClientError(
            f"Embedding service returned HTTP {exc.response.status_code}"
        )
    except httpx.RequestError:
        raise EmbeddingClientError(
            "Embedding service is not reachable — check OLLAMA_BASE_URL and network connectivity"
        )

    try:
        data = response.json()
    except Exception:
        raise EmbeddingClientError("Ollama response was not valid JSON")

    embeddings = data.get("embeddings")
    if not isinstance(embeddings, list) or len(embeddings) == 0:
        raise EmbeddingClientError(
            "Ollama response missing 'embeddings' list"
        )

    first = embeddings[0]
    if not isinstance(first, list):
        raise EmbeddingClientError(
            "Ollama 'embeddings[0]' is not a list"
        )

    if not all(isinstance(v, (int, float)) for v in first):
        raise EmbeddingClientError(
            "Ollama embedding contains non-numeric values"
        )

    if len(first) != EXPECTED_EMBEDDING_DIMENSIONS:
        raise EmbeddingClientError(
            f"Expected {EXPECTED_EMBEDDING_DIMENSIONS}-dimensional embedding, "
            f"got {len(first)}"
        )

    return [float(v) for v in first]


def format_pgvector_literal(vector: list[float]) -> str:
    """Format a float vector as a pgvector string literal.

    The returned string can be used directly in a psycopg query as the
    value for a ``::vector`` cast, e.g.::

        cursor.execute(
            "SELECT ... FROM legal_chunks WHERE embedding <-> %s::vector ...",
            (format_pgvector_literal(vec),),
        )

    Parameters
    ----------
    vector:
        A list of floats with exactly ``EXPECTED_EMBEDDING_DIMENSIONS`` elements.

    Returns
    -------
    str
        A bracket-enclosed, comma-separated literal such as ``[0.1,-0.2,0.3]``.

    Raises
    ------
    EmbeddingClientError
        If ``vector`` does not have exactly 1024 elements.
    """
    if len(vector) != EXPECTED_EMBEDDING_DIMENSIONS:
        raise EmbeddingClientError(
            f"format_pgvector_literal requires exactly "
            f"{EXPECTED_EMBEDDING_DIMENSIONS} dimensions, got {len(vector)}"
        )
    return "[" + ",".join(str(v) for v in vector) + "]"
