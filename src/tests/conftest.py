import pytest
from httpx import ASGITransport, AsyncClient

from instructor.config import settings
from instructor.curriculum.registry import CurriculumRegistry
from instructor.main import app


@pytest.fixture(scope="session", autouse=True)
def _init_app_state() -> None:
    """Populate app.state for tests that don't go through lifespan."""
    if not hasattr(app.state, "registry"):
        app.state.registry = CurriculumRegistry(settings.curriculum_path)


@pytest.fixture
def test_client() -> AsyncClient:
    """FastAPI test client using httpx."""
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")
