import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from instructor.config import settings
from instructor.curriculum.registry import CurriculumRegistry
from instructor.db import get_db
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


@pytest.fixture
def mock_db_session() -> AsyncMock:
    """Mock async database session for unit tests.

    Overrides the get_db dependency so endpoints don't need a real DB.
    Default behavior: get() returns None, execute() returns empty result.
    """
    session = AsyncMock()
    session.add = MagicMock()  # add() is synchronous
    session.get.return_value = None

    async def _refresh(obj: object, *_: object, **__: object) -> None:
        if hasattr(obj, "id"):
            obj.id = uuid.uuid4()

    session.refresh.side_effect = _refresh

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    session.execute.return_value = mock_result

    async def _override() -> AsyncMock:
        return session

    app.dependency_overrides[get_db] = _override
    yield session  # type: ignore[misc]
    app.dependency_overrides.pop(get_db, None)
