"""Health-check routes.

Two endpoints are exposed:

    * ``GET /health`` — small, privacy-safe service liveness payload
      (status, app name, environment, privacy mode). This endpoint is
      kept backward compatible and never reaches out to dependencies.
    * ``GET /health/dependencies`` — probes PostgreSQL, Redis, and
      local Ollama and reports per-dependency status. Always returns
      HTTP 200; the top-level ``status`` is ``"degraded"`` if any
      dependency fails.

Neither endpoint leaks credentials, DSNs, secrets, or any user data.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.config import Settings, get_settings
from app.services.dependency_health import run_dependency_checks

router = APIRouter(tags=["health"])


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# GET /health/dependencies
# ---------------------------------------------------------------------------


class CheckResult(BaseModel):
    """Per-dependency probe result."""

    status: str
    detail: str


class OllamaCheckResult(CheckResult):
    """Ollama probe result includes the list of locally available models."""

    models: list[str] = Field(default_factory=list)


class DependencyChecks(BaseModel):
    postgres: CheckResult
    redis: CheckResult
    ollama: OllamaCheckResult


class DependencyHealthResponse(BaseModel):
    """Aggregated dependency-health payload.

    ``status`` is ``"ok"`` only when every dependency reports ``"ok"``;
    otherwise it is ``"degraded"``. The HTTP status code is always 200
    so monitoring systems can read the structured payload.
    """

    status: str
    checks: DependencyChecks


@router.get(
    "/health/dependencies",
    response_model=DependencyHealthResponse,
    summary="Dependency connectivity check (PostgreSQL, Redis, Ollama)",
)
async def dependency_health(
    settings: Settings = Depends(get_settings),
) -> DependencyHealthResponse:
    """Probe PostgreSQL, Redis, and Ollama in parallel.

    All probes run with short timeouts and swallow exceptions, so
    this endpoint will not hang or 5xx if a dependency is down. Error
    messages are scrubbed of credentials and stack traces.
    """
    result = await run_dependency_checks(settings)
    return DependencyHealthResponse.model_validate(result)
