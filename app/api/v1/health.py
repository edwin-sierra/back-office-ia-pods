"""Endpoints de salud: liveness y readiness."""

from typing import Literal

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text

from app.api.deps import SessionDep, SettingsDep
from app.core.logging import get_logger

router = APIRouter(prefix="/health", tags=["health"])
logger = get_logger(__name__)


class HealthRead(BaseModel):
    status: Literal["ok", "unavailable"]
    service: str
    environment: str
    database: Literal["ok", "unavailable"] | None = None


@router.get("", response_model=HealthRead, summary="Liveness")
async def liveness(settings: SettingsDep) -> HealthRead:
    return HealthRead(status="ok", service=settings.name, environment=settings.environment)


@router.get(
    "/ready",
    response_model=HealthRead,
    summary="Readiness (verifica la base de datos)",
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": HealthRead}},
)
async def readiness(session: SessionDep, settings: SettingsDep) -> HealthRead | JSONResponse:
    try:
        await session.execute(text("SELECT 1"))
    except Exception as exc:
        logger.warning("readiness_db_unavailable", error=str(exc))
        body = HealthRead(
            status="unavailable",
            service=settings.name,
            environment=settings.environment,
            database="unavailable",
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=body.model_dump()
        )
    return HealthRead(
        status="ok", service=settings.name, environment=settings.environment, database="ok"
    )
