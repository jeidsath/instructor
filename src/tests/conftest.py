import pytest
from httpx import ASGITransport, AsyncClient

from instructor.main import app


@pytest.fixture
def test_client() -> AsyncClient:
    """FastAPI test client using httpx."""
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")
