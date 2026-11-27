from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.schema import CreateSchema, DropSchema

from app.core.security import verify_password
from app.db.base import Base
from app.db.session import get_engine
from app.modules.iam import repository
from app.modules.iam.service import UserAlreadyExistsError, bootstrap_user

pytestmark = pytest.mark.integration


async def test_bootstrap_persists_active_user_with_password_hash() -> None:
    schema = f"iam_bootstrap_{uuid4().hex}"

    async with get_engine().begin() as connection:
        await connection.execute(CreateSchema(schema))
        try:
            await connection.execute(
                text("SELECT set_config('search_path', :schema, true)"), {"schema": schema}
            )
            await connection.run_sync(Base.metadata.create_all)

            async with AsyncSession(bind=connection, expire_on_commit=False) as session:
                user = await bootstrap_user(
                    session,
                    "admin@example.test",
                    "Initial Admin",
                    "test-only-password",
                )

                persisted = await repository.get_user_by_email(session, "admin@example.test")
                assert persisted is user
                assert user.email == "admin@example.test"
                assert user.full_name == "Initial Admin"
                assert user.is_active is True
                assert user.password_hash != "test-only-password"
                assert verify_password("test-only-password", user.password_hash)
        finally:
            await connection.execute(DropSchema(schema, cascade=True))


async def test_bootstrap_conflict_preserves_persisted_user() -> None:
    schema = f"iam_bootstrap_conflict_{uuid4().hex}"

    async with get_engine().begin() as connection:
        await connection.execute(CreateSchema(schema))
        try:
            await connection.execute(
                text("SELECT set_config('search_path', :schema, true)"), {"schema": schema}
            )
            await connection.run_sync(Base.metadata.create_all)

            async with AsyncSession(bind=connection, expire_on_commit=False) as session:
                existing = await bootstrap_user(
                    session,
                    "admin@example.test",
                    "Existing Admin",
                    "existing-test-password",
                )

                with pytest.raises(UserAlreadyExistsError):
                    await bootstrap_user(
                        session,
                        "admin@example.test",
                        "Replacement Admin",
                        "replacement-test-password",
                    )

                persisted = await repository.get_user_by_email(session, "admin@example.test")
                assert persisted is existing
                assert persisted.full_name == "Existing Admin"
                assert persisted.password_hash == existing.password_hash
                assert persisted.is_active is True
        finally:
            await connection.execute(DropSchema(schema, cascade=True))
