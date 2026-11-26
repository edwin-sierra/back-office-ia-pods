## Context

El módulo `app/modules/iam/` y la API versionada son actualmente puntos de extensión: todavía no
hay usuarios, autenticación ni routers de negocio. IP-742 añade usuarios persistidos, bootstrap,
login, renovación, perfil autenticado y una dependencia reutilizable, sin incorporar RBAC. La
solución sigue el patrón existente router → service → repository, usa SQLAlchemy async y Alembic,
y reutiliza las primitivas JWT, hashing, errores y configuración previstas en el repositorio.

## Goals / Non-Goals

### Goals

- Cumplir todos los escenarios de `specs/iam-auth/spec.md`: persistencia y bootstrap; login válido,
  credenciales incorrectas, usuario inactivo y cuerpo inválido; renovación válida, token no válido
  y cuerpo inválido; perfil actual válido o no autenticado/inactivo; y resolución/protección mediante
  `CurrentUserDep`.
- Aplicar las duraciones existentes de access token (15 minutos) y refresh token (7 días), y no
  exponer ni registrar contraseñas o hashes.
- Mantener fuera de alcance roles, permisos, ABM de usuarios y cualquier otra funcionalidad no
  especificada.

### Non-Goals

- Incorporar RBAC o responder 403 por permisos en estos endpoints.
- Añadir un proveedor externo de identidad, almacenamiento de sesiones, revocación adicional,
  servicios, dependencias o infraestructura no requeridos por las specs.

## Decisions

### 1. Implementar IAM en su bounded context y conectar sus endpoints en la API v1

El módulo `app/modules/iam/` será dueño del modelo, schemas, repository, service, router y comando
de bootstrap; el router valida y delega, el service mantiene las reglas y transacciones, y el
repository se limita a consultas. El router IAM se registra en `app/api/v1/router.py`; las
dependencias HTTP comunes permanecen en `app/api/deps.py`, donde se incorpora `CurrentUserDep`.
Login es público, refresh autentica con refresh token y los endpoints protegidos reciben el usuario
activo mediante la dependencia. No se introduce una capa o abstracción nueva. Esto sigue
`CLAUDE.md` (capas, `app/api/deps.py`, estructura modular y `make check`/`make test`),
`docs/architecture.md` y `docs/guidelines.md` (router → service → repository, API `/api/v1` y
errores), `openspec/config.yaml` (stack y estructura de módulos) y `docs/adr/0001-record-architecture-decisions.md`.
Lo respaldan `app/modules/README.md`, `app/modules/iam/__init__.py`, `app/main.py`,
`app/api/v1/router.py`, `app/api/deps.py`, `tests/conftest.py`, `tests/unit/test_app.py` y
`tests/integration/test_health.py`; `pyproject.toml` concreta las librerías de aplicación y
pytest, y `Makefile` define los comandos de verificación.

### 2. Persistir usuarios con Alembic y crear el inicial mediante un comando seguro

El modelo `User` tendrá UUID, email único, nombre completo, hash de contraseña, estado activo y los
timestamps compartidos; se registrará en `app/db/models.py` para Alembic. Una migración Alembic
añadirá la tabla, sin asignar roles ni insertar usuarios. El service de bootstrap crea un usuario
activo cuando el email no existe; si ya existe, informa conflicto y conserva intacto el registro.
El comando se implementa en IAM sin añadir una biblioteca de CLI; la contraseña se solicita sin
eco y no se incluye en la salida ni en logs. El hash usa Argon2id (`pwdlib`), no texto claro.
Alternativa descartada: crear usuarios por un endpoint o asignar un rol inicial; ninguno está en
las specs y el primero aún no puede autenticarse para usar el back office. Sigue `CLAUDE.md`
(migración Alembic revisada, registro de modelos, commits en service y `make migrate`),
`docs/guidelines.md` (UUID/timestamps, unicidad, reversibilidad y hash Argon2id),
`docs/architecture.md` y `openspec/config.yaml`; aplica `docs/adr/0003-auth-jwt-and-api-keys.md`
para Argon2id. La implementación del repositorio que lo respalda está en `app/db/base.py`,
`app/db/models.py`, `app/db/session.py`, `migrations/env.py`, `migrations/script.py.mako`,
`alembic.ini`, `Makefile`, `pyproject.toml` y `app/modules/iam/__init__.py`; las convenciones y
referencias de integración están en `tests/conftest.py`, `tests/integration/test_health.py` y
`.github/workflows/ci.yml`.

### 3. Emitir y validar JWT diferenciados para access y refresh

Login acepta email y contraseña de un usuario activo; verifica el hash y emite un par de JWT:
access de 15 minutos y refresh de 7 días, con el tipo de token distinguible. Refresh solo acepta
un refresh token válido y emite un par nuevo. La validación comprueba expiración, emisión,
identidad (`sub`) y tipo; resuelve al usuario y rechaza identidades inactivas. `CurrentUserDep` y
`GET /auth/me` aceptan exclusivamente access tokens válidos de usuarios activos. Se usa
`Settings`/`APP_*` y el mecanismo JWT ya previsto, sin imprimir ni registrar credenciales o tokens.
Esto aplica `docs/adr/0003-auth-jwt-and-api-keys.md` (JWT propio, duraciones y secreto de
configuración), `docs/guidelines.md` (validación de claims, Argon2id y no registrar secretos),
`docs/stack.md` y `CLAUDE.md` (librerías, configuración y verificación); el código de referencia
es `app/core/security.py`, `app/core/config.py`, `app/core/logging.py`, `app/api/deps.py`,
`app/db/session.py` y `pyproject.toml`. El formato de error existente se respalda en
`app/core/exceptions.py` y `tests/unit/test_app.py`.

