"""Consultas y persistencia de usuarios IAM, sin control transaccional."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.iam.models import User
from app.modules.iam.schemas import UserCreate


async def create_user(session: AsyncSession, user_data: UserCreate) -> User:
    """Agrega el usuario a la transacción actual, sin hacer commit."""
    user = User(**user_data.model_dump())
    session.add(user)
    await session.flush()
    return user


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    """Busca un usuario por su email exacto."""
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: UUID) -> User | None:
    """Busca un usuario por su identificador."""
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()
