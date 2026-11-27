"""Reglas de negocio para crear el usuario inicial de IAM."""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.modules.iam import repository
from app.modules.iam.models import User
from app.modules.iam.schemas import UserCreate


class UserAlreadyExistsError(Exception):
    """El email indicado ya pertenece a un usuario."""


async def bootstrap_user(session: AsyncSession, email: str, full_name: str, password: str) -> User:
    """Crea y confirma un usuario activo con la contraseña protegida mediante Argon2id."""
    user_data = UserCreate(
        email=email,
        full_name=full_name,
        password_hash=hash_password(password),
    )
    if await repository.get_user_by_email(session, user_data.email) is not None:
        raise UserAlreadyExistsError

    try:
        user = await repository.create_user(session, user_data)
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        if await repository.get_user_by_email(session, user_data.email) is not None:
            raise UserAlreadyExistsError from error
        raise

    return user