Escenarios cubiertos explícitamente:

- **Inicio de sesión — Login exitoso:** credenciales válidas de usuario activo producen HTTP 200
  con `access_token`, `refresh_token`, `token_type: "bearer"` y `expires_in: 900`.
- **Inicio de sesión — Credenciales incorrectas:** email inexistente y contraseña incorrecta
  producen HTTP 401 con el mismo mensaje genérico, sin revelar si existe el email.
- **Inicio de sesión — Usuario inactivo:** credenciales correctas de usuario inactivo producen
  HTTP 401 y no habilitan la sesión.
- **Inicio de sesión — Cuerpo de login inválido:** falta de email o contraseña, o email inválido,
  produce HTTP 422 y `application/problem+json`.
- **Renovación de tokens — Renovar tokens:** refresh válido de usuario activo produce HTTP 200 con
  un nuevo par, `token_type: "bearer"` y `expires_in: 900`.
- **Renovación de tokens — Rechazar un token que no es un refresh válido:** access token, refresh
  inválido o expirado, o usuario inactivo producen HTTP 401; no se emite un nuevo par.
- **Renovación de tokens — Cuerpo de renovación inválido:** falta del refresh token o forma
  inválida produce HTTP 422 y `application/problem+json`.
- **Usuario autenticado actual — Consultar el perfil autenticado:** access válido de usuario activo
  produce HTTP 200 con id, email, nombre completo, estado y timestamps; ni contraseña ni hash
  aparecen en la respuesta.
- **Usuario autenticado actual — Rechazar identidad no autenticada o inactiva:** ausencia de token,
  token inválido o expirado, o usuario inactivo producen HTTP 401.
- **Dependencia de usuario actual — Resolver usuario autenticado:** un endpoint que usa
  `CurrentUserDep` recibe la identidad correspondiente a un access token válido de usuario activo.
- **Dependencia de usuario actual — Proteger endpoint sin identidad válida:** falta de access
  válido o usuario inactivo produce HTTP 401.

Los errores de API conservan el formato RFC 9457 establecido por
`docs/architecture.md`, `docs/guidelines.md` y `app/core/exceptions.py`; para las respuestas de
validación, el media type y el estado son los requeridos arriba. Los escenarios de autenticación
no generan una respuesta 403 por permisos.

### 4. Aplicar la excepción de autenticación sin introducir RBAC en IP-742

Los endpoints `/auth/*` solo autentican: login no requiere token, refresh exige refresh token y
`/me` exige access token; ninguno declara ni evalúa permisos RBAC. Se descarta aplicar
`require_permission` en esta historia porque contradice los escenarios y el alcance pre-RBAC
confirmados por la propuesta. Esta excepción coincide con `docs/guidelines.md` y
`docs/adr/0003-auth-jwt-and-api-keys.md` sigue siendo la decisión base de JWT, pero su afirmación
general sobre permisos para cada endpoint sí requiere una excepción explícita para auth. Además,
`openspec/config.yaml` todavía exceptúa solo login, por lo que también es inconsistente con la
spec aprobada. Se registra para el planificador la tarea de armonizar esa regla y crear un ADR que
amplíe o enmiende ADR 0003; este diseño no edita ninguno de esos archivos. Referencias:
`CLAUDE.md`, `docs/guidelines.md`, `openspec/config.yaml`, `docs/adr/0003-auth-jwt-and-api-keys.md`,
`app/api/deps.py`, `app/api/v1/router.py`, `openspec/changes/change-ip-742/proposal.md` y
`openspec/changes/change-ip-742/specs/iam-auth/spec.md`; `tests/unit/test_app.py` y
`tests/conftest.py` respaldan la convención de integración HTTP de la aplicación.

## Risks / Trade-offs

- **La regla RBAC vigente en `openspec/config.yaml` y la formulación general de ADR 0003 podrían
  llevar a añadir permisos y cambiar los resultados especificados.** Mitigación: seguir la
  excepción aprobada para `/auth/*` en este cambio y hacer que el planificador armonice la regla
  del config y registre la excepción en un nuevo ADR antes de reutilizarla como convención.
- **La contraseña usada en el bootstrap podría exponerse al operador o en logs.** Mitigación:
  solicitarla sin eco, almacenarla únicamente como hash Argon2id y no imprimirla ni registrarla;
  login devuelve el mismo error genérico para email inexistente y contraseña incorrecta.
- **Revertir la migración después de crear usuarios eliminaría sus registros y hashes.** Mitigación:
  hacer downgrade únicamente antes de poblar la tabla; si ya hay cuentas, preservar los datos con un
  respaldo seguro antes de revertir o preferir una corrección hacia delante.

## Migration Plan

1. Añadir la migración Alembic que crea la tabla de usuarios con UUID, email único, nombre completo,
   hash, estado y timestamps, siguiendo los mixins y convenciones actuales. No hay registros
   preexistentes que convertir ni backfill que ejecutar.
2. Aplicar la migración antes de desplegar el código que la usa (`make migrate` ejecuta
   `alembic upgrade head`); después desplegar el módulo y utilizar el comando de bootstrap para
   crear el primer usuario activo.
3. Reversión: retirar primero el código de IAM y luego aplicar el downgrade Alembic para eliminar
   la tabla. El downgrade no recupera usuarios creados: solo se ejecuta si la tabla sigue vacía;
   si ya contiene cuentas, conservarlas mediante un respaldo protegido antes de revertir o corregir
   hacia delante. El formato de migración existente implementa `upgrade()`/`downgrade()` en
   `migrations/script.py.mako`; `docs/guidelines.md`, `CLAUDE.md` y `Makefile` definen reversibilidad,
   revisión y operación de Alembic.
