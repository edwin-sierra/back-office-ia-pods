from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.iam import repository, service
from app.modules.iam.models import User
from app.modules.iam.schemas import UserCreate


@pytest.mark.asyncio
async def test_bootstrap_user_creates_active_user_with_password_hash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = User(
        id=uuid4(),
        email="admin@example.test",
        full_name="Initial Admin",
        password_hash="argon2id-test-hash",
        is_active=True,
    )
    session = AsyncMock(spec=AsyncSession)
    find_user = AsyncMock(return_value=None)
    create_user = AsyncMock(return_value=user)
    monkeypatch.setattr(repository, "get_user_by_email", find_user)
    monkeypatch.setattr(repository, "create_user", create_user)
    monkeypatch.setattr(service, "hash_password", lambda _: "argon2id-test-hash")

    created = await service.bootstrap_user(
        session, "admin@example.test", "Initial Admin", "test-only-password"
    )

    assert created is user
    assert create_user.await_args is not None
    assert create_user.await_args.args[1] == UserCreate(
        email="admin@example.test",
        full_name="Initial Admin",
        password_hash="argon2id-test-hash",
    )
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_bootstrap_user_conflict_does_not_modify_existing_user(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    existing = User(
        id=uuid4(),
        email="admin@example.test",
        full_name="Existing Admin",
        password_hash="existing-test-hash",
        is_active=False,
    )
    session = AsyncMock(spec=AsyncSession)
    find_user = AsyncMock(return_value=existing)
    create_user = AsyncMock()
    monkeypatch.setattr(repository, "get_user_by_email", find_user)
    monkeypatch.setattr(repository, "create_user", create_user)
    monkeypatch.setattr(service, "hash_password", lambda _: "new-test-hash")

    with pytest.raises(service.UserAlreadyExistsError):
        await service.bootstrap_user(
            session, "admin@example.test", "Replacement Admin", "test-only-password"
        )

    assert existing.full_name == "Existing Admin"
    assert existing.password_hash == "existing-test-hash"
    assert existing.is_active is False
    create_user.assert_not_awaited()
    session.commit.assert_not_awaited()


def test_bootstrap_command_reads_password_without_echoing_it(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    import sys

    from app.modules.iam import bootstrap

    entered_password = "test-only-password"
    prompts: list[str] = []

    async def create_user(email: str, full_name: str, password: str) -> bool:
        assert email == "admin@example.test"
        assert full_name == "Initial Admin"
        assert password == entered_password
        return True

    def prompt_for_password(prompt: str) -> str:
        prompts.append(prompt)
        return entered_password

    monkeypatch.setattr(bootstrap, "_create_user", create_user)
    monkeypatch.setattr("app.modules.iam.bootstrap.getpass.getpass", prompt_for_password)
    monkeypatch.setattr(
        sys,
        "argv",
        ["bootstrap", "--email", "admin@example.test", "--full-name", "Initial Admin"],
    )

    bootstrap.main()
    output = capsys.readouterr()

    assert prompts == ["Contraseña: "]
    assert "Usuario inicial creado." in output.out
    assert entered_password not in output.out
    assert entered_password not in output.err


def test_bootstrap_command_reports_conflict_without_password(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    import sys

    from app.modules.iam import bootstrap

    entered_password = "test-only-password"

    async def conflict(email: str, full_name: str, password: str) -> bool:
        return False

    monkeypatch.setattr(bootstrap, "_create_user", conflict)
    monkeypatch.setattr("app.modules.iam.bootstrap.getpass.getpass", lambda _: entered_password)
    monkeypatch.setattr(
        sys,
        "argv",
        ["bootstrap", "--email", "admin@example.test", "--full-name", "Initial Admin"],
    )

    with pytest.raises(SystemExit) as exception:
        bootstrap.main()

    output = capsys.readouterr()
    assert exception.value.code == 1
    assert "Conflicto" in output.err
    assert entered_password not in output.out
    assert entered_password not in output.err
