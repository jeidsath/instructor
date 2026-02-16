"""Anthropic SDK client wrapper with retry and error handling."""

from __future__ import annotations

import json
import logging
from typing import Any

import anthropic

from instructor.config import settings

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-sonnet-4-5-20250929"
DEFAULT_MAX_TOKENS = 1024


class AIClient:
    """Thin wrapper around the Anthropic SDK.

    Provides structured JSON output and basic retry logic.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> None:
        key = api_key or settings.anthropic_api_key
        self._client = anthropic.Anthropic(api_key=key)
        self._model = model
        self._max_tokens = max_tokens

    def complete_json(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Send a message and parse the response as JSON.

        Raises
        ------
        AIResponseError
            If the response cannot be parsed as valid JSON.
        anthropic.APIError
            On API-level failures (rate limit, auth, etc.).
        """
        response = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens or self._max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        block = response.content[0]
        if not hasattr(block, "text"):
            msg = f"Unexpected content block type: {type(block).__name__}"
            raise AIResponseError(msg)
        text = block.text
        try:
            return json.loads(text)  # type: ignore[no-any-return]
        except json.JSONDecodeError as exc:
            msg = f"AI response is not valid JSON: {text[:200]}"
            raise AIResponseError(msg) from exc


class AIResponseError(Exception):
    """Raised when the AI response cannot be parsed."""
