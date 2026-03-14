# Deep Technical & Product Analysis: Quantum Control Plane

> **Analysis Date:** 2026-03-14
> **Repository:** `mareksuchodolski12-hash/kwantowy`
> **Analyst Perspective:** Principal Software Architect / Distributed Systems & Quantum Platform Engineer

---

## PHASE 1 — COMPLETE REPOSITORY MAPPING

### 1.1 Full File Tree

```
kwantowy/
├── .devcontainer/
│   └── devcontainer.json
├── .editorconfig
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.yml
│   │   └── feature_request.yml
│   ├── copilot-instructions.md
│   ├── pull_request_template.md
│   └── workflows/
│       └── ci.yml
├── .gitignore
├── .gitkeep
├── .pre-commit-config.yaml
├── Makefile
├── README.md
├── docker-compose.yml
│
├── apps/
│   └── web/                                # Next.js 14 operational console
│       ├── .eslintrc.json
│       ├── Dockerfile
│       ├── README.md
│       ├── app/
│       │   ├── comparison/page.tsx         # Provider comparison view
│       │   ├── experiments/new/page.tsx     # Experiment submission form
│       │   ├── globals.css
│       │   ├── layout.tsx
│       │   ├── page.tsx                    # Root redirect → /experiments/new
│       │   └── runs/
│       │       ├── [id]/page.tsx           # Run detail view
│       │       └── page.tsx                # Run history table
│       ├── lib/api.ts                      # API client for backend
│       ├── next-env.d.ts
│       ├── next.config.js
│       ├── package-lock.json
│       ├── package.json
│       └── tsconfig.json
│
├── docs/
│   ├── adr/
│   │   ├── 0000-template.md
│   │   ├── 0001-queue-choice-redis.md
│   │   ├── 0002-persistence-model.md
│   │   ├── 0003-async-orchestration-design.md
│   │   └── README.md
│   ├── analysis/
│   │   ├── quantum-simulator-analysis.md
│   │   └── deep-platform-analysis.md       ← this file
│   ├── architecture/
│   │   ├── implementation-plan.md
│   │   ├── platform-architecture.md
│   │   └── threat-model.md
│   ├── demo-walkthrough.md
│   └── runbooks/
│       ├── README.md
│       ├── incident-job-failures.md
│       └── local-development.md
│
├── infra/
│   ├── helm/
│   │   ├── .gitkeep
│   │   ├── README.md
│   │   └── quantum-control-plane/
│   │       ├── Chart.yaml
│   │       ├── templates/
│   │       │   ├── api-deployment.yaml
│   │       │   ├── web-deployment.yaml
│   │       │   └── worker-deployment.yaml
│   │       └── values.yaml
│   ├── observability/
│   │   ├── grafana/
│   │   │   ├── dashboards/qcp-overview.json
│   │   │   └── provisioning/dashboards/dashboard.yml
│   │   ├── loki/loki-config.yml
│   │   └── prometheus/prometheus.yml
│   ├── policies/
│   │   ├── .gitkeep
│   │   ├── README.md
│   │   └── kubernetes/deployment.rego
│   └── terraform/
│       ├── .gitkeep
│       ├── README.md
│       ├── main.tf
│       ├── outputs.tf
│       └── variables.tf
│
├── packages/
│   └── contracts/                          # Shared Pydantic contract models
│       ├── .gitkeep
│       ├── README.md
│       ├── pyproject.toml
│       └── quantum_contracts/
│           ├── __init__.py
│           └── models.py
│
├── services/
│   └── api/                                # FastAPI control-plane service
│       ├── .gitignore
│       ├── Dockerfile
│       ├── README.md
│       ├── alembic.ini
│       ├── alembic/
│       │   ├── env.py
│       │   ├── script.py.mako
│       │   └── versions/
│       │       └── 0001_initial_schema.py
│       ├── app/
│       │   ├── __init__.py
│       │   ├── api/
│       │   │   ├── __init__.py
│       │   │   ├── deps.py                 # Dependency injection (DB session, Redis)
│       │   │   └── routes.py               # REST endpoint definitions
│       │   ├── core/
│       │   │   ├── __init__.py
│       │   │   ├── config.py               # Pydantic Settings (env-driven)
│       │   │   ├── correlation.py           # Correlation ID middleware + context var
│       │   │   ├── logging.py              # JSON structured logging
│       │   │   └── observability.py         # Prometheus metrics + OTEL tracing
│       │   ├── db/
│       │   │   ├── __init__.py
│       │   │   ├── base.py                 # SQLAlchemy declarative base
│       │   │   ├── models.py               # ORM models (Experiment, Job, Result, Audit)
│       │   │   └── session.py              # Async engine + session factory
│       │   ├── domain/
│       │   │   ├── __init__.py
│       │   │   ├── schemas.py              # Request/response Pydantic schemas
│       │   │   └── state_machine.py        # Job state transition enforcement
│       │   ├── main.py                     # FastAPI app creation + middleware
│       │   ├── queue/
│       │   │   ├── __init__.py
│       │   │   └── redis_queue.py          # Redis RPUSH/BLPOP queue abstraction
│       │   ├── repositories/
│       │   │   ├── __init__.py
│       │   │   ├── audit.py                # Audit event persistence
│       │   │   ├── experiments.py           # Experiment CRUD
│       │   │   ├── jobs.py                 # Job CRUD + state transitions
│       │   │   └── results.py              # Execution result persistence
│       │   ├── services/
│       │   │   ├── __init__.py
│       │   │   ├── job_service.py           # Job submission + query orchestration
│       │   │   ├── provider_factory.py      # Provider adapter factory
│       │   │   └── worker_service.py        # Job execution + retry logic
│       │   └── simulation/
│       │       ├── __init__.py
│       │       ├── ibm_runtime_adapter.py   # IBM Quantum Runtime backend adapter
│       │       ├── providers.py             # Abstract ExecutionProviderAdapter ABC
│       │       └── qiskit_adapter.py        # Local Qiskit BasicSimulator adapter
│       ├── pyproject.toml
│       └── tests/
│           ├── test_api_jobs.py
│           ├── test_healthz.py
│           ├── test_integration_async.py
│           └── test_state_machine.py
│
├── tests/
│   ├── e2e/
│   │   ├── .gitkeep
│   │   └── README.md
│   └── integration/
│       ├── .gitkeep
│       └── README.md
│
└── workers/
    └── quantum-runner/                     # Worker process for async job execution
        ├── .gitkeep
        ├── Dockerfile
        ├── README.md
        └── runner/
            └── main.py                     # Worker entry point (infinite loop)
```

