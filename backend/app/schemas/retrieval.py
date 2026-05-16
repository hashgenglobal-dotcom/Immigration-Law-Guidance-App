"""
Pydantic v2 schemas for the retrieval API (POST /api/retrieve).

Retrieval-only: these models represent the request and response for hybrid
vector+keyword search over public legal chunks. No raw query text is stored
anywhere — the query field lives in memory for the duration of a single
request and is never written to any database table.

query_hash (SHA-256 of lowercased, stripped query) is included in the
response so that future audit logs can reference queries by hash only,
without persisting the original text.

No answer generation, no LLM calls, and no writes to privacy_safe_answer_logs
are represented by these schemas.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class RetrievalRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description=(
            "Synthetic or user-provided question to retrieve relevant public "
            "legal chunks for. Raw query text is processed in memory only and "
            "must not be stored."
        ),
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Number of hybrid-ranked results to return (1–10).",
    )

    @field_validator("query", mode="before")
    @classmethod
    def strip_and_require_nonempty(cls, v: object) -> str:
        if not isinstance(v, str):
            raise ValueError("query must be a string")
        stripped = v.strip()
        if not stripped:
            raise ValueError("query must not be empty or whitespace-only")
        return stripped


class RetrievalResult(BaseModel):
    rank: int = Field(..., description="1-based position in the hybrid-ranked result list.")
    chunk_id: int
    citation: str = Field(..., description="CFR/INA citation string, e.g. '8 CFR § 208.7'.")
    official_url: str | None = Field(None, description="Canonical URL for the source section.")
    topic: str
    subtopic: str | None = None
    risk_level: str | None = None
    hybrid_score: float = Field(..., description="Reciprocal Rank Fusion score (higher = more relevant).")
    vector_rank: int | None = Field(None, description="Rank from pgvector cosine-distance search, if present.")
    keyword_rank: int | None = Field(None, description="Rank from PostgreSQL full-text search, if present.")
    vector_distance: float | None = Field(None, description="Cosine distance (lower = more similar).")
    keyword_score: float | None = Field(None, description="ts_rank_cd score from full-text search.")
    snippet: str = Field(..., description="Up to 500-character excerpt from the chunk content.")


class RetrievalResponse(BaseModel):
    status: str = Field(default="ok")
    # Static field present in every response — signals that no data was sent
    # to any public AI API and all processing ran on the local machine.
    privacy_mode: str = Field(default="local-first")
    # SHA-256(query.lower().strip()) — allows future hash-only audit metadata
    # without storing the original query text.
    query_hash: str
    top_k: int
    active_dataset: str | None = Field(
        None,
        description="Name of the currently active dataset version that was searched.",
    )
    results: list[RetrievalResult]


class RetrievalErrorResponse(BaseModel):
    status: str = Field(default="error")
    error_code: str = Field(..., description="Machine-readable error identifier.")
    message: str = Field(..., description="Human-readable error description.")
    # Always included so clients can confirm privacy posture even on error.
    privacy_mode: str = Field(default="local-first")
