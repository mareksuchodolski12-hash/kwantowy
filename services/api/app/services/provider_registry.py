"""Provider registry with capabilities metadata and automatic backend selection.

The registry maintains a catalogue of quantum execution providers, each annotated
with capability metadata (qubit limits, cost, simulator flag, fidelity, etc.).
Given a circuit's requirements the ``select`` method returns a ranked list of
suitable providers so callers can route jobs automatically.

Smart routing considers:
• circuit width (qubit count)
• estimated fidelity
• queue latency
• cost per shot
• hardware preference
"""

from __future__ import annotations

import logging

from quantum_contracts import (
    ExecutionProvider,
    ProviderCapabilities,
    ProviderRouteRequest,
    ProviderRouteResponse,
)

from app.core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default capability catalogue – one entry per supported provider.
# ---------------------------------------------------------------------------

_DEFAULT_CAPABILITIES: list[ProviderCapabilities] = [
    ProviderCapabilities(
        provider=ExecutionProvider.LOCAL_SIMULATOR,
        display_name="Qiskit BasicProvider (local)",
        max_qubits=24,
        max_shots=10000,
        is_simulator=True,
        estimated_cost_per_shot_usd=0.0,
        avg_queue_time_seconds=0.0,
        estimated_fidelity=1.0,
    ),
    ProviderCapabilities(
        provider=ExecutionProvider.SIMULATOR_AER,
        display_name="Qiskit Aer Simulator (local)",
        max_qubits=30,
        max_shots=10000,
        is_simulator=True,
        supports_mid_circuit_measurement=True,
        supports_dynamic_circuits=True,
        estimated_cost_per_shot_usd=0.0,
        avg_queue_time_seconds=0.0,
        estimated_fidelity=1.0,
    ),
    ProviderCapabilities(
        provider=ExecutionProvider.IBM_RUNTIME,
        display_name="IBM Quantum Runtime",
        max_qubits=127,
        max_shots=10000,
        is_simulator=False,
        supports_mid_circuit_measurement=True,
        supports_dynamic_circuits=True,
        estimated_cost_per_shot_usd=0.0016,
        avg_queue_time_seconds=120.0,
        estimated_fidelity=0.97,
    ),
    ProviderCapabilities(
        provider=ExecutionProvider.IONQ,
        display_name="IonQ Quantum Cloud",
        max_qubits=36,
        max_shots=10000,
        is_simulator=False,
        supports_mid_circuit_measurement=True,
        estimated_cost_per_shot_usd=0.01,
        avg_queue_time_seconds=60.0,
        estimated_fidelity=0.98,
    ),
    ProviderCapabilities(
        provider=ExecutionProvider.RIGETTI,
        display_name="Rigetti Quantum Cloud",
        max_qubits=80,
        max_shots=10000,
        is_simulator=False,
        supports_mid_circuit_measurement=False,
        estimated_cost_per_shot_usd=0.0035,
        avg_queue_time_seconds=90.0,
        estimated_fidelity=0.95,
    ),
]


