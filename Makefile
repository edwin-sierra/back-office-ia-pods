.DEFAULT_GOAL := help
COMPOSE := docker compose
RUN := $(COMPOSE) exec api

.PHONY: help
help: ## Lista los comandos disponibles
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-14s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------- setup
.PHONY: install
install: ## Instala dependencias locales y hooks de pre-commit
	uv sync
	uv run pre-commit install

.env:
	cp .env.example .env

# ---------------------------------------------------------------- docker
.PHONY: up down logs shell build
up: .env ## Levanta api + db en segundo plano
	$(COMPOSE) up -d --build
build: ## Reconstruye la imagen
	$(COMPOSE) build
down: ## Detiene los contenedores
	$(COMPOSE) down
logs: ## Sigue los logs de la api
	$(COMPOSE) logs -f api
shell: ## Shell dentro del contenedor api
	$(RUN) bash

# ---------------------------------------------------------------- db
.PHONY: migrate revision downgrade
migrate: ## Aplica migraciones (alembic upgrade head)
	$(RUN) alembic upgrade head
revision: ## Crea una migración: make revision m="add robots table"
	@test -n "$(m)" || (echo 'Uso: make revision m="mensaje"' && exit 1)
	$(RUN) alembic revision --autogenerate -m "$(m)"
downgrade: ## Revierte la última migración
	$(RUN) alembic downgrade -1

# ---------------------------------------------------------------- quality
.PHONY: test test-unit lint format typecheck check
test: ## Corre todos los tests con cobertura (dentro de docker)
	$(RUN) pytest --cov --cov-report=term-missing
test-unit: ## Corre solo tests unitarios (local, sin DB)
	uv run pytest -m "not integration"
lint: ## Lint con ruff
	uv run ruff check .
format: ## Formatea con ruff
	uv run ruff format .
	uv run ruff check --fix .
typecheck: ## Chequeo de tipos con mypy
	uv run mypy
check: lint typecheck test-unit ## Lint + tipos + tests unitarios (pre-PR)
	uv run ruff format --check .
