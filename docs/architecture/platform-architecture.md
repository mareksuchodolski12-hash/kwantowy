# Platform Architecture

## Planes

- **Control plane** (`services/api`): validation, persistence, orchestration, API contracts.
- **Execution plane** (`workers/quantum-runner`): provider-specific run execution and lifecycle transitions.

## Data path

1. UI submits experiment/job to API.
2. API writes experiment/job/audit records to Postgres and enqueues a queue message.
3. Worker dequeues and dispatches to provider adapter (`local_simulator` or `ibm_runtime`).
4. Worker persists canonical result payload + status transitions.
5. UI fetches runs/results and comparison view.

## Observability path

- API `/metrics` exposes Prometheus counters/histograms.
- structured JSON logs from API/worker can be scraped by Loki agents.
- OpenTelemetry spans exported over OTLP when endpoint is configured.
