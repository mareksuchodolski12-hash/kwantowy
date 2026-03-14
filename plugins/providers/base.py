"""Base interface for QCP provider plugins."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ProviderInfo:
    """Metadata describing a plugin provider's capabilities."""

    display_name: str
    max_qubits: int
    max_shots: int = 10000
    supports_mid_circuit_measurement: bool = False
    supports_dynamic_circuits: bool = False
    is_simulator: bool = True
    estimated_cost_per_shot_usd: float = 0.0
    avg_queue_time_seconds: float = 0.0
    estimated_fidelity: float = 1.0


class BaseProvider(ABC):
    """Abstract base class for provider plugins.

    All external providers must subclass this and implement the
    ``info`` and ``execute`` methods.
    """

    name: str = ""

    @abstractmethod
    def info(self) -> ProviderInfo:
        """Return provider metadata and capabilities."""

    @abstractmethod
    async def execute(self, qasm: str, shots: int) -> dict[str, int]:
        """Execute a QASM circuit and return measurement counts."""
