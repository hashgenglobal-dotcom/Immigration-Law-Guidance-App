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


class ConversationTurn(BaseModel):
    """Visible Ask turn sent for one request only (never stored server-side)."""

    role: str = Field(..., description="user or assistant")
    content: str = Field(..., min_length=1, max_length=400)

    @field_validator("role", mode="before")
    @classmethod
    def normalize_role(cls, v: object) -> str:
        if not isinstance(v, str):
            raise ValueError("role must be a string")
        role = v.strip().lower()
        if role not in ("user", "assistant"):
            raise ValueError("role must be user or assistant")
        return role

    @field_validator("content", mode="before")
    @classmethod
    def strip_content(cls, v: object) -> str:
        if not isinstance(v, str):
            raise ValueError("content must be a string")
        stripped = v.strip()
        if not stripped:
            raise ValueError("content must not be empty")
        return stripped


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
    selected_category: str | None = Field(
        default=None,
        max_length=64,
        description=(
            "Optional legacy category hint. Not required for normal Ask. "
            "Never persisted server-side."
        ),
    )
    conversation: list[ConversationTurn] = Field(
        default_factory=list,
        max_length=4,
        description=(
            "Optional prior visible turns from the current session only. "
            "Processed in memory for follow-up disambiguation; never stored."
        ),
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


class ClarificationOption(BaseModel):
    label: str = Field(..., description="Display label for a clarification chip/button.")
    value: str = Field(..., description="Machine-readable category value for the next request.")


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
    status: str = Field(
        default="ok",
        description="ok | needs_clarification",
    )
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
    clarifying_question: str | None = Field(
        None,
        description="Follow-up question when status is needs_clarification.",
    )
    options: list[ClarificationOption] | None = Field(
        None,
        description="Selectable categories when status is needs_clarification.",
    )
    used_chunks: list[ChatUsedChunk] = Field(default_factory=list)


class ChatErrorResponse(BaseModel):
    status: str = Field(default="error")
    error_code: str = Field(..., description="Machine-readable error identifier.")
    message: str = Field(..., description="Human-readable error description.")
    # Always included so clients can confirm privacy posture even on error.
    privacy_mode: str = Field(default="local-first")
