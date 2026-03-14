# Deep Senior-Level Analysis: Quantum Control Plane Repository

> **Analysis Date:** 2026-03-14  
> **Repository:** `mareksuchodolski12-hash/kwantowy`  
> **Scope:** Full codebase — architecture, quantum model, correctness, security, and improvement recommendations.

---

## SECTION 1 — FILE TREE

```
kwantowy/
├── .devcontainer/
│   └── devcontainer.json
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.yml
│   │   └── feature_request.yml
│   ├── copilot-instructions.md
│   ├── pull_request_template.md
│   └── workflows/
│       └── ci.yml
├── .pre-commit-config.yaml
├── .editorconfig
├── .gitignore
├── Makefile
├── README.md
├── docker-compose.yml
│
├── apps/
│   └── web/                          # Next.js 14 frontend
│       ├── app/
│       │   ├── comparison/page.tsx
│       │   ├── experiments/new/page.tsx
│       │   ├── globals.css
│       │   ├── layout.tsx
│       │   ├── page.tsx
│       │   └── runs/
│       │       ├── [id]/page.tsx
│       │       └── page.tsx
│       ├── lib/api.ts
│       ├── next.config.js
│       ├── package.json
│       └── tsconfig.json
│
├── docs/
│   ├── analysis/
│   │   └── quantum-simulator-analysis.md   ← this file
│   ├── adr/
│   │   ├── 0001-queue-choice-redis.md
│   │   ├── 0002-persistence-model.md
│   │   └── 0003-async-orchestration-design.md
│   ├── architecture/
│   │   ├── implementation-plan.md
│   │   ├── platform-architecture.md
│   │   └── threat-model.md
│   ├── demo-walkthrough.md
│   └── runbooks/
│       ├── incident-job-failures.md
│       └── local-development.md
│
├── infra/
│   ├── helm/
│   │   └── quantum-control-plane/
│   │       ├── Chart.yaml
│   │       ├── templates/
│   │       │   ├── api-deployment.yaml
│   │       │   ├── web-deployment.yaml
│   │       │   └── worker-deployment.yaml
│   │       └── values.yaml
│   ├── observability/
│   │   ├── grafana/
│   │   ├── loki/
│   │   └── prometheus/
│   ├── policies/
│   │   └── kubernetes/deployment.rego
│   └── terraform/
│       ├── main.tf
│       ├── outputs.tf
│       └── variables.tf
│
├── packages/
│   └── contracts/                    # Shared Pydantic models (Python package)
│       └── quantum_contracts/
│           ├── __init__.py
│           └── models.py
│
├── services/
│   └── api/                          # FastAPI service (main backend)
│       ├── alembic/                  # DB migrations
│       ├── app/
│       │   ├── api/
│       │   │   ├── deps.py
│       │   │   └── routes.py
│       │   ├── core/
│       │   │   ├── config.py
│       │   │   ├── correlation.py
│       │   │   ├── logging.py
│       │   │   └── observability.py
│       │   ├── db/
│       │   │   ├── base.py
│       │   │   ├── models.py
│       │   │   └── session.py
│       │   ├── domain/
│       │   │   ├── schemas.py
│       │   │   └── state_machine.py
│       │   ├── queue/
│       │   │   └── redis_queue.py
│       │   ├── repositories/
│       │   │   ├── audit.py
│       │   │   ├── experiments.py
│       │   │   ├── jobs.py
│       │   │   └── results.py
│       │   ├── services/
│       │   │   ├── job_service.py
│       │   │   ├── provider_factory.py
│       │   │   └── worker_service.py
│       │   ├── simulation/
│       │   │   ├── ibm_runtime_adapter.py   ← IBM Quantum backend
│       │   │   ├── providers.py             ← Abstract adapter base
│       │   │   └── qiskit_adapter.py        ← Local Qiskit simulator
│       │   └── main.py
│       ├── tests/
│       │   ├── test_api_jobs.py
│       │   ├── test_healthz.py
│       │   ├── test_integration_async.py
│       │   └── test_state_machine.py
│       └── pyproject.toml
│
├── tests/
│   ├── e2e/
│   └── integration/
│
└── workers/
    └── quantum-runner/
        ├── Dockerfile
        └── runner/
            └── main.py               ← Worker entry point
```

