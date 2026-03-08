BIN_DIR := .bin
CONFTEST := $(BIN_DIR)/conftest
HELM := $(BIN_DIR)/helm

.PHONY: bootstrap tools conftest helm up down lint typecheck test test-integration format migrate worker api web policy build demo

bootstrap: tools
	python -m pip install --upgrade pip
	python -m pip install -e packages/contracts
	python -m pip install -e services/api[dev]
	cd apps/web && npm install
	python -m pip install pre-commit
	pre-commit install

tools: conftest helm

conftest:
	@mkdir -p $(BIN_DIR)
	@if [ ! -x $(CONFTEST) ]; then ./scripts/install_conftest.sh $(BIN_DIR); fi

helm:
	@mkdir -p $(BIN_DIR)
	@if [ ! -x $(HELM) ]; then ./scripts/install_helm.sh $(BIN_DIR); fi

up:
	docker compose up -d

down:
	docker compose down

migrate:
	cd services/api && alembic upgrade head

api:
	cd services/api && uvicorn app.main:app --reload

worker:
	PYTHONPATH=services/api python workers/quantum-runner/runner/main.py

web:
	cd apps/web && npm run dev

lint:
	cd services/api && ruff check .
	cd apps/web && npm run lint

typecheck:
	cd services/api && mypy .
	cd apps/web && npm run typecheck

test:
	cd services/api && pytest -q

test-integration:
	cd services/api && pytest -q tests/test_integration_async.py

policy: tools
	$(HELM) template qcp infra/helm/quantum-control-plane | $(CONFTEST) test - -p infra/policies --namespace kubernetes.security

build:
	docker build -f services/api/Dockerfile -t qcp-api:local .
	docker build -f workers/quantum-runner/Dockerfile -t qcp-worker:local .
	docker build -f apps/web/Dockerfile -t qcp-web:local .

format:
	cd services/api && ruff format .
	cd apps/web && npm run format

demo:
	./scripts/demo_local.sh

check-conflicts:
	./scripts/check_conflict_markers.sh
