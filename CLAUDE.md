# CLAUDE.md

Guía para Claude Code en este repositorio. Leer antes de cualquier cambio.

## Qué es

API FastAPI (dockerizada) que es la fuente de datos de robots RPA: **catálogo**, **ejecuciones** (disparo vía HTTP, consulta y actualización) y **roles/permisos**.

Contexto completo:
- [docs/brief.md](docs/brief.md): problema, alcance, actores, permisos y roadmap.
- [docs/architecture.md](docs/architecture.md): capas, flujo de ejecución, máquina de estados y modelo.
- [docs/guidelines.md](docs/guidelines.md): reglas de código, API, DB, seguridad, testing y Git.
- [docs/stack.md](docs/stack.md) y [docs/adr/](docs/adr/): stack y decisiones.

## Comandos

```bash
make up            # levanta api + db (docker compose), crea .env si falta
make migrate       # alembic upgrade head (dentro del contenedor)
make revision m="add robots table"   # nueva migración autogenerada
make test          # todos los tests con cobertura (dentro de docker, con DB)
make check         # ruff + format + mypy + tests unitarios (local, sin DB)
make format        # formatear y autofix
uv run pytest tests/unit/test_app.py -k nombre   # un test puntual
```

API local: http://localhost:8000/docs

## Estructura

```
app/
  main.py                 create_app(): middlewares, handlers y routers
  core/                   config (Settings APP_*), logging, exceptions (AppError → problem+json), security
  db/                     base.py (Base, mixins), session.py (get_session), models.py (registro para Alembic)
  api/deps.py             SessionDep, SettingsDep (y luego CurrentUserDep, require_permission)
  api/v1/router.py        registra los routers de cada módulo
  modules/<modulo>/       models · schemas · repository · service · router · client
migrations/               Alembic async
tests/unit · tests/integration (@pytest.mark.integration, requiere Postgres)
openspec/                 specs (fuente de verdad) y changes
```

## Reglas no negociables

1. **Capas**: router → service → repository. Sin lógica de negocio ni queries en los routers. Los services lanzan `AppError` (nunca `HTTPException`) y hacen commit; los repositories no hacen commit.
2. **Permisos**: todo endpoint de negocio declara `require_permission("recurso:accion")`.
3. **DB**: todo cambio de esquema va con migración Alembic revisada. Registrar los modelos nuevos en `app/db/models.py`. Nunca `create_all` fuera de tests.
4. **Tests**: toda capability nueva con tests (feliz, 422, 401, 403, 404/409). HTTP saliente mockeado con `respx`. Cobertura ≥ 80%.
5. **Tipos y estilo**: `mypy --strict` y `ruff` en verde. Type hints en todo.
6. **Seguridad**: no loguear ni persistir secretos, tokens, passwords o API keys en texto plano. `trigger_url` validado contra la allowlist.
7. **Config**: solo vía `get_settings()`; agregar las variables nuevas a `.env.example`.
8. **Idioma**: código, endpoints, tablas y commits en inglés; docs y OpenSpec en español.

## Flujo de trabajo (OpenSpec)

Toda feature o cambio de comportamiento pasa por un change de OpenSpec:

1. `/openspec-propose "<idea>"` → `openspec/changes/<id>/` (proposal, design, specs, tasks).
2. Esperar la revisión humana de la propuesta antes de implementar.
3. `/openspec-apply-change <id>`: implementar las tareas en orden y marcarlas al completarlas.
4. Correr `make check` (y `make test` si hay DB) antes de dar una tarea por terminada.
5. `/openspec-archive-change <id>` una vez mergeado.

Los cambios triviales (typos, docs y tooling) no requieren change. Commits con Conventional Commits; ramas `feat/<change-id>`.
