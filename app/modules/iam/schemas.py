"""Schemas de entrada y salida para usuarios IAM."""

import re
from datetime import datetime
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
        if re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value) is None:
            raise ValueError("Invalid email address")
        return value


class UserRead(BaseModel):
    """Representación pública de un usuario, sin credenciales."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