class ProviderRegistry:
    """In-memory provider capability catalogue and routing engine."""

    def __init__(self) -> None:
        self._providers: dict[ExecutionProvider, ProviderCapabilities] = {}
        for cap in _DEFAULT_CAPABILITIES:
            self._providers[cap.provider] = cap
        # Mark providers as enabled/disabled based on runtime configuration.
        self._apply_runtime_config()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def list_capabilities(self) -> list[ProviderCapabilities]:
        """Return capabilities for all registered providers."""
        return list(self._providers.values())

    def get_capabilities(self, provider: ExecutionProvider) -> ProviderCapabilities | None:
        """Return capabilities for a single provider, or ``None``."""
        return self._providers.get(provider)

    def update_capabilities(self, provider: ExecutionProvider, **kwargs: object) -> None:
        """Update specific capability fields for a provider at runtime.

        This allows the benchmarking engine to push live fidelity / queue
        metrics into the routing catalogue.
        """
        cap = self._providers.get(provider)
        if cap:
            self._providers[provider] = cap.model_copy(update=kwargs)  # type: ignore[arg-type]

    def select(self, request: ProviderRouteRequest) -> ProviderRouteResponse:
        """Select the best provider for the given circuit requirements.

        Providers are filtered by qubit capacity, shot limit, fidelity
        threshold, and queue latency cap, then scored by a weighted
        heuristic combining cost, queue wait, fidelity, and hardware
        preference.
        """
        candidates = self._filter_candidates(request)
        if not candidates:
            return ProviderRouteResponse(
                recommended=ExecutionProvider.LOCAL_SIMULATOR,
                alternatives=[],
                reason="No suitable provider found; falling back to local simulator.",
            )

        scored = sorted(candidates, key=lambda c: self._score(c, request))
        best = scored[0]
        alternatives = [c.provider for c in scored[1:]]

        reason = self._explain(best, request)
        return ProviderRouteResponse(
            recommended=best.provider,
            alternatives=alternatives,
            reason=reason,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _apply_runtime_config(self) -> None:
        """Enable or disable providers based on ``settings``."""
        ibm = self._providers.get(ExecutionProvider.IBM_RUNTIME)
        if ibm:
            self._providers[ExecutionProvider.IBM_RUNTIME] = ibm.model_copy(
                update={"enabled": settings.ibm_runtime_enabled}
            )
        # IonQ / Rigetti are stub adapters – disabled by default.
        for stub in (ExecutionProvider.IONQ, ExecutionProvider.RIGETTI):
            cap = self._providers.get(stub)
            if cap:
                self._providers[stub] = cap.model_copy(update={"enabled": False})

    def _filter_candidates(self, request: ProviderRouteRequest) -> list[ProviderCapabilities]:
        candidates: list[ProviderCapabilities] = []
        for cap in self._providers.values():
            if not cap.enabled:
                continue
            if cap.provider in request.exclude_providers:
                continue
            if cap.max_qubits < request.qubit_count:
                continue
            if cap.max_shots < request.shots:
                continue
            if request.max_cost_usd is not None:
                total_cost = cap.estimated_cost_per_shot_usd * request.shots
                if total_cost > request.max_cost_usd:
                    continue
            # Smart routing: fidelity threshold
            if request.min_fidelity is not None:
                if cap.estimated_fidelity < request.min_fidelity:
                    continue
            # Smart routing: queue latency cap
            if request.max_queue_seconds is not None:
                if cap.avg_queue_time_seconds > request.max_queue_seconds:
                    continue
            candidates.append(cap)
        return candidates

    @staticmethod
    def _score(cap: ProviderCapabilities, request: ProviderRouteRequest) -> float:
        """Lower score = better match.

        Weights combine cost, queue wait, fidelity, and hardware preference.
        """
        score: float = 0.0
        # Prefer hardware when requested, otherwise prefer simulators (cheaper).
        if request.prefer_hardware:
            score = score + (0.0 if not cap.is_simulator else 100.0)
        else:
            score = score + (0.0 if cap.is_simulator else 50.0)
        # Prefer lower cost.
        cost_weight: float = float(cap.estimated_cost_per_shot_usd) * float(request.shots) * 10.0
        score = score + cost_weight
        # Prefer shorter queue wait.
        queue_weight: float = float(cap.avg_queue_time_seconds) * 0.1
        score = score + queue_weight
        # Prefer higher fidelity – penalise lower fidelity.
        fidelity_penalty: float = (1.0 - cap.estimated_fidelity) * 200.0
        score = score + fidelity_penalty
        return score

    @staticmethod
    def _explain(cap: ProviderCapabilities, request: ProviderRouteRequest) -> str:
        parts: list[str] = [f"Selected {cap.display_name}"]
        if request.prefer_hardware and not cap.is_simulator:
            parts.append("(hardware preferred)")
        elif cap.is_simulator:
            parts.append("(simulator, zero cost)")
        cost = cap.estimated_cost_per_shot_usd * request.shots
        if cost > 0:
            parts.append(f"est. cost ${cost:.4f}")
        parts.append(f"fidelity {cap.estimated_fidelity:.2f}")
        return " ".join(parts)


# Module-level singleton for convenience.
_registry: ProviderRegistry | None = None


def get_provider_registry() -> ProviderRegistry:
    """Return the module-level provider registry singleton."""
    global _registry  # noqa: PLW0603
    if _registry is None:
        _registry = ProviderRegistry()
    return _registry