---

## SECTION 2 — MAIN ENTRY POINTS

| Entry Point | Location | Role |
|---|---|---|
| **API Server** | `services/api/app/main.py` | FastAPI ASGI application. Run via `uvicorn app.main:app` |
| **Worker Process** | `workers/quantum-runner/runner/main.py` | Async job runner. Dequeues from Redis and executes circuits. Run via `python runner/main.py` |
| **Web Frontend** | `apps/web/app/page.tsx` | Next.js 14 App Router root page |
| **DB Migrations** | `services/api/alembic/versions/0001_initial_schema.py` | Alembic migration for PostgreSQL schema |
| **Makefile** | `Makefile` | Orchestration: `make api`, `make worker`, `make web`, `make up` |

---

## SECTION 3 — IMPORTANT FILES WITH FULL CODE

### 3.1 Shared Contracts — `packages/contracts/quantum_contracts/models.py`

```python
from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class JobState(str, Enum):
    SUBMITTED = "submitted"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ExecutionProvider(str, Enum):
    LOCAL_SIMULATOR = "local_simulator"
    IBM_RUNTIME = "ibm_runtime"


class CircuitPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    qasm: str = Field(min_length=1)
    shots: int = Field(default=1024, ge=1, le=10000)


class RetryPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_attempts: int = Field(default=3, ge=1, le=10)
    timeout_seconds: int = Field(default=30, ge=1, le=600)


class Experiment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    circuit: CircuitPayload
    created_at: datetime


class Job(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    experiment_id: UUID
    status: JobState
    provider: ExecutionProvider
    attempts: int = 0
    correlation_id: str
    idempotency_key: str | None = None
    remote_run_id: str | None = None
    created_at: datetime
    updated_at: datetime


class ExecutionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: UUID
    provider: ExecutionProvider
    backend: str
    counts: dict[str, int]
    shots: int
    duration_ms: int
    completed_at: datetime
    remote_run_id: str | None = None
```

### 3.2 API Main — `services/api/app/main.py`

```python
from fastapi import FastAPI

from app.api.routes import router
from app.core.correlation import CorrelationIdMiddleware
from app.core.logging import configure_logging
from app.core.observability import MetricsMiddleware, configure_tracing, instrument_fastapi

configure_logging()
configure_tracing()

app = FastAPI(title="Quantum Control Plane API")
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(MetricsMiddleware)
app.include_router(router)
instrument_fastapi(app)
```

### 3.3 Worker Entry Point — `workers/quantum-runner/runner/main.py`

```python
import asyncio

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings
from app.queue.redis_queue import RedisQueue
from app.services.worker_service import WorkerService


async def run() -> None:
    redis = Redis.from_url(settings.redis_url)
    queue = RedisQueue(redis)
    engine = create_async_engine(settings.database_url, future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    while True:
        item = await queue.dequeue(timeout=5)
        if not item:
            continue
        job_id, correlation_id = item
        async with session_factory() as session:
            worker = WorkerService(session, queue)
            await worker.process_job(job_id, correlation_id)


if __name__ == "__main__":
    asyncio.run(run())
```

### 3.4 Local Qiskit Simulator — `services/api/app/simulation/qiskit_adapter.py`

```python
import asyncio
import time
from datetime import UTC, datetime

from qiskit import transpile
from qiskit.providers.basic_provider import BasicProvider
from qiskit.qasm2 import loads
from quantum_contracts import CircuitPayload, ExecutionProvider, ExecutionResult

from app.simulation.providers import ExecutionProviderAdapter


class LocalQiskitSimulator(ExecutionProviderAdapter):
    provider = ExecutionProvider.LOCAL_SIMULATOR

    async def run(self, payload: CircuitPayload, timeout_seconds: int, job_id: str) -> ExecutionResult:
        started = time.monotonic()
        circuit = loads(payload.qasm)
        backend = BasicProvider().get_backend("basic_simulator")
        compiled = transpile(circuit, backend)

        result = await asyncio.wait_for(
            asyncio.to_thread(lambda: backend.run(compiled, shots=payload.shots).result()),
            timeout=timeout_seconds,
        )
        counts = result.get_counts()
        duration_ms = int((time.monotonic() - started) * 1000)
        return ExecutionResult(
            job_id=job_id,
            provider=self.provider,
            backend="qiskit_basic_simulator",
            counts={str(k): int(v) for k, v in counts.items()},
            shots=payload.shots,
            duration_ms=duration_ms,
            completed_at=datetime.now(UTC),
        )
```

