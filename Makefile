.DEFAULT_GOAL := ajuda
BACK := cd backend &&
FRONT := cd frontend &&

.PHONY: ajuda instalar db db-parar api worker portal \
        formatar lint tipos testes testes-unit testes-integracao verificar \
        migracao migrar

ajuda: ## Lista os comandos
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-18s %s\n", $$1, $$2}'

# ---------------------------------------------------------------- ambiente
instalar: ## Instala dependências do backend (uv) e do frontend (pnpm)
	$(BACK) uv sync
	$(FRONT) pnpm install

db: ## Sobe o PostgreSQL (dev + testes) no Docker
	docker compose up -d --wait db

db-parar: ## Para o PostgreSQL
	docker compose stop db

# ---------------------------------------------------------------- execução
api: ## API FastAPI com reload em http://localhost:8000
	$(BACK) uv run uvicorn lastro.entrypoints.api.app:app --reload

worker: ## Worker de tarefas
	$(BACK) uv run lastro-worker

portal: ## Portal React (Vite) em http://localhost:5173
	$(FRONT) pnpm dev

# ---------------------------------------------------------------- qualidade
formatar: ## Formata e corrige automaticamente (ruff + biome)
	$(BACK) uv run ruff format . && uv run ruff check --fix .
	$(FRONT) pnpm check:fix

lint: ## Lint sem alterar arquivos (inclui regra de camadas)
	$(BACK) uv run ruff format --check . && uv run ruff check .
	$(FRONT) pnpm check

tipos: ## Checagem de tipos (mypy strict + tsc)
	$(BACK) uv run mypy
	$(FRONT) pnpm tipos

testes: ## Todos os testes com cobertura (precisa de make db)
	$(BACK) uv run pytest --cov --cov-report=term-missing

testes-unit: ## Só testes unitários, sem banco
	$(BACK) uv run pytest -m "not integration" --cov --cov-report=term-missing

testes-integracao: ## Só testes de integração (precisa de make db)
	$(BACK) uv run pytest -m integration

verificar: lint tipos testes ## Tudo que precisa passar antes de um commit

# ---------------------------------------------------------------- migrações
migracao: ## Gera migração a partir dos modelos: make migracao m="descricao"
	@test -n "$(m)" || (echo 'uso: make migracao m="descricao"' && exit 1)
	$(BACK) uv run alembic revision --autogenerate -m "$(m)"

migrar: ## Aplica as migrações pendentes
	$(BACK) uv run alembic upgrade head
