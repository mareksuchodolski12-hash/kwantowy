# Roadmap

## Quantum Control Plane — Product Roadmap

### ✅ Delivered

- **Core Platform**: Experiment submission, job queue, worker execution, result storage
- **Multi-Provider Support**: Local simulator, IBM Runtime, Aer, IonQ (stub), Rigetti (stub)
- **Workflow Orchestration**: Declarative multi-step experiment pipelines
- **Provider Benchmarking**: Calibration circuits, fidelity tracking, Prometheus metrics
- **Cost Governance**: Budget management, per-job cost tracking, alerts
- **Multi-Tenant Platform**: Organisation → Team → Project hierarchy
- **Circuit Optimisation**: Transpilation pipeline with noise-aware mapping
- **Experiment Versioning**: Circuit lineage tracking with version history
- **Result Comparison**: Side-by-side provider comparison with fidelity scores
- **Dashboard**: Next.js web console with experiment management and result charts
- **Observability**: Prometheus metrics, OpenTelemetry traces, Grafana dashboards
- **Python SDK**: `QCPClient` with submit, poll, and wait-for-result helpers
- **CLI Tool**: `qcp` command for terminal-based experiment management
- **Provider Leaderboard**: Ranked hardware comparison page
- **Interactive Demo**: One-click Bell State, Grover, and Deutsch-Jozsa experiments
- **Plugin System**: Extensible provider interface for external backends
- **Auto-Benchmark Worker**: Periodic calibration with metric updates

### 🔜 Next (v0.4)

- **Real Hardware Execution**: Production IonQ and Rigetti adapter implementations
- **Error Mitigation**: Zero-noise extrapolation and measurement error mitigation
- **Pulse-Level Control**: Qiskit Pulse integration for hardware-native gates
- **Experiment Templates**: Shareable experiment blueprints with parameterisation
- **Collaborative Notebooks**: Jupyter integration with QCP SDK
- **Webhook Notifications**: Job completion callbacks via HTTP/Slack/email

### 🔮 Future (v0.5+)

- **Hybrid Classical-Quantum Workflows**: Variational algorithm loops (VQE, QAOA)
- **Federated Execution**: Multi-region job distribution with latency-aware routing
- **Marketplace**: Community-contributed circuits, providers, and analysis tools
- **RBAC**: Role-based access control at org/team/project level
- **Audit Trail**: Full event sourcing with compliance reporting
- **SLA Management**: Provider SLA tracking with automatic failover
- **GPU-Accelerated Simulation**: cuQuantum backend for large-circuit simulation
