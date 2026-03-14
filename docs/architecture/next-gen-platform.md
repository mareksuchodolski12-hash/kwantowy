# Next-Generation Quantum Developer Platform

## 1. Product Vision

**Quantum Control Plane evolves from a job execution engine into the industry's
first open, multi-provider quantum developer platform that gives teams
reproducible, observable, and cost-optimised quantum experiments — across every
major hardware vendor — from a single API.**

The platform targets three personas:

| Persona | Need |
|---------|------|
| **Quantum researcher** | Run circuits on multiple backends, compare fidelity, reproduce experiments. |
| **ML / optimisation engineer** | Compose hybrid classical–quantum workflows without managing provider SDKs. |
| **Platform / DevOps engineer** | Observe, cost-control, and govern quantum workloads in a shared environment. |

### Why now?

Current cloud quantum platforms (IBM Quantum, Amazon Braket, Azure Quantum) are
vertically integrated — each locks the user into its own SDK, its own queue, and
its own result format.  Developers who need to compare hardware, optimise costs,
or chain classical and quantum steps must write substantial glue code themselves.

Quantum Control Plane already solves the execution and observability pieces.
Adding multi-provider routing, experiment versioning, workflow orchestration, and
result comparison creates a horizontal layer that **no single vendor offers**.

---

## 2. Technical Architecture

### 2.1 Current state

```
Client → FastAPI API → PostgreSQL → Redis Queue → Worker → Quantum Provider → Result
```

Core components:

- **Control plane** (`services/api`): FastAPI app with Pydantic contracts,
  SQLAlchemy + Alembic persistence, Redis-based job queue with visibility
  timeout and DLQ.
- **Execution plane** (`workers/quantum-runner`): Async worker with provider
  adapter pattern, job-state machine, retry with exponential back-off.
- **Provider adapters** (`app/simulation/`): `LocalQiskitSimulator` and
  `IbmRuntimeAdapter` behind an abstract `ExecutionProviderAdapter` interface.
- **Observability**: Prometheus counters/histograms, OpenTelemetry traces,
  structured JSON logs.

### 2.2 Target state

```
                        ┌───────────────────────────┐
                        │  Next.js Console / CLI     │
                        └────────────┬──────────────┘
                                     │
                        ┌────────────▼──────────────┐
                        │   FastAPI Control Plane    │
                        │  ┌──────────────────────┐  │
                        │  │  Provider Registry    │  │  ← GET /v1/providers
                        │  │  Route Selection      │  │  ← POST /v1/providers/select
                        │  │  Experiment Versioning│  │
                        │  │  Workflow Engine       │  │
                        │  │  Circuit Optimiser     │  │
                        │  └──────────────────────┘  │
                        └──┬────────┬────────┬──────┘
                           │        │        │
               ┌───────────▼──┐ ┌───▼───┐ ┌──▼──────────┐
               │  PostgreSQL  │ │ Redis │ │ Object Store │
               │  (metadata,  │ │ Queue │ │ (circuits,   │
               │   versions)  │ │       │ │  datasets)   │
               └──────────────┘ └───┬───┘ └─────────────┘
                                    │
                        ┌───────────▼──────────────┐
                        │   Worker Pool             │
                        │  ┌──────────────────────┐ │
                        │  │  Provider Adapters    │ │
                        │  │  ┌────┬────┬────┬──┐ │ │
                        │  │  │Loc │IBM │IonQ│Rig│ │ │
                        │  │  └────┴────┴────┴──┘ │ │
                        │  │  Circuit Transpiler   │ │
                        │  └──────────────────────┘ │
                        └──────────────────────────┘
                                    │
               ┌────────────────────┼────────────────────┐
               │                    │                    │
        ┌──────▼──────┐    ┌───────▼───────┐    ┌──────▼──────┐
        │  Qiskit     │    │  IBM Runtime  │    │  IonQ /     │
        │  Simulator  │    │  (hardware)   │    │  Rigetti    │
        └─────────────┘    └───────────────┘    └─────────────┘
```

### 2.3 New components

| Component | Purpose | Implementation |
|-----------|---------|----------------|
| **Provider Registry** | Capability catalogue + weighted route selection | `app/services/provider_registry.py` (implemented) |
| **Stub Adapters** | IonQ and Rigetti interface contracts | `app/simulation/{ionq,rigetti}_adapter.py` (implemented) |
| **Selection API** | `GET /v1/providers`, `POST /v1/providers/select` | `app/api/routes.py` (implemented) |
| **Workflow Engine** | DAG-based step orchestration for multi-step experiments | Future — Temporal or lightweight in-process DAG |
| **Experiment Versioning** | Immutable snapshots of circuit + parameters + results | Future — content-addressed hashing in PostgreSQL |
| **Circuit Optimiser** | Pre-execution transpile / gate reduction pipeline | Future — Qiskit PassManager integration |
| **Result Comparator** | Cross-provider fidelity and statistical comparison | Contract defined (`ResultComparison` model) |

