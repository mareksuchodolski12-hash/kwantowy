.PHONY: bootstrap up down lint typecheck test test-integration format migrate worker api web policy build demo benchmark

bootstrap:
	python -m pip install --upgrade pip
	python -m pip install -e packages/contracts
	python -m pip install -e packages/sdk
	python -m pip install -e packages/cli
	python -m pip install -e services/api[dev]
	cd apps/web && npm install
	python -m pip install pre-commit
	pre-commit install

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
	cd packages/cli && ruff check .
	cd apps/web && npm run lint

typecheck:
	cd services/api && mypy .
	cd apps/web && npm run typecheck

test:
	cd services/api && pytest -q

test-integration:
	cd services/api && pytest -q tests/test_integration_async.py

policy:
	conftest test infra/helm/quantum-control-plane/templates -p infra/policies

build:
	docker build -f services/api/Dockerfile -t qcp-api:local .
	docker build -f workers/quantum-runner/Dockerfile -t qcp-worker:local .
	docker build -f apps/web/Dockerfile -t qcp-web:local .

format:
	cd services/api && ruff format .
	cd apps/web && npm run format

demo:
	@echo "1) make up && make migrate"
	@echo "2) make api, make worker, make web"
	@echo "3) submit run from http://localhost:3000"
	@echo "4) inspect metrics at /metrics, Prometheus :9090, Grafana :3001"

benchmark:
	PYTHONPATH=services/api python workers/benchmark-runner/benchmark_worker.py
