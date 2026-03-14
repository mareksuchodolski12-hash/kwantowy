# Quantum Control Plane — Comprehensive System Analysis

> **Date**: 2026-03-14
> **Author**: Architecture Review
> **Version**: 1.0.0

---

## Table of Contents

1. [High-Level Explanation (Step 1)](#1-high-level-explanation)
2. [Architecture Breakdown (Step 2)](#2-architecture-breakdown)
3. [Module Explanation (Step 3)](#3-module-explanation)
4. [Execution Flow (Step 4)](#4-execution-flow)
5. [Algorithms and Scientific Logic (Step 5)](#5-algorithms-and-scientific-logic)
6. [Dependencies (Step 6)](#6-dependencies)
7. [Code Maturity (Step 7)](#7-code-maturity)
8. [Demo Readiness (Step 8)](#8-demo-readiness)
9. [Demo Plan (Step 9)](#9-demo-plan)
10. [Improvement Roadmap (Step 10)](#10-improvement-roadmap)

---

## 1. High-Level Explanation

### What This Project Is

The **Quantum Control Plane (QCP)** is a distributed platform for submitting,
managing, and executing quantum circuits across multiple quantum computing
providers. It serves as a unified orchestration layer — a "control plane" — that
abstracts away the differences between quantum hardware vendors and simulators.

### Problem It Solves

Quantum computing today is fragmented. Each hardware provider (IBM, IonQ,
Rigetti, AWS Braket) has its own SDK, API, and execution model. QCP solves this
by providing:

- A **single REST API** to submit quantum circuits to any provider
- **Asynchronous job execution** with retry logic and state tracking
- **Provider benchmarking** to compare hardware quality
- **Smart routing** to select the best provider for a given circuit
- **Circuit optimisation** before execution (transpilation, noise-aware mapping)
- **Cost governance** with budget controls
- **Experiment versioning** and **workflow orchestration**
- **Full observability** with Prometheus metrics, Grafana dashboards, and
  OpenTelemetry traces

### Domain

This project belongs to **quantum computing infrastructure / platform
engineering**. It operates at the intersection of:

- **Quantum computing** — circuit execution on real and simulated backends
- **Distributed systems** — async job queues, workers, state machines
- **Developer tooling** — CLI, SDK, web dashboard
- **Infrastructure** — Kubernetes, Helm, Terraform, Docker

### Technologies and Languages

| Layer            | Technology                                              |
| ---------------- | ------------------------------------------------------- |
| Backend API      | Python 3.11+, FastAPI 0.115+, Uvicorn                  |
| Database         | PostgreSQL 16 (prod), SQLite + aiosqlite (dev)          |
| ORM              | SQLAlchemy 2.0+ (async), Alembic migrations             |
| Queue            | Redis 7 (prod), fakeredis (dev)                         |
| Quantum          | Qiskit 1.2+, Qiskit IBM Runtime 0.36+                  |
| Frontend         | Next.js 14, React 18, TypeScript 5.5, Tailwind CSS 3   |
| Charts           | Recharts                                                |
| CLI              | Python Click, Rich console                              |
| SDK              | Python httpx                                            |
| Observability    | Prometheus, Grafana 11.3, Loki 3.2, OpenTelemetry 1.30 |
| Deployment       | Docker, Kubernetes, Helm, Terraform                     |
| CI/CD            | GitHub Actions                                          |
| Code quality     | Ruff (lint/format), mypy (types), ESLint, pre-commit    |

---

## 2. Architecture Breakdown

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DEVELOPER INTERFACES                        │
│                                                                     │
│    ┌──────────┐    ┌──────────┐    ┌──────────────────────────┐    │
│    │   CLI    │    │   SDK    │    │     Web Dashboard        │    │
│    │  (qcp)   │    │ (Python) │    │  (Next.js / React)       │    │
│    └────┬─────┘    └────┬─────┘    └───────────┬──────────────┘    │
│         │               │                      │                    │
└─────────┼───────────────┼──────────────────────┼────────────────────┘
          │               │                      │
          ▼               ▼                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         CONTROL PLANE                               │
│                                                                     │
│    ┌──────────────────────────────────────────────────────────┐     │
│    │              FastAPI REST API (:8000)                    │     │
│    │                                                          │     │
│    │  /v1/experiments  /v1/jobs  /v1/results  /v1/providers  │     │
│    │  /v1/workflows    /v1/benchmarks  /v1/budgets           │     │
│    │  /v1/circuits/optimise  /v1/orgs  /v1/teams             │     │
│    │                                                          │     │
│    │  ┌────────────┐  ┌────────────┐  ┌────────────────┐    │     │
│    │  │ Job Service│  │ Workflow   │  │ Provider       │    │     │
│    │  │            │  │ Engine     │  │ Registry       │    │     │
│    │  └────────────┘  └────────────┘  └────────────────┘    │     │
│    │  ┌────────────┐  ┌────────────┐  ┌────────────────┐    │     │
│    │  │ Circuit    │  │ Benchmark  │  │ Cost           │    │     │
│    │  │ Optimiser  │  │ Service    │  │ Governance     │    │     │
│    │  └────────────┘  └────────────┘  └────────────────┘    │     │
│    └────────────┬────────────────────────────────────────────┘     │
│                 │                                                    │
│    ┌────────────▼───────────┐    ┌──────────────────────┐          │
│    │  PostgreSQL (storage)  │    │  Redis (job queue)   │          │
│    │  experiments, jobs,    │    │  FIFO + DLQ +        │          │
│    │  results, audit_events │    │  visibility timeout  │          │
│    └────────────────────────┘    └──────────┬───────────┘          │
│                                              │                      │
└──────────────────────────────────────────────┼──────────────────────┘
                                               │
┌──────────────────────────────────────────────┼──────────────────────┐
│                      EXECUTION PLANE         │                      │
│                                              ▼                      │
│    ┌─────────────────────────────────────────────────┐              │
│    │           Quantum Runner (Worker)               │              │
│    │                                                  │              │
│    │  dequeue → transition(RUNNING) → execute →      │              │
│    │  store result → transition(SUCCEEDED/FAILED)    │              │
│    │                                                  │              │
│    │  ┌──────────┐ ┌──────────┐ ┌──────────────────┐│              │
│    │  │  Qiskit  │ │   IBM    │ │  IonQ / Rigetti  ││              │
│    │  │ Simulator│ │ Runtime  │ │   (stubs)        ││              │
│    │  └──────────┘ └──────────┘ └──────────────────┘│              │
│    └─────────────────────────────────────────────────┘              │
│                                                                      │
│    ┌─────────────────────────────────────────────────┐              │
│    │        Benchmark Runner (Worker)                │              │
│    └─────────────────────────────────────────────────┘              │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                      OBSERVABILITY PLANE                             │
│                                                                      │
│    ┌────────────┐   ┌──────────┐   ┌────────────┐                  │
│    │ Prometheus │──▶│ Grafana  │   │    Loki    │                  │
│    │  (:9090)   │   │ (:3001)  │   │ (log agg.) │                  │
│    └────────────┘   └──────────┘   └────────────┘                  │
│                                                                      │
│    OpenTelemetry traces (OTLP exporter)                             │
└──────────────────────────────────────────────────────────────────────┘
```

### Entry Points

| Entry Point                                | Purpose                       |
| ------------------------------------------ | ----------------------------- |
| `services/api/app/main.py`                 | FastAPI application           |
| `workers/quantum-runner/runner/main.py`    | Async job execution worker    |
| `workers/benchmark-runner/benchmark_worker.py` | Auto-benchmarking worker  |
| `packages/cli/qcp_cli/main.py`            | CLI tool (`qcp`)              |
| `packages/sdk/quantum_sdk/client.py`       | Python SDK (`QCPClient`)      |
| `apps/web/app/layout.tsx`                  | Web dashboard (Next.js)       |
| `start_local.py`                           | Local development launcher    |

### Core Modules and Responsibilities

| Module                       | Responsibility                                              |
| ---------------------------- | ----------------------------------------------------------- |
| `app/api/routes.py`         | REST API endpoints (20+ routes under `/v1/`)                |
| `app/services/job_service.py` | Job submission, idempotency, experiment creation           |
| `app/services/worker_service.py` | Job execution, retry logic, result storage              |
| `app/services/workflow_engine.py` | Multi-step workflow orchestration                      |
| `app/services/provider_registry.py` | Capability-based provider ranking and selection      |
| `app/services/circuit_optimiser.py` | Circuit transpilation and optimisation pipeline      |
| `app/services/benchmarking.py` | Provider calibration and fidelity tracking                |
| `app/services/cost_governance.py` | Budget enforcement and cost tracking                  |
| `app/services/result_comparator.py` | Cross-provider result comparison                     |
| `app/services/experiment_versioning.py` | Experiment version management                     |
| `app/services/tenant.py`    | Multi-tenant hierarchy (org → team → project)               |
| `app/simulation/`           | Provider adapters (Qiskit, IBM Runtime, IonQ, Rigetti)      |
| `app/queue/redis_queue.py`  | Redis FIFO queue with visibility timeout and DLQ            |
| `app/domain/state_machine.py` | Job state transitions (SUBMITTED→QUEUED→RUNNING→…)       |
| `app/core/observability.py` | Prometheus metrics, OpenTelemetry tracing                    |

---

## 3. Module Explanation

### `services/api/` — Backend API Service

**Purpose**: The core FastAPI application that handles all REST API requests,
manages experiments and jobs, and orchestrates the quantum execution pipeline.

#### `app/api/` — REST API Layer

- **`routes.py`** (637 lines): All 20+ API endpoints grouped by domain:
  - Health checks: `GET /healthz`, `GET /readyz`
  - API Keys: `POST /v1/api-keys`, `GET /v1/api-keys`
  - Experiments: `POST /v1/experiments`, `GET /v1/experiments`,
    `GET /v1/experiments/{id}`, version management
  - Jobs: `GET /v1/jobs`, `GET /v1/jobs/{id}`
  - Results: `GET /v1/results/{id}`, `POST /v1/results/compare`
  - Providers: `GET /v1/providers`, `POST /v1/providers/select`
  - Workflows: `POST /v1/workflows`, `GET /v1/workflows`, run management
  - Budgets: `POST /v1/budgets`, `GET /v1/budgets`
  - Benchmarks: `POST /v1/benchmarks`, `GET /v1/benchmarks`
  - Circuits: `POST /v1/circuits/optimise`
  - Multi-tenant: Orgs, teams, projects
- **`deps.py`**: FastAPI dependency injection (DB session, Redis, API key auth)

#### `app/core/` — Infrastructure Layer

- **`config.py`**: Pydantic settings from environment variables (`QCP_` prefix)
- **`logging.py`**: Structured JSON logging configuration
- **`observability.py`**: Prometheus counters/histograms/gauges, OpenTelemetry
  tracing, metrics middleware
- **`correlation.py`**: Request correlation ID middleware (propagated through the
  entire job lifecycle)

#### `app/db/` — Database Layer

- **`models.py`**: SQLAlchemy ORM models for all 12+ tables (experiments, jobs,
  results, audit_events, api_keys, benchmarks, workflows, workflow_runs,
  budgets, cost_records, organisations, teams, projects)
- **`session.py`**: Async SQLAlchemy engine and session factory
- **`base.py`**: Declarative base class

#### `app/domain/` — Domain Logic

- **`schemas.py`**: Pydantic request/response models for all API endpoints
- **`state_machine.py`**: Valid state transitions for jobs
  (`SUBMITTED→QUEUED→RUNNING→SUCCEEDED/FAILED`) with `InvalidStateTransition`
  exception

#### `app/repositories/` — Data Access Layer

- **`jobs.py`**: CRUD for jobs, state transitions, idempotency key lookup
- **`experiments.py`**: CRUD for experiments
- **`results.py`**: CRUD for execution results
- **`audit.py`**: Event sourcing audit log
- **`api_keys.py`**: API key generation, validation, rotation

#### `app/services/` — Business Logic (~1654 LOC)

- **`job_service.py`**: Job submission pipeline (create experiment → create job
  → transition to QUEUED → commit → enqueue to Redis)
- **`worker_service.py`**: Job processing (dequeue → transition to RUNNING →
  execute via provider → store result → transition to SUCCEEDED/FAILED → retry
  on failure)
- **`workflow_engine.py`**: Multi-step workflow orchestration with step
  sequencing
- **`provider_registry.py`**: Capability-based provider selection with scoring
  (cost, queue wait, hardware preference)
- **`provider_factory.py`**: Provider adapter instantiation based on
  `ExecutionProvider` enum
- **`circuit_optimiser.py`**: Circuit transpilation pipeline (depth reduction,
  noise-aware qubit mapping, shot optimisation)
- **`benchmarking.py`**: Provider calibration using Bell-state circuits, fidelity
  tracking, Prometheus metric export
- **`cost_governance.py`**: Budget creation, cost recording, spend tracking
- **`result_comparator.py`**: Cross-provider result comparison with statistical
  analysis
- **`experiment_versioning.py`**: Experiment snapshot and version management
- **`tenant.py`**: Multi-tenant hierarchy (organisation → team → project)

#### `app/simulation/` — Provider Adapters

- **`providers.py`**: Abstract base class `ExecutionProviderAdapter` with
  `run()` and `poll()` methods
- **`qiskit_adapter.py`**: Local Qiskit BasicProvider simulator — the only fully
  functional adapter
- **`ibm_runtime_adapter.py`**: IBM Quantum Runtime adapter (requires
  credentials)
- **`ionq_adapter.py`**: IonQ adapter (stub — raises `NotImplementedError`)
- **`rigetti_adapter.py`**: Rigetti adapter (stub — raises `NotImplementedError`)

#### `app/queue/` — Job Queue

- **`redis_queue.py`**: Redis-based FIFO queue with:
  - Enqueue/dequeue with JSON serialisation
  - Visibility timeout via sorted set (processing set)
  - Dead-letter queue (DLQ) for permanently failed jobs
  - Acknowledgement on completion
  - Requeue of timed-out messages
  - Queue depth, DLQ length, and processing count metrics

---

### `packages/` — Reusable Python Packages

#### `packages/contracts/` — Shared Data Models

- **`quantum_contracts/models.py`**: Pydantic models shared across all
  components:
  - Enums: `JobState`, `ExecutionProvider`, `OptimisationStrategy`,
    `WorkflowState`
  - Core: `CircuitPayload`, `RetryPolicy`, `Experiment`, `Job`,
    `ExecutionResult`, `ErrorResponse`
  - Advanced: `BenchmarkResult`, `WorkflowDefinition`, `WorkflowRun`, `Budget`,
    `OptimisedCircuit`, `ResultComparison`, `Organisation`, `Team`, `Project`,
    `ProviderCapabilities`, etc.

#### `packages/sdk/` — Python SDK

- **`quantum_sdk/client.py`**: `QCPClient` class with synchronous methods:
  - `run_circuit()` — submit a quantum circuit for execution
  - `get_results()` — fetch results for a job
  - `list_experiments()` — list all experiments
  - `wait_for_result()` — poll until job completes

#### `packages/cli/` — Command-Line Tool

- **`qcp_cli/main.py`**: Click-based CLI with commands:
  - `qcp login` — store API key
  - `qcp experiment run` — submit a circuit
  - `qcp experiment list` — list experiments
  - `qcp run status` — check job status
  - `qcp result show` — display results
- **`qcp_cli/config.py`**: Credential storage in `~/.qcp/config.json`

---

### `workers/` — Job Execution Workers

#### `workers/quantum-runner/` — Main Worker

- **`runner/main.py`**: Async event loop that:
  1. Connects to Redis and PostgreSQL
  2. Recovers stuck jobs on startup (jobs in RUNNING state from crashed workers)
  3. Polls the Redis queue with a 5-second timeout
  4. Processes jobs via `WorkerService`
  5. Periodically requeues timed-out messages (every 60 seconds)
  6. Handles graceful shutdown on SIGINT/SIGTERM

#### `workers/benchmark-runner/` — Benchmark Worker

- **`benchmark_worker.py`**: Periodically runs calibration circuits against all
  providers and records benchmark results

---

### `apps/web/` — Web Dashboard

#### Pages

- **`/`** → redirects to `/experiments`
- **`/experiments`** → list experiments with `ExperimentTable`
- **`/experiments/new`** → submit new circuit with `ExperimentForm`
- **`/runs/[id]`** → job detail view with `ResultChart` and `StatusBadge`
- **`/providers`** → provider leaderboard
- **`/comparison`** → multi-provider result comparison
- **`/demo`** → interactive demo with pre-built circuits (Bell State, Grover,
  Deutsch-Jozsa)

#### Components

- **`ExperimentForm.tsx`**: Circuit submission form with QASM input
- **`ExperimentTable.tsx`**: Experiment list with status indicators
- **`ResultChart.tsx`**: Bar chart of measurement counts using Recharts
- **`StatusBadge.tsx`**: Coloured badge for job states
- **`ProviderBadge.tsx`**: Badge for provider identification

#### API Client

- **`lib/api.ts`**: Typed fetch wrapper for all API endpoints

---

### `plugins/` — External Provider Plugins

- **`providers/base.py`**: `BaseProvider` ABC with `info()` and `execute()`
  methods
- **`providers/aws_braket/`**: AWS Braket provider (stub with plugin.yaml
  descriptor)
- **`providers/custom_simulator/`**: Custom simulator example

---

### `infra/` — Infrastructure

- **`helm/`**: Kubernetes Helm chart for QCP deployment
- **`terraform/`**: Infrastructure as Code for cloud provisioning
- **`observability/`**: Prometheus scrape config, Grafana dashboards and
  provisioning, Loki log aggregation config
- **`policies/`**: Kubernetes security policies

---

### `docs/` — Documentation

- **`getting-started.md`**: Onboarding guide
- **`architecture/`**: Detailed architecture documents (platform architecture,
  next-gen platform vision, threat model, implementation plan)
- **`adr/`**: Architecture Decision Records (Redis queue choice, persistence
  model, async orchestration design)
- **`analysis/`**: Technical analyses (quantum simulator analysis, deep platform
  analysis)
- **`runbooks/`**: Operational runbooks (local development, incident response)
- **`cli.md`**, **`sdk.md`**, **`experiments.md`**, **`workflows.md`**,
  **`providers.md`**, **`benchmarking.md`**: Feature-specific documentation
- **`demo-walkthrough.md`**: Interactive demo guide

---

## 4. Execution Flow

### End-to-End: Circuit Submission to Result Retrieval

#### Step 1 — Client Submits Circuit

The user submits a quantum circuit through one of three interfaces:

- **Web UI** (`/demo` page): Selects a pre-built circuit, clicks "Run"
- **CLI**: `qcp experiment run --name bell --qasm "OPENQASM 2.0;..."`
- **SDK**: `client.run_circuit(name="bell", qasm="...", shots=1024)`

All interfaces call `POST /v1/experiments` with a JSON body containing the
circuit name, QASM string, shot count, provider choice, and retry policy.

#### Step 2 — API Processes Request

In `app/api/routes.py`, the `create_experiment` endpoint:

1. Validates the request body via Pydantic (`SubmitExperimentRequest`)
2. Extracts the correlation ID from the `X-Correlation-ID` header (or generates
   one)
3. Delegates to `JobService.submit()`

#### Step 3 — Job Service Creates Records

In `app/services/job_service.py`, `JobService.submit()`:

1. Checks for idempotency key — if a matching job exists, returns it immediately
2. Creates an `Experiment` record in PostgreSQL via `ExperimentRepository`
3. Creates a `Job` record via `JobRepository`
4. Transitions the job state from `SUBMITTED` → `QUEUED` via the state machine
5. Logs an audit event (`job.queued`)
6. **Commits the database transaction** (critical: this must happen before
   enqueue)
7. Enqueues the job ID to the Redis queue
8. Increments the `qcp_jobs_submitted_total` Prometheus counter

#### Step 4 — Worker Dequeues Job

In `workers/quantum-runner/runner/main.py`, the worker loop:

1. Calls `queue.dequeue(timeout=5)` — blocks for up to 5 seconds
2. Receives a `(job_id, correlation_id)` tuple
3. Delegates to `WorkerService.process_job()`

#### Step 5 — Worker Executes Circuit

In `app/services/worker_service.py`, `WorkerService.process_job()`:

1. Loads the `JobModel` from the database
2. Transitions the job state to `RUNNING`
3. Increments the attempt counter
4. Records queue latency (time from enqueue to dequeue)
5. **Commits the RUNNING state** (makes it visible to API and stuck-job
   recovery)
6. Loads the associated `ExperimentModel` to get the QASM circuit
7. Instantiates the appropriate provider adapter via `get_provider()`
8. Calls `adapter.run(payload, timeout_seconds, job_id)`

#### Step 6 — Provider Adapter Executes

In `app/simulation/qiskit_adapter.py` (for the local simulator):

1. Parses the QASM string into a Qiskit `QuantumCircuit`
2. Selects the `basic_simulator` backend
3. Transpiles the circuit for the backend
4. Runs the circuit with the specified shot count in a thread pool
5. Collects measurement counts from the result
6. Returns an `ExecutionResult` with counts, duration, and metadata

#### Step 7 — Result Storage

Back in `WorkerService.process_job()`:

1. Stores the `ExecutionResult` in PostgreSQL via `ResultRepository`
2. Transitions the job state to `SUCCEEDED`
3. Logs an audit event (`job.succeeded`)
4. Commits the transaction
5. Acknowledges the Redis message (removes from processing set)
6. Records execution duration and success metrics

#### Step 8 — Client Retrieves Result

The client polls `GET /v1/jobs/{id}` to check the job status. Once the status is
`succeeded`, it fetches `GET /v1/results/{id}` to get the measurement counts.

The web dashboard auto-polls every second and displays the results as a bar
chart.

### Failure and Retry Flow

If the provider adapter throws an exception or times out:

1. `WorkerService._handle_failure()` is called
2. If `attempts < max_attempts`: transitions `RUNNING → FAILED → QUEUED`,
   re-enqueues the job, increments retry counter
3. If `attempts >= max_attempts`: transitions to `FAILED` permanently, moves the
   message to the dead-letter queue (DLQ)

### Stuck Job Recovery

The worker main loop periodically (every 60 seconds) calls
`queue.requeue_timed_out()` to recover messages stuck in the Redis processing
set (e.g., from a crashed worker). On startup, it also recovers database-level
stuck jobs — transitioning any jobs in `RUNNING` state back to `QUEUED`.

### Data Flow Summary

```
Client → POST /v1/experiments → JobService → PostgreSQL (experiment + job)
                                            → Redis (enqueue job_id)

Redis → Worker → WorkerService → Provider Adapter → Qiskit → Measurement counts
                                                   ↓
                                PostgreSQL (result) → Redis (ack)

Client → GET /v1/results/{id} → ResultRepository → PostgreSQL → Response
```

---

## 5. Algorithms and Scientific Logic

### Quantum Circuit Execution

The core scientific operation is **quantum circuit simulation**. QCP accepts
circuits in **OpenQASM 2.0** format — a standard text-based quantum assembly
language.

**Example Bell State Circuit:**

```qasm
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
h q[0];
cx q[0],q[1];
measure q -> c;
```

This creates a 2-qubit entangled state where measuring always yields either
`00` or `11` with roughly equal probability (~50% each).

**Execution pipeline:**

1. Parse QASM → Qiskit `QuantumCircuit` object
2. Transpile for the target backend (gate decomposition, qubit mapping)
3. Simulate N shots (repeated measurements)
4. Collect measurement statistics (counts of each bitstring outcome)

### Circuit Optimisation Pipeline

The circuit optimiser (`circuit_optimiser.py`) implements several strategies:

1. **Gate count estimation**: Counts gate operations in QASM by matching known
   gate keywords (`h`, `cx`, `x`, `y`, `z`, `rx`, `ry`, `rz`, etc.)

2. **Depth estimation**: Counts sequential gate lines as a rough circuit depth
   approximation

3. **Identity elimination** (MEDIUM+ strategies): Removes consecutive identical
   self-inverse gates (`x x → identity`, `h h → identity`) which cancel each
   other out

4. **Noise-aware qubit mapping**: When enabled, maps logical qubits to physical
   qubits with lower indices first (proxy for better-calibrated qubits on real
   hardware)

5. **Shot optimisation**: Adjusts the number of measurement repetitions based on
   circuit complexity:
   - Simple circuits (≤2 gates): capped at 512 shots
   - Medium circuits (≤10 gates): unchanged
   - Complex circuits (>10 gates): scaled by `log₂(gate_count + 1) / 4`

6. **Fidelity estimation**: `fidelity = max(0, 1 - gates × 0.001)` — a
   heuristic approximation

### Provider Benchmarking

The benchmarking engine (`benchmarking.py`) uses a **Bell-state calibration
circuit** to measure provider quality:

- **Fidelity**: How closely results match the ideal probability distribution
- **Gate error**: Average error rate per quantum gate
- **Readout error**: Measurement error rate
- **Queue time**: Time waiting before execution begins
- **Execution time**: Wall-clock execution duration

Currently accepts pre-measured values rather than computing them from raw
results.

### Smart Provider Routing

The provider registry (`provider_registry.py`) ranks providers based on:

- **Hardware capabilities** (qubit count, supported gate sets)
- **Current benchmarks** (fidelity, error rates)
- **Queue wait time** (lower is better)
- **Cost** (estimated per-shot cost)

Returns a scored, ranked list of provider recommendations.

### Result Comparison

The result comparator (`result_comparator.py`) performs statistical comparison
of execution results across providers:

- Normalises count distributions
- Compares measurement probabilities
- Computes similarity metrics between distributions

---

## 6. Dependencies

### Python Backend Dependencies

| Package                             | Version   | Purpose                                      |
| ----------------------------------- | --------- | -------------------------------------------- |
| `fastapi`                           | ≥0.115    | Async REST API framework                     |
| `uvicorn`                           | ≥0.32     | ASGI server                                  |
| `sqlalchemy`                        | ≥2.0      | Async ORM and database toolkit               |
| `asyncpg`                           | ≥0.30     | PostgreSQL async driver                       |
| `aiosqlite`                         | ≥0.20     | SQLite async driver (dev)                     |
| `alembic`                           | ≥1.14     | Database migrations                           |
| `redis`                             | ≥5.2      | Redis async client                            |
| `pydantic`                          | ≥2.0      | Data validation and serialisation             |
| `pydantic-settings`                 | ≥2.6      | Environment-based configuration               |
| `qiskit`                            | ≥1.2      | Quantum circuit simulation and transpilation  |
| `qiskit-ibm-runtime`               | ≥0.36     | IBM Quantum hardware access                   |
| `prometheus-client`                 | ≥0.21     | Prometheus metrics exposition                 |
| `opentelemetry-api`                 | ≥1.30     | Distributed tracing API                       |
| `opentelemetry-sdk`                 | ≥1.30     | Tracing SDK and span processing               |
| `opentelemetry-instrumentation-fastapi` | ≥0.51 | Auto-instrumentation for FastAPI              |
| `opentelemetry-exporter-otlp-proto-http` | ≥1.30 | OTLP trace exporter                          |

### Python Dev Dependencies

| Package        | Version | Purpose                    |
| -------------- | ------- | -------------------------- |
| `pytest`       | ≥8.3    | Test framework             |
| `pytest-asyncio` | ≥0.24 | Async test support         |
| `httpx`        | ≥0.27   | HTTP client (API testing)  |
| `fakeredis`    | ≥2.25   | Redis mock for tests       |
| `ruff`         | ≥0.8    | Linter and formatter       |
| `mypy`         | ≥1.13   | Static type checking       |
| `pre-commit`   | —       | Git hook automation        |

### Python SDK/CLI Dependencies

| Package  | Version | Purpose                     |
| -------- | ------- | --------------------------- |
| `httpx`  | ≥0.27   | HTTP client for SDK         |
| `click`  | ≥8.1    | CLI framework               |
| `rich`   | ≥13.9   | Terminal formatting          |

### Frontend Dependencies

| Package       | Version | Purpose                           |
| ------------- | ------- | --------------------------------- |
| `next`        | 14.2.5  | React meta-framework (SSR, routing) |
| `react`       | 18.3.1  | UI component library              |
| `recharts`    | 2.15.0  | Chart library for result visualisation |
| `tailwindcss` | 3.4.1   | Utility-first CSS framework       |
| `typescript`  | 5.5.4   | Static typing for JavaScript      |
| `eslint`      | 8.57.1  | JavaScript/TypeScript linter      |

### Infrastructure Dependencies

| Tool         | Version | Purpose                        |
| ------------ | ------- | ------------------------------ |
| PostgreSQL   | 16      | Primary database                |
| Redis        | 7       | Job queue and caching           |
| Prometheus   | 2.54.1  | Metrics collection              |
| Grafana      | 11.3.1  | Metrics dashboards              |
| Loki         | 3.2.1   | Log aggregation                 |
| Docker       | —       | Containerisation                |
| Kubernetes   | —       | Container orchestration         |
| Helm         | —       | Kubernetes package management   |
| Terraform    | —       | Infrastructure as Code          |

### Runtime Requirements

- **Python** ≥ 3.11
- **Node.js** ≥ 20
- **Docker** and **Docker Compose** (for the full stack)

---

## 7. Code Maturity

### Production-Ready Components

| Component                  | Status        | Evidence                                     |
| -------------------------- | ------------- | -------------------------------------------- |
| REST API (FastAPI)         | ✅ Mature     | 20+ endpoints, auth, validation, error handling |
| Job state machine          | ✅ Mature     | Well-tested transitions, guard rails           |
| Redis queue                | ✅ Mature     | DLQ, visibility timeout, metrics               |
| Worker service             | ✅ Mature     | Retry logic, stuck-job recovery, graceful shutdown |
| Database models            | ✅ Mature     | 12+ tables, proper relationships                |
| Observability              | ✅ Mature     | 15+ Prometheus metrics, OpenTelemetry, correlation IDs |
| Qiskit local simulator     | ✅ Functional | Fully working with thread-pool execution        |
| Circuit optimiser          | ✅ Functional | Multiple strategies, tested                     |
| Audit logging              | ✅ Functional | Event sourcing pattern                          |
| API key authentication     | ✅ Functional | Key generation, validation, rotation            |

### Research Prototype Components

| Component                  | Status          | Notes                                        |
| -------------------------- | --------------- | -------------------------------------------- |
| IBM Runtime adapter        | 🟡 Conditional | Works but requires IBM credentials            |
| IonQ adapter               | ⚠️ Stub         | Raises `NotImplementedError`                  |
| Rigetti adapter            | ⚠️ Stub         | Raises `NotImplementedError`                  |
| AWS Braket plugin          | ⚠️ Stub         | Plugin structure exists, not integrated        |
| Custom simulator plugin    | ⚠️ Stub         | Plugin structure exists, basic example         |
| Benchmarking service       | 🟡 Partial     | Accepts pre-measured values; no real execution |
| Smart routing              | 🟡 Partial     | Scoring logic exists; limited real-world data  |
| Cost governance            | 🟡 Partial     | Budget model exists; costs are estimated       |
| Noise-aware qubit mapping  | 🟡 Heuristic   | Simple index-based proxy, not real calibration |
| Fidelity estimation        | 🟡 Heuristic   | Linear approximation: `1 - gates × 0.001`     |

### Unfinished Code and TODOs

- **IonQ and Rigetti adapters**: Only stubs — raise `NotImplementedError`
- **AWS Braket plugin**: Plugin structure and `plugin.yaml` exist but the
  provider is not wired into the main adapter factory
- **Integration tests**: `tests/integration/` and `tests/e2e/` directories
  contain only `.gitkeep` and `README.md` placeholder files
- **Benchmark runner**: Accepts pre-measured values rather than actually
  executing calibration circuits
- **Real cost tracking**: Cost governance uses estimated values, no integration
  with provider billing APIs

### Dead Code

No significant dead code found. The codebase is clean and well-organised.

### Missing Components

- **User authentication** (beyond API keys): No OAuth, SSO, or RBAC
- **Rate limiting**: No request throttling
- **Circuit validation**: Limited QASM validation (relies on Qiskit parser)
- **Real hardware calibration data**: Benchmark service uses synthetic data
- **Persistent workflow state**: Workflows stored in memory during execution
- **WebSocket notifications**: Clients must poll for results; no push mechanism

---

## 8. Demo Readiness

### What Already Works

The following components are fully functional and can be demonstrated:

1. **Local development launcher** (`start_local.py`):
   - Starts FastAPI API + background worker using SQLite + fakeredis
   - No Docker required
   - Automatically creates database tables and seeds an API key

2. **Quantum circuit execution**:
   - Submit circuits via API, get results from the local Qiskit simulator
   - Full job lifecycle: SUBMITTED → QUEUED → RUNNING → SUCCEEDED

3. **Web dashboard** (`apps/web`):
   - Interactive demo page with 3 pre-built circuits
   - Real-time job status polling
   - Result visualisation with bar charts

4. **API documentation**:
   - Swagger UI at `/docs`
   - ReDoc at `/redoc`

5. **CLI tool**:
   - API key generation
   - Circuit submission
   - Result retrieval

6. **SDK**:
   - Programmatic circuit submission and result polling

7. **Circuit optimisation**:
   - POST `/v1/circuits/optimise` with multiple strategies

### Minimal Functionality for a Demo

A complete demo requires:

1. **Start the API + worker**: `python start_local.py`
2. **Start the web UI**: `cd apps/web && npm run dev`
3. **Open the demo page**: `http://localhost:3000/demo`
4. **Select a circuit** (Bell State, Grover, Deutsch-Jozsa)
5. **Click "Run"** → watch status update → see measurement chart

### What Must Be Configured for the Web Demo

The web dashboard needs the API URL configured. By default it expects
`http://localhost:8000`. The demo page (`apps/web/app/demo/page.tsx`) uses
`lib/api.ts` which reads the API base URL from environment or defaults to
`http://localhost:8000`.

### Minimal Demo Architecture

```
┌─────────────────────┐         ┌──────────────────────────────────┐
│   Web Browser       │         │    start_local.py                │
│                     │  HTTP   │                                  │
│   localhost:3000    │────────▶│    FastAPI API (:8000)           │
│   (Next.js dev)     │         │    + Background Worker           │
│                     │         │    + SQLite DB                   │
│   /demo page        │         │    + fakeredis Queue             │
│   - Bell State      │         │                                  │
│   - Grover          │         │    Qiskit Local Simulator        │
│   - Deutsch-Jozsa   │         │                                  │
└─────────────────────┘         └──────────────────────────────────┘
```

---

## 9. Demo Plan

### Prerequisites

```bash
# Python 3.11+ and Node.js 20+ must be installed
python --version  # ≥ 3.11
node --version    # ≥ 20
```

### Setup Commands

```bash
# 1. Install Python dependencies
make bootstrap

# 2. Start the API + worker (Terminal 1)
python start_local.py

# 3. Start the web UI (Terminal 2)
cd apps/web && npm run dev
```

### Demo Walkthrough

1. **Open the API docs**: Navigate to `http://localhost:8000/docs` to see all
   available endpoints

2. **Open the web dashboard**: Navigate to `http://localhost:3000`

3. **Navigate to the Demo page**: Click "Demo" in the navigation bar or go to
   `http://localhost:3000/demo`

4. **Select a circuit**: Choose from:
   - **Bell State** — 2-qubit entanglement (expect ~50% `00` and ~50% `11`)
   - **Grover (2-qubit)** — quantum search (expect amplified `11` result)
   - **Deutsch-Jozsa** — quantum oracle (expect deterministic `11` result)

5. **Click "Run"**: The demo page will:
   - Submit the circuit to `POST /v1/experiments`
   - Poll `GET /v1/jobs/{id}` every second
   - Fetch results from `GET /v1/results/{id}` once succeeded
   - Display a bar chart of measurement counts

6. **Programmatic demo** (optional):
   ```bash
   # Generate an API key
   python examples/quickstart.py --generate-key demo

   # Submit a circuit via SDK
   QCP_API_KEY=qcp_... python examples/quickstart.py
   ```

7. **Circuit optimisation demo** (optional):
   ```bash
   curl -X POST http://localhost:8000/v1/circuits/optimise \
     -H "Content-Type: application/json" \
     -d '{
       "circuit": {"qasm": "OPENQASM 2.0;\ninclude \"qelib1.inc\";\nqreg q[2];\ncreg c[2];\nh q[0];\ncx q[0],q[1];\nmeasure q -> c;", "shots": 1024},
       "config": {"strategy": "medium", "noise_aware_mapping": true, "shot_optimisation": true}
     }'
   ```

### Expected Input and Output

**Input** (Bell State circuit):

```json
{
  "name": "bell-state-demo",
  "circuit": {
    "qasm": "OPENQASM 2.0;\ninclude \"qelib1.inc\";\nqreg q[2];\ncreg c[2];\nh q[0];\ncx q[0],q[1];\nmeasure q -> c;",
    "shots": 1024
  },
  "provider": "local_simulator"
}
```

**Output** (measurement counts):

```json
{
  "result": {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "provider": "local_simulator",
    "backend": "qiskit_basic_simulator",
    "counts": { "00": 512, "11": 512 },
    "shots": 1024,
    "duration_ms": 45,
    "completed_at": "2026-03-14T21:00:00Z"
  }
}
```

---

## 10. Improvement Roadmap

### Top 10 Technical Improvements

#### 1. Implement Real Provider Adapters

**Priority**: High
**Effort**: Medium

Complete the IonQ and Rigetti adapter stubs. Wire the AWS Braket plugin into the
adapter factory. This would enable multi-provider execution and meaningful
benchmark comparisons.

#### 2. Add WebSocket Push Notifications

**Priority**: High
**Effort**: Medium

Replace client-side polling with WebSocket connections for real-time job status
updates. This would reduce API load and improve the user experience, especially
for long-running jobs on real hardware.

#### 3. Implement Real Benchmark Execution

**Priority**: High
**Effort**: Medium

Modify the benchmarking service to actually execute calibration circuits on
available providers and compute fidelity, gate error, and readout error from raw
measurement results rather than accepting pre-measured values.

#### 4. Add Integration and End-to-End Tests

**Priority**: High
**Effort**: Medium

The `tests/integration/` and `tests/e2e/` directories are empty placeholders.
Add integration tests that verify the full job lifecycle with the local simulator
and end-to-end tests that exercise the web dashboard.

#### 5. Implement RBAC and OAuth Authentication

**Priority**: Medium
**Effort**: High

The current API key authentication is functional but limited. Add OAuth 2.0/OIDC
support, role-based access control, and tie API keys to organisations/teams in
the multi-tenant hierarchy.

#### 6. Add Request Rate Limiting

**Priority**: Medium
**Effort**: Low

Add rate limiting middleware (e.g., `slowapi`) to prevent API abuse. This is
especially important before exposing the platform to external users.

#### 7. Implement Real Cost Tracking

**Priority**: Medium
**Effort**: Medium

Integrate with provider billing APIs (IBM, IonQ) to record actual execution
costs. Use this data for budget enforcement in the cost governance service rather
than relying on estimates.

#### 8. Add Circuit Validation

**Priority**: Medium
**Effort**: Low

Add QASM syntax and semantic validation before accepting circuits. Currently the
system relies on Qiskit's parser to catch errors, which only happens at execution
time. Early validation would provide better error messages.

#### 9. Implement Persistent Workflow State

**Priority**: Low
**Effort**: Medium

Store workflow execution state in the database rather than keeping it in memory
during execution. This enables workflow recovery after API restarts and
long-running multi-step workflows.

#### 10. Add Grafana Dashboard Presets

**Priority**: Low
**Effort**: Low

Create pre-built Grafana dashboards for common monitoring scenarios: job
throughput, provider comparison, error rates, queue health, and cost tracking.
The Grafana provisioning infrastructure exists but dashboards are minimal.

### Refactoring Suggestions

- **Extract provider adapter interface**: Unify the internal
  `ExecutionProviderAdapter` and plugin `BaseProvider` into a single interface
- **Centralise error handling**: Add FastAPI exception handlers for common
  errors instead of per-route `try/except` blocks
- **Split routes.py**: The 637-line routes file should be split into domain-
  specific route modules (jobs, experiments, workflows, providers, etc.)
- **Add repository pattern generics**: Create a base repository class to reduce
  boilerplate in the 5+ repository implementations

### Performance Improvements

- **Connection pooling**: Configure SQLAlchemy connection pool sizes for
  production workloads
- **Redis pipelining**: Batch Redis operations where possible (e.g., metrics
  refresh)
- **Circuit caching**: Cache transpiled circuits by QASM hash to avoid
  re-transpilation for repeated circuits
- **Async batch processing**: Allow the worker to process multiple jobs
  concurrently rather than one at a time

### Architectural Improvements

- **Event-driven architecture**: Replace polling with an event bus (e.g., Redis
  Streams or Kafka) for inter-service communication
- **Horizontal worker scaling**: Add worker registration and load balancing for
  multi-worker deployments
- **API versioning strategy**: Prepare for API v2 with a clear versioning and
  deprecation policy
- **Separate read/write models**: Consider CQRS for the results and benchmarks
  data path where reads vastly outnumber writes
