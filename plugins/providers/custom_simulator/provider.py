"""Custom simulator provider plugin for QCP (example).

This is a minimal example showing how to build a custom simulator
that plugs into the Quantum Control Plane as an external provider.
"""

from __future__ import annotations

import random

from plugins.providers.base import BaseProvider, ProviderInfo


class CustomSimulatorProvider(BaseProvider):
    """Trivial two-qubit simulator for demonstration purposes."""

    name = "custom_simulator"

    def info(self) -> ProviderInfo:
        return ProviderInfo(
            display_name="Custom Simulator",
            max_qubits=8,
            is_simulator=True,
            estimated_cost_per_shot_usd=0.0,
            avg_queue_time_seconds=0.0,
            estimated_fidelity=0.99,
        )

    async def execute(self, qasm: str, shots: int) -> dict[str, int]:
        """Return random Bell-state–like measurement counts."""
        counts: dict[str, int] = {}
        for _ in range(shots):
            state = random.choice(["00", "11"])
            counts[state] = counts.get(state, 0) + 1
        return counts
