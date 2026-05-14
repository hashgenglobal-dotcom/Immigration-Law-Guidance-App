"""Application settings.

Privacy-first configuration loaded from environment variables (or a local
`.env` file during development).

PRIVACY RULES (enforced by defaults below):
    * `STORE_USER_QUESTIONS` defaults to **False**. The backend must NOT
      persist full user question text or full generated answer text by
      default. Only privacy-safe metadata (hashes, citations used,
      retrieved chunk IDs, risk level, refusal flag, latency, etc.)
      may be logged into `privacy_safe_answer_logs`.
    * Real user queries must be processed by LOCAL models only
      (Ollama / vLLM via `OLLAMA_BASE_URL`). Do NOT introduce any
      public AI API client (OpenAI, Anthropic, etc.) here.

This module deliberately exposes only configuration. It does not open
database or Redis connections — those will be added in later steps.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the FastAPI backend.

    Values are read from environment variables. A `.env` file at the
    repository root (or `backend/.env`) is also supported during local
    development. See `.env.example` for the canonical list of variables.
    """

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(
        default="Immigration Law Guidance App",
        validation_alias="APP_NAME",
    )
    app_env: str = Field(
        default="development",
        validation_alias="APP_ENV",
    )
    app_debug: bool = Field(
        default=True,
        validation_alias="APP_DEBUG",
    )

    database_url: str | None = Field(
        default=None,
        validation_alias="DATABASE_URL",
    )
    redis_url: str | None = Field(
        default=None,
        validation_alias="REDIS_URL",
    )

    ollama_base_url: str = Field(
        default="http://localhost:11434",
        validation_alias="OLLAMA_BASE_URL",
    )

    # PRIVACY: full user question text and full generated answer text
    # must NOT be stored by default. This flag stays False unless an
    # operator deliberately opts in. Even when True, the application
    # code should still prefer storing privacy-safe metadata only.
    store_user_questions: bool = Field(
        default=False,
        validation_alias="STORE_USER_QUESTIONS",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached `Settings` instance.

    Using `lru_cache` ensures we parse environment variables once per
    process, which is the standard FastAPI + pydantic-settings pattern.
    """
    return Settings()
