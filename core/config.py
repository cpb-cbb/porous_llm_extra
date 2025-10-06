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
    llm_provider: str = Field(default="zhipu", alias="LLM_PROVIDER")
    llm_api_key: Optional[str] = Field(default=None, alias="LLM_API_KEY")
    llm_model: Optional[str] = Field(default=None, alias="LLM_MODEL")
    llm_base_url: Optional[str] = Field(default=None, alias="LLM_BASE_URL")
    llm_organization: Optional[str] = Field(default=None, alias="LLM_ORG")
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

    def resolve_provider(self, override: Optional[str] = None) -> str:
        provider = (override or self.llm_provider or "zhipu").strip().lower()
        if not provider:
            raise ValueError("LLM provider cannot be empty")
        return provider

    def resolve_model(self, provider: Optional[str] = None) -> str:
        provider_name = self.resolve_provider(provider)
        if provider_name in {"zhipu", "glm"}:
            return self.zhipu_model
        if self.llm_model:
            return self.llm_model
        # Fallback to Zhipu default if no provider-specific override is supplied
        return self.zhipu_model

    def require_api_key(self, provider: Optional[str] = None) -> str:
        """Return the configured API key or raise a helpful error."""

        provider_name = self.resolve_provider(provider)
        if provider_name in {"zhipu", "glm"}:
            if self.zhipu_api_key:
                return self.zhipu_api_key
            if self.llm_api_key:
                return self.llm_api_key
            raise ValueError(
                "Missing ZHIPUAI_API_KEY (or LLM_API_KEY fallback). Please export one of them or add it to your .env file."
            )

        if self.llm_api_key:
            return self.llm_api_key

        raise ValueError(
            f"Missing LLM_API_KEY for provider '{provider_name}'. Please export the environment variable or add it to your .env file."
        )


@lru_cache
def get_settings() -> Settings:
    """Load settings once and cache the result for the app lifecycle."""

    try:
        return Settings()  # type: ignore[call-arg]
    except ValidationError as exc:  # pragma: no cover - defensive guard
        raise RuntimeError(f"Invalid configuration: {exc}") from exc


# Convenience alias used across the codebase
settings: Settings = get_settings()
