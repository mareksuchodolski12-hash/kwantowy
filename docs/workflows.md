# Workflows

Workflows allow you to orchestrate multi-step experiment pipelines with
dependency tracking.

## Creating a Workflow

```bash
curl -X POST http://localhost:8000/v1/workflows \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_KEY" \
  -d '{
    "workflow": {
      "name": "bell-benchmark",
      "description": "Run Bell state on multiple providers",
      "steps": [
        { "name": "simulate", "action": "run_circuit", "provider": "local_simulator" },
        { "name": "hardware", "action": "run_circuit", "provider": "ibm_runtime", "depends_on": ["simulate"] }
      ],
      "circuit": { "qasm": "OPENQASM 2.0; ...", "shots": 1024 }
    }
  }'
```

## Workflow Steps

Each step has:

| Field | Description |
|-------|-------------|
| `name` | Unique step identifier |
| `action` | Action to execute (e.g. `run_circuit`) |
| `provider` | Target execution provider |
| `params` | Additional parameters |
| `depends_on` | List of step names that must complete first |

## Monitoring Runs

```bash
# List all workflow runs
curl http://localhost:8000/v1/workflows/runs -H "X-API-Key: YOUR_KEY"

# Get a specific run
curl http://localhost:8000/v1/workflows/runs/{run_id} -H "X-API-Key: YOUR_KEY"
```