### 3.5 IBM Runtime Adapter — `services/api/app/simulation/ibm_runtime_adapter.py`

```python
import asyncio
import time
from datetime import UTC, datetime

from qiskit.qasm2 import loads
from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit_ibm_runtime import SamplerV2 as Sampler
from quantum_contracts import CircuitPayload, ExecutionProvider, ExecutionResult

from app.core.config import settings
from app.simulation.providers import ExecutionProviderAdapter


class IbmRuntimeAdapter(ExecutionProviderAdapter):
    provider = ExecutionProvider.IBM_RUNTIME

    def __init__(self) -> None:
        if not settings.ibm_runtime_token:
            raise ValueError("IBM Runtime token is required when provider is enabled")
        self.service = QiskitRuntimeService(
            channel=settings.ibm_runtime_channel,
            token=settings.ibm_runtime_token,
            instance=settings.ibm_runtime_instance,
        )

    async def run(self, payload: CircuitPayload, timeout_seconds: int, job_id: str) -> ExecutionResult:
        started = time.monotonic()
        circuit = loads(payload.qasm)

        def _run() -> tuple[dict[str, int], str]:
            backend = self.service.backend(settings.ibm_runtime_backend)
            sampler = Sampler(mode=backend)
            job = sampler.run([circuit], shots=payload.shots)
            result = job.result(timeout=timeout_seconds)
            data = result[0].data.c.get_counts()
            return {str(k): int(v) for k, v in data.items()}, job.job_id()

        counts, remote_id = await asyncio.wait_for(asyncio.to_thread(_run), timeout=timeout_seconds)
        return ExecutionResult(
            job_id=job_id,
            provider=self.provider,
            backend=settings.ibm_runtime_backend,
            counts=counts,
            shots=payload.shots,
            duration_ms=int((time.monotonic() - started) * 1000),
            completed_at=datetime.now(UTC),
            remote_run_id=remote_id,
        )
```

### 3.6 State Machine — `services/api/app/domain/state_machine.py`

```python
from quantum_contracts import JobState

ALLOWED_TRANSITIONS: dict[JobState, set[JobState]] = {
    JobState.SUBMITTED: {JobState.QUEUED, JobState.FAILED},
    JobState.QUEUED: {JobState.RUNNING, JobState.FAILED},
    JobState.RUNNING: {JobState.SUCCEEDED, JobState.FAILED},
    JobState.SUCCEEDED: set(),
    JobState.FAILED: {JobState.QUEUED},
}


class InvalidStateTransition(Exception):
    pass


def ensure_transition(current: JobState, next_state: JobState) -> None:
    if next_state not in ALLOWED_TRANSITIONS[current]:
        raise InvalidStateTransition(f"invalid transition from {current.value} to {next_state.value}")
```

### 3.7 Worker Service — `services/api/app/services/worker_service.py`

