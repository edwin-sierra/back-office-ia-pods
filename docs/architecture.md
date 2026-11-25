# Arquitectura

## Vista general

```
             ┌───────────────┐   JWT    ┌──────────────────────────────┐
 Usuarios ──▶│   Cliente /   │ ───────▶ │        API (FastAPI)          │
             │   Front-end   │          │  /api/v1                      │
             └───────────────┘          │  ┌────────┐ ┌──────────────┐ │
                                        │  │  iam   │ │    robots    │ │
                                        │  └────────┘ └──────────────┘ │
                                        │  ┌──────────────────────────┐ │      ┌────────────┐
                                        │  │        executions        │─┼─────▶│ PostgreSQL │
                                        │  └───────────┬──────────────┘ │      └────────────┘
                                        └──────────────┼───────────────┘
                                   HTTP trigger        │        ▲  PATCH /executions/{id}
                                   (httpx)             ▼        │  (API key)
                                        ┌──────────────────────────────┐
                                        │   Robot RPA / Runner externo  │
                                        └──────────────────────────────┘
```

## Capas

Cada módulo de `app/modules/<modulo>/` sigue esta estructura:

```
router.py      → HTTP: parsea y valida la entrada, aplica auth y permisos, delega y serializa la salida
   │
service.py     → Reglas de negocio, máquina de estados, transacciones (commit), orquestación
   │      └──▶ client.py   → Integraciones HTTP externas (httpx), aisladas y mockeables
   │
repository.py  → Acceso a datos con SQLAlchemy (solo queries, sin commit)
   │
models.py      → Tablas (SQLAlchemy)          schemas.py → DTOs (Pydantic)
```

Reglas:

- Un router **nunca** accede al repository ni hace queries directamente.
- Un service **nunca** importa `fastapi` ni lanza `HTTPException`: lanza subclases de `AppError` (`app/core/exceptions.py`), que se traducen a `problem+json`.
- Un módulo puede usar el **service** de otro módulo, pero nunca su repository ni sus modelos internos.
- `app/core/` contiene lo transversal: config, logging, errores y seguridad. `app/db/` contiene la base declarativa y las sesiones.

## Flujo de ejecución de un robot

```
Operador            API                         DB                Robot (trigger_url)
   │ POST /robots/{id}/executions               │                        │
   │  {params} + Idempotency-Key                │                        │
   │──────────▶│ valida permiso executions:trigger                       │
   │           │ valida robot activo + params    │                        │
   │           │ INSERT execution (PENDING) ────▶│                        │
   │           │ POST trigger_url {execution_id, params, callback_url} ──▶│
   │           │◀──────────────────────────────── 2xx / error / timeout ──│
   │           │ UPDATE status = TRIGGERED       │                        │
   │           │         o TRIGGER_FAILED ──────▶│                        │
   │◀──────────│ 202 {execution}                 │                        │
   │           │                                  │                        │
   │           │◀──── PATCH /executions/{id} {status: RUNNING} (API key) ─│
   │           │◀──── PATCH /executions/{id} {status: SUCCEEDED, result} ─│
```

### Máquina de estados

```
PENDING ──▶ TRIGGERED ──▶ RUNNING ──▶ SUCCEEDED
   │            │            ├──────▶ FAILED
   │            │            └──────▶ CANCELLED
   │            └──────────────────▶ FAILED | CANCELLED
   └──▶ TRIGGER_FAILED
```

- Los estados finales (`SUCCEEDED`, `FAILED`, `CANCELLED`, `TRIGGER_FAILED`) son inmutables.
- Una transición inválida responde `409 Conflict`.
- `started_at` se completa al pasar a `RUNNING`, y `finished_at` al llegar a un estado final.
- Idempotencia: si se repite un `Idempotency-Key` del mismo usuario y robot, se devuelve la misma ejecución.

### Disparo HTTP (trigger)

- `httpx.AsyncClient` con timeout (`APP_TRIGGER_TIMEOUT_SECONDS`) y retries acotados solo ante errores de conexión.
- El `trigger_url` debe pertenecer a `APP_TRIGGER_ALLOWED_HOSTS` (mitiga SSRF).
- Se guarda un resumen del disparo (status HTTP, latencia, error truncado). Nunca se guardan headers de autenticación.
- El secreto de autenticación del trigger, si existe, se guarda cifrado o se referencia por nombre de variable de entorno. Se define en `add-robot-catalog`.

## Modelo de dominio (conceptual)

```
User ─┬─< UserRole >─── Role ─┬─< RolePermission >─── Permission
      │                       │
      │ triggered_by          │
      ▼                       │
Execution >──── Robot ───< ApiKey (opcional: scoped a un robot)
```

| Entidad | Campos clave |
|---|---|
| `Robot` | id, code (único), name, description, version, trigger_url, trigger_method, trigger_timeout, params_schema (JSONB), is_active, timestamps |
| `Execution` | id, robot_id, triggered_by_user_id, status, params (JSONB), result (JSONB), error, trigger_response (JSONB), idempotency_key, started_at, finished_at, timestamps |
| `User` | id, email (único), full_name, password_hash, is_active, timestamps |
| `Role` | id, name (único), description |
| `Permission` | id, code (único, `recurso:accion`), description |
| `ApiKey` | id, name, prefix, key_hash, robot_id (nullable), scopes, expires_at, revoked_at, last_used_at |

El esquema definitivo de cada entidad se define en su change de OpenSpec.

## Cross-cutting

- **Errores**: RFC 9457 (`application/problem+json`) con `type`, `title`, `status`, `detail`, `instance` y `code`.
- **Observabilidad**: logs JSON con `request_id` (header `X-Request-ID`), `/api/v1/health` (liveness) y `/api/v1/health/ready` (DB).
- **Configuración**: solo por variables de entorno (`APP_*`), validadas al iniciar.
- **Tiempo**: todo en UTC, `timestamptz`.
