# Quantum Runner Worker

Async worker that consumes queued jobs from Redis and executes providers via adapter abstraction:

- local simulator (`qiskit` basic simulator)
- IBM Runtime (`qiskit-ibm-runtime`) when enabled

## Run locally

```bash
PYTHONPATH=services/api python workers/quantum-runner/runner/main.py
```
