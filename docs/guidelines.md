# Lineamientos y buenas prácticas

Estas reglas aplican a todo el código, incluido el generado con Claude Code. Si una regla no aplica a un caso concreto, se documenta la excepción en el change de OpenSpec o en un ADR.

## 1. Idioma y nombres

- **Código, identificadores, tablas, endpoints y mensajes de commit**: inglés.
- **Documentación (`docs/`, OpenSpec) y docstrings**: español.
- Tablas en plural y `snake_case` (`robots`, `executions`, `role_permissions`).
- Permisos con formato `<recurso>:<accion>` (`executions:trigger`).

## 2. Código Python

- Type hints en todo; `mypy --strict` sin errores. `Any` solo si está justificado.
- `ruff check` y `ruff format` sin errores (line length 100).
- Async de punta a punta: nada de I/O bloqueante en handlers ni en services.
- Funciones cortas, con una sola responsabilidad. Preferir composición a herencia.
- Sin lógica de negocio en routers (ver [architecture.md](architecture.md#capas)).
- Los services lanzan `AppError` y sus subclases, nunca `HTTPException`.
- Sin `print`: usar `get_logger(__name__)` con eventos en `snake_case` y campos estructurados:
  `logger.info("execution_triggered", execution_id=..., robot_id=...)`.
- Configuración solo vía `Settings` (`app/core/config.py`); nunca `os.environ` disperso.

## 3. Diseño de API

- Prefijo `/api/v1`. Recursos en plural; sub-recursos para relaciones (`/robots/{robot_id}/executions`).
- Métodos: `GET` lectura, `POST` creación o acción, `PATCH` actualización parcial, `DELETE` baja (lógica cuando hay historial).
- Códigos HTTP: `201` creado, `202` aceptado (disparo), `204` sin contenido, `400/422` validación, `401` sin autenticación, `403` sin permiso, `404`, `409` conflicto de estado.
- Schemas separados por caso: `RobotCreate`, `RobotUpdate`, `RobotRead`. Nunca exponer modelos ORM.
- Paginación `?limit=&offset=` (límite máximo 100) con respuesta `{ "items": [...], "total": n, "limit": l, "offset": o }`.
- Filtros por query params explícitos; orden por `?sort=-created_at`.
- Errores en RFC 9457 (`application/problem+json`) a través de los handlers de `app/core/exceptions.py`.
- Cada endpoint tiene `summary`, `tags` y `response_model`; documentar las respuestas de error relevantes.
- IDs como UUID; fechas en ISO-8601 UTC.

## 4. Base de datos

- Todo cambio de esquema va **con migración Alembic** (`make revision m="..."`). El autogenerate se revisa a mano antes de commitear.
- Prohibido `Base.metadata.create_all()` fuera de tests.
- PK UUID (`UUIDPrimaryKeyMixin`), `created_at` y `updated_at` con `timestamptz` (`TimestampMixin`).
- Naming convention de constraints ya configurada en `app/db/base.py`.
- Índices para toda FK y para los campos de filtro frecuentes (`executions.status`, `executions.robot_id`, `executions.created_at`).
- `JSONB` para datos semiestructurados (parámetros y resultados); validar su forma con Pydantic.
- Las migraciones deben ser reversibles (`downgrade` implementado), salvo excepción documentada.
- El commit de la transacción lo hace el service; los repositories no hacen commit.

## 5. Seguridad

- Secretos solo por variables de entorno; `.env` nunca se commitea.
- Passwords con Argon2id (pwdlib). API keys: se muestran una sola vez y se guarda solo hash y prefijo.
- JWT de vida corta (15 min) + refresh token. Validar `exp`, `iat`, `sub` y el tipo de token.
- **Todo endpoint declara su permiso** con `require_permission(...)`, salvo `/health` y `/auth/*`.
  Los endpoints `/auth/*` solo autentican y no evalúan permisos ni responden 403: login es
  público, refresh requiere un refresh token válido y los demás requieren un access token válido.
- Mínimo privilegio: los robots solo actualizan **sus** ejecuciones.
- SSRF: `trigger_url` validado contra `APP_TRIGGER_ALLOWED_HOSTS`; sin redirects automáticos.
- Nunca loguear passwords, tokens, API keys, headers `Authorization` ni payloads sensibles.
- Validar y acotar tamaños de entrada (parámetros, resultados y strings).
- Dependencias actualizadas; revisar advisories antes de cada release.

## 6. Testing

- `tests/unit/`: services y lógica pura, sin DB ni red.
- `tests/integration/` (`@pytest.mark.integration`): endpoints contra PostgreSQL real.
- Toda llamada `httpx` saliente se mockea con `respx`.
- Por cada endpoint de negocio: caso feliz, validación (422), no autenticado (401), sin permiso (403) y no encontrado o conflicto cuando aplique.
- Tests con estructura AAA (Arrange / Act / Assert) y nombres descriptivos: `test_trigger_execution_returns_409_when_robot_inactive`.
- Cobertura mínima 80% (`fail_under` en `pyproject.toml`).

## 7. Git y revisiones

- Rama principal `main`, protegida. Ramas `feat/<change-id>`, `fix/<desc>`, `chore/<desc>`.
- [Conventional Commits](https://www.conventionalcommits.org/): `feat(executions): trigger robot via http`.
- Un PR por change de OpenSpec, con link al change y checklist de tareas.
- CI en verde (lint, tipos, migraciones, tests y build) antes de mergear.

## 8. Flujo con OpenSpec + Claude Code

1. **Explorar** (opcional): `/openspec-explore` para discutir la idea.
2. **Proponer**: `/openspec-propose "<descripción>"`. Genera `proposal.md`, `design.md`, `specs/` y `tasks.md` en `openspec/changes/<change-id>/`.
3. **Revisar**: una persona revisa la propuesta y las specs antes de implementar. Se ajusta con `/openspec-update-change`.
4. **Implementar**: `/openspec-apply-change <change-id>`. Claude Code ejecuta `tasks.md` respetando `CLAUDE.md` y estos lineamientos.
5. **Verificar**: `make check` y `make test` en verde; revisión del PR.
6. **Archivar**: `/openspec-archive-change <change-id>`. Las specs pasan a `openspec/specs/` como fuente de verdad.

Las specs en `openspec/specs/` describen el comportamiento vigente; `docs/` describe el contexto, el stack y las decisiones.

## 9. Docker

- Imagen multi-stage, usuario no-root, sin herramientas de build en runtime.
- La imagen no contiene secretos ni `.env`.
- `docker compose` solo para desarrollo local; en producción se usa la imagen con variables inyectadas.
