"""Dependencias comunes de la capa HTTP."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_session

SessionDep = Annotated[AsyncSession, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]

# Se agregan con los changes de OpenSpec:
# CurrentUserDep   -> add-iam-auth
# require_permission("robots:read") -> add-rbac
# CurrentRobotDep  -> add-service-api-keys
