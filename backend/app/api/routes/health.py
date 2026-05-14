"""Health-check routes.

Three endpoints are exposed:

    * ``GET /health`` — small, privacy-safe service liveness payload
      (status, app name, environment, privacy mode). This endpoint is
      kept backward compatible and never reaches out to dependencies.
    * ``GET /health/dependencies`` — probes PostgreSQL, Redis, and
      local Ollama and reports per-dependency status. Always returns
      HTTP 200; the top-level ``status`` is ``"degraded"`` if any
      dependency fails.
    * ``GET /health/schema`` — verifies the local PostgreSQL database
      has all tables defined in ``database/migrations/001-initial-schema.sql``.
      Reads only ``information_schema.tables``; never touches user
      content. Always HTTP 200, with ``status`` ``"ok"`` or ``"degraded"``.

None of these endpoints leak credentials, DSNs, secrets, or any user data.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.config import Settings, get_settings
from app.services.dependency_health import run_dependency_checks
from app.services.schema_health import run_schema_health

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


# ---------------------------------------------------------------------------
# GET /health/schema
# ---------------------------------------------------------------------------


class SchemaHealthResponse(BaseModel):
    """Result of verifying the local DB schema against the migration.

    ``privacy_safe_answer_logs_present`` is called out explicitly: it
    is the privacy-safe audit table that must exist. The legacy
    ``answer_logs`` table (which stored full question/answer text)
    must NOT exist in this database.
    """

    status: str
    required_tables_count: int
    existing_tables_count: int
    missing_tables: list[str] = Field(default_factory=list)
    privacy_safe_answer_logs_present: bool
    detail: str | None = None


@router.get(
    "/health/schema",
    response_model=SchemaHealthResponse,
    response_model_exclude_none=True,
    summary="Verify required migration tables exist in PostgreSQL",
)
async def schema_health(
    settings: Settings = Depends(get_settings),
) -> SchemaHealthResponse:
    """Read ``information_schema.tables`` and report missing migration tables.

    This probe does NOT read or store user question text or generated
    answer text — it only inspects table metadata. Returns HTTP 200
    even when the database is unreachable; in that case ``status`` is
    ``"degraded"`` and ``detail`` contains a short, credential-free
    error message.
    """
    result = await run_schema_health(settings)
    return SchemaHealthResponse.model_validate(result)
