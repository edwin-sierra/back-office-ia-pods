from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.schema import CreateSchema, DropSchema

from app.db.base import Base
from app.db.session import get_engine
from app.modules.iam.repository import create_user, get_user_by_email, get_user_by_id
from app.modules.iam.schemas import UserCreate

pytestmark = pytest.mark.integration


async def test_user_repository_persists_queries_and_respects_unique_email() -> None:
    schema = f"iam_repository_{uuid4().hex}"

    async with get_engine().begin() as connection:
        await connection.execute(CreateSchema(schema))
        await connection.execute(
            text("SELECT set_config('search_path', :schema, true)"), {"schema": schema}
        )
        await connection.run_sync(Base.metadata.create_all)

        async with AsyncSession(bind=connection, expire_on_commit=False) as session:
            user_data = UserCreate(
                email="person@example.test",
                full_name="Test Person",
                password_hash="encoded-hash-placeholder",
            )
            user = await create_user(session, user_data)

            assert session.in_transaction()
            assert (await get_user_by_id(session, user.id)) is user
            assert (await get_user_by_email(session, "person@example.test")) is user

            with pytest.raises(IntegrityError):
                async with session.begin_nested():
                    await create_user(
                        session,
                        UserCreate(
                            email="person@example.test",
                            full_name="Another Person",
                            password_hash="another-encoded-hash-placeholder",
                        ),
                    )

            assert (await get_user_by_email(session, "person@example.test")) is user

        await connection.execute(DropSchema(schema, cascade=True))
