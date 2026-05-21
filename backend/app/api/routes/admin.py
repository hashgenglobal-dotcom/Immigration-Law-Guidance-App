"""Admin read-only API (POST-09). Requires auth."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps.auth import get_current_user_required
from app.core.config import Settings, get_settings
from app.schemas.auth import AuthUserResponse
from app.services.admin_service import list_dataset_summary, source_registry_summary

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/datasets")
async def admin_datasets(
    _user: AuthUserResponse = Depends(get_current_user_required),
    settings: Settings = Depends(get_settings),
) -> dict:
    summary = await list_dataset_summary(settings)
    return {"status": "ok", **summary, "privacy_mode": "local-first"}


@router.get("/sources")
async def admin_sources(
    _user: AuthUserResponse = Depends(get_current_user_required),
    settings: Settings = Depends(get_settings),
) -> dict:
    sources = await source_registry_summary(settings)
    return {"status": "ok", "sources": sources, "privacy_mode": "local-first"}
