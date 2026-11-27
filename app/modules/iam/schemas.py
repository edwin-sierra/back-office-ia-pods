"""Schemas de entrada y salida para usuarios IAM."""

import re
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserCreate(BaseModel):
    """Datos internos necesarios para persistir un usuario."""

    email: str = Field(max_length=320)
    full_name: str = Field(min_length=1, max_length=255)
    password_hash: str = Field(min_length=1, max_length=255)
    is_active: bool = True

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return _normalize_email(value)


class LoginRequest(BaseModel):
    """Credenciales enviadas al endpoint de inicio de sesión."""

    email: str = Field(max_length=320)
    password: str = Field(min_length=1)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return _normalize_email(value)


class LoginResponse(BaseModel):
    """Par de tokens emitido al autenticar un usuario."""

    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = Field(default="bearer")
    expires_in: int = 900


def _normalize_email(value: str) -> str:
    """Valida y normaliza una dirección de correo."""
    local_part, separator, domain = value.partition("@")
    local_pattern = r"[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+)*"
    domain_label = r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    domain_pattern = rf"{domain_label}(?:\.{domain_label})+"
    if (
        not separator
        or re.fullmatch(local_pattern, local_part) is None
        or re.fullmatch(domain_pattern, domain) is None
    ):
        raise ValueError("Invalid email address")
    return value.lower()


class UserRead(BaseModel):
    """Representación pública de un usuario, sin credenciales."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
