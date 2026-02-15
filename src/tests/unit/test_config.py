import pytest

from instructor.config import Settings


@pytest.mark.unit
def test_default_settings() -> None:
    s = Settings(
        database_url="postgresql+asyncpg://localhost/test",
        anthropic_api_key="test-key",
    )
    assert s.app_env == "development"
    assert s.is_development is True
    assert s.log_level == "info"


@pytest.mark.unit
def test_production_settings() -> None:
    s = Settings(
        database_url="postgresql+asyncpg://localhost/test",
        anthropic_api_key="test-key",
        app_env="production",
    )
    assert s.is_development is False
