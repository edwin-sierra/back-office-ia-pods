# Back Office IA Pods — RPA API

API (FastAPI + PostgreSQL, dockerizada) que funciona como fuente de datos de una flota de robots RPA:

- **Catálogo** de robots.
- **Ejecuciones**: disparar un robot vía HTTP, consultar sus ejecuciones y actualizar su estado o resultado.
- **Roles y permisos** (RBAC) para usuarios, y API keys para robots.

> Estado: estructura base. Las features se implementan como changes de [OpenSpec](openspec/) (ver el roadmap en [docs/brief.md](docs/brief.md#roadmap-changes-de-openspec)).

## Requisitos

- Docker y Docker Compose
- [uv](https://docs.astral.sh/uv/) (desarrollo local, lint y tipos)
- Node.js ≥ 20 + `npm i -g @fission-ai/openspec` (para el flujo OpenSpec)

## Quickstart

```bash
cp .env.example .env        # o lo crea `make up` automáticamente
make up                     # api + postgres
make migrate                # aplica migraciones
open http://localhost:8000/docs
```

Verificar:

```bash
curl localhost:8000/api/v1/health         # liveness
curl localhost:8000/api/v1/health/ready   # readiness (DB)
```

## Desarrollo

```bash
make install     # uv sync + pre-commit install
make check       # ruff + format + mypy + tests unitarios
make test        # todos los tests (en docker, con DB)
make help        # todos los comandos
```

## Documentación

| Documento | Contenido |
|---|---|
| [docs/brief.md](docs/brief.md) | Problema, objetivos, alcance, actores, permisos, roadmap |
| [docs/stack.md](docs/stack.md) | Stack y justificación |
| [docs/architecture.md](docs/architecture.md) | Capas, flujo de ejecución, máquina de estados, modelo |
| [docs/guidelines.md](docs/guidelines.md) | Lineamientos y buenas prácticas |
| [docs/adr/](docs/adr/) | Decisiones de arquitectura |
| [CLAUDE.md](CLAUDE.md) | Reglas para Claude Code |
| [openspec/](openspec/) | Specs vigentes y changes en curso |
