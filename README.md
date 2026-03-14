# Quantum Control Plane (QCP)

An open developer platform for quantum computing — submit QASM circuits, orchestrate multi-step experiments, benchmark providers, and visualise results. Think [MLflow](https://mlflow.org/) or [Airflow](https://airflow.apache.org/), but for quantum.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## Platform Overview

```
┌──────────────────────────────────────────────────────┐
│  Developer Platform: SDK · CLI · REST API (/v1/)     │
├──────────────────────────────────────────────────────┤
│  Control Plane: Experiments · Workflows · Cost Gov   │
├──────────────────────────────────────────────────────┤
│  Execution Plane: Workers · Providers · Simulators   │
├──────────────────────────────────────────────────────┤
│  Dashboard: Experiments · Leaderboard · Demo · Runs  │
└──────────────────────────────────────────────────────┘
```

| Layer | Components |
|-------|-----------|
| **Control Plane** | FastAPI API, experiments, workflows, cost governance, circuit optimisation |
| **Execution Plane** | Async workers, provider adapters, local/Aer simulators, IBM Runtime |
| **Developer Platform** | Python SDK, `qcp` CLI, OpenAPI REST API |
| **Dashboard** | Next.js 14 web console, provider leaderboard, interactive demo |
| **Infrastructure** | PostgreSQL, Redis queue, Prometheus, Grafana, OpenTelemetry |

## ⚡ Quickstart (5 minutes)

**Prerequisites:** Python ≥ 3.11, Node 20, Docker

```bash
make bootstrap    # Install all dependencies (SDK, CLI, API, web)
make up           # Start Postgres + Redis (infrastructure only)
make migrate      # Apply database migrations
make api          # Start API server on port 8000 (terminal 1)
make worker       # Start job worker (terminal 2)
make web          # Start web console on port 3000 (terminal 3)
```

> **Tip:** For zero-Docker local development using SQLite + fakeredis, run
> `python start_local.py` instead of steps 2–5 above, then `make web` in a
> separate terminal.

### Full Docker Stack

To run **all** services (including observability) via Docker:

```bash
make up-all       # Start all services in Docker (postgres, redis, api, worker, web, prometheus, grafana, loki)
```

To start infrastructure and observability only (then run api/worker/web locally):

```bash
make up-infra     # Start Postgres, Redis, Prometheus, Grafana, Loki
make migrate
make api          # terminal 1
make worker       # terminal 2
make web          # terminal 3
```

### Service URLs

| Service | URL |
|---------|-----|
| Web Console | http://localhost:3000 |
| Interactive Demo | http://localhost:3000/demo |
| Provider Leaderboard | http://localhost:3000/providers |
| API Docs (Swagger) | http://localhost:8000/docs |
| API Docs (ReDoc) | http://localhost:8000/redoc |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3001 |

## Authentication

```bash
# Generate an API key
curl -X POST http://localhost:8000/v1/api-keys \
  -H "Content-Type: application/json" \
  -d '{"name": "dev"}' | python3 -m json.tool

export QCP_API_KEY=qcp_...
```

## Python SDK

```bash
pip install -e packages/sdk
```

```python
from quantum_sdk import QCPClient

client = QCPClient(api_key="qcp_...")
job = client.run_experiment(
    name="bell",
    qasm=open("bell.qasm").read(),
    shots=1024,
)
result = client.wait_for_result(job["job"]["id"])
print(result["result"]["counts"])
```

## CLI

```bash
pip install -e packages/cli

qcp login
qcp experiment run bell.qasm --provider local_simulator
qcp experiment list
qcp run status <job_id>
qcp result show <job_id>
```

## REST API

All endpoints are under `/v1/` with OpenAPI documentation at `/docs`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/v1/api-keys` | Create API key |
| `POST` | `/v1/experiments` | Submit experiment |
| `GET` | `/v1/experiments` | List experiments |
| `GET` | `/v1/jobs/{id}` | Get job status |
| `GET` | `/v1/results/{id}` | Get results |
| `GET` | `/v1/providers` | List providers |
| `POST` | `/v1/providers/select` | Smart provider routing |
| `POST` | `/v1/benchmarks` | Run benchmark |
| `GET` | `/v1/benchmarks` | List benchmarks |
| `POST` | `/v1/workflows` | Create workflow |
| `POST` | `/v1/budgets` | Create budget |
| `POST` | `/v1/circuits/optimise` | Optimise circuit |
| `POST` | `/v1/results/compare` | Compare results |

## Project Structure

```
├── services/api/          # FastAPI control plane
├── workers/
│   ├── quantum-runner/    # Job execution worker
│   └── benchmark-runner/  # Auto-benchmark worker
├── apps/web/              # Next.js dashboard
├── packages/
│   ├── sdk/               # Python SDK
│   ├── cli/               # CLI tool (qcp)
│   └── contracts/         # Shared Pydantic models
├── plugins/providers/     # External provider plugins
├── docs/                  # Documentation
├── infra/                 # Helm, Terraform, observability
└── examples/              # Quickstart scripts
```

## Provider Plugins

External providers can be added under `plugins/providers/`:

```python
from plugins.providers.base import BaseProvider, ProviderInfo

class MyProvider(BaseProvider):
    name = "my_provider"
    def info(self) -> ProviderInfo: ...
    async def execute(self, qasm: str, shots: int) -> dict[str, int]: ...
```

Included examples: `aws_braket` (stub), `custom_simulator`.

## Development

```bash
make lint       # ruff + eslint
make typecheck  # mypy + tsc
make test       # pytest
make format     # ruff format
make benchmark  # Run auto-benchmark worker
```

### Makefile Targets

| Target | Description |
|--------|-------------|
| `make bootstrap` | Install all Python and Node dependencies |
| `make up` | Start Postgres + Redis only |
| `make up-infra` | Start Postgres, Redis, Prometheus, Grafana, Loki |
| `make up-all` | Start all services via Docker Compose |
| `make down` | Stop all Docker services |
| `make migrate` | Apply database migrations (Alembic) |
| `make api` | Start API server locally (port 8000) |
| `make worker` | Start job worker locally |
| `make web` | Start web console locally (port 3000) |
| `make lint` | Run ruff + eslint |
| `make typecheck` | Run mypy + tsc |
| `make test` | Run pytest |
| `make build` | Build Docker images |
| `make benchmark` | Run auto-benchmark worker |

## Documentation

- [Getting Started](docs/getting-started.md)
- [Architecture](ARCHITECTURE.md)
- [CLI Reference](docs/cli.md)
- [SDK Guide](docs/sdk.md)
- [Experiments](docs/experiments.md)
- [Workflows](docs/workflows.md)
- [Providers & Plugins](docs/providers.md)
- [Benchmarking](docs/benchmarking.md)
- [Contributing](CONTRIBUTING.md)
- [Roadmap](ROADMAP.md)
