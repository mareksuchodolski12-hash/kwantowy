# Architecture

## Quantum Control Plane — System Architecture

### Overview

The Quantum Control Plane (QCP) is a distributed platform for running quantum
circuits across multiple providers.  It follows a layered architecture with
clear separation between the control plane, execution plane, and developer
interfaces.

```
┌─────────────────────────────────────────────────────────┐
│                    Developer Platform                     │
│  ┌─────────┐  ┌─────────┐  ┌──────────────────────────┐ │
│  │   CLI   │  │   SDK   │  │       REST API (/v1/)    │ │
│  │  (qcp)  │  │ (Python)│  │      FastAPI + OpenAPI   │ │
│  └────┬────┘  └────┬────┘  └────────────┬─────────────┘ │
│       │            │                     │               │
├───────┴────────────┴─────────────────────┴───────────────┤
│                     Control Plane                         │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  Experiments  │  │  Workflows   │  │     Cost      │  │
│  │  & Versioning │  │  Engine      │  │  Governance   │  │
│  └──────┬───────┘  └──────┬───────┘  └───────┬───────┘  │
│         │                 │                   │          │
│  ┌──────┴─────────────────┴───────────────────┴───────┐  │
│  │                  Job Queue (Redis)                  │  │
│  │           FIFO + Visibility Timeout + DLQ           │  │
│  └─────────────────────┬──────────────────────────────┘  │
│                        │                                 │
├────────────────────────┼─────────────────────────────────┤
│                  Execution Plane                         │
│  ┌─────────────────────┴──────────────────────────────┐  │
│  │               Worker (quantum-runner)               │  │
│  └──┬──────┬───────┬──────────┬───────────┬───────────┘  │
│     │      │       │          │           │              │
│  ┌──┴──┐┌──┴──┐┌───┴───┐┌────┴────┐┌─────┴──────┐      │
│  │Local││ Aer ││  IBM  ││  IonQ   ││  Rigetti   │      │
│  │ Sim ││ Sim ││Runtime││(plugin) ││  (plugin)  │      │
│  └─────┘└─────┘└───────┘└─────────┘└────────────┘      │
│                                                          │
├──────────────────────────────────────────────────────────┤
│                      Dashboard                           │
│  ┌──────────────┐  ┌─────────────┐  ┌────────────────┐  │
│  │  Experiment   │  │  Provider   │  │     Run        │  │
│  │     UI        │  │ Leaderboard │  │  Comparison    │  │
│  └──────────────┘  └─────────────┘  └────────────────┘  │
│                                                          │
├──────────────────────────────────────────────────────────┤
│                    Infrastructure                        │
│  PostgreSQL │ Redis │ Prometheus │ Grafana │ OpenTelemetry│
└──────────────────────────────────────────────────────────┘
```

### Control Plane

The API server (`services/api/`) is a FastAPI application that handles:

- **Experiment Management**: Create, list, and version experiments with QASM circuits.
- **Job Scheduling**: Submit jobs to the Redis queue with idempotency and retry policies.
- **Workflow Orchestration**: Declarative multi-step pipelines with dependency tracking.
- **Cost Governance**: Budget enforcement, per-job cost tracking, and spend alerts.
- **Provider Registry**: Capability-based provider selection and smart routing.
- **Circuit Optimisation**: Transpilation pipeline with noise-aware qubit mapping.

### Execution Plane

Workers poll the Redis queue and execute circuits on provider backends:

- **quantum-runner** (`workers/quantum-runner/`): The main execution worker. Dequeues
  jobs, runs circuits via provider adapters, stores results, and handles retries.
- **benchmark-runner** (`workers/benchmark-runner/`): Periodically executes
  calibration circuits and updates provider fidelity metrics.

### Worker Architecture

```
Worker Loop
  │
  ├─ dequeue(timeout=5s)
  │    └─ Redis BLPOP on "quantum:jobs"
  │
  ├─ process_job(job_id, correlation_id)
  │    ├─ transition → RUNNING
  │    ├─ execute circuit via provider adapter
  │    ├─ store result
  │    ├─ transition → SUCCEEDED
  │    └─ ack message
  │
  ├─ on failure:
  │    ├─ retry if attempts < max_attempts
  │    └─ move to DLQ on permanent failure
  │
  └─ periodic: requeue_timed_out() every 60s
```

### Provider Adapters

Each provider has an adapter that translates QASM circuits into provider-specific
API calls.  The adapter interface:

1. **Built-in adapters** live in `services/api/app/simulation/` and service modules.
2. **External plugins** implement `plugins/providers/base.py:BaseProvider` and are
   registered via `plugin.yaml` descriptors.

### Database Schema

The PostgreSQL database has 14 tables managed by SQLAlchemy + Alembic:

| Table | Purpose |
|-------|---------|
| `experiments` | Circuit definitions and metadata |
| `jobs` | Execution jobs with state machine |
| `results` | Measurement counts and timing data |
| `benchmarks` | Provider calibration results |
| `workflows` | Workflow definitions |
| `workflow_runs` | Workflow execution instances |
| `budgets` | Cost governance budgets |
| `cost_records` | Per-job cost entries |
| `organisations` | Top-level tenant entities |
| `teams` | Teams within organisations |
| `projects` | Projects within teams |
| `api_keys` | API key hashes and metadata |
| `audit_events` | Event sourcing log |
| `experiment_versions` | Circuit version history |

### Queue Architecture

Redis is used as a reliable job queue with:

- **FIFO delivery**: `RPUSH` / `BLPOP` on the `quantum:jobs` list.
- **Visibility timeout**: A sorted set tracks in-flight messages. If a worker
  crashes, messages are re-enqueued after the timeout expires.
- **Dead Letter Queue**: Jobs that exceed `max_attempts` are moved to a DLQ list.
- **Invariant**: The DB transaction is always committed *before* the message is
  enqueued, ensuring workers always find the job row.

### Observability

- **Prometheus**: Custom gauges and counters for queue depth, job latency,
  provider fidelity, and cost metrics.
- **OpenTelemetry**: Distributed tracing across API → Queue → Worker.
- **Structured Logging**: JSON logs with correlation IDs for request tracing.
- **Grafana**: Pre-configured dashboards for platform health.
