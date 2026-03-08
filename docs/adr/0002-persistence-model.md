# ADR 0002: Persistence model for experiments/jobs/results/audit

- **Status**: Accepted
- **Date**: 2026-03-08

## Context

We need durable state for orchestration and query APIs.

## Decision

Use PostgreSQL with relational tables:
- `experiments`
- `jobs`
- `results`
- `audit_events`

Manage schema with Alembic migrations.

## Consequences

- Strong consistency for state transitions and result lookup.
- SQL-friendly auditability and operations.
- Requires migration discipline from first release.