```python
import logging
from datetime import UTC, datetime

from quantum_contracts import CircuitPayload, ExecutionProvider, JobState
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ExperimentModel, JobModel
from app.domain.state_machine import InvalidStateTransition
from app.queue.redis_queue import RedisQueue
from app.repositories.audit import AuditRepository
from app.repositories.jobs import JobRepository
from app.repositories.results import ResultRepository
from app.services.provider_factory import get_provider

logger = logging.getLogger(__name__)


class WorkerService:
    def __init__(self, session: AsyncSession, queue: RedisQueue):
        self.session = session
        self.jobs = JobRepository(session)
        self.results = ResultRepository(session)
        self.audit = AuditRepository(session)
        self.queue = queue

    async def process_job(self, job_id: str, correlation_id: str) -> None:
        job_model = await self.session.scalar(select(JobModel).where(JobModel.id == job_id))
        if job_model is None:
            return
        provider = ExecutionProvider(job_model.provider)
        try:
            await self.jobs.transition(job_model.id, JobState.RUNNING)
        except InvalidStateTransition:
            return

        await self.jobs.increment_attempt(job_model.id)
        if job_model.queued_at:
            queue_latency_seconds.labels(provider=provider.value).observe(
                max((datetime.now(UTC) - job_model.queued_at).total_seconds(), 0)
            )

        exp = await self.session.scalar(select(ExperimentModel).where(ExperimentModel.id == job_model.experiment_id))
        if exp is None:
            await self.jobs.transition(job_model.id, JobState.FAILED)
            await self.session.commit()
            return

        payload = CircuitPayload(qasm=exp.circuit_qasm, shots=exp.shots)
        adapter = get_provider(provider)
        try:
            result = await adapter.run(payload, job_model.timeout_seconds, str(job_model.id))
            if result.remote_run_id:
                await self.jobs.set_remote_run_id(job_model.id, result.remote_run_id)
            await self.results.save(result)
            await self.jobs.transition(job_model.id, JobState.SUCCEEDED)
            ...
        except TimeoutError:
            await self._handle_failure(job_model, correlation_id, provider, "timeout")
        except Exception as exc:
            await self._handle_failure(job_model, correlation_id, provider, str(exc))
```

---

## SECTION 4 — ARCHITECTURE EXPLANATION

### Overview

This is a **Quantum Control Plane** — a cloud-native job orchestration platform that accepts quantum circuits in OpenQASM 2.0 format, routes them to quantum backends (local simulator or IBM Quantum), and returns measurement results. It is **not** a quantum simulator itself; it is the **management layer** that drives quantum simulators.

```
Client (HTTP)
     │  POST /v1/jobs  {qasm, shots, provider, retry_policy}
     ▼
┌──────────────────┐
│  FastAPI API      │  ← services/api/app/main.py
│  (+ middlewares)  │    CorrelationId, Metrics, OTEL
└──────────┬───────┘
           │  persist Experiment + Job (SUBMITTED→QUEUED)
           ▼
┌──────────────────┐        ┌─────────────────┐
│  PostgreSQL DB    │        │  Redis Queue     │
│  (experiments,   │◄──────►│  (quantum.jobs)  │
│   jobs, results) │        └────────┬────────┘
└──────────────────┘                 │  BLPOP
                                     ▼
                             ┌───────────────────┐
                             │  Worker Process    │  ← workers/quantum-runner/runner/main.py
                             │  (WorkerService)   │
                             └────────┬──────────┘
                                      │
                         ┌────────────┴─────────────┐
                         ▼                           ▼
              ┌────────────────────┐    ┌───────────────────────┐
              │  LocalQiskitSim    │    │  IbmRuntimeAdapter    │
              │  (qiskit BasicSim) │    │  (qiskit-ibm-runtime) │
              └────────────────────┘    └───────────────────────┘
```

### How qubits are represented

The system **does not implement its own qubit representation**. Qubits are described abstractly as OpenQASM 2.0 source code strings:

```
qreg q[2];   # declare 2 qubits
creg c[2];   # declare 2 classical bits
```

The QASM string is stored in the `experiments` table (`circuit_qasm` column) and passed verbatim to Qiskit at execution time. Qiskit internally represents the n-qubit state as a complex statevector of dimension 2^n.

### How gates are applied

Gates are parsed from QASM by `qiskit.qasm2.loads()`, which constructs a `QuantumCircuit` object. Qiskit's `BasicSimulator` then:

1. Transpiles the circuit to its native gate set (`transpile(circuit, backend)`)
2. Applies gate matrices to the statevector using unitary matrix multiplication

The gate implementation is entirely delegated to Qiskit — no custom gate math exists in this codebase.

### How the quantum state evolves

Qiskit's `BasicSimulator` (the `basic_simulator` backend) is a **density-matrix / statevector simulator**:
- Initialises the state |0⟩^⊗n as a 2^n complex array
- Applies gate unitary U as: `|ψ'⟩ = U|ψ⟩`
- Multi-qubit gates use tensor products of gate matrices

This codebase defers entirely to Qiskit for the physics.

### How measurement is implemented

