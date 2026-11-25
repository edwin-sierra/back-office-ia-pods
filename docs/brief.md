# Brief del proyecto — Back Office IA Pods (RPA)

## Problema

Hoy no hay una fuente única de verdad sobre los robots RPA: cuáles existen, cómo se disparan, quién los ejecutó, con qué parámetros y qué resultado tuvieron. Tampoco hay un control de acceso que defina quién puede consultar, configurar u operar cada robot.

## Objetivo

Construir una API (FastAPI, dockerizada) que sea **el sistema de registro** de los robots RPA y sus ejecuciones, con control de acceso basado en roles.

### Objetivos concretos

1. **Catálogo de robots**: alta, baja lógica, modificación y consulta. Incluye la configuración necesaria para dispararlo: `trigger_url`, método, autenticación, timeout y esquema de parámetros.
2. **Ejecuciones**:
   - **Ejecutar**: la API registra la ejecución y llama por HTTP al endpoint del robot para dispararlo.
   - **Consultar**: listado con filtros (robot, estado, fechas, usuario) y detalle.
   - **Actualizar**: el robot (o su runner) reporta su avance y su resultado final.
3. **Trazabilidad**: quién disparó, cuándo, con qué parámetros, cuánto tardó y qué devolvió.
4. **Roles y permisos**: RBAC configurable. Cada endpoint exige un permiso explícito.

## Actores

| Actor            | Tipo     | Descripción                                                                  |
|------------------|----------|------------------------------------------------------------------------------|
| Admin            | Usuario  | Gestiona usuarios, roles, permisos, API keys y el catálogo.                  |
| Operador         | Usuario  | Consulta el catálogo, dispara ejecuciones y consulta su estado.              |
| Viewer           | Usuario  | Solo lectura del catálogo y de las ejecuciones.                              |
| Robot / Runner   | Servicio | Se autentica con API key y actualiza el estado y el resultado de sus ejecuciones. |

## Alcance v1

- API REST `/api/v1` documentada con OpenAPI.
- Persistencia en PostgreSQL con migraciones Alembic.
- Autenticación JWT (usuarios) + API keys (robots).
- RBAC con roles base sembrados (`admin`, `operator`, `viewer`).
- Disparo síncrono vía HTTP con timeout y registro del resultado del disparo.

### Fuera de alcance (v1)

- Interfaz de usuario (front-end).
- Scheduling o cron de ejecuciones.
- Colas o workers propios para ejecutar robots.
- Multi-tenant.
- Gestión de artefactos o binarios de los robots.

## Glosario

| Término          | Definición                                                                               |
|------------------|-------------------------------------------------------------------------------------------|
| **Robot**        | Automatización RPA registrada en el catálogo.                                            |
| **Execution**    | Una corrida de un robot, con su estado, parámetros, resultado y tiempos.                 |
| **Trigger**      | Llamado HTTP que la API hace al `trigger_url` del robot para iniciar una ejecución.       |
| **Callback**     | Actualización que el robot envía a la API (`PATCH /executions/{id}`).                     |
| **Role**         | Conjunto nombrado de permisos asignable a usuarios.                                       |
| **Permission**   | Capacidad atómica con formato `<recurso>:<accion>`, por ejemplo `executions:trigger`.     |
| **API Key**      | Credencial de servicio para robots y runners. Se guarda solo su hash.                     |

## Permisos iniciales

| Permiso               | admin | operator | viewer | robot (API key) |
|-----------------------|:-----:|:--------:|:------:|:---------------:|
| `robots:read`         |   ✔   |    ✔     |   ✔    |                 |
| `robots:write`        |   ✔   |          |        |                 |
| `executions:read`     |   ✔   |    ✔     |   ✔    |  ✔ (propias)    |
| `executions:trigger`  |   ✔   |    ✔     |        |                 |
| `executions:update`   |   ✔   |          |        |  ✔ (propias)    |
| `iam:manage`          |   ✔   |          |        |                 |

## Roadmap (changes de OpenSpec)

Orden sugerido. Cada ítem es un change independiente con su propuesta, specs, diseño y tareas.

1. **`add-iam-auth`**: usuarios, hash argon2, `POST /auth/login`, `POST /auth/refresh`, `GET /auth/me`.
2. **`add-rbac`**: roles, permisos, asignaciones, seed de roles base y dependencia `require_permission(...)`.
3. **`add-robot-catalog`**: CRUD de robots y validación de `trigger_url` contra una allowlist.
4. **`add-robot-executions`**: disparo HTTP, listado, detalle, máquina de estados e idempotencia.
5. **`add-service-api-keys`**: emisión, rotación y revocación de API keys; `PATCH /executions/{id}` autenticado por robot.
6. **`add-audit-log`** (opcional): registro de acciones administrativas.

## Criterios de éxito

- Un operador puede disparar un robot y ver su estado final sin intervención manual.
- Toda ejecución queda trazada: usuario, parámetros, tiempos y resultado.
- Ningún endpoint de negocio es accesible sin el permiso correspondiente (cubierto por tests).
- `docker compose up` levanta el entorno completo en un solo paso.
