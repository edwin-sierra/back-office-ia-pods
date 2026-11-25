"""Errores de dominio y handlers que responden en formato RFC 9457 (problem+json)."""

from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger

PROBLEM_JSON = "application/problem+json"

logger = get_logger(__name__)


class AppError(Exception):
    """Error base de la aplicación. Los servicios lanzan subclases; nunca HTTPException."""

    status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR
    code: str = "internal_error"
    title: str = "Internal Server Error"

    def __init__(self, detail: str | None = None, **extra: Any) -> None:
        super().__init__(detail or self.title)
        self.detail = detail or self.title
        self.extra = extra


class NotFoundError(AppError):
    status_code = HTTPStatus.NOT_FOUND
    code = "not_found"
    title = "Resource not found"


class ConflictError(AppError):
    status_code = HTTPStatus.CONFLICT
    code = "conflict"
    title = "Conflict"


class UnauthorizedError(AppError):
    status_code = HTTPStatus.UNAUTHORIZED
    code = "unauthorized"
    title = "Unauthorized"


class ForbiddenError(AppError):
    status_code = HTTPStatus.FORBIDDEN
    code = "forbidden"
    title = "Forbidden"


class DomainValidationError(AppError):
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    code = "validation_error"
    title = "Validation error"


def _problem(
    request: Request,
    *,
    status: int,
    title: str,
    detail: str,
    code: str,
    **extra: Any,
) -> JSONResponse:
    body: dict[str, Any] = {
        "type": f"about:blank#{code}",
        "title": title,
        "status": status,
        "detail": detail,
        "instance": request.url.path,
        "code": code,
        **extra,
    }
    return JSONResponse(status_code=status, content=body, media_type=PROBLEM_JSON)


async def app_error_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, AppError):  # pragma: no cover
        raise exc
    return _problem(
        request,
        status=exc.status_code,
        title=exc.title,
        detail=exc.detail,
        code=exc.code,
        **exc.extra,
    )


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, StarletteHTTPException):  # pragma: no cover
        raise exc
    status = exc.status_code
    return _problem(
        request,
        status=status,
        title=HTTPStatus(status).phrase,
        detail=str(exc.detail),
        code=HTTPStatus(status).name.lower(),
    )


async def validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, RequestValidationError):  # pragma: no cover
        raise exc
    return _problem(
        request,
        status=HTTPStatus.UNPROCESSABLE_ENTITY,
        title="Validation error",
        detail="Request validation failed",
        code="validation_error",
        errors=[{"loc": e["loc"], "msg": e["msg"], "type": e["type"]} for e in exc.errors()],
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled_exception", exc_info=exc)
    return _problem(
        request,
        status=HTTPStatus.INTERNAL_SERVER_ERROR,
        title="Internal Server Error",
        detail="An unexpected error occurred",
        code="internal_error",
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
