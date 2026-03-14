# Runbook: Local Development

## With Docker (Recommended)

1. `make bootstrap`
2. `make up` — starts Postgres + Redis only
3. `make migrate`
4. Start API/worker/web in separate shells (`make api`, `make worker`, `make web`)
5. Submit run from UI and verify status progression in Run History.

## Full Docker Stack

1. `make bootstrap`
2. `make up-all` — starts all services including observability
3. Visit http://localhost:3000 (web), http://localhost:8000/docs (API),
   http://localhost:9090 (Prometheus), http://localhost:3001 (Grafana).

## Without Docker (SQLite + fakeredis)

1. `make bootstrap`
2. `python start_local.py` — starts API + background worker on port 8000
3. `make web` — starts web console on port 3000 (separate terminal)
4. No migrations needed — tables are auto-created in SQLite.
