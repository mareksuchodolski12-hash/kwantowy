# Platform Architecture

## Planes

- **Control plane** (`services/api`): validation, persistence, orchestration, API contracts.
- **Execution plane** (`workers/quantum-runner`): provider-specific run execution and lifecycle transitions.

## Data path

1. UI submits experiment/job to API.
2. API writes experiment/job/audit records to Postgres and enqueues a queue message.
3. Worker dequeues and dispatches to provider adapter (`local_simulator` or `ibm_runtime`).
4. For IBM Runtime: worker submits provider job, persists remote id, polls status with backoff, ingests result idempotently.
5. Worker persists canonical result payload + status transitions.
6. UI fetches runs/results and provider comparison summary.

## Observability path

- API `/metrics` exposes counters, gauges, and histograms for orchestration and provider lifecycle.
- structured JSON logs from API/worker include correlation IDs.
- OpenTelemetry spans exported over OTLP when endpoint is configured.
