"""Retrieval route — POST /api/retrieve.

Exposes hybrid vector+keyword retrieval over active public legal_chunks
as a FastAPI endpoint.

PRIVACY / SECURITY RULES (must not be loosened without team review):
    * Raw query text is processed in memory only and never written to
      any database table or log.
    * Only a SHA-256 hash of the lowercased, stripped query is included
      in the response — for future hash-only audit metadata if needed.
    * Retrieval only: no answer generation, no LLM chat, no writes to
      privacy_safe_answer_logs, no public AI APIs.
    * Error messages never echo the user's query.
"""

from __future__ import annotations

import hashlib

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status

from app.api.deps.rate_limit import enforce_retrieve_rate_limit
from app.core.config import Settings, get_settings
from app.schemas.retrieval import RetrievalRequest, RetrievalResponse
from app.services.ollama_embedding_client import EmbeddingClientError
from app.services.retrieval_service import RetrievalService

router = APIRouter(tags=["retrieval"])


@router.post(
    "/api/retrieve",
    response_model=RetrievalResponse,
    summary="Hybrid retrieval over active public legal chunks",
    description=(
        "Embed the query locally with Ollama nomic-embed-text, run hybrid "
        "vector+keyword search (pgvector cosine distance + plainto_tsquery + "
        "Reciprocal Rank Fusion) over active legal_chunks, and return ranked "
        "citation results. Retrieval only — no answer generation, no LLM chat, "
        "no public AI APIs. Raw query text is never stored."
    ),
)
async def retrieve_hybrid(
    body: RetrievalRequest,
    settings: Settings = Depends(get_settings),
    _rate_limit: None = Depends(enforce_retrieve_rate_limit),
) -> RetrievalResponse:
    """Run hybrid retrieval and return ranked legal chunk citations.

    The raw query is processed in memory and never written to any table.
    Only a one-way SHA-256 hash of the lowercased, stripped query appears
    in the response for potential future hash-only audit use.

    Errors never include the raw query, the database DSN, or stack traces.
    """
    # Hash computed in memory only — never persisted anywhere.
    query_hash = hashlib.sha256(body.query.lower().strip().encode()).hexdigest()

    service = RetrievalService(settings)

    try:
        results, active_dataset = await service.retrieve_hybrid(
            query=body.query,
            top_k=body.top_k,
        )
    except EmbeddingClientError:
        # Ollama is unreachable or returned an unexpected response.
        # Raw query is not echoed in this error.
        raise HTTPException(
            status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "error",
                "error_code": "OLLAMA_UNAVAILABLE",
                "message": (
                    "Local embedding service is not available. "
                    "Ensure Ollama is running: ollama serve"
                ),
                "privacy_mode": "local-first",
            },
        )
    except Exception:
        # Database config error or query failure.
        # Raw query and DSN are not echoed in this error.
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "error_code": "RETRIEVAL_ERROR",
                "message": "An internal error occurred during retrieval.",
                "privacy_mode": "local-first",
            },
        )

    return RetrievalResponse(
        query_hash=query_hash,
        top_k=body.top_k,
        active_dataset=active_dataset,
        results=results,
    )
