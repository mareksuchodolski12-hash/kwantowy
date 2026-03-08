# Quantum Control Plane

Quantum Control Plane is a platform for defining and executing specialized quantum workloads with clear control-plane and execution-plane boundaries.

## Phase 3+ hardening highlights

- FastAPI control plane + async worker with provider abstraction
- Local simulator + IBM Runtime provider adapters
- Deterministic policy checks (`make policy`) via managed local conftest toolchain
- Prometheus metrics, OTEL tracing hooks, Grafana dashboard, Loki pipeline config
- Docker/Compose/Helm/Terraform delivery path
- CI: lint, typecheck, tests, image builds, Trivy, SBOM, policy checks

## Local quickstart

```bash
make bootstrap
make up
make migrate
make api
make worker
```

## Deterministic gates

```bash
make lint
make typecheck
make test
make policy
```

## Demo

- Local deterministic demo: `./scripts/demo_local.sh`
- IBM Runtime demo (optional credentials): `./scripts/demo_remote.sh`

## Image tagging strategy

- CI build tags should include immutable git SHA (`<repo>:sha-<shortsha>`)
- Optional release tags can map to semver (`vX.Y.Z`) after validation
- Helm values support repository+tag driven deployments

## Operational Guarantees

### SLIs to track
- Job success rate by provider
- p95 queue latency
- p95 execution duration
- provider error rate (transient/permanent)
- retry volume and exhausted retry budget counts

### Suggested SLOs (initial)
- Local simulator success rate: >= 99%
- Control plane p95 queue latency: < 5s
- Worker p95 execution duration (local): < 30s for reference circuits

### Runbook mapping
- Local setup and boot: `docs/runbooks/local-development.md`
- Job failure triage: `docs/runbooks/incident-job-failures.md`

## Documentation map

- `docs/architecture/implementation-plan.md`
- `docs/architecture/platform-architecture.md`
- `docs/architecture/threat-model.md`
- `docs/demo-walkthrough.md`
- `CHANGELOG.md`
