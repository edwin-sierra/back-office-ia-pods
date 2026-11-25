"""Router raíz de la API v1. Cada módulo registra aquí su router."""

from fastapi import APIRouter

from app.api.v1 import health

api_router = APIRouter()
api_router.include_router(health.router)

# Se agregan con los changes de OpenSpec, p.ej.:
# from app.modules.robots.router import router as robots_router
# api_router.include_router(robots_router)
