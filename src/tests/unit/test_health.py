import pytest
from httpx import AsyncClient


@pytest.mark.unit
async def test_health_endpoint(test_client: AsyncClient) -> None:
    async with test_client as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
