# API Service (FastAPI)

## Capabilities

- submit experiment/job with provider selection (`local_simulator`, `ibm_runtime`)
- async queue orchestration via Redis
- worker-driven execution lifecycle with retries/timeouts
- PostgreSQL persistence for experiments, jobs, results, audit events
- metrics endpoint (`/metrics`) and OpenTelemetry instrumentation support

## Endpoints

- `GET /healthz`
- `GET /readyz`
- `GET /metrics`
- `POST /v1/jobs`
- `GET /v1/jobs/{job_id}`
- `GET /v1/jobs`
- `GET /v1/jobs/{job_id}/result`

## IBM Runtime notes

IBM provider is implemented behind the provider abstraction with `qiskit-ibm-runtime`.
Current limitation: long-duration remote workflows are executed inline in worker run processing; future phase will add dedicated poller synchronization for multi-hour runs and advanced cancellation semantics.
