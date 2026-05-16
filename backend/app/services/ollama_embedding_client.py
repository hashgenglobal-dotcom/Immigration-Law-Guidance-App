"""
Local-only Ollama embedding client for retrieval use.

PRIVACY / SECURITY RULES (must not be loosened without team review):
    * This client only contacts the LOCAL Ollama daemon. It must never be
      pointed at OpenAI, Anthropic, or any public AI API endpoint.
    * Query text is used only to construct the HTTP payload for a single
      request. It is never logged, printed, persisted, or included in
      error messages.
    * This client is RETRIEVAL-ONLY. It embeds queries so that pgvector
      cosine-distance search can be run against pre-embedded public legal
      chunks. It does not generate answers and has no connection to the
      privacy_safe_answer_logs table.
"""

from __future__ import annotations

import httpx

from app.core.config import get_settings

DEFAULT_EMBEDDING_MODEL = "nomic-embed-text"
EXPECTED_EMBEDDING_DIMENSIONS = 768


class EmbeddingClientError(Exception):
    """Raised when the Ollama embedding client cannot produce a valid vector.

    Error messages are intentionally safe: they never include raw query text,
    URL credentials, HTTP response bodies, or Python stack traces.
    """


async def embed_query(
    query: str,
    *,
    model: str = DEFAULT_EMBEDDING_MODEL,
    ollama_base_url: str | None = None,
    timeout_seconds: float = 30.0,
) -> list[float]:
    """Embed a single query string using the local Ollama daemon.

    Parameters
    ----------
    query:
        The text to embed. Whitespace is stripped before the request is
        sent. The raw text is never logged or persisted.
    model:
        Ollama model name. Defaults to ``nomic-embed-text`` (768 dims).
    ollama_base_url:
        Base URL of the local Ollama daemon. Defaults to
        ``settings.ollama_base_url`` (``http://localhost:11434``).
    timeout_seconds:
        Total request timeout in seconds.

    Returns
    -------
    list[float]
        A 768-dimensional embedding vector.

    Raises
    ------
    EmbeddingClientError
        On empty input, network failure, unexpected response shape, or
        wrong embedding dimensions. The message is always privacy-safe.
    """
    stripped = query.strip()
    if not stripped:
        raise EmbeddingClientError("query must not be empty")

    base_url = ollama_base_url or get_settings().ollama_base_url
    endpoint = f"{base_url.rstrip('/')}/api/embed"
    payload = {"model": model, "input": stripped}

    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            response = await client.post(endpoint, json=payload)
            response.raise_for_status()
    except httpx.TimeoutException:
        raise EmbeddingClientError(
            f"Ollama embedding request timed out after {timeout_seconds}s"
        )
    except httpx.HTTPStatusError as exc:
        raise EmbeddingClientError(
            f"Ollama returned HTTP {exc.response.status_code}"
        )
    except httpx.RequestError:
        raise EmbeddingClientError(
            "Ollama is not reachable — ensure the local Ollama daemon is running"
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
        If ``vector`` does not have exactly 768 elements.
    """
    if len(vector) != EXPECTED_EMBEDDING_DIMENSIONS:
        raise EmbeddingClientError(
            f"format_pgvector_literal requires exactly "
            f"{EXPECTED_EMBEDDING_DIMENSIONS} dimensions, got {len(vector)}"
        )
    return "[" + ",".join(str(v) for v in vector) + "]"
