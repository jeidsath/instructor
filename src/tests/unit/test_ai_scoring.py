import json
from typing import Any
from unittest.mock import MagicMock, patch

import anthropic
import pytest

from instructor.ai.client import AIClient, AIResponseError, _strip_code_fences
from instructor.ai.evaluator import (
    score_composition,
    score_comprehension,
    score_translation,
)

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _mock_client(response_data: dict[str, Any]) -> AIClient:
    """Create a mock AIClient that returns *response_data* as JSON."""
    client = MagicMock(spec=AIClient)
    client.complete_json.return_value = response_data
    return client


def _perfect_response() -> dict[str, Any]:
    return {
        "score": 5,
        "max_score": 5,
        "errors": [],
        "corrected_response": "Perfect translation.",
        "feedback": "Excellent work!",
    }


def _partial_response() -> dict[str, Any]:
    return {
        "score": 3,
        "max_score": 5,
        "errors": [
            {
                "type": "grammar",
                "location": "word 3",
                "error": "wrong case",
                "expected": "accusative",
                "explanation": "Direct objects take the accusative.",
            }
        ],
        "corrected_response": "Corrected translation.",
        "feedback": "Good attempt, but watch case usage.",
    }


def _zero_response() -> dict[str, Any]:
    return {
        "score": 0,
        "max_score": 5,
        "errors": [
            {
                "type": "meaning",
                "location": "entire response",
                "error": "unrelated",
                "expected": "a translation of the source",
                "explanation": "The response does not address the source text.",
            }
        ],
        "corrected_response": "Model translation.",
        "feedback": "The response does not match the source text.",
    }


# ------------------------------------------------------------------
# AIScoreResult
# ------------------------------------------------------------------


@pytest.mark.unit
class TestAIScoreResult:
    """AIScoreResult dataclass behavior."""

    def test_perfect_score(self) -> None:
        client = _mock_client(_perfect_response())
        r = score_translation(
            client,
            source="amor",
            response="love",
            direction="Latin to English",
            language="Latin",
        )
        assert r.score == 1.0
        assert r.raw_score == 5
        assert r.correct is True
        assert r.errors == []

    def test_partial_score(self) -> None:
        client = _mock_client(_partial_response())
        r = score_translation(
            client,
            source="test",
            response="test",
            direction="Latin to English",
            language="Latin",
        )
        assert r.score == pytest.approx(0.6)
        assert r.raw_score == 3
        assert r.correct is False  # 3/5 = 0.6 < 0.8

    def test_zero_score(self) -> None:
        client = _mock_client(_zero_response())
        r = score_translation(
            client,
            source="test",
            response="unrelated",
            direction="Latin to English",
            language="Latin",
        )
        assert r.score == 0.0
        assert r.correct is False

    def test_correct_threshold_at_4(self) -> None:
        """Score of 4/5 = 0.8 should be considered correct."""
        data = _perfect_response()
        data["score"] = 4
        client = _mock_client(data)
        r = score_translation(
            client,
            source="t",
            response="t",
            direction="Latin to English",
            language="Latin",
        )
        assert r.correct is True


# ------------------------------------------------------------------
# Error parsing
# ------------------------------------------------------------------


@pytest.mark.unit
class TestErrorParsing:
    """Error details are correctly extracted from AI response."""

    def test_errors_parsed(self) -> None:
        client = _mock_client(_partial_response())
        r = score_translation(
            client,
            source="t",
            response="t",
            direction="Latin to English",
            language="Latin",
        )
        assert len(r.errors) == 1
        err = r.errors[0]
        assert err.error_type == "grammar"
        assert err.location == "word 3"
        assert err.expected == "accusative"

    def test_empty_errors(self) -> None:
        client = _mock_client(_perfect_response())
        r = score_translation(
            client,
            source="t",
            response="t",
            direction="Latin to English",
            language="Latin",
        )
        assert r.errors == []

    def test_missing_error_fields_default(self) -> None:
        """Error dicts with missing keys should use defaults."""
        data = _perfect_response()
        data["errors"] = [{"type": "grammar"}]
        client = _mock_client(data)
        r = score_translation(
            client,
            source="t",
            response="t",
            direction="Latin to English",
            language="Latin",
        )
        err = r.errors[0]
        assert err.error_type == "grammar"
        assert err.location == ""
        assert err.error == ""


# ------------------------------------------------------------------
# Prompt construction
# ------------------------------------------------------------------


