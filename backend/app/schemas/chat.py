"""
Pydantic v2 schemas for the chat API (POST /api/chat).

Chat-only: these models represent the request and response for the
local-LLM answer-generation endpoint. The raw user message lives in
memory for the duration of a single request and is never written to
any database table.

query_hash (SHA-256 of lowercased, stripped message) is included in
the response so that future audit logs can reference queries by hash
only, without persisting the original text.

No raw message, no raw prompt, no chat history, and no user identity
fields appear in any response model. privacy_safe_answer_logs is not
written to by these schemas.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description=(
            "User question to answer using retrieved public legal chunks. "
            "Raw message text is processed in memory only and must not be stored."
        ),
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Number of hybrid-ranked chunks to retrieve and use for answer generation (1–10).",
    )

    @field_validator("message", mode="before")
    @classmethod
    def strip_and_require_nonempty(cls, v: object) -> str:
        if not isinstance(v, str):
            raise ValueError("message must be a string")
        stripped = v.strip()
        if not stripped:
            raise ValueError("message must not be empty or whitespace-only")
        return stripped


class ChatCitation(BaseModel):
    citation: str = Field(..., description="CFR/INA citation string, e.g. '8 CFR § 208.7'.")
    official_url: str | None = Field(None, description="Canonical URL for the source section.")
    topic: str | None = None
    subtopic: str | None = None
    risk_level: str | None = None


class ChatUsedChunk(BaseModel):
    rank: int = Field(..., description="1-based position in the hybrid-ranked result list.")
    chunk_id: int
    citation: str = Field(..., description="CFR/INA citation string, e.g. '8 CFR § 208.7'.")
    official_url: str | None = Field(None, description="Canonical URL for the source section.")
    topic: str | None = None
    subtopic: str | None = None
    risk_level: str | None = None
    hybrid_score: float = Field(..., description="Reciprocal Rank Fusion score (higher = more relevant).")
    snippet: str = Field(..., description="Up to 500-character excerpt from the chunk content.")
    dataset_version: str | None = Field(
        None,
        description="Dataset version name for this chunk.",
    )
    source_family: str | None = Field(
        None,
        description="MVP source family for this chunk.",
    )


class ChatResponse(BaseModel):
    status: str = Field(default="ok")
    # Static field present in every response — signals that no data was sent
    # to any public AI API and all processing ran on the local machine.
    privacy_mode: str = Field(default="local-first")
    # SHA-256(message.lower().strip()) — allows future hash-only audit metadata
    # without storing the original message text.
    query_hash: str
    answer: str = Field(..., description="Plain-language legal information grounded in retrieved chunks.")
    citations: list[ChatCitation]
    disclaimer: str = Field(
        ...,
        description=(
            "Legal disclaimer included in every response. States that this is "
            "general legal information only, not legal advice, and does not "
            "create an attorney-client relationship."
        ),
    )
    active_dataset: str | None = Field(
        None,
        description="Summary of dataset versions searched (backward-compatible string).",
    )
    active_datasets: list[str] = Field(
        default_factory=list,
        description="All dataset_versions with status='active' included in search.",
    )
    mvp_sources: list[str] = Field(
        default_factory=list,
        description="Deduplicated MVP source families (eCFR, INA, USCIS PM).",
    )
    used_chunks: list[ChatUsedChunk]


class ChatErrorResponse(BaseModel):
    status: str = Field(default="error")
    error_code: str = Field(..., description="Machine-readable error identifier.")
    message: str = Field(..., description="Human-readable error description.")
    # Always included so clients can confirm privacy posture even on error.
    privacy_mode: str = Field(default="local-first")
