"""Amazon Braket provider plugin for QCP (stub).

This module demonstrates how an external cloud provider can be
integrated as a QCP plugin.  The actual Braket SDK calls are stubbed
out; replace them with real ``braket.aws`` calls to connect to
Amazon Braket hardware or simulators.
"""

from __future__ import annotations

from plugins.providers.base import BaseProvider, ProviderInfo


class AwsBraketProvider(BaseProvider):
    """Amazon Braket provider adapter."""

    name = "aws_braket"

    def info(self) -> ProviderInfo:
        return ProviderInfo(
            display_name="Amazon Braket",
            max_qubits=34,
            is_simulator=False,
            estimated_cost_per_shot_usd=0.003,
            avg_queue_time_seconds=45.0,
            estimated_fidelity=0.94,
        )

    async def execute(self, qasm: str, shots: int) -> dict[str, int]:
        raise NotImplementedError(
            "AWS Braket provider is a stub. Install amazon-braket-sdk and configure AWS credentials."
        )
