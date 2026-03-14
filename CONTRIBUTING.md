# Contributing to Quantum Control Plane

Thank you for considering contributing to the Quantum Control Plane (QCP)!

## Getting Started

1. **Fork** the repository and clone your fork.
2. Run `make bootstrap` to install all dependencies.
3. Run `make up` to start PostgreSQL and Redis via Docker.
4. Run `make migrate` to apply database migrations.
5. Run `make test` to verify everything works.

## Development Workflow

```bash
# Start services
make up && make migrate

# Run the API server (port 8000)
make api

# Run the worker (separate terminal)
make worker

# Run the web console (port 3000)
make web

# Lint and typecheck
make lint
make typecheck

# Run tests
make test
```

## Project Structure

| Directory | Description |
|-----------|-------------|
| `services/api/` | FastAPI control plane API |
| `workers/quantum-runner/` | Async job execution worker |
| `workers/benchmark-runner/` | Auto-benchmark worker |
| `apps/web/` | Next.js dashboard |
| `packages/sdk/` | Python SDK |
| `packages/cli/` | CLI tool |
| `packages/contracts/` | Shared Pydantic models |
| `plugins/providers/` | External provider plugins |
| `docs/` | Documentation |
| `infra/` | Helm, Terraform, observability |

## Code Style

- **Python**: Ruff for linting and formatting, mypy for type checking (`strict` mode).
- **TypeScript**: ESLint + Next.js config, `strict` tsconfig.
- **Line length**: 120 characters.
- Run `make format` before committing.
- Pre-commit hooks are installed via `make bootstrap`.

## Pull Request Guidelines

1. Keep PRs focused — one feature or fix per PR.
2. Include tests for new functionality.
3. Update documentation for architecture-impacting changes.
4. Ensure `make lint`, `make typecheck`, and `make test` all pass.
5. Write clear commit messages.

## Adding a Provider Plugin

See [`plugins/providers/README.md`](plugins/providers/README.md) for the plugin interface.

1. Create a new directory under `plugins/providers/`.
2. Implement the `BaseProvider` interface.
3. Add a `plugin.yaml` descriptor.
4. Submit a PR with tests.

## Reporting Issues

- Use GitHub Issues with a clear title and reproduction steps.
- Label with `bug`, `enhancement`, or `question`.

## Code of Conduct

Be respectful, inclusive, and constructive. We follow the
[Contributor Covenant](https://www.contributor-covenant.org/).
