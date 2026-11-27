from collections.abc import AsyncIterator, Iterator
from typing import cast
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.security import hash_password
from app.db.session import get_session
from app.modules.iam import repository
from app.modules.iam.models import User


@pytest.fixture
def login_users() -> list[User]:
    return [
        User(
            id=uuid4(),
            email="person@example.test",
            full_name="Test Person",
            password_hash=hash_password("correct-password"),
            is_active=True,
        )
    ]


@pytest.fixture
def login_api(
    app: FastAPI, login_users: list[User], monkeypatch: pytest.MonkeyPatch
) -> Iterator[None]:
    async def override_session() -> AsyncIterator[AsyncSession]:
        yield cast(AsyncSession, object())

    async def find_user_by_email(_session: AsyncSession, email: str) -> User | None:
        return next((user for user in login_users if user.email == email), None)

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_settings] = lambda: Settings(
        jwt_secret_key="test-signing-key-that-is-not-a-secret"
    )
    monkeypatch.setattr(repository, "get_user_by_email", find_user_by_email)
    yield
    app.dependency_overrides.clear()


async def test_login_returns_access_and_refresh_tokens(
    client: AsyncClient, login_api: None
) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "person@example.test", "password": "correct-password"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 900


@pytest.mark.parametrize("email_exists", [False, True])
async def test_login_rejects_invalid_credentials_with_same_message(
    client: AsyncClient,
    login_api: None,
    login_users: list[User],
    email_exists: bool,
) -> None:
    email = "person@example.test" if email_exists else "unknown@example.test"
    password = "wrong-password"

    response = await client.post("/api/v1/auth/login", json={"email": email, "password": password})

    assert response.status_code == 401
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["detail"] == "Invalid email or password"
    assert "access_token" not in response.json()
    assert "refresh_token" not in response.json()


async def test_login_rejects_inactive_user(
    client: AsyncClient, login_api: None, login_users: list[User]
) -> None:
    login_users[0].is_active = False

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "person@example.test", "password": "correct-password"},
    )

    assert response.status_code == 401


@pytest.mark.parametrize(
    "payload",
    [
        {"password": "correct-password"},
        {"email": "person@example.test"},
        {"email": "not-an-email", "password": "correct-password"},
    ],
)
async def test_login_rejects_invalid_request_body(
    client: AsyncClient, login_api: None, payload: dict[str, str]
) -> None:
    response = await client.post("/api/v1/auth/login", json=payload)

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
