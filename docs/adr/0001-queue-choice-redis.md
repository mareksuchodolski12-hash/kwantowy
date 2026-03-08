# ADR 0001: Queue choice for phase 2

- **Status**: Accepted
- **Date**: 2026-03-08

## Context

Phase 2 requires local-first async job orchestration with minimal operational overhead.

## Decision

Use Redis lists (`RPUSH`/`BLPOP`) as the queue primitive for API-to-worker handoff.

## Consequences

- Simple local development and CI setup.
- Clear migration path to a managed broker in later phases.
- At-least-once delivery semantics require idempotent workers.
