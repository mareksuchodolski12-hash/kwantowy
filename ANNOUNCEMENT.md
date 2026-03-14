# Quantum Control Plane — Public Announcement

---

## 1. Hacker News Post

**Title:**
Show HN: Quantum Control Plane – an open platform for orchestrating quantum experiments

**Body:**

Hi HN,

I'm sharing Quantum Control Plane (QCP), an open developer platform I built for running and orchestrating quantum computing experiments. Think MLflow or Airflow, but for quantum circuits.

**What it does:**

- Submit OpenQASM 3 circuits via REST API, Python SDK, or CLI
- Execute experiments across multiple quantum providers (IBM Runtime, IonQ, Rigetti, local simulators)
- Orchestrate multi-step workflows with a DAG-based engine
- Benchmark quantum backends on fidelity, latency, and cost
- Compare results with statistical analysis
- Visualise everything in a Next.js dashboard

**Architecture overview:**

The platform has four layers:

1. **Developer tools** — Python SDK (`qcp-sdk`), CLI (`qcp`), REST API
2. **Control plane** — FastAPI service handling experiments, versioning, circuit optimisation, cost governance, and multi-tenant hierarchy (Org → Team → Project)
3. **Execution plane** — async job runners and benchmark workers backed by Redis queues with visibility timeout and dead-letter support
4. **Dashboard** — Next.js / React / TypeScript web console with provider leaderboard and interactive demo

Data layer: PostgreSQL (12 tables, Alembic migrations), Redis (queue + cache).

Observability: Prometheus, Grafana, Loki, OpenTelemetry.

Infrastructure: Docker Compose for local dev, Helm charts and Terraform modules for production.

**What problem it solves:**

Right now, running quantum experiments usually means writing one-off scripts, manually tracking results, and dealing with provider-specific APIs. QCP gives you a single interface to submit circuits, track experiment versions, compare runs across providers, and enforce cost budgets — all through a consistent API.

**Tech stack:**

- Backend: FastAPI, PostgreSQL, Redis, Qiskit
- Workers: async job runners, benchmark workers
- Frontend: Next.js 14, React, TypeScript, Tailwind CSS, Recharts
- Developer tools: Python SDK, CLI (Click + Rich)
- Infra: Docker, Terraform, Helm, Prometheus, Grafana, OpenTelemetry

**Background:**

I built this as a self-taught developer to push my engineering skills in distributed systems, backend architecture, and developer platforms. The codebase includes things like DAG-based orchestration, visibility-timeout queues, circuit optimisation passes, provider-capability routing, and cost governance — areas I wanted to learn by building, not just reading about.

I'm sharing it now because I'd really appreciate feedback from more experienced engineers. If you see architectural mistakes, questionable patterns, or things I could do better — please tell me. That's exactly why I'm posting.

Repo: https://github.com/mareksuchodolski12-hash/kwantowy

Docs, architecture guide, ADRs, and runbooks are all in the repo.

I'm also open to job opportunities in backend/platform/infrastructure engineering — feel free to reach out if you think my work shows potential.

Thanks for reading.

---

## 2. Reddit Post

**Title:**
Quantum Control Plane — an open platform for orchestrating quantum computing experiments (feedback welcome)

**Body:**

I've been working on an open developer platform called **Quantum Control Plane (QCP)** and I'm releasing it publicly to get feedback.

**What it is:**

An orchestration layer for quantum computing experiments. You submit QASM circuits, run them across different quantum providers, track versions, compare results, and manage costs — all through a unified API, SDK, CLI, or web dashboard.

Think MLflow or Airflow, but purpose-built for quantum workflows.

**Key features:**

- Circuit submission and execution (OpenQASM 3)
- Circuit optimisation (gate-count reduction, depth minimisation)
- Experiment versioning with audit history
- DAG-based workflow orchestration
- Provider benchmarking (fidelity, latency, cost)
- Smart provider routing based on capabilities
- Cost governance with org-level budgets
- Multi-tenant hierarchy (Org → Team → Project)
- Result comparison with statistical analysis
- Interactive Next.js dashboard with provider leaderboard

**Tech stack:**

| Layer | Stack |
|-------|-------|
| Backend | FastAPI, PostgreSQL, Redis, Qiskit |
| Workers | Async job runners, benchmark workers |
| Frontend | Next.js 14, React, TypeScript, Tailwind CSS |
| Dev tools | Python SDK, CLI (Click + Rich) |
| Infra | Docker, Terraform, Helm |
| Observability | Prometheus, Grafana, Loki, OpenTelemetry |

