# ADR 0005: IBM Runtime polling and retry budget strategy

- **Status**: Accepted
- **Date**: 2026-03-08

## Context

IBM Runtime jobs can be long-running and may fail transiently.

## Decision

Use explicit lifecycle control in worker:
1. submit and persist remote provider run id
2. poll provider status with exponential backoff and total timeout budget
3. fetch and persist result idempotently after success
4. classify errors as transient/permanent
5. retry only transient failures within per-job retry budget

## Consequences

- deterministic remote lifecycle behavior
- clear operational metrics for polling and failures
- robust idempotency for repeated poll/ingest cycles