---

## 3. Differentiating Features

### 3.1 Multi-provider routing (implemented)

The `ProviderRegistry` maintains per-provider capability metadata (max qubits,
shot limits, cost, queue latency, feature flags) and exposes a scoring-based
`select()` method.  The API endpoint `POST /v1/providers/select` lets clients
or the platform itself choose the best backend for a given circuit.

```python
from quantum_contracts import ProviderRouteRequest

req = ProviderRouteRequest(qubit_count=5, shots=1024, prefer_hardware=True)
resp = registry.select(req)
# resp.recommended == ExecutionProvider.IBM_RUNTIME
# resp.alternatives == [ExecutionProvider.RIGETTI, ...]
```

### 3.2 Provider benchmarking & automatic backend selection

The registry scoring function considers:

- **Qubit capacity** — filter providers that cannot handle the circuit.
- **Cost** — estimated per-shot cost multiplied by shot count.
- **Queue latency** — average wait time from historical data.
- **Hardware preference** — bias toward real QPUs when requested.
- **Exclusion list** — skip specific providers per-request.

Future: feed live telemetry (Prometheus metrics) back into the registry so
scoring adapts to real-time queue depths and error rates.

### 3.3 Reproducible experiment pipelines

Every experiment is stored as an immutable `(circuit_qasm, shots, provider,
retry_policy)` tuple.  Adding content-addressed versioning (SHA-256 of the
canonical circuit) enables:

- **Exact replay**: re-run the same circuit on the same or different provider.
- **Diffing**: compare two experiment versions side-by-side.
- **Lineage**: trace which optimisation pass transformed a circuit.

### 3.4 Result comparison across providers

The `ResultComparison` contract model captures side-by-side execution results
with per-provider fidelity scores:

```json
{
  "experiment_name": "bell-state",
  "results": [
    {"provider": "local_simulator", "counts": {"00": 510, "11": 514}, ...},
    {"provider": "ibm_runtime",     "counts": {"00": 498, "11": 526}, ...}
  ],
  "fidelity_scores": {"local_simulator": 0.998, "ibm_runtime": 0.972}
}
```

### 3.5 Cost optimisation and scheduling

The selection API already factors cost.  Future enhancements:

- **Budget caps** per team / API key.
- **Spot scheduling** — queue jobs for off-peak windows on hardware providers.
- **Cost dashboards** — Grafana panels sourced from audit events.

### 3.6 Hybrid classical–quantum workflows

A lightweight workflow engine (initially an in-process DAG runner, later backed
by Temporal) would allow users to define multi-step pipelines:

```yaml
steps:
  - name: optimise
    type: classical
    image: qiskit-optimizer:latest
    inputs: {circuit: "$circuit"}
  - name: execute
    type: quantum
    provider: auto
    inputs: {circuit: "$optimise.output"}
  - name: analyse
    type: classical
    image: result-analyser:latest
    inputs: {result: "$execute.result"}
```

### 3.7 Circuit optimisation pipelines

A pre-execution hook in the worker can apply Qiskit `PassManager` transpilation
to reduce gate count and depth before dispatching to a provider.  This is
transparent to the user and logged in the audit trail.

### 3.8 Advanced observability for quantum jobs

Already present:

- `qcp_jobs_submitted_total`, `qcp_jobs_succeeded_total`, `qcp_jobs_failed_total`
- `qcp_execution_duration_seconds`, `qcp_queue_latency_seconds`
- Per-provider label cardinality

Planned additions:

- **Circuit complexity metrics** — gate count, depth, qubit utilisation.
- **Fidelity tracking** — statistical divergence from ideal simulation.
- **Provider health** — error rate, timeout rate, calibration freshness.
- **Cost accounting** — cumulative spend per provider / API key.

---

## 4. Roadmap

### Phase 1 — Multi-provider foundation ✅ (this PR)

- [x] Extend `ExecutionProvider` enum (`IONQ`, `RIGETTI`, `SIMULATOR_AER`).
- [x] Add `ProviderCapabilities`, `ProviderRouteRequest/Response`, `ResultComparison` contracts.
- [x] Implement `ProviderRegistry` with capability catalogue and scoring.
- [x] Create stub adapters for IonQ and Rigetti.
- [x] Expose `GET /v1/providers` and `POST /v1/providers/select` endpoints.
- [x] Add 10 tests covering registry logic and API integration.

