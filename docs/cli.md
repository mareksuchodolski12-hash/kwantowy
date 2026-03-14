# CLI Reference

## Installation

```bash
pip install -e packages/cli
```

## Authentication

```bash
qcp login --api-key YOUR_KEY --url http://localhost:8000
```

Or set environment variables:

```bash
export QCP_API_KEY=qcp_...
export QCP_BASE_URL=http://localhost:8000
```

## Commands

### `qcp experiment run`

Submit a QASM circuit for execution.

```bash
qcp experiment run bell.qasm --provider local_simulator --shots 1024
```

Options:

| Flag | Default | Description |
|------|---------|-------------|
| `--provider` | `local_simulator` | Execution provider |
| `--shots` | `1024` | Number of measurement shots |
| `--name` | filename | Experiment name |
| `--wait` | off | Wait for result and print it |

### `qcp experiment list`

List all experiments.

```bash
qcp experiment list
```

### `qcp run status`

Show the status of a job.

```bash
qcp run status JOB_ID
```

### `qcp result show`

Display results for a completed job.

```bash
qcp result show JOB_ID
```

## Configuration

Credentials are stored in `~/.qcp/config.json` after `qcp login`.  Environment
variables `QCP_API_KEY` and `QCP_BASE_URL` take precedence.