### 1.2 System Entry Points

| Entry Point | Location | Launch Command | Role |
|---|---|---|---|
| **API Server** | `services/api/app/main.py` | `uvicorn app.main:app` | FastAPI ASGI app — HTTP interface for job CRUD |
| **Worker Process** | `workers/quantum-runner/runner/main.py` | `python runner/main.py` | Async loop: dequeue → execute → persist |
| **Web Frontend** | `apps/web/app/page.tsx` | `npm run dev` / `npm run start` | Next.js 14 App Router operational console |
| **DB Migrations** | `services/api/alembic/` | `alembic upgrade head` | PostgreSQL schema management |
| **Docker Compose** | `docker-compose.yml` | `docker compose up` | Full stack orchestration (7 services) |
| **Makefile** | `Makefile` | `make api`, `make worker`, etc. | Developer workflow shortcuts |

### 1.3 Services, Modules, and Infrastructure Components

| Component | Type | Technology | Purpose |
|---|---|---|---|
| `services/api` | Backend Service | FastAPI + SQLAlchemy + asyncpg | Control plane: validation, persistence, queue dispatch |
| `workers/quantum-runner` | Worker Process | Python asyncio | Execution plane: circuit execution + result persistence |
| `apps/web` | Frontend | Next.js 14 (React) | Operational console for submission and monitoring |
| `packages/contracts` | Shared Library | Pydantic models | Cross-service contract types (Job, Experiment, etc.) |
| PostgreSQL | Infrastructure | PostgreSQL 16 | Persistent state store (experiments, jobs, results, audit) |
| Redis | Infrastructure | Redis 7 | Job queue (RPUSH/BLPOP list) |
| Prometheus | Observability | Prometheus v2.54.1 | Metrics scraping from `/metrics` endpoint |
| Grafana | Observability | Grafana 11.3.1 | Dashboard visualization (QCP Overview) |
| Loki | Observability | Grafana Loki 3.2.1 | Log aggregation pipeline |
| Helm Chart | Deployment | Helm 3 | Kubernetes deployment manifests (api, worker, web) |
| Terraform | Infrastructure | Terraform ≥ 1.8.0 | Kubernetes namespace baseline |
| OPA/Conftest | Governance | Rego policies | Deployment security policy enforcement |

### 1.4 Architectural Boundary Analysis

```
┌─────────────────────────────────────────────────────────────────────────┐
│ API LAYER                                                                │
│ services/api/app/api/routes.py        ← HTTP endpoints (REST)           │
│ services/api/app/api/deps.py          ← Dependency injection            │
│ services/api/app/core/correlation.py  ← Request correlation middleware   │
│ services/api/app/core/observability.py← Metrics middleware               │
│ services/api/app/domain/schemas.py    ← Request/response validation      │
├─────────────────────────────────────────────────────────────────────────┤
│ SERVICE LAYER                                                            │
│ services/api/app/services/job_service.py    ← Job submission logic       │
│ services/api/app/services/worker_service.py ← Job execution orchestration│
│ services/api/app/services/provider_factory.py ← Provider routing         │
│ services/api/app/domain/state_machine.py    ← State transition rules     │
├─────────────────────────────────────────────────────────────────────────┤
│ REPOSITORY LAYER                                                         │
│ services/api/app/repositories/experiments.py ← Experiment CRUD           │
│ services/api/app/repositories/jobs.py        ← Job CRUD + transitions    │
│ services/api/app/repositories/results.py     ← Result persistence        │
│ services/api/app/repositories/audit.py       ← Audit event logging       │
│ services/api/app/db/models.py                ← SQLAlchemy ORM models     │
│ services/api/app/db/session.py               ← Async session factory     │
├─────────────────────────────────────────────────────────────────────────┤
│ WORKER SYSTEM                                                            │
│ workers/quantum-runner/runner/main.py  ← Infinite loop: dequeue+process  │
│ services/api/app/queue/redis_queue.py  ← Redis RPUSH/BLPOP abstraction   │
├─────────────────────────────────────────────────────────────────────────┤
│ SIMULATION PROVIDERS                                                     │
│ services/api/app/simulation/providers.py         ← ABC interface         │
│ services/api/app/simulation/qiskit_adapter.py    ← Local Qiskit sim      │
│ services/api/app/simulation/ibm_runtime_adapter.py ← IBM Quantum backend │
├─────────────────────────────────────────────────────────────────────────┤
│ INFRASTRUCTURE                                                           │
│ docker-compose.yml                    ← Local stack (7 containers)       │
│ infra/helm/quantum-control-plane/     ← Kubernetes deployment            │
│ infra/terraform/                      ← Namespace provisioning           │
│ infra/observability/                  ← Prometheus, Grafana, Loki        │
│ infra/policies/                       ← OPA Rego security policies       │
│ .github/workflows/ci.yml             ← CI pipeline (lint, test, build)   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.5 End-to-End System Execution Flow

1. **Infrastructure boot**: `docker compose up` starts PostgreSQL, Redis, API, Worker, Web, Prometheus, Grafana, and Loki.
2. **Schema initialization**: `alembic upgrade head` applies `0001_initial_schema.py` — creates `experiments`, `jobs`, `results`, `audit_events` tables.
3. **User interaction**: Browser navigates to `http://localhost:3000` → Next.js app redirects to `/experiments/new`.
4. **Experiment submission**: User fills form (name, QASM, shots, provider) → `submitJob()` calls `POST /v1/jobs` on the API.
5. **API processing**: FastAPI route handler → `JobService.submit()` persists Experiment + Job (SUBMITTED→QUEUED) + audit event, then enqueues a Redis message.
6. **Worker pickup**: Worker's infinite loop calls `BLPOP` on `quantum.jobs` → receives `{job_id, correlation_id}`.
7. **Job execution**: `WorkerService.process_job()` transitions job to RUNNING, resolves the provider adapter, calls `adapter.run()` with the QASM payload and shot count.
8. **Simulation**: The adapter (local Qiskit or IBM Runtime) parses QASM, transpiles the circuit, runs simulation, and returns measurement counts.
9. **Result persistence**: Worker saves `ExecutionResult` → transitions job to SUCCEEDED → commits transaction → emits metrics.
10. **Result retrieval**: UI fetches `GET /v1/jobs/{id}` and `GET /v1/jobs/{id}/result` to display status and measurement histogram.

