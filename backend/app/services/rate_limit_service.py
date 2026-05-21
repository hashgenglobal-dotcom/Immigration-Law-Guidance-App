"""Redis-backed fixed-window rate limiting for API abuse protection."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

import redis.asyncio as aioredis
from fastapi import HTTPException, Request, status

from app.core.config import Settings


class RateLimitExceeded(Exception):
    """Client exceeded configured limit."""

    def __init__(self, endpoint: str) -> None:
        self.endpoint = endpoint
        super().__init__(endpoint)


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    remaining: int
    limit: int


def _client_key(request: Request, user_subject: str | None) -> str:
    if user_subject:
        raw = f"user:{user_subject}"
    else:
        client_id = request.headers.get("X-Client-Id")
        if client_id and len(client_id) <= 128:
            raw = f"cid:{client_id.strip()}"
        else:
            host = request.client.host if request.client else "unknown"
            raw = f"ip:{host}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


async def _redis_client(settings: Settings) -> aioredis.Redis | None:
    if not settings.redis_url:
        return None
    return aioredis.from_url(settings.redis_url, decode_responses=True)


async def check_rate_limit(
    *,
    settings: Settings,
    request: Request,
    endpoint: str,
    limit_per_minute: int,
    user_subject: str | None = None,
) -> RateLimitResult:
    """Increment counter; raise RateLimitExceeded when over limit."""
    if not settings.rate_limit_enabled or limit_per_minute <= 0:
        return RateLimitResult(allowed=True, remaining=limit_per_minute, limit=limit_per_minute)

    if settings.app_env == "development":
        return RateLimitResult(allowed=True, remaining=limit_per_minute, limit=limit_per_minute)

    client = await _redis_client(settings)
    if client is None:
        return RateLimitResult(allowed=True, remaining=limit_per_minute, limit=limit_per_minute)

    key = f"rl:{endpoint}:{_client_key(request, user_subject)}"
    try:
        count = await client.incr(key)
        if count == 1:
            await client.expire(key, 60)
        remaining = max(0, limit_per_minute - count)
        if count > limit_per_minute:
            raise RateLimitExceeded(endpoint)
        return RateLimitResult(allowed=True, remaining=remaining, limit=limit_per_minute)
    finally:
        await client.aclose()


def rate_limit_http_exception(endpoint: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail={
            "status": "error",
            "error_code": "RATE_LIMIT_EXCEEDED",
            "message": "Too many requests. Please wait and try again.",
            "endpoint": endpoint,
            "privacy_mode": "local-first",
        },
    )
