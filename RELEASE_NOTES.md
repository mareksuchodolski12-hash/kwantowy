# Release Notes — v0.3.0

**Quantum Control Plane (QCP)** — First Public Release

---

## Project Overview

Quantum Control Plane is an open developer platform for quantum computing.
Submit QASM circuits, orchestrate multi-step experiments, benchmark providers,
and visualize results through a unified interface. Think MLflow or Airflow,
but for quantum.

---

## Key Features

- **Circuit Submission & Execution** — Submit OpenQASM 3 circuits to local
  simulators or cloud quantum backends (IBM Runtime, IonQ, Rigetti).
- **Circuit Optimisation** — Automatic gate-count reduction, depth
  minimisation, and transpilation via Qiskit.
- **Experiment Versioning** — Track experiment revisions with full audit
  history and diff support.
- **Workflow Orchestration** — Define multi-step DAG workflows with
  automatic dependency resolution and retries.
- **Provider Benchmarking** — Auto-benchmark providers on fidelity, latency,
  and cost; compare results side-by-side.
- **Smart Routing** — Capability-based provider selection that ranks
  backends by qubit count, connectivity, and availability.
- **Cost Governance** — Organisation-level budgets, cost tracking, and
  automatic job rejection when limits are exceeded.
- **Multi-Tenant Hierarchy** — Organisations → Teams → Projects with
  scoped resource isolation.
- **Result Comparison** — Statistical comparison of execution results
  across providers and circuit variants.
- **Observability** — Prometheus metrics, Grafana dashboards, Loki logs,
  and OpenTelemetry tracing out of the box.
- **Plugin System** — Drop-in provider plugins with a simple base class
  and YAML descriptor.
- **Interactive Dashboard** — Next.js web console with live experiment
  monitoring, provider leaderboard, and a drag-and-drop demo page.

---

## Architecture Summary

```
┌──────────────────────────────────────────────────────────┐
│                   Developer Platform                      │
│  Python SDK  ·  CLI (qcp)  ·  REST API  ·  Web Console   │
├──────────────────────────────────────────────────────────┤
│                    Control Plane                          │
│  FastAPI · Circuit Optimiser · Workflow Engine · Router    │
├──────────────────────────────────────────────────────────┤
│                   Execution Plane                         │
│  Quantum Runner · Benchmark Runner · Provider Plugins     │
├──────────────────────────────────────────────────────────┤
│                    Data Layer                              │
│  PostgreSQL · Redis Queue · Alembic Migrations            │
├──────────────────────────────────────────────────────────┤
│                   Infrastructure                          │
│  Docker Compose · Helm · Terraform · Prometheus · Grafana │
└──────────────────────────────────────────────────────────┘
```

---

## Components

### Control Plane (`services/api`)
FastAPI application providing 20+ REST endpoints under `/v1/`. Includes
circuit optimisation, experiment versioning, workflow orchestration, cost
governance, smart provider routing, and API-key authentication.

### Execution Plane (`workers/`)
- **quantum-runner** — Consumes jobs from the Redis queue, executes circuits
  on the selected provider, and writes results back to PostgreSQL.
- **benchmark-runner** — Periodically benchmarks all registered providers
  and publishes fidelity / latency metrics.

### SDK / CLI (`packages/`)
- **quantum-sdk** — Python client library wrapping the REST API with async
  support and Pydantic models.
- **qcp CLI** — Click-based command-line tool for experiment management,
  job submission, and result inspection.
- **contracts** — Shared Pydantic schemas used across all Python packages.

### Dashboard (`apps/web`)
Next.js 14 application with experiment views, run monitoring, provider
leaderboard, result comparison charts, and an interactive circuit demo page.

### Provider Plugins (`plugins/providers`)
Extensible plugin system using a `BaseProvider` abstract class and
`plugin.yaml` descriptors. Ships with AWS Braket (stub) and a custom
simulator example.

---

## Getting Started

### Prerequisites
- Python ≥ 3.11
- Node.js ≥ 20
- Docker and Docker Compose

### Quick Start

```bash
# Install all dependencies
make bootstrap

# Start infrastructure (PostgreSQL, Redis, Prometheus, Grafana)
make up

# Run database migrations
make migrate

# Start the API server (port 8000)
make api

# Start the job execution worker
make worker

# Start the web dashboard (port 3000)
make web
```

### Service URLs

| Service           | URL                          |
|-------------------|------------------------------|
| Web Console       | http://localhost:3000         |
| Interactive Demo  | http://localhost:3000/demo    |
| API Documentation | http://localhost:8000/docs    |
| Prometheus        | http://localhost:9090         |
| Grafana           | http://localhost:3001         |

---

## What's New in v0.3.0

- Circuit optimiser with gate-count and depth reduction
- Workflow orchestration engine with DAG scheduling
- Provider benchmarking and auto-ranking
- Cost governance with organisation-level budgets
- Multi-tenant hierarchy (Organisations / Teams / Projects)
- Result comparison with statistical analysis
- Experiment versioning with audit trail
- Interactive demo page in the web dashboard
- Helm chart and Terraform modules for production deployment
- Trivy security scanning and SBOM generation in CI
- OPA policy checks for Kubernetes manifests

---

## Upgrade Notes

This is the first public release. No migration from a previous version is
required.

---

## Known Limitations

- IonQ and Rigetti provider adapters are stubs (raise `NotImplementedError`).
- Integration and end-to-end test suites are scaffolded but not yet
  populated.
- The `NEXT_PUBLIC_API_KEY` is passed as an environment variable; a
  browser-based login flow is planned for a future release.

---

## License

MIT — see [LICENSE](LICENSE) for details.
