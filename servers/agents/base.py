from __future__ import annotations

import logging
import time
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from zai import ZhipuAiClient

from core.config import settings

logger = logging.getLogger(__name__)


def _ensure_logging_configured() -> None:
    """Configure a basic logging setup if the app has not done so yet."""

    if logging.getLogger().handlers:
        return

    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


_ensure_logging_configured()


class BaseZhipuAgent:
    """Shared retry + parsing logic for Zhipu GLM based agents."""

    def __init__(
        self,
        *,
        system_prompt: str,
        model: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_tokens: int | None = None,
        retry_attempts: int | None = None,
        retry_delay: float | None = None,
    ) -> None:
        self._settings = settings
        api_key = self._settings.require_api_key()
        self.client = ZhipuAiClient(api_key=api_key)

        self.system_prompt = system_prompt
        self.model = model or self._settings.zhipu_model
        self.temperature = temperature if temperature is not None else self._settings.temperature
        self.top_p = top_p if top_p is not None else self._settings.top_p
        self.max_tokens = max_tokens if max_tokens is not None else self._settings.max_tokens
        self.retry_attempts = retry_attempts if retry_attempts is not None else self._settings.api_max_retries
        self.retry_delay = retry_delay if retry_delay is not None else self._settings.api_retry_delay

    # -- public API -----------------------------------------------------

    def run(self, **prompt_vars: Any) -> Any:
        """Execute the agent with retry + parse logic."""

        messages = self.build_messages(**prompt_vars)
        for attempt in range(self.retry_attempts + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    top_p=self.top_p,
                    max_tokens=self.max_tokens,
                    stream=False,
                )
                content = self._extract_response_text(response)
                return self.parse_response(content, **prompt_vars)
            except Exception as exc:  # noqa: BLE001 - surface upstream errors
                is_last_attempt = attempt >= self.retry_attempts
                logger.warning(
                    "Agent %s failed on attempt %s/%s: %s",
                    self.__class__.__name__,
                    attempt + 1,
                    self.retry_attempts + 1,
                    exc,
                )
                if is_last_attempt:
                    raise
                sleep_seconds = self.retry_delay * (attempt + 1)
                logger.debug("Retrying in %.2f seconds", sleep_seconds)
                time.sleep(sleep_seconds)
        raise RuntimeError("Unexpected agent retry loop termination")

    # -- hooks to override ---------------------------------------------

    def build_messages(self, **prompt_vars: Any) -> List[Dict[str, str]]:
        raise NotImplementedError

    def parse_response(self, content: str, **prompt_vars: Any) -> Any:
        return content

    # -- helpers --------------------------------------------------------

    @staticmethod
    def _extract_response_text(response: Any) -> str:
        try:
            return response.choices[0].message.content.strip()
        except (AttributeError, IndexError, TypeError) as exc:  # pragma: no cover - defensive
            raise ValueError(f"Failed to parse response payload: {response}") from exc
