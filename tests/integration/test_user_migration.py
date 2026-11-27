from uuid import uuid4

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError
from sqlalchemy.schema import CreateSchema, DropSchema

from app.db.session import get_engine
from migrations.versions import v0001_create_users

pytestmark = pytest.mark.integration


def _upgrade_users(connection: Connection) -> None:
    with Operations.context(MigrationContext.configure(connection)):
        v0001_create_users.upgrade()


def _downgrade_users(connection: Connection) -> None:
    with Operations.context(MigrationContext.configure(connection)):
        v0001_create_users.downgrade()


async def test_user_migration_is_reversible_and_enforces_unique_email() -> None:
    schema = f"user_migration_{uuid4().hex}"

    async with get_engine().begin() as connection:
        await connection.execute(CreateSchema(schema))
        await connection.execute(
            text("SELECT set_config('search_path', :schema, true)"), {"schema": schema}
        )
        await connection.run_sync(_upgrade_users)

        user_id = uuid4()
        await connection.execute(
            text(
                "INSERT INTO users (id, email, full_name, password_hash) "
                "VALUES (:id, :email, :full_name, :password_hash)"
            ),
            {
                "id": user_id,
                "email": "person@example.test",
                "full_name": "Test Person",
                "password_hash": "encoded-hash-placeholder",
            },
        )
        user = (
            await connection.execute(
                text("SELECT is_active, created_at, updated_at FROM users WHERE id = :id"),
                {"id": user_id},
            )
        ).one()
        assert user.is_active is True
        assert user.created_at is not None
        assert user.updated_at is not None

        with pytest.raises(IntegrityError):
            async with connection.begin_nested():
                await connection.execute(
                    text(
                        "INSERT INTO users (id, email, full_name, password_hash) "
                        "VALUES (:id, :email, :full_name, :password_hash)"
                    ),
                    {
                        "id": uuid4(),
                        "email": "person@example.test",
                        "full_name": "Another Person",
                        "password_hash": "encoded-hash-placeholder",
                    },
                )

        await connection.run_sync(_downgrade_users)
        table_exists = await connection.scalar(text("SELECT to_regclass('users') IS NOT NULL"))
        assert table_exists is False
        await connection.execute(DropSchema(schema, cascade=True))
