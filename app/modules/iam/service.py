"""Reglas de negocio para crear el usuario inicial de IAM."""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.modules.iam import repository
from app.modules.iam.models import User
from app.modules.iam.schemas import LoginRequest, LoginResponse, UserCreate


class UserAlreadyExistsError(Exception):
    """El email indicado ya pertenece a un usuario."""


async def login_user(
    session: AsyncSession, credentials: LoginRequest, settings: Settings
) -> LoginResponse:
    """Valida las credenciales y emite tokens para un usuario activo."""
    user = await repository.get_user_by_email(session, credentials.email)
    if (
        user is None
        or not user.is_active
        or not verify_password(credentials.password, user.password_hash)
    ):
        raise UnauthorizedError("Invalid email or password")

    return LoginResponse(
        access_token=create_access_token(user.id, settings),
        refresh_token=create_refresh_token(user.id, settings),
    )


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
