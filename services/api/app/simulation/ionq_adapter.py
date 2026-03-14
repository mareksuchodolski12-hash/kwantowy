"""Stub adapter for IonQ Quantum Cloud.

This adapter provides the interface contract for IonQ integration.
It raises ``NotImplementedError`` until an IonQ API token and SDK
integration are configured, allowing the platform to advertise the
provider in its registry without requiring runtime credentials.
"""

from __future__ import annotations

from quantum_contracts import CircuitPayload, ExecutionProvider, ExecutionResult

from app.simulation.providers import ExecutionProviderAdapter


class IonqAdapter(ExecutionProviderAdapter):
    provider = ExecutionProvider.IONQ

    async def run(self, payload: CircuitPayload, timeout_seconds: int, job_id: str) -> ExecutionResult:
        raise NotImplementedError(
            "IonQ provider is not yet implemented. Set QCP_IONQ_API_TOKEN and install the IonQ SDK to enable."
        )