@pytest.mark.unit
class TestPromptConstruction:
    """Verify correct prompts are sent to the AI client."""

    def test_translation_prompt_includes_source(self) -> None:
        client = _mock_client(_perfect_response())
        score_translation(
            client,
            source="amor vincit omnia",
            response="love conquers all",
            direction="Latin to English",
            language="Latin",
        )
        call_kwargs = client.complete_json.call_args.kwargs
        assert "amor vincit omnia" in call_kwargs["user"]
        assert "love conquers all" in call_kwargs["user"]
        assert "Latin to English" in call_kwargs["user"]

    def test_composition_prompt_includes_level(self) -> None:
        client = _mock_client(_perfect_response())
        score_composition(
            client,
            prompt="Write about your family",
            response="familia mea est magna",
            language="Latin",
            level="beginner",
        )
        call_kwargs = client.complete_json.call_args.kwargs
        assert "beginner" in call_kwargs["user"]
        assert "familia mea est magna" in call_kwargs["user"]

    def test_comprehension_prompt_includes_passage(self) -> None:
        client = _mock_client(_perfect_response())
        score_comprehension(
            client,
            passage="Gallia est omnis divisa in partes tres.",
            question="How many parts is Gaul divided into?",
            response="Three parts",
            language="Latin",
        )
        call_kwargs = client.complete_json.call_args.kwargs
        assert "Gallia est omnis divisa" in call_kwargs["user"]
        assert "Three parts" in call_kwargs["user"]

    def test_system_prompt_sent(self) -> None:
        client = _mock_client(_perfect_response())
        score_translation(
            client,
            source="t",
            response="t",
            direction="Latin to English",
            language="Latin",
        )
        call_kwargs = client.complete_json.call_args.kwargs
        assert "Ancient Greek and Latin" in call_kwargs["system"]


# ------------------------------------------------------------------
# Client wrapper
# ------------------------------------------------------------------


@pytest.mark.unit
class TestAIClient:
    """AIClient.complete_json parsing behavior."""

    def test_valid_json_parsed(self) -> None:
        response_text = json.dumps({"score": 5, "feedback": "great"})
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=response_text)]

        with patch("instructor.ai.client.anthropic") as mock_anthropic:
            mock_anthropic.Anthropic.return_value.messages.create.return_value = (
                mock_message
            )
            mock_anthropic.RateLimitError = anthropic.RateLimitError
            mock_anthropic.InternalServerError = anthropic.InternalServerError
            client = AIClient(api_key="test-key")
            result = client.complete_json(system="sys", user="usr")

        assert result["score"] == 5

    def test_invalid_json_raises(self) -> None:
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="not json at all")]

        with patch("instructor.ai.client.anthropic") as mock_anthropic:
            mock_anthropic.Anthropic.return_value.messages.create.return_value = (
                mock_message
            )
            mock_anthropic.RateLimitError = anthropic.RateLimitError
            mock_anthropic.InternalServerError = anthropic.InternalServerError
            client = AIClient(api_key="test-key")
            with pytest.raises(AIResponseError, match="not valid JSON"):
                client.complete_json(system="sys", user="usr")


# ------------------------------------------------------------------
# Retry, timeout, and markdown stripping
# ------------------------------------------------------------------


def _make_api_error(
    cls: type[anthropic.APIStatusError],
) -> anthropic.APIStatusError:
    """Create an Anthropic API error with a mock response."""
    mock_resp = MagicMock()
    mock_resp.request = MagicMock()
    mock_resp.status_code = 429 if cls is anthropic.RateLimitError else 500
    return cls(message="transient error", response=mock_resp, body=None)