Measurement is defined in QASM as `measure q[i] -> c[i]`. Qiskit simulates it by:
1. Computing the Born-rule probability for each bitstring: `P(x) = |⟨x|ψ⟩|²`
2. Sampling that distribution `shots` times (the `shots` parameter, 1–10,000)
3. Returning a `counts` dictionary: `{"00": 512, "11": 512}` (example for Bell state)

The platform stores this histogram in `result_payload` (PostgreSQL JSON column) and returns it via the REST API.

### State Machine

```
SUBMITTED ──► QUEUED ──► RUNNING ──► SUCCEEDED
    │             │          │
    └─────────────┴──────► FAILED ──► QUEUED (retry)
```

The `ensure_transition()` function enforces valid transitions. Retries re-enqueue from `FAILED → QUEUED` up to `max_attempts` times.

---

## SECTION 5 — QUANTUM MODEL USED

### Classification: **Circuit Runner / Quantum Job Orchestration Platform**

This is **not a quantum simulator**. It is a **quantum job orchestration layer** that:

| Aspect | This codebase | True simulator |
|---|---|---|
| Statevector math | ❌ delegated to Qiskit | ✅ custom complex arrays |
| Gate matrix operations | ❌ delegated to Qiskit | ✅ custom matrix multiply |
| Measurement sampling | ❌ delegated to Qiskit | ✅ custom probabilistic sampling |
| Circuit scheduling | ✅ custom (Redis queue) | ❌ not applicable |
| Result persistence | ✅ PostgreSQL | ❌ not applicable |
| Multi-backend routing | ✅ local + IBM Runtime | ❌ not applicable |

### Quantum Frameworks Used

| Framework | Role |
|---|---|
| **Qiskit ≥ 1.2.0** | Circuit parsing (`qasm2.loads`), transpilation, local simulation via `BasicSimulator` |
| **qiskit-ibm-runtime ≥ 0.36.1** | IBM Quantum backend access via `SamplerV2`, `QiskitRuntimeService` |
| **NumPy** | Used internally by Qiskit for statevector arithmetic (not imported directly) |

### Input Format

OpenQASM 2.0 strings. Example:
```qasm
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
h q[0];
cx q[0], q[1];
measure q[0] -> c[0];
measure q[1] -> c[1];
```
This creates a 2-qubit Bell state. Expected counts with 1024 shots: `{"00": ~512, "11": ~512}`.

---

## SECTION 6 — PROBLEMS / BUGS

### 6.1 CI: Helm templates are not valid YAML (FIXED)

**Severity:** Critical (blocks CI)

**Root cause:** `instrumenta/conftest-action@master` attempts to parse raw Helm templates as YAML. Go template syntax (`{{ .Values.image.api }}`) is interpreted by the YAML parser as a flow mapping with a complex key, causing:
```
yaml: invalid map key: map[interface {}]interface {}{".Values.image.api":interface {}(nil)}
```

**Fix applied:** Updated the `policy-checks` CI job to:
1. Install Helm via `azure/setup-helm@v4`
2. Render templates with `helm template` to produce valid Kubernetes YAML
3. Run conftest on the rendered output (replacing the unmaintained `instrumenta/conftest-action@master`)

### 6.2 CI: Helm templates missing resource limits (FIXED)

**Severity:** High (violates OPA policy, would cause conftest to fail even after YAML fix)

**Root cause:** The OPA policy (`infra/policies/kubernetes/deployment.rego`) denies any Deployment whose containers lack `resources`:
```rego
deny[msg] {
  input.kind == "Deployment"
  container := input.spec.template.spec.containers[_]
  not container.resources
  msg := sprintf("deployment %s missing resource requests/limits", [input.metadata.name])
}
```
No container spec in any of the three Helm templates had a `resources` block.

**Fix applied:** Added `resources.requests` and `resources.limits` to all three container specs (`api`, `worker`, `web`) and added corresponding defaults to `values.yaml`.

### 6.3 CI: Outdated Trivy action (FIXED)

**Severity:** Medium (blocks security scanning)

**Root cause:** `aquasecurity/trivy-action@0.28.0` fails to install the Trivy binary in the GitHub Actions environment, exiting with code 1 before scanning begins.

**Fix applied:** Updated to `aquasecurity/trivy-action@0.30.0` and added `ignore-unfixed: true` to prevent false-positive failures on vulnerabilities that have no available fix.

