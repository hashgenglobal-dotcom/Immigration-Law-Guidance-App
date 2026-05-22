"""Pydantic schemas for Official Updates API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class UpdateTopicSchema(BaseModel):
    id: str
    label: str
    description: str


class OfficialUpdateItem(BaseModel):
    id: int
    publisher: str
    title: str
    official_url: str
    published_at: str
    summary_bullets: list[str]
    topic_tags: list[str]
    topic_labels: list[str]
    fetched_at: str
    has_official_excerpt: bool = False


class OfficialUpdateDetail(OfficialUpdateItem):
    raw_excerpt: str | None = None
    ask_prefill_message: str = Field(
        ...,
        description="Suggested question for Ask bridge (not stored server-side).",
    )


class OfficialUpdatesListResponse(BaseModel):
    status: str = "ok"
    privacy_mode: str = "local-first"
    items: list[OfficialUpdateItem]
    count: int
    total: int
    limit: int
    offset: int
    topics_filter: list[str] = Field(default_factory=list)


class OfficialUpdateDetailResponse(BaseModel):
    status: str = "ok"
    privacy_mode: str = "local-first"
    item: OfficialUpdateDetail


class UpdateTopicsResponse(BaseModel):
    status: str = "ok"
    topics: list[UpdateTopicSchema]