@pytest.mark.unit
class TestAIClientRetry:
    """Retry logic for transient API errors."""

    def test_retry_on_rate_limit_succeeds(self) -> None:
        """Rate limit on first attempt, success on second."""
        response_text = json.dumps({"result": "ok"})
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=response_text)]

        rate_limit_err = _make_api_error(anthropic.RateLimitError)

        with (
            patch("instructor.ai.client.anthropic") as mock_anthropic,
            patch("instructor.ai.client.time.sleep") as mock_sleep,
        ):
            mock_create = mock_anthropic.Anthropic.return_value.messages.create
            mock_create.side_effect = [rate_limit_err, mock_message]
            mock_anthropic.RateLimitError = anthropic.RateLimitError
            mock_anthropic.InternalServerError = anthropic.InternalServerError

            client = AIClient(api_key="test-key", max_retries=3)
            result = client.complete_json(system="sys", user="usr")

        assert result == {"result": "ok"}
        assert mock_create.call_count == 2
        mock_sleep.assert_called_once_with(1.0)

    def test_max_retries_exceeded_raises(self) -> None:
        """All retries exhausted raises the last error."""
        rate_limit_err = _make_api_error(anthropic.RateLimitError)

        with (
            patch("instructor.ai.client.anthropic") as mock_anthropic,
            patch("instructor.ai.client.time.sleep"),
        ):
            mock_create = mock_anthropic.Anthropic.return_value.messages.create
            mock_create.side_effect = rate_limit_err
            mock_anthropic.RateLimitError = anthropic.RateLimitError
            mock_anthropic.InternalServerError = anthropic.InternalServerError

            client = AIClient(api_key="test-key", max_retries=2)
            with pytest.raises(anthropic.RateLimitError):
                client.complete_json(system="sys", user="usr")

        assert mock_create.call_count == 2

    def test_internal_server_error_retried(self) -> None:
        """InternalServerError is retried like RateLimitError."""
        response_text = json.dumps({"ok": True})
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=response_text)]

        server_err = _make_api_error(anthropic.InternalServerError)

        with (
            patch("instructor.ai.client.anthropic") as mock_anthropic,
            patch("instructor.ai.client.time.sleep"),
        ):
            mock_create = mock_anthropic.Anthropic.return_value.messages.create
            mock_create.side_effect = [server_err, mock_message]
            mock_anthropic.RateLimitError = anthropic.RateLimitError
            mock_anthropic.InternalServerError = anthropic.InternalServerError

            client = AIClient(api_key="test-key", max_retries=3)
            result = client.complete_json(system="sys", user="usr")

        assert result == {"ok": True}

    def test_timeout_not_retried(self) -> None:
        """APITimeoutError is not retried — it propagates immediately."""
        timeout_err = anthropic.APITimeoutError(request=MagicMock())

        with patch("instructor.ai.client.anthropic") as mock_anthropic:
            mock_create = mock_anthropic.Anthropic.return_value.messages.create
            mock_create.side_effect = timeout_err
            mock_anthropic.RateLimitError = anthropic.RateLimitError
            mock_anthropic.InternalServerError = anthropic.InternalServerError

            client = AIClient(api_key="test-key", max_retries=3)
            with pytest.raises(anthropic.APITimeoutError):
                client.complete_json(system="sys", user="usr")

        assert mock_create.call_count == 1


@pytest.mark.unit
class TestStripCodeFences:
    """Markdown code fence stripping."""

    def test_json_code_fence(self) -> None:
        text = '```json\n{"score": 5}\n```'
        assert _strip_code_fences(text) == '{"score": 5}'

    def test_plain_code_fence(self) -> None:
        text = '```\n{"score": 5}\n```'
        assert _strip_code_fences(text) == '{"score": 5}'

    def test_no_fence_passthrough(self) -> None:
        text = '{"score": 5}'
        assert _strip_code_fences(text) == '{"score": 5}'

    def test_fence_with_surrounding_text(self) -> None:
        text = 'Here is the JSON:\n```json\n{"a": 1}\n```\nDone.'
        assert _strip_code_fences(text) == '{"a": 1}'

    def test_complete_json_with_fences(self) -> None:
        """End-to-end: AIClient parses fenced JSON correctly."""
        fenced = '```json\n{"score": 5, "feedback": "great"}\n```'
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=fenced)]

        with patch("instructor.ai.client.anthropic") as mock_anthropic:
            mock_anthropic.Anthropic.return_value.messages.create.return_value = (
                mock_message
            )
            mock_anthropic.RateLimitError = anthropic.RateLimitError
            mock_anthropic.InternalServerError = anthropic.InternalServerError

            client = AIClient(api_key="test-key")
            result = client.complete_json(system="sys", user="usr")

        assert result["score"] == 5


# ------------------------------------------------------------------
# Feedback and corrected response
# ------------------------------------------------------------------


@pytest.mark.unit
class TestFeedbackAndCorrection:
    """feedback and corrected_response are propagated."""

    def test_feedback_present(self) -> None:
        client = _mock_client(_partial_response())
        r = score_translation(
            client,
            source="t",
            response="t",
            direction="Latin to English",
            language="Latin",
        )
        assert r.feedback == "Good attempt, but watch case usage."

    def test_corrected_response_present(self) -> None:
        client = _mock_client(_partial_response())
        r = score_translation(
            client,
            source="t",
            response="t",
            direction="Latin to English",
            language="Latin",
        )
        assert r.corrected_response == "Corrected translation."

    def test_defaults_on_missing_fields(self) -> None:
        """Missing optional fields in AI response get empty defaults."""
        client = _mock_client({"score": 3, "max_score": 5})
        r = score_translation(
            client,
            source="t",
            response="t",
            direction="Latin to English",
            language="Latin",
        )
        assert r.feedback == ""
        assert r.corrected_response == ""
        assert r.errors == []