---

## PHASE 2 — ARCHITECTURE ANALYSIS

### 2.1 Architecture Diagram

```
                        ┌───────────────────────────────────────────────────────┐
                        │                  OBSERVABILITY                         │
                        │  Prometheus ← scrape /metrics                         │
                        │  Grafana    ← dashboards (qcp-overview)               │
                        │  Loki       ← JSON structured logs                    │
                        │  OTEL       ← distributed traces (OTLP export)        │
                        └───────────────────────────────────────────────────────┘
                                          ▲ metrics, logs, traces
                                          │
 ┌────────────┐     ┌──────────────────────┴───────────────────────┐
 │ Next.js    │     │              CONTROL PLANE (API)              │
 │ Frontend   │────►│  FastAPI + CorrelationId + Metrics middleware │
 │ (port 3000)│ HTTP│                                               │
 └────────────┘     │  ┌─────────────┐  ┌──────────────┐           │
                    │  │ JobService   │  │ Schemas      │           │
    Browser ───────►│  │ (submit,     │  │ (Pydantic    │           │
    POST /v1/jobs   │  │  get, list)  │  │  validation) │           │
                    │  └──────┬───────┘  └──────────────┘           │
                    │         │                                      │
                    │  ┌──────┴───────────────────────────────────┐ │
                    │  │           REPOSITORY LAYER                │ │
                    │  │  ExperimentRepo │ JobRepo │ ResultRepo    │ │
                    │  │  AuditRepo      │ StateMachine            │ │
                    │  └──────┬──────────┴─────────┬──────────────┘ │
                    └─────────┼────────────────────┼────────────────┘
                              │                    │
                    ┌─────────▼──────────┐  ┌──────▼────────┐
                    │  PostgreSQL 16     │  │  Redis 7      │
                    │  (experiments,     │  │  (quantum.jobs │
                    │   jobs, results,   │  │   RPUSH/BLPOP) │
                    │   audit_events)    │  └──────┬────────┘
                    └────────────────────┘         │ BLPOP
                                                   │
                    ┌──────────────────────────────▼───────────────┐
                    │            EXECUTION PLANE (Worker)           │
                    │                                               │
                    │  runner/main.py → WorkerService.process_job() │
                    │                                               │
                    │  ┌─────────────────┐  ┌────────────────────┐ │
                    │  │ LocalQiskitSim  │  │ IbmRuntimeAdapter  │ │
                    │  │ (BasicProvider) │  │ (SamplerV2)        │ │
                    │  └─────────────────┘  └────────────────────┘ │
                    └──────────────────────────────────────────────┘
```

### 2.2 Request Lifecycle

```
HTTP Request
    │
    ├── CorrelationIdMiddleware: extract/generate X-Correlation-ID → ContextVar
    ├── MetricsMiddleware: start timer, expose /metrics endpoint
    │
    ▼
routes.py → endpoint function
    │
    ├── Depends(get_session): create AsyncSession from SQLAlchemy pool
    ├── Depends(get_redis): create Redis connection from URL
    │
    ▼
JobService (instantiated per-request)
    │
    ├── Check idempotency_key → return existing if found
    ├── ExperimentRepository.create() → flush to DB
    ├── JobRepository.create() → flush (status=SUBMITTED)
    ├── JobRepository.transition(QUEUED) → state machine check + flush
    ├── RedisQueue.enqueue_job() → RPUSH to "quantum.jobs"
    ├── AuditRepository.log() → persist audit event
    ├── session.commit() → atomic commit of all changes
    ├── Increment Prometheus counter (qcp_jobs_submitted_total)
    │
    ▼
Return SubmitExperimentResponse {experiment, job}
```

### 2.3 Job Lifecycle (State Machine)

```
    ┌──────────┐
    │ SUBMITTED│ ──(validation + enqueue)──► ┌────────┐
    └──────────┘                              │ QUEUED │
         │                                    └───┬────┘
         │ (fail at submit)                       │
         ▼                                        │ (worker picks up)
    ┌────────┐                                    ▼
    │ FAILED │ ◄──(execution error)────── ┌─────────┐
    └───┬────┘                             │ RUNNING │
        │                                  └────┬────┘
        │ (retry: attempts < max_attempts)      │
        │                                       │ (success)
        ▼                                       ▼
    ┌────────┐                           ┌───────────┐
    │ QUEUED │ (re-enqueue)              │ SUCCEEDED │
    └────────┘                           └───────────┘
```

**Transition table** (enforced by `state_machine.py`):

| Current State | Allowed Next States |
|---|---|
| SUBMITTED | QUEUED, FAILED |
| QUEUED | RUNNING, FAILED |
| RUNNING | SUCCEEDED, FAILED |
| SUCCEEDED | _(terminal)_ |
| FAILED | QUEUED _(retry)_ |

### 2.4 Queue/Worker Model

- **Queue primitive**: Redis List (`quantum.jobs`) using `RPUSH` (enqueue) and `BLPOP` (blocking dequeue with 5-second timeout).
- **Message format**: `{"job_id": "<uuid>", "correlation_id": "<uuid>"}` — JSON serialized.
- **Delivery semantics**: At-least-once. If the worker crashes after `BLPOP` but before `session.commit()`, the message is lost. The queue does not have acknowledgment semantics.
- **Worker concurrency**: Single-threaded async loop. One worker processes one job at a time. Horizontal scaling is achieved by running multiple worker replicas.
- **Execution model**: Provider adapters use `asyncio.to_thread()` to run synchronous Qiskit simulation in a thread pool, freeing the event loop.

### 2.5 Database Interactions

All DB operations use SQLAlchemy 2.0 async with asyncpg (PostgreSQL) or aiosqlite (tests).

| Table | Key Operations | Write Path |
|---|---|---|
| `experiments` | INSERT on submit, SELECT on get | API (submit) |
| `jobs` | INSERT, UPDATE (state transitions), SELECT | API (submit), Worker (transitions) |
| `results` | UPSERT (merge), SELECT | Worker (save result) |
| `audit_events` | INSERT only | API (submit), Worker (success/failure/retry) |

