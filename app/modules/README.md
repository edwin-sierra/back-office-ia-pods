# Módulos de dominio

Un paquete por bounded context. Cada módulo sigue la misma estructura:

| Archivo         | Responsabilidad                                                             |
|-----------------|------------------------------------------------------------------------------|
| `models.py`     | Modelos SQLAlchemy (heredan de `app.db.base.Base`).                          |
| `schemas.py`    | Schemas Pydantic de entrada/salida: `XCreate`, `XUpdate`, `XRead`, filtros. |
| `repository.py` | Acceso a datos. Solo queries; sin reglas de negocio; no hace commit.        |
| `service.py`    | Reglas de negocio, transacciones (commit), orquestación. Lanza `AppError`.  |
| `router.py`     | Endpoints HTTP. Valida, aplica permisos, delega en el service.              |
| `client.py`     | (Opcional) Clientes HTTP externos con `httpx.AsyncClient`.                  |

Módulos actuales:

- `robots/` — catálogo de robots.
- `executions/` — ejecuciones por robot.
- `iam/` — usuarios, roles, permisos y API keys.

Al crear modelos nuevos, importarlos en `app/db/models.py` para que Alembic los detecte.
