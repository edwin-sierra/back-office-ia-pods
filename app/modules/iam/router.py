"""Endpoints HTTP de autenticación IAM."""

from fastapi import APIRouter

from app.api.deps import SessionDep, SettingsDep
from app.modules.iam.schemas import LoginRequest, LoginResponse
from app.modules.iam.service import login_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse, summary="Iniciar sesión")
async def login(
    credentials: LoginRequest, session: SessionDep, settings: SettingsDep
) -> LoginResponse:
    """Autentica las credenciales y devuelve los tokens de acceso y renovación."""
    return await login_user(session, credentials, settings)