**Transaction boundary**: The API commits once at the end of `submit()`. The worker commits once per `process_job()` call (success or failure path). All intermediate operations use `flush()` for ordering within the transaction.

### 2.6 Simulation Provider Abstraction

```python
class ExecutionProviderAdapter(ABC):
    provider: ExecutionProvider

    @abstractmethod
    async def run(self, payload: CircuitPayload, timeout_seconds: int, job_id: str) -> ExecutionResult:
        ...

    async def poll(self, remote_run_id: str) -> tuple[bool, ExecutionResult | None]:
        return True, None  # Default: synchronous completion
```

**Implementations**:

| Adapter | Backend | Execution Model |
|---|---|---|
| `LocalQiskitSimulator` | `BasicProvider` → `basic_simulator` | `asyncio.to_thread(backend.run(...))` with `asyncio.wait_for(timeout)` |
| `IbmRuntimeAdapter` | `QiskitRuntimeService` → `SamplerV2` | `asyncio.to_thread(_run)` with `asyncio.wait_for(timeout)` |

**Factory** (`provider_factory.py`):
- `IBM_RUNTIME` → `IbmRuntimeAdapter()` (requires `ibm_runtime_enabled=True` + valid token)
- Anything else → `LocalQiskitSimulator()`

---

## PHASE 3 — QUANTUM COMPUTATION MODEL

### 3.1 System Classification

This system is a **Quantum Job Orchestration Platform** — specifically, a cloud-native control plane for managing quantum circuit execution across multiple backends.

| Characteristic | This Platform | Pure Simulator | Hybrid |
|---|---|---|---|
| Custom statevector math | ❌ | ✅ | Partial |
| Custom gate matrices | ❌ | ✅ | Partial |
| Custom measurement sampling | ❌ | ✅ | Partial |
| Circuit scheduling & queuing | ✅ | ❌ | ✅ |
| Multi-backend routing | ✅ | ❌ | ✅ |
| Result persistence & comparison | ✅ | ❌ | ✅ |
| Provider abstraction layer | ✅ | ❌ | ✅ |

**Verdict**: This is a **job orchestration platform** that delegates all quantum physics to external engines (Qiskit for local simulation, IBM Quantum Runtime for cloud execution). It provides the management layer: scheduling, state management, retry logic, observability, and multi-backend comparison.

### 3.2 Qubit Representation

The platform **does not implement qubit representation**. Qubits are described in OpenQASM 2.0 strings:

```qasm
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];     // 2-qubit register
creg c[2];     // 2 classical bits for measurement
h q[0];        // Hadamard gate on qubit 0
cx q[0], q[1]; // CNOT gate → entanglement
measure q[0] -> c[0];
measure q[1] -> c[1];
```

The QASM string is:
1. Stored as `circuit_qasm` (TEXT column in PostgreSQL `experiments` table)
2. Parsed by `qiskit.qasm2.loads()` into a `QuantumCircuit` object
3. Transpiled for the target backend via `transpile(circuit, backend)`
4. Executed by the backend's native simulator engine

Qiskit internally represents the n-qubit state as a complex statevector of dimension 2^n (for `BasicSimulator`) or a density matrix (for noise models).

### 3.3 Circuit Payload Structure

```python
class CircuitPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    qasm: str = Field(min_length=1)           # OpenQASM 2.0 source
    shots: int = Field(default=1024, ge=1, le=10000)  # Measurement repetitions
```

**Constraints**:
- `qasm`: minimum 1 character (no syntax validation at submission time — deferred to worker)
- `shots`: 1–10,000 (Pydantic validation)
- `extra="forbid"`: strict schema, no unknown fields allowed

### 3.4 Measurement Model

Measurement follows the standard quantum mechanics Born rule, entirely delegated to Qiskit:

1. `measure q[i] -> c[i]` in QASM defines measurement instructions
2. Qiskit computes `P(x) = |⟨x|ψ⟩|²` for each computational basis state
3. Samples the distribution `shots` times
4. Returns `counts: dict[str, int]` — e.g., `{"00": 512, "11": 512}` for a Bell state

The platform stores this histogram in the `results.result_payload` JSON column and returns it via `GET /v1/jobs/{id}/result`.

### 3.5 Provider Integration

| Provider | SDK | Authentication | Execution |
|---|---|---|---|
| **Local Simulator** | `qiskit >= 1.2.0` | None | `BasicProvider().get_backend("basic_simulator")` |
| **IBM Quantum Runtime** | `qiskit-ibm-runtime >= 0.36.1` | Token + channel + instance (env vars) | `QiskitRuntimeService` → `SamplerV2` → `backend.run()` |

**IBM Runtime configuration** (environment variables):
- `QCP_IBM_RUNTIME_ENABLED=true`
- `QCP_IBM_RUNTIME_TOKEN=<ibm_api_token>`
- `QCP_IBM_RUNTIME_CHANNEL=ibm_quantum`
- `QCP_IBM_RUNTIME_INSTANCE=<hub/group/project>`
- `QCP_IBM_RUNTIME_BACKEND=ibm_brisbane`

### 3.6 Quantum Job Execution Flow

```
1. User submits QASM + shots + provider via POST /v1/jobs
2. API validates request, persists Experiment + Job, enqueues to Redis
3. Worker dequeues job, loads Experiment's circuit_qasm
4. Provider factory resolves adapter (Local or IBM)
5. Adapter:
   a. Parses QASM → QuantumCircuit (qiskit.qasm2.loads)
   b. Transpiles for target backend
   c. Runs simulation/execution in a thread pool
   d. Collects measurement counts
6. Worker saves ExecutionResult, transitions job to SUCCEEDED
7. User retrieves counts via GET /v1/jobs/{id}/result
```

---

## PHASE 4 — CODE QUALITY & ENGINEERING REVIEW

### 4.1 Architectural Strengths

