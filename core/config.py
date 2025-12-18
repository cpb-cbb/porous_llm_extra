"""Application configuration helpers."""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from dotenv import load_dotenv

class Settings(BaseSettings):
    """Centralised project settings.

    Values are loaded from environment variables (optionally via a ``.env`` file).
    Defaults are chosen for local development but can be overridden per deployment.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    # LLM / API configuration
    llm_model: str = Field(default="zhipuai/glm-4-plus", alias="LLM_MODEL")
    llm_api_key: Optional[str] = Field(default=None, alias="LLM_API_KEY")
    llm_base_url: Optional[str] = Field(default=None, alias="LLM_BASE_URL")

    # LLM parameters
    temperature: float = Field(default=0.1, alias="TEMPERATURE", ge=0, le=2)
    top_p: float = Field(default=0.7, alias="TOP_P", ge=0, le=1)
    max_tokens: int = Field(default=8000, alias="MAX_TOKENS", gt=0)
    

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")


@lru_cache
def get_settings() -> Settings:
    """Load settings once and cache the result for the app lifecycle."""

    try:
        return Settings()  # type: ignore[call-arg]
    except ValidationError as exc:  # pragma: no cover - defensive guard
        raise RuntimeError(f"Invalid configuration: {exc}") from exc


# Convenience alias used across the codebase
settings: Settings = get_settings()
