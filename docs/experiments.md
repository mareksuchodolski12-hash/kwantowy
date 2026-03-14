# Experiments

Experiments are the core unit of work in QCP. Each experiment defines a quantum
circuit (in OpenQASM format) and execution parameters.

## Creating an Experiment

### Via API

```bash
curl -X POST http://localhost:8000/v1/experiments \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_KEY" \
  -d '{
    "name": "bell-state",
    "description": "Two-qubit Bell state",
    "provider": "local_simulator",
    "circuit": {
      "qasm": "OPENQASM 2.0; include \"qelib1.inc\"; qreg q[2]; creg c[2]; h q[0]; cx q[0],q[1]; measure q -> c;",
      "shots": 1024
    },
    "retry_policy": { "max_attempts": 3, "timeout_seconds": 30 }
  }'
```

### Via SDK

```python
client.run_experiment(name="bell-state", qasm=qasm, shots=1024)
```

### Via CLI

```bash
qcp experiment run bell.qasm --provider local_simulator
```

## Experiment Versioning

Each experiment can have multiple versions tracking circuit changes:

```bash
curl -X POST http://localhost:8000/v1/experiments/{id}/versions \
  -H "X-API-Key: YOUR_KEY" \
  -d '{"circuit_qasm": "..."}'
```

## Lifecycle

1. **Submit** — experiment and job created
2. **Queued** — job enqueued to Redis
3. **Running** — worker executing circuit
4. **Succeeded / Failed** — result stored or retry triggered