1. **Clean separation of concerns**: API layer → service layer → repository layer → DB. Clear boundaries with minimal cross-layer coupling.
2. **Shared contracts package**: `packages/contracts` provides canonical Pydantic models used by both API and worker — prevents schema drift.
3. **State machine enforcement**: Explicit transition rules in `state_machine.py` with `ensure_transition()` — prevents invalid job state mutations.
4. **Idempotency support**: `Idempotency-Key` header on job submission prevents duplicate job creation.
5. **Correlation ID propagation**: End-to-end traceability from HTTP request through queue to worker via `ContextVar` and message payload.
6. **Provider abstraction**: `ExecutionProviderAdapter` ABC with `poll()` hook — extensible to new backends.
7. **Observability built-in**: Prometheus counters/histograms, OpenTelemetry traces, JSON structured logging — production-grade instrumentation from day one.
8. **Audit trail**: Every lifecycle event persisted in `audit_events` table with correlation ID.
9. **Infrastructure-as-code**: Helm chart, Terraform baseline, Docker Compose, OPA policies, CI pipeline — complete deployment story.
10. **Strict typing**: `mypy --strict`, Pydantic `ConfigDict(extra="forbid")`, typed repositories.

### 4.2 Issues by Severity

#### CRITICAL

| # | Issue | Location | Impact |
|---|---|---|---|
| C1 | **No authentication or authorization** | `routes.py` — all endpoints open | Any network-reachable client can submit circuits, list all jobs, read all results. IBM credentials could be abused for expensive quantum runs. |
| C2 | **Queue message loss on worker crash** | `redis_queue.py` — `BLPOP` removes message atomically | If the worker crashes after dequeue but before committing, the job is permanently lost in QUEUED state with no recovery path. |

#### HIGH

| # | Issue | Location | Impact |
|---|---|---|---|
| H1 | **No QASM validation at submission time** | `schemas.py` — `min_length=1` only | Invalid QASM is accepted, persisted, and queued. Worker discovers the error, wastes a retry cycle, produces confusing failure. |
| H2 | **Stale RUNNING jobs never recovered** | `worker_service.py` — no timeout sweep | If worker crashes mid-execution, job stays RUNNING forever. No background process detects and fails stuck jobs. |
| H3 | **Worker has no graceful shutdown** | `runner/main.py` — `while True` with no signal handling | SIGTERM during Kubernetes rolling update kills worker mid-job. Job left in inconsistent state. |
| H4 | **Single-threaded worker** | `runner/main.py` — sequential processing | One job at a time per worker. Long-running IBM jobs (minutes/hours) completely block the worker. |
| H5 | **No tenant isolation** | `list_jobs` returns all jobs, no user/org model | Multi-user deployment leaks job data across users. |

#### MEDIUM

| # | Issue | Location | Impact |
|---|---|---|---|
| M1 | **`BasicProvider` deprecation** | `qiskit_adapter.py` | Will break on Qiskit 2.0 upgrade. Should use `AerSimulator`. |
| M2 | **IBM Runtime adapter blocks worker thread** | `ibm_runtime_adapter.py` | `asyncio.to_thread(_run)` blocks for full IBM job duration. `poll()` method exists but is unimplemented. |
| M3 | **No pagination on list endpoints** | `routes.py`, `jobs.py` | Hard-coded limit of 100. Will cause performance issues at scale. |
| M4 | **Redis connection not pooled in deps** | `deps.py` — creates new connection per request | Each API request creates and closes a Redis connection. High overhead under load. |
| M5 | **No rate limiting** | All endpoints | Unbounded submission rate could overwhelm queue and workers. |
| M6 | **No DB connection pool tuning** | `session.py` — default pool settings | SQLAlchemy defaults may not handle production concurrency. |
| M7 | **Audit events grow unbounded** | `audit.py` — insert only, no retention | No TTL or archival policy. Table will grow indefinitely. |

#### LOW

| # | Issue | Location | Impact |
|---|---|---|---|
| L1 | **`instrument_fastapi(app)` uses `Any`** | `observability.py:48` | `# type: ignore[no-untyped-def]` suppresses type checking. |
| L2 | **Test DB file created in working directory** | `test_api_jobs.py` — `./test_api.db` | Test artifacts left in source tree. |
| L3 | **No OpenAPI schema versioning** | `main.py` | API version `v1` in routes but not in OpenAPI metadata. |
| L4 | **`readyz` has inline import** | `routes.py:34` — `from typing import Any, cast` inside function | Style inconsistency; should be at module level. |

### 4.3 Security Concerns (Ranked)

1. **Unauthenticated API** (Critical) — IBM token abuse, data exfiltration.
2. **No input sanitization for QASM** (High) — potential for resource-exhaustion attacks via expensive circuits.
3. **Redis without ACL/TLS** (Medium) — queue poisoning in shared network environments.
4. **IBM token in environment variable** (Medium) — visible in Docker inspect, process environment.
5. **No CORS configuration** (Low) — web frontend may fail in cross-origin deployments.
6. **Database credentials in default config** (Low) — `quantum:quantum` as default password.

### 4.4 Concurrency and Data Consistency

- **Positive**: Single atomic `session.commit()` per operation ensures transactional consistency.
- **Positive**: State machine check + update in same transaction prevents race conditions on single-worker deployments.
- **Risk**: With multiple workers, two workers could `BLPOP` different jobs for the same experiment. However, since job IDs are unique and state transitions are per-job, this is safe.
- **Risk**: Multiple workers running concurrent `select + update` on the same job model could race. The `flush()` within a transaction provides isolation only if using `SERIALIZABLE` or row-level locking (not configured — default is `READ COMMITTED`).
- **Recommendation**: Add `SELECT ... FOR UPDATE` in `JobRepository.transition()` to prevent concurrent state mutations.

---

## PHASE 5 — SCALABILITY ANALYSIS

### 5.1 Current Capacity Profile

| Component | Current Design | Estimated Throughput |
|---|---|---|
| API Server | Single uvicorn process | ~500–1000 req/s (FastAPI + asyncpg) |
| Worker | Single-threaded async loop | ~100 jobs/day (local sim, ~1s each) |
| PostgreSQL | Single instance, no replication | ~10,000 writes/s |
| Redis | Single instance, no clustering | ~100,000 ops/s |
| Queue | Redis List (no partitioning) | Single consumer group |

### 5.2 Scale: 10,000 Jobs/Day (~7 jobs/min)

**Status**: Achievable with minor tuning.

| Component | Change Required |
|---|---|
| API | No change. Well within capacity. |
| Workers | 2–3 worker replicas to handle burst. |
| PostgreSQL | Add indexes on `jobs.status`, `jobs.experiment_id`. |
| Redis | No change. |
| Observability | Already adequate. |

