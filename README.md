# Quantum Control Plane

Quantum Control Plane is a platform for defining and executing specialized quantum workloads with a clean control-plane/worker architecture.

## Phase 3 Highlights

- **Backend control plane**: FastAPI API, async queue orchestration, provider abstraction, local + IBM Runtime support.
- **Execution plane**: independent worker consuming queued jobs and persisting canonical results.
- **Frontend**: Next.js operational console for submission, run history, run details, and provider comparison.
- **Observability**: Prometheus metrics, Grafana dashboards, OpenTelemetry traces, Loki-ready log pipeline.
- **Platform hardening**: Dockerfiles, Helm chart, Terraform baseline, CI build/security/SBOM/policy checks.

## Local quickstart

```bash
make bootstrap
make up
make migrate
make api
make worker
make web
```

Open:
- Web: http://localhost:3000
- API docs: http://localhost:8000/docs
- Metrics: http://localhost:8000/metrics
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001

## IBM Runtime configuration

Set environment variables for remote provider runs:

- `QCP_IBM_RUNTIME_ENABLED=true`
- `QCP_IBM_RUNTIME_TOKEN=...`
- `QCP_IBM_RUNTIME_CHANNEL=ibm_quantum`
- `QCP_IBM_RUNTIME_INSTANCE=...`
- `QCP_IBM_RUNTIME_BACKEND=ibm_brisbane` (or desired backend)

If IBM credentials are absent, local simulation remains fully supported.

## Documentation

- `docs/architecture/implementation-plan.md`
- `docs/architecture/platform-architecture.md`
- `docs/architecture/threat-model.md`
- `docs/runbooks/*.md`
- `docs/demo-walkthrough.md`
