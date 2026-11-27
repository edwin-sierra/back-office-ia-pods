from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.schema import CreateSchema, DropSchema

from app.db.base import Base
from app.db.session import get_engine
from app.modules.iam.repository import create_user, get_user_by_email, get_user_by_id
from app.modules.iam.schemas import UserCreate

pytestmark = pytest.mark.integration


async def test_user_repository_reads_flushed_row_and_returns_none_for_missing_users() -> None:
    schema = f"iam_repository_contract_{uuid4().hex}"

    async with get_engine().begin() as connection:
        await connection.execute(CreateSchema(schema))
        try:
            await connection.execute(
                text("SELECT set_config('search_path', :schema, true)"), {"schema": schema}
            )
            await connection.run_sync(Base.metadata.create_all)

            async with AsyncSession(bind=connection, expire_on_commit=False) as session:
                user = await create_user(
                    session,
                    UserCreate(
                        email="persisted@example.test",
                        full_name="Persisted Test User",
                        password_hash="encoded-hash-placeholder",
                        is_active=False,
                    ),
                )
                session.expunge(user)

                found_by_id = await get_user_by_id(session, user.id)
                assert found_by_id is not None
                assert found_by_id.id == user.id
                assert found_by_id.email == "persisted@example.test"
                assert found_by_id.full_name == "Persisted Test User"
                assert found_by_id.is_active is False

                found_by_email = await get_user_by_email(session, "persisted@example.test")
                assert found_by_email is found_by_id
                assert await get_user_by_email(session, "missing@example.test") is None
                assert await get_user_by_id(session, uuid4()) is None
        finally:
            await connection.execute(DropSchema(schema, cascade=True))
