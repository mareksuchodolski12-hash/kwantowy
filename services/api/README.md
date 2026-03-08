# API Service (FastAPI)

## Capabilities

- submit experiment/job with provider selection (`local_simulator`, `ibm_runtime`)
- async queue orchestration via Redis
- worker-driven execution lifecycle with retries/timeouts
- IBM Runtime remote lifecycle: submit -> persist remote id -> poll with backoff -> ingest result
- PostgreSQL persistence for experiments, jobs, results, audit events
- metrics endpoint (`/metrics`) and OpenTelemetry instrumentation hooks

## Endpoints

- `GET /healthz`
- `GET /readyz`
- `GET /metrics`
- `POST /v1/jobs`
- `GET /v1/jobs/{job_id}`
- `GET /v1/jobs`
- `GET /v1/jobs/{job_id}/result`
- `GET /v1/comparison`

## Metrics notes

`/metrics` is a stable Prometheus text endpoint that includes:
- job submissions/success/failure counters
- state transition counters
- retry and provider error counters
- queue depth/latency, poll latency/backoff, execution duration histograms
