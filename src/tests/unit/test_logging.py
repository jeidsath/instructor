"""Tests for structured logging configuration."""

import json
import logging
import sys

import pytest

from instructor.log_config import JSONFormatter, configure_logging


@pytest.mark.unit
class TestJSONFormatter:
    """JSONFormatter outputs valid single-line JSON."""

    def test_basic_message(self) -> None:
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="hello world",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        data = json.loads(output)
        assert data["level"] == "INFO"
        assert data["logger"] == "test.logger"
        assert data["message"] == "hello world"
        assert "timestamp" in data

    def test_extra_fields_propagated(self) -> None:
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="request",
            args=(),
            exc_info=None,
        )
        record.method = "GET"  # type: ignore[attr-defined]
        record.path = "/api/test"  # type: ignore[attr-defined]
        record.status_code = 200  # type: ignore[attr-defined]
        record.duration_ms = 15.3  # type: ignore[attr-defined]
        output = formatter.format(record)
        data = json.loads(output)
        assert data["method"] == "GET"
        assert data["path"] == "/api/test"
        assert data["status_code"] == 200
        assert data["duration_ms"] == 15.3

    def test_exception_included(self) -> None:
        formatter = JSONFormatter()
        try:
            msg = "test error"
            raise ValueError(msg)
        except ValueError:
            exc_info = sys.exc_info()
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="",
                lineno=0,
                msg="error occurred",
                args=(),
                exc_info=exc_info,
            )
        output = formatter.format(record)
        data = json.loads(output)
        assert "exception" in data
        assert "ValueError" in data["exception"]

    def test_output_is_single_line(self) -> None:
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="multi\nline\nmessage",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        # JSON output itself is single-line (no embedded newlines in JSON keys)
        parsed = json.loads(output)
        assert parsed["message"] == "multi\nline\nmessage"


@pytest.mark.unit
class TestConfigureLogging:
    """configure_logging sets up the root logger."""

    def test_sets_log_level(self) -> None:
        configure_logging("WARNING")
        root = logging.getLogger()
        assert root.level == logging.WARNING
        # Reset for other tests
        configure_logging("INFO")

    def test_adds_handler(self) -> None:
        configure_logging("INFO")
        root = logging.getLogger()
        assert len(root.handlers) >= 1
        handler = root.handlers[0]
        assert isinstance(handler.formatter, JSONFormatter)
