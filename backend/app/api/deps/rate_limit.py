"""FastAPI dependencies for rate limiting."""

from __future__ import annotations

from fastapi import Depends, Request

from app.core.config import Settings, get_settings
from app.services.rate_limit_service import (
    RateLimitExceeded,
    check_rate_limit,
    rate_limit_http_exception,
)


async def enforce_chat_rate_limit(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> None:
    try:
        await check_rate_limit(
            settings=settings,
            request=request,
            endpoint="chat",
            limit_per_minute=settings.rate_limit_chat_per_minute,
        )
    except RateLimitExceeded as exc:
        raise rate_limit_http_exception(exc.endpoint) from exc


async def enforce_retrieve_rate_limit(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> None:
    try:
        await check_rate_limit(
            settings=settings,
            request=request,
            endpoint="retrieve",
            limit_per_minute=settings.rate_limit_retrieve_per_minute,
        )
    except RateLimitExceeded as exc:
        raise rate_limit_http_exception(exc.endpoint) from exc
