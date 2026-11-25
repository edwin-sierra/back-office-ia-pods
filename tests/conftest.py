"""Fixtures compartidas.

- `client`: cliente HTTP async contra la app en memoria (sin red).
- Los tests marcados `@pytest.mark.integration` requieren PostgreSQL
  (APP_DATABASE_URL); con `make test` corren dentro de docker compose.
"""

import os
from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("APP_ENVIRONMENT", "test")

from app.core.config import get_settings
from app.main import create_app


@pytest.fixture(scope="session")
def app() -> FastAPI:
    get_settings.cache_clear()
    return create_app()


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