**Bottleneck**: Worker throughput. Local simulation takes 100ms–1s per job. IBM Runtime jobs take 30s–5min. With 3 workers, max ~2,600 local jobs/day at 1s each, or ~1,700 at worst case. **4–6 workers** recommended.

### 5.3 Scale: 1,000,000 Jobs/Day (~700 jobs/min)

**Status**: Requires significant redesign.

| Component | Bottleneck | Solution |
|---|---|---|
| API | Connection pooling, request rate | Multiple uvicorn workers behind load balancer. Tune asyncpg pool (`pool_size=20, max_overflow=40`). |
| Workers | Sequential processing, no concurrency | **Redesign**: Replace single-threaded loop with concurrent worker pool (e.g., `asyncio.Semaphore(N)` + task group). 50–100 worker replicas. |
| PostgreSQL | Write volume (~12 writes/job = 12M writes/day) | **Read replicas** for GET endpoints. **Write sharding** by job ID. **Partitioned tables** by `created_at` for time-series queries. |
| Redis | Single list = single consumer | **Replace** Redis List with **Redis Streams** (`XADD`/`XREADGROUP`) for consumer groups, or migrate to **Apache Kafka** for partitioned, durable queuing. |
| Queue | At-least-once delivery without ack | Redis Streams provide `XACK` semantics. Kafka provides offset-based replay. |
| Audit | Unbounded growth | **Move to append-only log** (Kafka topic) or **time-series DB** (TimescaleDB). Implement retention policy. |

**Key redesign**: Introduce **async polling** for IBM Runtime jobs. Currently, each IBM job blocks a worker for the entire execution time (minutes). With 1M jobs/day and even 10% IBM, that's 100K blocking jobs — would need 7,000+ workers. With async polling, a single worker can track thousands of pending IBM jobs.

### 5.4 Scale: 100,000,000 Jobs/Day (~70,000 jobs/min)

**Status**: Requires complete platform re-architecture.

| Component | Architecture |
|---|---|
| API | **Horizontally scaled stateless pods** behind global load balancer. Rate limiting + admission control. API Gateway (Kong/Envoy) with circuit breaker. |
| Workers | **Event-driven architecture**. Replace polling with Kafka consumer groups. 500–1,000 worker pods with auto-scaling (KEDA) based on queue depth. Each worker runs N concurrent circuit executions. |
| PostgreSQL | **Distributed SQL** (CockroachDB/YugabyteDB) or **purpose-built stores**: job metadata in PostgreSQL (sharded by org), results in object storage (S3) with metadata index. |
| Redis | **Eliminate** as primary queue. Use Kafka with topic partitioning by provider. Redis retained for caching (job status cache, idempotency store with TTL). |
| Queue | **Kafka** with partitions by `(provider, priority)`. Dead-letter topics for failed jobs. Exactly-once semantics via Kafka transactions. |
| Audit | **Kafka → ClickHouse/BigQuery** for analytical queries. No longer in PostgreSQL. |
| Results | **Object Storage** (S3/GCS) for full result payloads. PostgreSQL stores metadata + S3 pointer. |
| Provider Adapters | **Independent microservices** per provider (local-sim-service, ibm-runtime-service, aws-braket-service). Each with independent scaling and rate limiting per provider API quota. |

**Architecture at 100M/day**:

```
Client → API Gateway (Kong) → API Service (50+ pods)
                                    │
                               ┌────┴────┐
                               │  Kafka   │ ← partitioned by (provider, priority)
                               └────┬────┘
                     ┌──────────────┼──────────────┐
                     ▼              ▼               ▼
              Local Worker    IBM Worker      AWS Worker
              (200 pods)      (100 pods)      (100 pods)
                     │              │               │
                     ▼              ▼               ▼
              Local Sim       IBM Quantum     AWS Braket
                     │              │               │
                     └──────────────┼──────────────┘
                                    ▼
                           Result Store (S3 + metadata in CRDB)
```

### 5.5 Scaling Summary Matrix

| Dimension | 10K/day | 1M/day | 100M/day |
|---|---|---|---|
| API pods | 1 | 5–10 | 50+ |
| Worker pods | 4–6 | 50–100 | 500–1,000 |
| Database | Single PG | PG + read replicas | CockroachDB / sharded PG |
| Queue | Redis List | Redis Streams / Kafka | Kafka (partitioned) |
| Result storage | PG JSON column | PG JSON column | S3 + metadata index |
| Provider architecture | In-process adapter | In-process adapter | Dedicated microservices |
| Estimated monthly infra cost | $50–100 | $2,000–5,000 | $50,000–200,000 |

---

## PHASE 6 — STARTUP PRODUCT ANALYSIS

### 6.1 Problem Statement

**Quantum computing is hard to operationalize.** Research teams and enterprises experimenting with quantum algorithms face:

1. **Backend fragmentation**: IBM Quantum, AWS Braket, Google Cirq, IonQ, Rigetti — each with different SDKs, APIs, and execution models.
2. **No unified job management**: Circuit submission, status tracking, retry logic, and result comparison require custom glue code per backend.
3. **No observability**: Quantum experiments lack the operational tooling (metrics, logs, audit trails) standard in classical infrastructure.
4. **Reproducibility crisis**: Without persistent state and experiment tracking, quantum research results are difficult to reproduce.

### 6.2 Target Customers

| Segment | Description | Pain Point | Willingness to Pay |
|---|---|---|---|
| **Quantum Research Labs** | University and corporate labs running quantum experiments | Need multi-backend comparison, result tracking, reproducibility | Medium ($500–5K/month) |
| **Enterprise R&D** | Large companies exploring quantum advantage (finance, pharma, logistics) | Need compliance, audit trails, access control, cost management | High ($5K–50K/month) |
| **Quantum Software Startups** | Companies building quantum applications | Need backend abstraction to avoid vendor lock-in | Medium ($1K–10K/month) |
| **Quantum Education** | Universities teaching quantum computing | Need simple submission interface, result visualization | Low ($100–500/month) |
| **Managed Service Providers** | Cloud platforms offering quantum-as-a-service | Need white-label orchestration layer | High (custom pricing) |

### 6.3 Developer Experience

Developers would interact with the platform in three ways:

