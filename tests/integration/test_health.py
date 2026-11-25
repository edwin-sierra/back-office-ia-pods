import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration


async def test_readiness_with_database(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health/ready")

    assert response.status_code == 200
    assert response.json()["database"] == "ok"
