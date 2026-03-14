# Benchmarking

QCP includes an automated benchmarking system that periodically runs calibration
circuits against all providers and tracks fidelity, gate error, and queue time
metrics.

## How It Works

The benchmark worker (`workers/benchmark-runner/`) runs on a configurable
interval (default: 5 minutes):

1. Executes a Bell-state calibration circuit on each provider.
2. Records fidelity, gate error, readout error, queue time, and execution time.
3. Updates Prometheus metrics for dashboarding and alerting.
4. Powers the Provider Leaderboard page.

## Running the Benchmark Worker

```bash
# Default 5-minute interval
make benchmark

# Custom interval (seconds)
QCP_BENCHMARK_INTERVAL=60 make benchmark
```

## Manual Benchmark

```bash
curl -X POST http://localhost:8000/v1/benchmarks \
  -H "X-API-Key: YOUR_KEY" \
  -d '{
    "provider": "local_simulator",
    "fidelity": 0.99,
    "avg_gate_error": 0.001,
    "readout_error": 0.005
  }'
```

## Viewing Results

### API

```bash
curl http://localhost:8000/v1/benchmarks -H "X-API-Key: YOUR_KEY"
```

### Dashboard

Visit the [Provider Leaderboard](/providers) to see ranked providers with
fidelity scores, queue times, and cost per shot.

## Prometheus Metrics

| Metric | Description |
|--------|-------------|
| `qcp_provider_fidelity` | Calibration fidelity per provider |
| `qcp_provider_gate_error` | Average gate error per provider |
| `qcp_provider_readout_error` | Readout error per provider |
| `qcp_provider_queue_latency_seconds` | Queue latency per provider |
| `qcp_provider_execution_time_ms` | Execution time per provider |