**1. REST API (primary)**:
```bash
# Submit a quantum circuit
curl -X POST https://api.qcp.io/v1/jobs \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "bell-state-experiment",
    "circuit": {
      "qasm": "OPENQASM 2.0; include \"qelib1.inc\"; qreg q[2]; creg c[2]; h q[0]; cx q[0],q[1]; measure q[0]->c[0]; measure q[1]->c[1];",
      "shots": 4096
    },
    "provider": "ibm_runtime"
  }'

# Check job status
curl https://api.qcp.io/v1/jobs/<job_id>

# Get results
curl https://api.qcp.io/v1/jobs/<job_id>/result
```

**2. Python SDK** (planned):
```python
from qcp import Client

client = Client(api_key="...")
job = client.submit(qasm="...", shots=1024, provider="ibm_runtime")
result = job.wait()
print(result.counts)  # {"00": 512, "11": 512}
```

**3. Web Console** (existing):
- Submit experiments via form
- Monitor job history and status
- Compare results across providers

### 6.4 Competitive Analysis

| Feature | QCP (this platform) | IBM Quantum | AWS Braket | Azure Quantum |
|---|---|---|---|---|
| Multi-backend routing | ✅ (local + IBM, extensible) | ❌ (IBM only) | ✅ (IonQ, Rigetti, etc.) | ✅ (IonQ, Quantinuum, etc.) |
| Self-hosted option | ✅ | ❌ | ❌ | ❌ |
| Open source | ✅ | ❌ | ❌ | ❌ |
| Job orchestration + retry | ✅ | Limited | Limited | Limited |
| Audit trail | ✅ | ❌ | CloudTrail | Azure Monitor |
| Cost management | ❌ (planned) | ❌ | ✅ | ✅ |
| Circuit optimization | ❌ (planned) | ✅ | Partial | Partial |
| Noise modeling | ❌ (via Qiskit) | ✅ | Via provider | Via provider |

**Competitive advantage**: Open-source, self-hosted, multi-backend orchestration with enterprise-grade observability. No existing player offers this combination.

**Competitive weakness**: Lacks circuit optimization, noise modeling, real-time hardware calibration data, and the massive ecosystems of IBM/AWS/Azure.

### 6.5 Product Strategy

#### MVP (Already ~70% built)
- Multi-backend job submission (local + IBM)
- Job lifecycle management with retries
- Result persistence and retrieval
- Web console for experiment submission
- **Missing for MVP launch**: Authentication, QASM validation, basic rate limiting

#### Developer Onboarding
1. `pip install qcp-sdk` → Python client library
2. Sign up at `qcp.io` → get API key
3. Submit first circuit in 3 lines of code
4. View results in web console

#### API Product
- **Free tier**: 100 local simulation jobs/month
- **Developer**: $29/month — 10K local jobs, 100 IBM/cloud jobs
- **Team**: $199/month — 100K local jobs, 1K cloud jobs, team management, audit logs
- **Enterprise**: Custom — unlimited local, dedicated workers, SSO, SLA, on-premise deployment

#### Pricing Model
- **Per-job pricing** for cloud provider executions (markup on IBM/AWS costs)
- **Flat subscription** for platform access + local simulation
- **Compute-based** for self-hosted (by worker instance count)

---

## PHASE 7 — ROADMAP TO PRODUCTION

### Phase 1: MVP (Weeks 1–6)

**Goal**: Deployable SaaS with core functionality.

| Week | Deliverable | Details |
|---|---|---|
| 1–2 | **Authentication & Authorization** | API key authentication, JWT tokens, user model, per-user job isolation |
| 2–3 | **QASM Validation** | Pre-parse QASM at submission time, return 422 for invalid circuits |
| 3–4 | **Graceful Worker Shutdown** | SIGTERM handling, job recovery for stuck RUNNING jobs |
| 4–5 | **Rate Limiting & Pagination** | Per-user rate limits, cursor-based pagination on all list endpoints |
| 5–6 | **Production Deployment** | Managed PostgreSQL (RDS/Cloud SQL), managed Redis (ElastiCache), TLS everywhere, Kubernetes on EKS/GKE |

**Exit criteria**: Single-tenant SaaS deployable on Kubernetes with authn, monitoring, and reliable job execution.

### Phase 2: Beta Platform (Weeks 7–14)

**Goal**: Multi-tenant platform with SDK and developer experience.

| Week | Deliverable | Details |
|---|---|---|
| 7–8 | **Python SDK** | `qcp-sdk` package: submit, poll, wait, list results. Published to PyPI. |
| 8–9 | **Multi-tenancy** | Organization model, RBAC (admin, member, viewer), API key scoping |
| 9–10 | **AWS Braket Provider** | New `BraketAdapter` implementing `ExecutionProviderAdapter`. Support IonQ, Rigetti. |
| 10–11 | **Async IBM Polling** | Non-blocking IBM job submission + polling loop. Free worker to process other jobs. |
| 11–12 | **Cost Tracking** | Per-job cost estimation and tracking. Budget alerts. |
| 12–14 | **Enhanced Web Console** | Job filtering, result visualization (histogram charts), experiment comparison dashboard |

**Exit criteria**: Beta program with 10–20 external users. Python SDK published. 3+ quantum backends supported.

### Phase 3: Production System (Weeks 15–26)

**Goal**: Production-grade SaaS with enterprise features.

| Week | Deliverable | Details |
|---|---|---|
| 15–16 | **Kafka Migration** | Replace Redis queue with Kafka for durable, partitioned messaging |
| 17–18 | **Circuit Optimization** | Auto-transpilation, gate decomposition, routing optimization per backend |
| 19–20 | **Webhook Notifications** | Job completion webhooks, Slack/Teams integrations |
| 21–22 | **SOC 2 Preparation** | Encryption at rest, access logging, data retention policies, pen testing |
| 23–24 | **Billing Integration** | Stripe integration, usage-based billing, invoice generation |
| 25–26 | **Public Launch** | Marketing site, documentation, API reference, tutorials |

**Exit criteria**: Public SaaS launch with paid customers. SOC 2 Type I in progress.

### Phase 4: Enterprise Version (Weeks 27–52)

**Goal**: Enterprise-ready platform for large organizations.

| Quarter | Deliverable |
|---|---|
| Q3 | **SSO/SAML integration**, air-gapped deployment option, custom SLA |
| Q3 | **Advanced analytics**: experiment comparison, statistical significance testing, noise characterization |
| Q4 | **Workflow engine**: multi-step quantum algorithms, variational circuits (VQE, QAOA), hybrid classical-quantum pipelines |
| Q4 | **Marketplace**: community-contributed circuit templates, provider plugins |

