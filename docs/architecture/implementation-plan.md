# Implementation Plan

## Phase 3 scope delivered

- operational frontend and API integration
- provider abstraction expanded to include IBM Runtime
- observability (metrics + traces + dashboards + logging pipeline path)
- deployment story (Docker, Helm, Terraform)
- security and governance (policy checks, threat model, CI security/SBOM)

## Phase 4 – Multi-provider foundation (delivered)

- multi-provider enum (IonQ, Rigetti, simulator_aer) in contracts
- provider registry with capabilities metadata and weighted scoring
- stub adapters for IonQ and Rigetti
- provider listing and selection API (`GET /v1/providers`, `POST /v1/providers/select`)

## Remaining roadmap

- robust IBM async status synchronization loop for long-running runtime jobs
- multi-tenant RBAC model and authn/authz layer
- production-grade secret rotation and key management integration
- IonQ and Rigetti SDK integration
- result comparison and fidelity scoring
- experiment versioning with content-addressed circuits
- workflow orchestration for hybrid classical–quantum pipelines
- circuit optimisation pre-execution hooks
- cost governance and per-key budgets

See [next-gen-platform.md](next-gen-platform.md) for the full architecture vision and roadmap.
