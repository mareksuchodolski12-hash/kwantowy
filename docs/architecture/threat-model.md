# Threat Model (Initial)

## Assets

- IBM Runtime credentials
- experiment/circuit payloads
- execution results and audit trail

## Primary threats

1. **Credential leakage**: IBM token exposed in logs or source.
2. **Unauthorized run submission**: unauthenticated API usage.
3. **Queue poisoning**: forged messages in Redis.
4. **Data tampering**: mutable job/result records without auditability.
5. **Supply-chain risk**: vulnerable images/dependencies.

## Mitigations in this phase

- secret-driven config for IBM credentials (env vars; no hard-coded secrets)
- audit event persistence for lifecycle changes
- CI security scan + SBOM generation
- policy checks for deployment manifest quality
- provider abstraction boundary to isolate external runtime integration

## Follow-ups

- introduce authn/authz and signed service-to-service identity
- enforce Redis ACL/TLS in non-local environments
- add database encryption-at-rest policy enforcement
