# QCP Provider Plugins

This directory contains external quantum execution provider plugins.

Each subdirectory is a self-contained provider adapter that can be registered
with the Quantum Control Plane.

## Structure

```
plugins/providers/
├── aws_braket/          # Amazon Braket provider
├── custom_simulator/    # Example custom simulator
└── README.md
```

## Writing a Provider Plugin

A provider plugin must implement the `BaseProvider` interface:

```python
from plugins.providers.base import BaseProvider, ProviderInfo

class MyProvider(BaseProvider):
    name = "my_provider"

    def info(self) -> ProviderInfo:
        return ProviderInfo(
            display_name="My Provider",
            max_qubits=20,
            is_simulator=True,
        )

    async def execute(self, qasm: str, shots: int) -> dict[str, int]:
        # Run circuit, return measurement counts
        ...
```

Then register it in `plugin.yaml`:

```yaml
name: my_provider
version: 0.1.0
entry_point: my_provider.provider:MyProvider
```

## Included Plugins

| Plugin | Description | Status |
|--------|-------------|--------|
| `aws_braket` | Amazon Braket integration | Stub |
| `custom_simulator` | Example custom simulator | Example |
