# Demo Walkthrough (Deterministic)

Use shell scripts for deterministic demo output instead of browser automation.

## Prerequisites

```bash
make bootstrap
make up
make migrate
```

Start API + worker in separate terminals:

```bash
make api
make worker
```

## Local execution flow (curl-based)

```bash
./scripts/demo_local.sh
```

This script performs:
1. `POST /v1/jobs` with `provider=local_simulator`
2. Poll `GET /v1/jobs/{id}` until terminal state
3. Fetch `GET /v1/jobs/{id}/result`
4. Fetch `GET /v1/comparison`

## Remote execution flow (IBM Runtime, optional)

Set env vars first:
- `QCP_IBM_RUNTIME_ENABLED=true`
- `QCP_IBM_RUNTIME_TOKEN=...`
- `QCP_IBM_RUNTIME_CHANNEL=ibm_quantum`
- `QCP_IBM_RUNTIME_INSTANCE=...`

Then run:

```bash
./scripts/demo_remote.sh
```

If credentials are not present, script exits cleanly with a skip message.

## Expected output sample

See `docs/assets/sample-run-export.json` for a representative output artifact.
