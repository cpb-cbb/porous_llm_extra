"""Application configuration helpers."""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralised project settings.

    Values are loaded from environment variables (optionally via a ``.env`` file).
    Defaults are chosen for local development but can be overridden per deployment.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    # LLM / API configuration
    zhipu_api_key: Optional[str] = Field(default=None, alias="ZHIPUAI_API_KEY")
    zhipu_model: str = Field(default="glm-4.5", alias="ZHIPUAI_MODEL")
    api_max_retries: int = Field(default=3, alias="ZHIPUAI_API_MAX_RETRIES", ge=0)
    api_retry_delay: float = Field(default=5.0, alias="ZHIPUAI_API_RETRY_DELAY", ge=0)
    api_timeout: float = Field(default=60.0, alias="ZHIPUAI_API_TIMEOUT", gt=0)
    temperature: float = Field(default=0.1, alias="ZHIPUAI_TEMPERATURE", ge=0, le=2)
    top_p: float = Field(default=0.7, alias="ZHIPUAI_TOP_P", ge=0, le=1)
    max_tokens: int = Field(default=8000, alias="ZHIPUAI_MAX_TOKENS", gt=0)

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    def require_api_key(self) -> str:
        """Return the configured API key or raise a helpful error."""

        if not self.zhipu_api_key:
            raise ValueError(
                "Missing ZHIPUAI_API_KEY. Please export the environment variable or add it to your .env file."
            )
        return self.zhipu_api_key


@lru_cache
def get_settings() -> Settings:
    """Load settings once and cache the result for the app lifecycle."""

    try:
        return Settings()  # type: ignore[call-arg]
    except ValidationError as exc:  # pragma: no cover - defensive guard
        raise RuntimeError(f"Invalid configuration: {exc}") from exc


# Convenience alias used across the codebase
settings: Settings = get_settings()