---

## PHASE 8 — FINAL CTO ASSESSMENT

### 8.1 Technical Maturity

**Rating: 6/10 — Strong Prototype, Not Yet Production-Ready**

| Aspect | Rating | Notes |
|---|---|---|
| Architecture | 8/10 | Clean layering, clear boundaries, good abstractions. Staff-level design. |
| Code Quality | 7/10 | Typed, linted, tested. Some mypy workarounds. Strict Pydantic models. |
| Security | 3/10 | No auth, no CORS, no rate limiting. IBM credentials in env vars. Critical gap. |
| Reliability | 5/10 | State machine is solid, but no crash recovery, no dead-letter queue, no graceful shutdown. |
| Scalability | 4/10 | Single-threaded worker, Redis List queue, no pagination. Won't survive production load. |
| Observability | 8/10 | Prometheus, OTEL, Grafana, structured logging — production-grade from day one. |
| Infrastructure | 7/10 | Docker, Helm, Terraform, OPA policies, CI/CD. Comprehensive for a prototype. |
| Testing | 5/10 | Unit + integration tests exist, but coverage is thin. No e2e tests, no load tests, no property-based tests. |
| Documentation | 7/10 | ADRs, architecture docs, threat model, runbooks, demo walkthrough. Above average. |

### 8.2 Feasibility as a Startup

**Rating: 7/10 — Viable with focused execution**

**In favor**:
- The quantum computing market is growing rapidly ($1.3B in 2024, projected $5.3B by 2029).
- No dominant open-source orchestration platform exists. IBM Qiskit Runtime, AWS Braket, and Azure Quantum are closed, single-vendor solutions.
- The "backend abstraction + orchestration" value proposition mirrors what Kubernetes did for containers — and it worked.
- The codebase demonstrates genuine engineering depth: state machines, audit trails, correlation IDs, provider abstraction — this is not a toy project.
- Open-source go-to-market is proven (HashiCorp, Confluent, Elastic). Open-source orchestrator + hosted SaaS is a viable model.

**Against**:
- The total addressable market for quantum computing tooling is still small (thousands of research teams, not millions of developers).
- IBM and AWS have enormous head starts in quantum ecosystems and customer relationships.
- Quantum advantage hasn't been proven for most commercial use cases, limiting near-term demand.
- The team would need deep quantum computing expertise to build circuit optimization and noise modeling — the features that differentiate premium offerings.

### 8.3 Biggest Risks

1. **Security exposure**: Launching without authentication could lead to abuse (especially IBM credential misuse) that kills the project before it starts.
2. **Market timing**: Quantum computing adoption could be slower than expected. The platform needs classical simulation value (optimization, benchmarking) to survive a "quantum winter."
3. **Provider dependency**: Heavy reliance on IBM/AWS APIs creates concentration risk. Provider pricing changes or API deprecations could break the business model.
4. **Scalability cliff**: The current single-threaded worker design will fail under load. Fixing this requires significant re-architecture before onboarding paying customers.
5. **Competition from incumbents**: IBM or AWS could add orchestration features to their existing platforms, eliminating the differentiation.

### 8.4 Biggest Opportunities

1. **First-mover in open-source quantum orchestration**: No credible open-source competitor exists. Community-driven adoption could build a moat.
2. **Multi-cloud quantum abstraction**: As quantum backends proliferate (IonQ, Rigetti, Google, Quantinuum), the "Kubernetes for quantum" positioning becomes more valuable.
3. **Enterprise compliance**: Audit trails, access control, and on-premise deployment are table stakes for enterprise quantum adoption — and the architecture already supports them.
4. **Education market**: Universities teaching quantum computing need simple, accessible tooling. Free tier + web console = low-friction adoption.
5. **Hybrid classical-quantum workflows**: Extending to support variational algorithms (VQE, QAOA) would address the most commercially relevant quantum use cases.

### 8.5 Recommended Next Steps (Priority Order)

| Priority | Action | Time | Impact |
|---|---|---|---|
| **P0** | Add API key authentication and per-user job isolation | 1 week | Eliminates critical security exposure |
| **P0** | Add QASM validation at submission time | 2 days | Prevents wasted compute and confusing errors |
| **P0** | Add graceful worker shutdown + stuck-job recovery | 3 days | Prevents data loss on deployments |
| **P1** | Implement async IBM Runtime polling | 1 week | 10x worker efficiency for cloud jobs |
| **P1** | Add pagination to list endpoints | 2 days | Prevents API degradation at scale |
| **P1** | Replace `BasicProvider` with `AerSimulator` | 1 day | Prevents Qiskit 2.0 breakage |
| **P1** | Add `SELECT FOR UPDATE` to state transitions | 1 day | Prevents race conditions with multiple workers |
| **P2** | Build Python SDK | 2 weeks | Developer adoption accelerator |
| **P2** | Add AWS Braket provider | 1 week | Multi-cloud value proposition |
| **P2** | Migrate Redis List to Redis Streams | 1 week | Durable queue with consumer groups |
| **P3** | SOC 2 preparation | 8 weeks | Enterprise sales enablement |
| **P3** | Public SaaS launch | 4 weeks | Revenue generation |

### 8.6 Honest Assessment

This is **one of the better-architected quantum platform prototypes** in the open-source space. The engineering decisions (state machines, provider abstraction, shared contracts, observability-first design) reflect staff-level thinking. The codebase is clean, typed, and testable.

However, it is **not production-ready**. The security gaps (no auth, no rate limiting) are disqualifying for any deployment beyond localhost. The worker architecture will not scale beyond toy workloads. The queue lacks durability guarantees.

**The path to production is clear and achievable**: 4–6 weeks of focused work on auth, worker reliability, and basic scaling would produce a deployable MVP. The architecture supports this evolution — no fundamental redesign is needed for the first 10K jobs/day.

**As a startup, the timing is interesting**: quantum computing is at an inflection point. The platform solves a real problem (backend fragmentation + operational tooling). Whether the market is large enough to sustain a venture-backed startup depends on quantum adoption velocity — but the open-source positioning provides a hedge.

**Bottom line**: Ship auth, fix the worker, launch an alpha. The architecture is sound. Execution determines outcome.
