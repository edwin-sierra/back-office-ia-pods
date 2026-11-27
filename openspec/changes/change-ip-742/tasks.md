## 1. Convención de autenticación

- [x] 1.1 Armonizar `openspec/config.yaml` con la excepción de `docs/guidelines.md` y registrar en `docs/adr/0004-authentication-without-rbac.md` que `/auth/*` no evalúa permisos: login es público, refresh autentica con refresh token y los demás endpoints de auth exigen access token según corresponda; no se agrega RBAC ni respuestas 403. No requiere pruebas automáticas porque solo modifica configuración de OpenSpec y documentación versionada.

## 2. Persistencia de usuarios

- [x] 2.1 Implementar `User` en `app/modules/iam/models.py`, registrarlo en `app/db/models.py` y añadir la migración Alembic reversible para UUID, email único, nombre completo, hash Argon2id, estado activo y timestamps, sin crear usuarios ni roles; las pruebas de integración con PostgreSQL comprueban upgrade, downgrade y unicidad del email; `uv run python -m compileall -q app && uv run python -c "from app.main import app"`, `uv run ruff check . && uv run ruff format --check . && uv run mypy` y `uv run pytest` pasan.

## 3. Contratos y acceso a datos IAM

- [x] 3.1 Añadir schemas de entrada y salida en `app/modules/iam/schemas.py` y consultas sin commit en `app/modules/iam/repository.py`; pruebas unitarias cubren validación/serialización y pruebas de integración con PostgreSQL verifican persistencia y consultas de usuarios, incluida la unicidad; `uv run python -m compileall -q app && uv run python -c "from app.main import app"`, `uv run ruff check . && uv run ruff format --check . && uv run mypy` y `uv run pytest` pasan.

## 4. Primitivas de credenciales y JWT

- [x] 4.1 Implementar en `app/core/security.py` el hash y verificación Argon2id y la emisión/validación de JWT con `Settings`: distinguir access y refresh, validar `exp`, `iat`, `sub` y tipo, y usar las duraciones de 15 minutos y 7 días; pruebas unitarias comprueban hashes no reversibles, claims/duraciones y rechazo de tokens inválidos, expirados o del tipo incorrecto, sin registrar secretos; `uv run python -m compileall -q app && uv run python -c "from app.main import app"`, `uv run ruff check . && uv run ruff format --check . && uv run mypy` y `uv run pytest` pasan.

## 5. Bootstrap inicial

- [x] 5.1 Implementar el servicio y comando de bootstrap en `app/modules/iam/` sin añadir una dependencia CLI: crea un usuario activo y almacena solo el hash Argon2id; ante email existente informa conflicto y conserva el registro intacto; solicita la contraseña sin eco y no la muestra ni registra. Pruebas unitarias del servicio/comando y de integración con PostgreSQL cubren creación, conflicto, falta de modificación y ausencia de la contraseña en salida/logs; `uv run python -m compileall -q app && uv run python -c "from app.main import app"`, `uv run ruff check . && uv run ruff format --check . && uv run mypy` y `uv run pytest` pasan.

## 6. Inicio de sesión

- [ ] 6.1 Implementar service y `POST /api/v1/auth/login` en `app/modules/iam/`, registrar el router en `app/api/v1/router.py` y mantenerlo público, sin permisos RBAC. Las pruebas de API verifican que credenciales válidas de usuario activo devuelven HTTP 200 con `access_token`, `refresh_token`, `token_type: "bearer"` y `expires_in: 900`; email inexistente y contraseña incorrecta devuelven HTTP 401 con el mismo mensaje genérico; usuario inactivo devuelve 401; cuerpo incompleto o email inválido devuelve 422 `application/problem+json`; ninguno devuelve 403. `uv run python -m compileall -q app && uv run python -c "from app.main import app"`, `uv run ruff check . && uv run ruff format --check . && uv run mypy` y `uv run pytest` pasan.

## 7. Renovación de tokens

- [ ] 7.1 Implementar service y `POST /api/v1/auth/refresh` en `app/modules/iam/`; aceptar exclusivamente refresh tokens válidos y emitir un nuevo par con `token_type: "bearer"` y `expires_in: 900`, sin permisos RBAC. Las pruebas de API comprueban HTTP 200 para refresh válido; HTTP 401 y ausencia de nuevo par para access token, refresh inválido o expirado y usuario inactivo; y HTTP 422 `application/problem+json` si falta el token o su forma es inválida; no hay respuestas 403. `uv run python -m compileall -q app && uv run python -c "from app.main import app"`, `uv run ruff check . && uv run ruff format --check . && uv run mypy` y `uv run pytest` pasan.

## 8. Usuario autenticado actual

- [ ] 8.1 Añadir `CurrentUserDep` a `app/api/deps.py` y `GET /api/v1/auth/me` en `app/modules/iam/`, conectado al router v1 y sin permisos RBAC. Las pruebas de API verifican que un endpoint que usa la dependencia recibe al usuario activo identificado por el access token; `/me` devuelve HTTP 200 con id, email, nombre completo, estado y timestamps, sin contraseña ni hash; ausencia de token, token inválido o expirado y usuario inactivo producen HTTP 401; ninguno de los endpoints devuelve 403. `uv run python -m compileall -q app && uv run python -c "from app.main import app"`, `uv run ruff check . && uv run ruff format --check . && uv run mypy`, `uv run pytest`, `make check` y `make test` pasan.
