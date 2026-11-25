# Stack tecnológico

## Runtime

| Pieza | Versión | Por qué |
|---|---|---|
| **Python** | 3.13 | Versión estable actual, tipado moderno (`type`, `StrEnum`, genéricos PEP 695). |
| **FastAPI** | ≥ 0.115 | Framework async, validación con Pydantic, OpenAPI automático, inyección de dependencias (auth y permisos). |
| **Pydantic v2** | ≥ 2.9 | Schemas de entrada y salida; validación rápida (núcleo en Rust). |
| **pydantic-settings** | ≥ 2.6 | Configuración tipada desde variables de entorno (prefijo `APP_`). |
| **SQLAlchemy 2.0 (async)** | ≥ 2.0.36 | ORM con tipado `Mapped[]`, sesiones async y queries explícitas. |
| **asyncpg** | ≥ 0.30 | Driver async de PostgreSQL de alto rendimiento. |
| **Alembic** | ≥ 1.14 | Migraciones versionadas y revisables (autogenerate más revisión manual). |
| **PostgreSQL** | 16 | Relacional robusto; `JSONB` para parámetros y resultados de ejecuciones. |
| **httpx** | ≥ 0.28 | Cliente HTTP async para disparar robots (timeouts y retries controlados). |
| **PyJWT** | ≥ 2.10 | Emisión y validación de JWT (access y refresh). |
| **pwdlib[argon2]** | ≥ 0.2 | Hash de passwords con Argon2id (recomendación OWASP). |
| **structlog** | ≥ 24.4 | Logs estructurados en JSON con `request_id` por request. |
| **uvicorn** | ≥ 0.32 | Servidor ASGI. |

## Desarrollo y calidad

| Pieza | Uso |
|---|---|
| **uv** | Gestor de dependencias, entornos y lockfile (`uv.lock`). Reemplaza pip, pip-tools y virtualenv. |
| **ruff** | Linter y formatter (reemplaza flake8, isort, black y bandit-lite). |
| **mypy** (strict) | Chequeo estático de tipos, con plugin de Pydantic. |
| **pytest + pytest-asyncio** | Tests async. |
| **pytest-cov** | Cobertura (mínimo 80%). |
| **respx** | Mock de llamadas `httpx` (disparo de robots). |
| **pre-commit** | Hooks locales: ruff, mypy, detección de claves privadas, etc. |

## Infraestructura

| Pieza | Uso |
|---|---|
| **Docker** (multi-stage) | Imagen liviana, usuario no-root, healthcheck. |
| **docker compose** | Entorno local: `api` (hot reload) + `db` (Postgres con healthcheck). |
| **GitHub Actions** | CI: lint, typecheck, migraciones, tests contra Postgres y build de la imagen. |

## Flujo de trabajo

| Pieza | Uso |
|---|---|
| **Claude Code** | Desarrollo asistido; reglas del proyecto en `CLAUDE.md`. |
| **OpenSpec** | Desarrollo guiado por especificaciones: cada feature es un change en `openspec/changes/`. |

## Decisiones descartadas

- **Celery, ARQ o colas propias**: el disparo es un llamado HTTP al robot (ver [ADR 0002](adr/0002-robot-trigger-via-http.md)).
- **IdP externo (OIDC)**: se usa JWT propio en v1 (ver [ADR 0003](adr/0003-auth-jwt-and-api-keys.md)). El diseño permite migrar después.
- **Poetry o pip**: uv es más rápido y tiene un lockfile reproducible.
