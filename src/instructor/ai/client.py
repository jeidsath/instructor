"""Anthropic SDK client wrapper with retry and error handling."""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

import anthropic

from instructor.config import settings

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-sonnet-4-5-20250929"
DEFAULT_MAX_TOKENS = 1024
DEFAULT_TIMEOUT = 30.0
MAX_RETRIES = 3
INITIAL_BACKOFF = 1.0

_CODE_FENCE_RE = re.compile(r"```(?:json)?\s*\n?(.*?)\n?\s*```", re.DOTALL)


def _strip_code_fences(text: str) -> str:
    """Strip markdown code fences from text, returning inner content."""
    match = _CODE_FENCE_RE.search(text)
    if match:
        return match.group(1).strip()
    return text


class AIClient:
    """Thin wrapper around the Anthropic SDK.

    Provides structured JSON output with retry logic for transient
    failures.  Retries on ``RateLimitError`` and ``InternalServerError``
    with exponential backoff (up to *max_retries* attempts).  Requests
    time out after *timeout* seconds.  Markdown code fences are stripped
    from responses before JSON parsing.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
    ) -> None:
        key = api_key or settings.anthropic_api_key
        self._client = anthropic.Anthropic(api_key=key)
        self._model = model
        self._max_tokens = max_tokens
        self._timeout = timeout
        self._max_retries = max_retries

    def complete_json(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Send a message and parse the response as JSON.

        Retries up to *max_retries* times on transient API errors
        (rate limits, server errors) with exponential backoff.
        Strips markdown code fences from responses before parsing.

        Raises
        ------
        AIResponseError
            If the response cannot be parsed as valid JSON.
        anthropic.RateLimitError
            If rate-limited on every retry attempt.
        anthropic.InternalServerError
            If the server returns 5xx on every retry attempt.
        anthropic.APITimeoutError
            If the request exceeds the configured timeout.
        """
        last_error: Exception | None = None
        backoff = INITIAL_BACKOFF

        for attempt in range(self._max_retries):
            try:
                response = self._client.messages.create(
                    model=self._model,
                    max_tokens=max_tokens or self._max_tokens,
                    system=system,
                    messages=[{"role": "user", "content": user}],
                    timeout=self._timeout,
                )
                break
            except (
                anthropic.RateLimitError,
                anthropic.InternalServerError,
            ) as exc:
                last_error = exc
                if attempt < self._max_retries - 1:
                    time.sleep(backoff)
                    backoff *= 2
        else:
            raise last_error  # type: ignore[misc]

        block = response.content[0]
        if not hasattr(block, "text"):
            msg = f"Unexpected content block type: {type(block).__name__}"
            raise AIResponseError(msg)
        text = _strip_code_fences(block.text)
        try:
            return json.loads(text)  # type: ignore[no-any-return]
        except json.JSONDecodeError as exc:
            msg = f"AI response is not valid JSON: {text[:200]}"
            raise AIResponseError(msg) from exc


class AIResponseError(Exception):
    """Raised when the AI response cannot be parsed."""
