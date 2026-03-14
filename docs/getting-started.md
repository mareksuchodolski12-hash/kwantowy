# Getting Started

## Prerequisites

- Python ≥ 3.11
- Node.js ≥ 20
- Docker and Docker Compose

## Quick Start (5 minutes)

```bash
# 1. Clone the repository
git clone https://github.com/your-org/kwantowy.git
cd kwantowy

# 2. Install dependencies
make bootstrap

# 3. Start infrastructure (Postgres + Redis only)
make up

# 4. Apply database migrations
make migrate

# 5. Start the API server (port 8000)
make api

# 6. In another terminal — start the worker
make worker

# 7. In another terminal — start the web console (port 3000)
make web
```

## Zero-Docker Local Development

For development without running Docker at all, use the local launcher
which uses SQLite + fakeredis:

```bash
# Install dependencies
make bootstrap

# Start API + background worker (no Docker needed)
python start_local.py

# In another terminal — start the web console
make web
```

## Verify Installation

### API Health Check

```bash
curl http://localhost:8000/healthz
# {"status":"ok"}
```

### Generate an API Key

```bash
curl -X POST http://localhost:8000/v1/api-keys \
  -H "Content-Type: application/json" \
  -d '{"name": "dev"}'
```

Save the returned `key` value — you'll need it for all authenticated requests.

### Submit Your First Experiment

```bash
curl -X POST http://localhost:8000/v1/experiments \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_KEY" \
  -d '{
    "name": "bell-state",
    "circuit": {
      "qasm": "OPENQASM 2.0; include \"qelib1.inc\"; qreg q[2]; creg c[2]; h q[0]; cx q[0],q[1]; measure q -> c;",
      "shots": 1024
    }
  }'
```

### Using the Python SDK

```python
from quantum_sdk import QCPClient

client = QCPClient(api_key="qcp_...")
job = client.run_experiment(
    name="bell",
    qasm=open("bell.qasm").read(),
    shots=1024,
)
print(job["job"]["status"])
```

### Using the CLI

```bash
pip install -e packages/cli
qcp login --api-key YOUR_KEY
qcp experiment run bell.qasm --provider local_simulator
```

## Services

| Service | URL |
|---------|-----|
| Web Console | http://localhost:3000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| API Docs (ReDoc) | http://localhost:8000/redoc |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3001 |

## Full Docker Stack

To start all services (including observability) via Docker:

```bash
make up-all
```

To start only infrastructure and observability (then run api/worker/web locally):

```bash
make up-infra
make migrate
make api          # terminal 1
make worker       # terminal 2
make web          # terminal 3
```
