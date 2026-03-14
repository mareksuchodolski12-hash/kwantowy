# Quantum Control Plane (kwantowy)

A developer platform for running quantum circuits as a service — submit QASM circuits, schedule jobs, execute on local simulators or IBM Quantum Runtime, and retrieve results via a clean REST API.

## Architecture

| Component | Technology |
|-----------|-----------|
| API server | FastAPI (Python 3.11) |
| Job queue | Redis (BLPOP + visibility timeout + DLQ) |
| Worker | Async Python, graceful shutdown |
| Database | PostgreSQL (SQLAlchemy + Alembic) |
| Providers | Qiskit local simulator, IBM Quantum Runtime |
| Frontend | Next.js 14 operational console |
| Observability | Prometheus metrics, OpenTelemetry traces, Grafana dashboards |

## ⚡ Quickstart (under 5 minutes)

**Prerequisites:** Python ≥ 3.11, Node 20, Docker

```bash
# 1. Install dependencies
make bootstrap

# 2. Start infrastructure (Postgres + Redis)
make up

# 3. Run database migrations
make migrate

# 4. Start the API server (terminal 1)
make api

# 5. Start the worker (terminal 2)
make worker

# 6. (Optional) Start the web console (terminal 3)
make web
```

Open:
- Web console: http://localhost:3000
- API docs (Swagger UI): http://localhost:8000/docs
- Metrics: http://localhost:8000/metrics
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001

## Authentication

All API endpoints (except `/healthz`, `/readyz`, and `POST /v1/api-keys`) require an `X-API-Key` header.

**Generate your first API key:**

```bash
curl -s -X POST http://localhost:8000/v1/api-keys \
  -H "Content-Type: application/json" \
  -d '{"name": "my-dev-key"}' | python3 -m json.tool
```

Use the returned `key` value in all subsequent requests:

```bash
export QCP_API_KEY=qcp_...
curl -s http://localhost:8000/v1/jobs \
  -H "X-API-Key: $QCP_API_KEY" | python3 -m json.tool
```

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/v1/api-keys` | Create an API key (unauthenticated) |
| `GET` | `/v1/api-keys` | List API keys |
| `DELETE` | `/v1/api-keys/{id}` | Revoke an API key |
| `POST` | `/v1/experiments` | Submit a circuit (201 Created) |
| `POST` | `/v1/jobs` | Submit a circuit (alias) |
| `GET` | `/v1/jobs` | List all jobs |
| `GET` | `/v1/jobs/{job_id}` | Get job status |
| `GET` | `/v1/jobs/{job_id}/result` | Get job result |
| `GET` | `/v1/results/{job_id}` | Get job result (alias) |
| `GET` | `/healthz` | Health check |
| `GET` | `/readyz` | Readiness check |

## Submit a circuit (curl)

```bash
curl -s -X POST http://localhost:8000/v1/experiments \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $QCP_API_KEY" \
  -d '{
    "name": "bell-state",
    "circuit": {
      "qasm": "OPENQASM 2.0; include \"qelib1.inc\"; qreg q[2]; creg c[2]; h q[0]; cx q[0],q[1]; measure q -> c;",
      "shots": 1024
    }
  }' | python3 -m json.tool
```

## Python SDK

```bash
pip install packages/sdk
```

```python
from quantum_sdk import QCPClient

client = QCPClient(api_key="qcp_...", base_url="http://localhost:8000")

# Submit a circuit
resp = client.run_circuit(
    name="bell-state",
    qasm='OPENQASM 2.0; include "qelib1.inc"; qreg q[2]; creg c[2]; h q[0]; cx q[0],q[1]; measure q -> c;',
    shots=1024,
)
job_id = resp["job"]["id"]

# Poll until done and get result
result = client.wait_for_result(job_id)
print(result["result"]["counts"])  # e.g. {"00": 512, "11": 512}
```

See `examples/quickstart.py` for a complete runnable example.

## Example circuits

| Circuit | QASM |
|---------|------|
| Single qubit flip | `OPENQASM 2.0; include "qelib1.inc"; qreg q[1]; creg c[1]; x q[0]; measure q[0] -> c[0];` |
| Hadamard superposition | `OPENQASM 2.0; include "qelib1.inc"; qreg q[1]; creg c[1]; h q[0]; measure q[0] -> c[0];` |
| Bell state | `OPENQASM 2.0; include "qelib1.inc"; qreg q[2]; creg c[2]; h q[0]; cx q[0],q[1]; measure q -> c;` |

## IBM Quantum Runtime

Set environment variables to run on real quantum hardware:

```bash
export QCP_IBM_RUNTIME_ENABLED=true
export QCP_IBM_RUNTIME_TOKEN=<your-ibm-token>
export QCP_IBM_RUNTIME_CHANNEL=ibm_quantum
export QCP_IBM_RUNTIME_INSTANCE=<hub/group/project>
export QCP_IBM_RUNTIME_BACKEND=ibm_brisbane
```

Then submit with `"provider": "ibm_runtime"` in your request.

## Environment configuration

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

## Docker deployment

```bash
# Start everything with Docker Compose
docker compose up -d

# Run migrations
docker compose exec api alembic upgrade head

# Generate an API key
docker compose exec api python -c "
import asyncio, sys
sys.path.insert(0, '.')
from app.repositories.api_keys import generate_api_key
print(generate_api_key())
"
```

## Development

```bash
make lint       # ruff + eslint
make typecheck  # mypy + tsc
make test       # pytest
make format     # ruff format
```

## Documentation

- `docs/architecture/` — platform architecture and ADRs
- `docs/runbooks/` — operational runbooks
- `docs/demo-walkthrough.md` — end-to-end demo guide

