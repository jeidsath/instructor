"""Structured JSON logging configuration."""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime


class JSONFormatter(logging.Formatter):
    """Format log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, object] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        exc = record.exc_info
        if exc and isinstance(exc, tuple) and exc[0]:
            log_data["exception"] = self.formatException(exc)
        # Propagate extra fields set via `extra={"key": val}`.
        for key in (
            "method",
            "path",
            "status_code",
            "duration_ms",
            "model",
            "tokens",
            "prompt_length",
            "learner_id",
            "session_id",
            "language",
        ):
            if hasattr(record, key):
                log_data[key] = getattr(record, key)
        return json.dumps(log_data, default=str)


def configure_logging(level: str = "INFO") -> None:
    """Set up structured JSON logging on the root logger."""
    root = logging.getLogger()
    root.setLevel(level.upper())

    # Remove existing handlers to avoid duplicates on reload.
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root.addHandler(handler)

    # Quiet noisy third-party loggers.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
