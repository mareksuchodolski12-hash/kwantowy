# Changelog

## Unreleased

### Added
- deterministic conftest bootstrap and policy gate (`make tools`, `make policy`)
- IBM Runtime lifecycle polling with timeout/retry budgets and error classification
- extended operational metrics and Grafana dashboard panels
- deterministic curl-based demo scripts for local and remote execution
- release-readiness docs (operational guarantees, runbooks, ADRs)

### Changed
- worker execution flow now persists remote run IDs and ingests results idempotently
- CI policy job now relies on Makefile-managed tooling path