### 6.4 Type annotation bugs in repositories (FIXED)

**Severity:** Low (mypy violation, potential runtime confusion)

**Root cause:**
- `ResultRepository.get_by_job_id(job_id: object)` — accepting `object` loses type safety
- `ExperimentRepository.get(experiment_id: object)` — same issue
- `JobService.submit()` called `experiments.get(str(existing_job.experiment_id))` — passing `str` instead of `UUID`

**Fix applied:** Changed signatures to accept `UUID`, added `from uuid import UUID` imports, fixed the call site in `job_service.py`.

### 6.5 IBM Runtime remote job ID was silently discarded (FIXED)

**Severity:** Medium (incomplete feature, data loss on process restart)

**Root cause:** `IbmRuntimeAdapter.run()` extracted the IBM remote job ID but assigned it to `_remote_id` (prefixed with `_`, intentionally ignored). This meant if the worker process crashed between job submission and result retrieval, the IBM job would be lost with no way to resume it.

**Fix applied:**
- Added `remote_run_id: str | None = None` field to `ExecutionResult` in the contracts package
- `IbmRuntimeAdapter.run()` now sets `remote_run_id=remote_id` on the returned `ExecutionResult`
- `WorkerService.process_job()` now calls `jobs.set_remote_run_id()` when a `remote_run_id` is present

### 6.6 `conftest-action@master` is an unmaintained pinned-to-master action

**Severity:** Medium (supply chain security risk)

Using `@master` pins to an uncontrolled, mutable ref. Any commit to the `instrumenta/conftest` repo would silently change CI behavior.

**Fix applied:** Replaced with direct conftest installation using a pinned version (`v0.56.0`) downloaded from the official GitHub release.

### 6.7 Worker process missing graceful shutdown

**Severity:** Low-Medium

The worker's infinite loop (`while True: ...`) has no signal handling. A SIGTERM from Kubernetes during a rolling deployment will kill the process mid-job, leaving a job in `RUNNING` state indefinitely with no path to recovery (it cannot transition back from `RUNNING` without a code path to do so).

**No fix applied (documented):** Requires adding `signal.signal(SIGTERM, ...)` with a shutdown flag.

### 6.8 `BasicProvider` deprecation

**Severity:** Low

`qiskit.providers.basic_provider.BasicProvider` is deprecated in Qiskit 1.x and will be removed in Qiskit 2.0. The replacement for local simulation is `qiskit_aer.AerSimulator` (for production workloads) or `qiskit.providers.basic_provider.BasicSimulator` (directly, without the factory).

**No fix applied (documented):** Requires updating the import and backend instantiation.

### 6.9 No authentication or authorization on any endpoint

**Severity:** High (security)

All REST endpoints (`POST /v1/jobs`, `GET /v1/jobs`, etc.) are unauthenticated. Any client with network access can submit circuits, list all jobs, and read all results.

**No fix applied (documented):** Requires adding JWT or API key authentication middleware.

### 6.10 `list_jobs` has no tenant or user scoping

**Severity:** Medium

`GET /v1/jobs` returns all jobs in the database up to a hard-coded limit of 100, with no filtering by user, tenant, or experiment. This leaks job metadata across users.

**No fix applied (documented):** Requires user/tenant model and query filtering.

---

## SECTION 7 — POSSIBLE IMPROVEMENTS

### 7.1 Replace `BasicProvider` with `AerSimulator`

```python
# Current (deprecated in Qiskit 1.x, removed in 2.0):
from qiskit.providers.basic_provider import BasicProvider
backend = BasicProvider().get_backend("basic_simulator")
compiled = transpile(circuit, backend)
result = backend.run(compiled, shots=payload.shots).result()

# Recommended (qiskit-aer, production-grade):
from qiskit_aer import AerSimulator
backend = AerSimulator()
compiled = transpile(circuit, backend)
result = backend.run(compiled, shots=payload.shots).result()
```

`AerSimulator` is faster (C++ implementation), supports noise models, density matrices, and stabilizer circuits — essential for realistic quantum simulation.

### 7.2 Add graceful shutdown to worker

