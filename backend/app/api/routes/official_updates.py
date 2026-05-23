"""Official Updates routes — government announcement feed."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.config import Settings, get_settings
from app.schemas.official_updates import (
    OfficialUpdateDetail,
    OfficialUpdateDetailResponse,
    OfficialUpdatesListResponse,
    UpdateTopicsResponse,
)
from app.services.official_updates_service import (
    OfficialUpdatesNotReadyError,
    get_update,
    list_topics,
    list_updates,
)

router = APIRouter(prefix="/api/updates", tags=["official-updates"])


def _not_ready(exc: OfficialUpdatesNotReadyError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={
            "status": "error",
            "error_code": "UPDATES_NOT_READY",
            "message": str(exc),
            "privacy_mode": "local-first",
        },
    )


@router.get("/topics", response_model=UpdateTopicsResponse)
async def get_topics() -> UpdateTopicsResponse:
    topics = await list_topics()
    return UpdateTopicsResponse(topics=topics)


@router.get("", response_model=OfficialUpdatesListResponse)
async def get_updates_list(
    topics: str | None = Query(
        default=None,
        description="Comma-separated topic ids (e.g. f1_j1,h1b). Omit for all official updates.",
    ),
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    settings: Settings = Depends(get_settings),
) -> OfficialUpdatesListResponse:
    try:
        data = await list_updates(settings, topics=topics, limit=limit, offset=offset)
    except OfficialUpdatesNotReadyError as exc:
        raise _not_ready(exc) from exc
    return OfficialUpdatesListResponse(**data)


@router.get("/{update_id}", response_model=OfficialUpdateDetailResponse)
async def get_update_detail(
    update_id: int,
    settings: Settings = Depends(get_settings),
) -> OfficialUpdateDetailResponse:
    try:
        row = await get_update(settings, update_id)
    except OfficialUpdatesNotReadyError as exc:
        raise _not_ready(exc) from exc

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "status": "error",
                "error_code": "UPDATE_NOT_FOUND",
                "message": "Official update not found.",
                "privacy_mode": "local-first",
            },
        )

    item = OfficialUpdateDetail(
        **{k: v for k, v in row.items() if k != "raw_excerpt"},
        raw_excerpt=row.get("raw_excerpt"),
    )
    return OfficialUpdateDetailResponse(item=item)
