from collections.abc import AsyncIterator

from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.session import get_session


async def test_liveness_ok(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "X-Request-ID" in response.headers


async def test_request_id_is_propagated(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health", headers={"X-Request-ID": "abc-123"})

    assert response.headers["X-Request-ID"] == "abc-123"


async def test_unknown_route_returns_problem_json(client: AsyncClient) -> None:
    response = await client.get("/api/v1/does-not-exist")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["code"] == "not_found"


async def test_app_error_returns_problem_json(app: FastAPI, client: AsyncClient) -> None:
    @app.get("/_test/not-found")
    async def _raise() -> None:
        raise NotFoundError("Robot not found", resource="robot")

    response = await client.get("/_test/not-found")
    body = response.json()

    assert response.status_code == 404
    assert body["detail"] == "Robot not found"
    assert body["resource"] == "robot"


async def test_readiness_returns_503_when_db_unavailable(app: FastAPI, client: AsyncClient) -> None:
    class BrokenSession:
        async def execute(self, *_: object) -> None:
            raise ConnectionError("db down")

    async def broken_session() -> AsyncIterator[AsyncSession]:
        yield BrokenSession()  # type: ignore[misc]

    app.dependency_overrides[get_session] = broken_session
    try:
        response = await client.get("/api/v1/health/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json()["database"] == "unavailable"
