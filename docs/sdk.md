# Python SDK

## Installation

```bash
pip install -e packages/sdk
```

## Quick Start

```python
from quantum_sdk import QCPClient

client = QCPClient(api_key="qcp_...", base_url="http://localhost:8000")

# Submit an experiment
job = client.run_experiment(
    name="bell",
    qasm=open("bell.qasm").read(),
    shots=1024,
)
print(job["job"]["status"])

# Wait for result
result = client.wait_for_result(job["job"]["id"])
print(result)
```

## API Reference

### `QCPClient`

```python
QCPClient(api_key: str, base_url: str = "http://localhost:8000", timeout: float = 30.0)
```

### Methods

| Method | Description |
|--------|-------------|
| `run_experiment(name, qasm, shots, provider, description)` | Submit an experiment |
| `run_circuit(name, qasm, shots, provider, ...)` | Submit a circuit (lower-level) |
| `get_job(job_id)` | Get job status |
| `get_results(job_id)` | Get execution results |
| `list_experiments()` | List all experiments |
| `list_jobs()` | List all jobs |
| `wait_for_result(job_id, poll_interval, max_wait)` | Poll until completion |