```python
import asyncio
import signal

shutdown_event = asyncio.Event()

def _handle_sigterm(*_: object) -> None:
    shutdown_event.set()

async def run() -> None:
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGTERM, _handle_sigterm)
    loop.add_signal_handler(signal.SIGINT, _handle_sigterm)

    ...
    while not shutdown_event.is_set():
        item = await queue.dequeue(timeout=1)
        if not item:
            continue
        job_id, correlation_id = item
        async with session_factory() as session:
            worker = WorkerService(session, queue)
            await worker.process_job(job_id, correlation_id)
```

### 7.3 Add authentication middleware

```python
# services/api/app/core/auth.py
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

async def require_api_key(key: str = Security(api_key_header)) -> str:
    if key not in settings.allowed_api_keys:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return key
```

Add `dependencies=[Depends(require_api_key)]` to the router or individual protected routes.

### 7.4 Implement async IBM Runtime polling (non-blocking worker)

The current `IbmRuntimeAdapter.run()` blocks the worker thread for the full duration of the IBM job (minutes to hours). The `poll()` method exists on `ExecutionProviderAdapter` but is unimplemented. The proper design:

1. `run()` submits the circuit and returns immediately with the remote job ID (no result yet)
2. Store `remote_run_id` on the job
3. Worker periodically calls `adapter.poll(remote_run_id)` until done
4. This frees the worker to process other jobs while waiting for IBM

### 7.5 Add input validation for QASM

Currently any string passes the `min_length=1` validation. A malformed QASM string causes `loads()` to raise an exception in the worker, not at submission time, wasting a job slot and producing a confusing error. Add pre-validation at submit time:

```python
from qiskit.qasm2 import loads as qasm_loads, QASM2ParseError
from fastapi import HTTPException

def validate_qasm(qasm: str) -> None:
    try:
        qasm_loads(qasm)
    except QASM2ParseError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid QASM: {exc}") from exc
```

### 7.6 Add job TTL / stale-job recovery

Jobs stuck in `RUNNING` (e.g., after a worker crash) are never recovered. Add a background task or cron job to find jobs that have been in `RUNNING` for longer than `timeout_seconds + grace_period` and transition them to `FAILED`.

### 7.7 Paginate `list_jobs`

The current hard-coded limit of 100 is insufficient for production:

```python
# In JobRepository:
async def list(self, limit: int = 50, offset: int = 0) -> list[Job]:
    rows = await self.session.scalars(
        select(JobModel)
        .order_by(JobModel.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return [self._to_contract(m) for m in rows]
```

### 7.8 Structured QASM validation field on `CircuitPayload`

```python
from pydantic import field_validator

class CircuitPayload(BaseModel):
    qasm: str = Field(min_length=1)
    shots: int = Field(default=1024, ge=1, le=10000)

    @field_validator("qasm")
    @classmethod
    def validate_qasm_syntax(cls, v: str) -> str:
        from qiskit.qasm2 import loads, QASM2ParseError
        try:
            loads(v)
        except QASM2ParseError as exc:
            raise ValueError(f"Invalid QASM 2.0 syntax: {exc}") from exc
        return v
```

This catches syntax errors at the HTTP layer before the job is persisted or queued.

### 7.9 Use `conftest` with a pinned SHA for supply-chain security

The old workflow used `instrumenta/conftest-action@master` (mutable ref). The new workflow downloads a pinned conftest binary by version. For maximum supply-chain security, also pin the SHA-256 of the downloaded binary:

```yaml
- name: Install conftest
  run: |
    CONFTEST_VERSION=0.56.0
    EXPECTED_SHA256=<sha256-from-release-page>
    curl -sL ".../conftest_${CONFTEST_VERSION}_Linux_x86_64.tar.gz" -o /tmp/conftest.tar.gz
    echo "${EXPECTED_SHA256}  /tmp/conftest.tar.gz" | sha256sum -c
    tar -xz -C /tmp conftest < /tmp/conftest.tar.gz
    sudo mv /tmp/conftest /usr/local/bin/conftest
```

### 7.10 Add experiment-level filtering to job list endpoint

```python
@router.get("/v1/jobs", response_model=JobListResponse)
async def list_jobs(
    experiment_id: UUID | None = None,
    status: JobState | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
) -> JobListResponse:
    ...
```
