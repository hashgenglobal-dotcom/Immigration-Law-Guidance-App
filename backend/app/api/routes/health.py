"""Health-check route.

Exposes `GET /health` so deployment platforms and local developers can
verify the service is up. The response intentionally contains only
non-sensitive metadata (app name, environment, privacy mode). It does
NOT include database credentials, secrets, or any user data.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.config import Settings, get_settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Schema for the `/health` payload."""

    status: str
    app_name: str
    environment: str
    privacy_mode: str


@router.get("/health", response_model=HealthResponse, summary="Service health check")
def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Return a small, privacy-safe status payload.

    The `privacy_mode` field is always `"local-first"` to make the
    operating model explicit to anyone hitting this endpoint: real
    user questions must be processed by local/private infrastructure
    only, and full question/answer text must not be stored by default.
    """
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        environment=settings.app_env,
        privacy_mode="local-first",
    )
