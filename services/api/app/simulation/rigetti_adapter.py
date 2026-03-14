"""Stub adapter for Rigetti Quantum Cloud.

This adapter provides the interface contract for Rigetti integration.
It raises ``NotImplementedError`` until a Rigetti API token and SDK
integration are configured, allowing the platform to advertise the
provider in its registry without requiring runtime credentials.
"""

from __future__ import annotations

from quantum_contracts import CircuitPayload, ExecutionProvider, ExecutionResult

from app.simulation.providers import ExecutionProviderAdapter


class RigettiAdapter(ExecutionProviderAdapter):
    provider = ExecutionProvider.RIGETTI

    async def run(self, payload: CircuitPayload, timeout_seconds: int, job_id: str) -> ExecutionResult:
        raise NotImplementedError(
            "Rigetti provider is not yet implemented. Set QCP_RIGETTI_API_TOKEN and install the pyQuil SDK to enable."
        )
