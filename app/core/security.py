"""Primitivas de seguridad para contraseñas y tokens JWT."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import UUID

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from app.core.config import Settings

TokenType = Literal["access", "refresh"]


@dataclass(frozen=True)
class TokenClaims:
    """Claims validados de un JWT de usuario."""

    subject: UUID
    token_type: TokenType
    issued_at: datetime
    expires_at: datetime


def hash_password(password: str) -> str:
    """Devuelve un hash Argon2id de la contraseña."""
    return PasswordHash.recommended().hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Comprueba una contraseña sin registrar ninguno de los valores recibidos."""
    return PasswordHash.recommended().verify(password, password_hash)


def create_access_token(subject: UUID, settings: Settings) -> str:
    """Emite un JWT de acceso con la duración configurada."""
    return _create_token(
        subject,
        "access",
        settings,
        timedelta(minutes=settings.jwt_access_token_ttl_minutes),
    )


def create_refresh_token(subject: UUID, settings: Settings) -> str:
    """Emite un JWT de renovación con la duración configurada."""
    return _create_token(
        subject,
        "refresh",
        settings,
        timedelta(days=settings.jwt_refresh_token_ttl_days),
    )


def decode_token(token: str, settings: Settings, expected_type: TokenType) -> TokenClaims:
    """Valida firma, expiración y claims obligatorios del tipo de token esperado."""
    payload = jwt.decode(
        token,
        settings.jwt_secret_key.get_secret_value(),
        algorithms=[settings.jwt_algorithm],
        options={"require": ["exp", "iat", "sub", "type"]},
    )

    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise InvalidTokenError("Invalid token subject")
    try:
        subject_id = UUID(subject)
    except ValueError as error:
        raise InvalidTokenError("Invalid token subject") from error

    token_type = payload.get("type")
    if token_type not in ("access", "refresh") or token_type != expected_type:
        raise InvalidTokenError("Invalid token type")

    return TokenClaims(
        subject=subject_id,
        token_type=token_type,
        issued_at=_claim_datetime(payload.get("iat")),
        expires_at=_claim_datetime(payload.get("exp")),
    )


def _create_token(
    subject: UUID,
    token_type: TokenType,
    settings: Settings,
    lifetime: timedelta,
) -> str:
    issued_at = datetime.now(UTC)
    payload = {
        "sub": str(subject),
        "iat": issued_at,
        "exp": issued_at + lifetime,
        "type": token_type,
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def _claim_datetime(value: object) -> datetime:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidTokenError("Invalid token timestamp")
    try:
        return datetime.fromtimestamp(value, UTC)
    except (OverflowError, OSError, ValueError) as error:
        raise InvalidTokenError("Invalid token timestamp") from error