### Phase 2 — Provider integration & result comparison (4–6 weeks)

- [ ] Integrate IonQ REST API via `cirq-ionq` / direct HTTP.
- [ ] Integrate Rigetti via `pyQuil` / QCS.
- [ ] Implement `GET /v1/experiments/{id}/compare` result comparison endpoint.
- [ ] Add fidelity scoring (Hellinger distance from ideal simulation).
- [ ] Feed live Prometheus metrics into registry scoring.

### Phase 3 — Experiment versioning & reproducibility (4–6 weeks)

- [ ] Content-addressed experiment versioning (circuit SHA-256).
- [ ] `GET /v1/experiments/{id}/versions` history endpoint.
- [ ] Experiment replay — re-submit a previous version on a new provider.
- [ ] Object store integration for large circuit / dataset artefacts.

### Phase 4 — Workflow orchestration (6–8 weeks)

- [ ] In-process DAG runner for multi-step experiments.
- [ ] `POST /v1/workflows` submission endpoint.
- [ ] Classical step execution (container-based or function-based).
- [ ] Hybrid classical–quantum pipeline support.
- [ ] Migration path to Temporal for production workloads.

### Phase 5 — Cost governance & multi-tenancy (4–6 weeks)

- [ ] Per-API-key cost budgets and rate limits.
- [ ] Team / organisation hierarchy with RBAC.
- [ ] Cost dashboards in Grafana.
- [ ] Spot scheduling for off-peak hardware access.

### Phase 6 — Circuit optimisation & advanced observability (4–6 weeks)

- [ ] Pre-execution Qiskit PassManager transpilation hook.
- [ ] Circuit complexity metrics (gate count, depth, qubit utilisation).
- [ ] Provider health tracking (error rate, calibration age).
- [ ] Fidelity drift alerting.

---

## 5. Core Technical Challenges

### 5.1 Provider API heterogeneity

Each quantum cloud provider uses a different SDK, authentication model, circuit
format, and result schema.  The `ExecutionProviderAdapter` abstraction must
normalise these differences while preserving provider-specific metadata.

**Mitigation:** Keep the adapter interface minimal (`run`, `poll`) and push
format translation into adapter internals.  The `ProviderCapabilities` model
captures what each provider can and cannot do.

### 5.2 Asynchronous long-running jobs

Hardware providers can take minutes to hours.  The current synchronous
`adapter.run()` blocks a worker thread.  For long-running jobs the system needs
an async submit → poll → complete lifecycle.

**Mitigation:** The existing `poll()` method on the adapter interface is the
hook for this.  Implement a separate poll loop in the worker that checks
in-flight jobs on a timer, distinct from the dequeue loop.

### 5.3 Result normalisation and fidelity

Providers return results in different formats (bit-string ordering, qubit
labelling, metadata fields).  Comparing results requires canonical normalisation.

**Mitigation:** Define a strict `ExecutionResult` canonical schema in the
contracts package.  Each adapter is responsible for mapping native results into
this schema.  Fidelity scoring uses Hellinger distance against an ideal
simulation baseline.

### 5.4 Cost tracking without provider billing APIs

Not all providers expose programmatic billing data.  Estimated costs must be
maintained in the registry and reconciled against provider invoices.

**Mitigation:** Use per-shot cost estimates in `ProviderCapabilities` and log
every execution in the audit trail.  Periodically reconcile against provider
dashboards.  Surface cost data in Grafana via Prometheus metrics.

### 5.5 Workflow orchestration complexity

Multi-step hybrid workflows introduce DAG scheduling, data dependencies between
steps, partial failure handling, and long-running state management.

**Mitigation:** Start with a minimal in-process DAG runner for simple linear
pipelines.  Gate complex workflows behind a feature flag.  Plan migration to
Temporal when workflow complexity justifies the operational overhead.

### 5.6 State machine evolution

Adding new job states (e.g. `OPTIMISING`, `POLLING`, `COMPARING`) requires
careful extension of the state machine without breaking existing transitions.

**Mitigation:** The existing `ALLOWED_TRANSITIONS` dictionary in
`state_machine.py` makes transitions explicit and testable.  New states are
added incrementally with tests covering every new edge.

### 5.7 Multi-tenancy and isolation

Supporting multiple teams with cost budgets, RBAC, and data isolation adds
significant complexity to the API key and database model.

**Mitigation:** Phase this in gradually — start with per-key budgets (soft
limits), then add organisation hierarchy.  Use PostgreSQL row-level security
for data isolation.
