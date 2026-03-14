"""Circuit optimisation pipeline.

Provides transpilation strategies, noise-aware qubit mapping, depth reduction,
and shot optimisation before circuits are routed to a provider.
"""

from __future__ import annotations

import hashlib
import logging
import math

from quantum_contracts import (
    CircuitPayload,
    OptimisationConfig,
    OptimisationStrategy,
    OptimisedCircuit,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Depth & gate count estimation from QASM (lightweight heuristic)
# ---------------------------------------------------------------------------

_GATE_KEYWORDS = frozenset(
    {
        "x",
        "y",
        "z",
        "h",
        "s",
        "t",
        "cx",
        "cz",
        "ccx",
        "swap",
        "rx",
        "ry",
        "rz",
        "u1",
        "u2",
        "u3",
        "sdg",
        "tdg",
        "id",
    }
)


def _count_gates(qasm: str) -> int:
    """Count gate operations in a QASM 2.0 string (heuristic)."""
    count = 0
    for line in qasm.splitlines():
        stripped = line.strip().rstrip(";").split()[0] if line.strip() else ""
        # Strip parameterised part, e.g. "rx(1.57)" -> "rx"
        token = stripped.split("(")[0]
        if token in _GATE_KEYWORDS:
            count += 1
    return max(count, 1)


def _estimate_depth(qasm: str) -> int:
    """Rough depth estimate – counts sequential gate lines."""
    depth = 0
    for line in qasm.splitlines():
        stripped = line.strip().rstrip(";").split()[0] if line.strip() else ""
        token = stripped.split("(")[0]
        if token in _GATE_KEYWORDS:
            depth += 1
    return max(depth, 1)


def circuit_hash(qasm: str) -> str:
    """SHA-256 hash of the circuit QASM."""
    return hashlib.sha256(qasm.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Shot optimisation
# ---------------------------------------------------------------------------


def optimise_shots(shots: int, gate_count: int) -> int:
    """Suggest an optimal shot count based on circuit complexity.

    For very simple circuits fewer shots suffice; complex circuits benefit
    from more samples.  Returns a value clamped to [1, 10000].
    """
    if gate_count <= 2:
        suggested = min(shots, 512)
    elif gate_count <= 10:
        suggested = shots
    else:
        suggested = min(int(shots * math.log2(gate_count + 1) / 4), 10000)
    return max(1, suggested)


# ---------------------------------------------------------------------------
# Qubit mapping (noise-aware placeholder)
# ---------------------------------------------------------------------------


def _build_qubit_mapping(qasm: str, noise_aware: bool) -> dict[int, int]:
    """Return a logical→physical qubit mapping.

    When *noise_aware* is ``True`` the mapper assigns lower-index physical
    qubits first (a proxy for better-calibrated qubits on real hardware).
    Otherwise returns an identity mapping.
    """
    # Parse qubit count from QASM qreg declarations
    qubit_indices: list[int] = []
    for line in qasm.splitlines():
        stripped = line.strip()
        if stripped.startswith("qreg "):
            # e.g. "qreg q[3];"
            bracket_start = stripped.index("[")
            bracket_end = stripped.index("]")
            n = int(stripped[bracket_start + 1 : bracket_end])
            qubit_indices.extend(range(n))

    if not qubit_indices:
        return {}

    if noise_aware:
        # Reverse to place logical qubit 0 on the "best" physical qubit
        physical = sorted(qubit_indices, reverse=True)
        return dict(zip(qubit_indices, physical, strict=False))

    return {q: q for q in qubit_indices}


# ---------------------------------------------------------------------------
# Main optimisation entry point
# ---------------------------------------------------------------------------

_STRATEGY_LEVELS: dict[OptimisationStrategy, int] = {
    OptimisationStrategy.NONE: 0,
    OptimisationStrategy.LIGHT: 1,
    OptimisationStrategy.MEDIUM: 2,
    OptimisationStrategy.HEAVY: 3,
    OptimisationStrategy.NOISE_AWARE: 3,
}


def optimise_circuit(payload: CircuitPayload, config: OptimisationConfig) -> OptimisedCircuit:
    """Run the optimisation pipeline and return an :class:`OptimisedCircuit`.

    The optimiser performs transpilation-level gate reduction heuristics,
    optional noise-aware qubit mapping, depth reduction, and shot optimisation.
    """
    original_qasm = payload.qasm
    original_depth = _estimate_depth(original_qasm)
    original_gates = _count_gates(original_qasm)

    level = _STRATEGY_LEVELS.get(config.strategy, 0)

    # --- Depth reduction heuristic ---
    # For MEDIUM+ strategies, collapse consecutive single-qubit identity patterns.
    optimised_qasm = original_qasm
    optimised_depth = original_depth
    optimised_gates = original_gates

    if level >= 2:
        # Remove identity-like gate pairs (x x -> noop, h h -> noop)
        lines = optimised_qasm.splitlines()
        reduced: list[str] = []
        skip_next = False
        for i, line in enumerate(lines):
            if skip_next:
                skip_next = False
                continue
            stripped = line.strip().rstrip(";")
            if i + 1 < len(lines):
                next_stripped = lines[i + 1].strip().rstrip(";")
                if stripped and next_stripped and stripped == next_stripped:
                    token = stripped.split()[0].split("(")[0]
                    if token in {"x", "y", "z", "h"}:
                        skip_next = True
                        continue
            reduced.append(line)
        optimised_qasm = "\n".join(reduced)
        optimised_depth = _estimate_depth(optimised_qasm)
        optimised_gates = _count_gates(optimised_qasm)

    # --- Noise-aware qubit mapping ---
    noise_aware = config.noise_aware_mapping or config.strategy == OptimisationStrategy.NOISE_AWARE
    qubit_mapping = _build_qubit_mapping(optimised_qasm, noise_aware)

    # --- Shot optimisation ---
    final_shots = payload.shots
    if config.shot_optimisation:
        final_shots = optimise_shots(payload.shots, optimised_gates)

    # --- Estimated fidelity (heuristic) ---
    fidelity = max(0.0, 1.0 - (optimised_gates * 0.001))

    logger.info(
        "circuit optimised",
        extra={
            "strategy": config.strategy.value,
            "original_depth": original_depth,
            "optimised_depth": optimised_depth,
            "original_gates": original_gates,
            "optimised_gates": optimised_gates,
            "shots": final_shots,
        },
    )

    return OptimisedCircuit(
        original_qasm=original_qasm,
        optimised_qasm=optimised_qasm,
        original_depth=original_depth,
        optimised_depth=optimised_depth,
        original_gate_count=original_gates,
        optimised_gate_count=optimised_gates,
        strategy_applied=config.strategy,
        qubit_mapping=qubit_mapping,
        estimated_fidelity=round(fidelity, 6),
    )
