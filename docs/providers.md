# Providers

QCP supports multiple quantum execution backends via a provider adapter
architecture.

## Built-in Providers

| Provider | Key | Type | Status |
|----------|-----|------|--------|
| Local Simulator | `local_simulator` | Simulator | ✅ Active |
| Aer Simulator | `simulator_aer` | Simulator | ✅ Active |
| IBM Runtime | `ibm_runtime` | Hardware | ✅ Active |
| IonQ | `ionq` | Hardware | 🔧 Stub |
| Rigetti | `rigetti` | Hardware | 🔧 Stub |

## Provider Selection

The smart routing engine selects the best provider based on:

- Qubit count requirements
- Fidelity constraints
- Cost limits
- Queue time preferences

```bash
curl -X POST http://localhost:8000/v1/providers/select \
  -H "X-API-Key: YOUR_KEY" \
  -d '{"qubit_count": 5, "prefer_hardware": true, "min_fidelity": 0.95}'
```

## Plugin System

External providers can be added via the plugin interface:

1. Create a directory under `plugins/providers/`
2. Implement `BaseProvider` from `plugins/providers/base.py`
3. Add a `plugin.yaml` descriptor

```python
from plugins.providers.base import BaseProvider, ProviderInfo

class MyProvider(BaseProvider):
    name = "my_provider"

    def info(self) -> ProviderInfo:
        return ProviderInfo(display_name="My Provider", max_qubits=20)

    async def execute(self, qasm: str, shots: int) -> dict[str, int]:
        # Execute circuit and return counts
        ...
```

See [`plugins/providers/README.md`](../plugins/providers/README.md) for details.