**Architecture:**

Four layers — developer tools (SDK, CLI, API), control plane (FastAPI with experiment management, circuit optimisation, cost governance), execution plane (Redis-backed async workers with visibility timeout and dead-letter queues), and a web dashboard.

12 PostgreSQL tables, Alembic migrations, plugin system for adding new providers.

**Repo:** https://github.com/mareksuchodolski12-hash/kwantowy

Full docs, architecture decision records, threat model, and runbooks are included.

**About me:**

I'm a self-taught developer. I built this project to learn distributed systems, backend architecture, and developer platform design by actually building something non-trivial. It's a learning project, not a production product (yet).

**What I'm looking for:**

- Architecture feedback — did I structure this well?
- Code review — are there patterns I'm misusing or better approaches?
- Suggestions — what would you add, remove, or change?
- General impressions — does this make sense as a platform?

Honest criticism is welcome. That's the whole point of sharing it.

Thanks for taking a look.

---

## 3. GitHub Repository Description

```
Open developer platform for quantum computing — submit QASM circuits, orchestrate experiments, benchmark providers, and visualise results.
```

(140 characters)

---

## 4. GitHub Release Message

**Title:** v0.3.0 — First Public Release

---

### Quantum Control Plane v0.3.0

The first public release of Quantum Control Plane (QCP) — an open developer platform for running and orchestrating quantum computing experiments.

#### Project overview

QCP provides a single interface to submit quantum circuits, execute them across multiple providers, orchestrate multi-step workflows, benchmark backends, and visualise results. It includes a Python SDK, a CLI, a REST API, and a web dashboard.

The goal is to do for quantum experiments what MLflow does for ML experiments — give developers a consistent way to track, compare, and manage their work.

#### Key features

- **Circuit submission and execution** — submit OpenQASM 3 circuits via API, SDK, or CLI and run them on IBM Runtime, IonQ, Rigetti, or local simulators
- **Circuit optimisation** — automatic gate-count reduction and depth minimisation
- **Experiment versioning** — full version history with audit trail
- **Workflow orchestration** — define multi-step experiment pipelines as DAGs
- **Provider benchmarking** — automated fidelity, latency, and cost benchmarking with a provider leaderboard
- **Smart routing** — capability-based provider selection and ranking
- **Cost governance** — org-level budgets with automatic job rejection when limits are exceeded
- **Multi-tenant hierarchy** — Org → Team → Project structure for managing access and resources
- **Result comparison** — statistical analysis across experiment runs
- **Interactive dashboard** — Next.js web console with charts, leaderboard, and demo page
- **Plugin system** — extend with custom quantum providers via a simple Python interface
- **Observability** — Prometheus metrics, Grafana dashboards, Loki logs, OpenTelemetry tracing

#### Architecture summary

```
Developer Tools          Control Plane              Execution Plane         Dashboard
─────────────────       ──────────────────         ─────────────────       ─────────
Python SDK (qcp-sdk)    FastAPI service             Async job runners       Next.js 14
CLI (qcp)               PostgreSQL (12 tables)      Benchmark workers       React + TypeScript
REST API (/v1/*)        Redis (queue + cache)       Redis queues (FIFO      Tailwind CSS
                        Alembic migrations            + visibility timeout  Recharts
                        Circuit optimiser              + DLQ)
                        Workflow engine
                        Cost governance
                        Provider registry
                        Multi-tenant service
```

Infrastructure: Docker Compose (local dev), Helm charts + Terraform modules (production), Prometheus + Grafana + Loki + OpenTelemetry (observability).

#### Known limitations

- IonQ and Rigetti provider adapters are stubs (real hardware integration planned for v0.4)
- Integration and E2E test suites are scaffolded but not yet populated
- Browser-based login flow is planned for a future release

#### What's next

See [ROADMAP.md](ROADMAP.md) for the v0.4 and v0.5+ plans, including real hardware providers, error mitigation, pulse-level control, Jupyter integration, and hybrid classical-quantum workflows.

#### Feedback welcome

This project was built by a self-taught developer as a way to learn distributed systems, backend architecture, and developer platform engineering. If you have feedback on the architecture, code quality, or direction — please open an issue or start a discussion. All input is appreciated.

Repo: https://github.com/mareksuchodolski12-hash/kwantowy
