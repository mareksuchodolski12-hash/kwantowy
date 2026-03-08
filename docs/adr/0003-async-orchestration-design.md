# ADR 0003: Async orchestration design

- **Status**: Accepted
- **Date**: 2026-03-08

## Context

Phase 2 requires submit -> queue -> execute -> persist end-to-end flow with retries and timeout.

## Decision

Adopt a control-plane + worker split:
- API persists experiment/job, transitions to `queued`, and enqueues a message.
- Worker dequeues, transitions state (`running` -> terminal), executes local simulation adapter, and persists results.
- Retry policy and timeout are per-job fields.

## Consequences

- Clear provider abstraction boundary.
- Deterministic state machine and audit trail.
- Requires correlation-id propagation and robust transition checks.
