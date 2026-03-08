# ADR 0004: Deterministic conftest bootstrap

- **Status**: Accepted
- **Date**: 2026-03-08

## Context

Policy checks were non-deterministic because `conftest` had to be installed manually.

## Decision

Manage `conftest` via repository-owned bootstrap script (`scripts/install_conftest.sh`) that:
- downloads a pinned version
- verifies checksum against release checksums
- verifies installed version
- places binary in `.bin/`

`make policy` always uses `.bin/conftest`.

## Consequences

- local and CI policy checks behave identically
- no hidden machine prerequisites for policy gate
