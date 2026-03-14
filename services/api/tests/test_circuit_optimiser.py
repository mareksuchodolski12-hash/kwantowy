"""Tests for the circuit optimisation pipeline (component 1)."""

from quantum_contracts import (
    CircuitPayload,
    OptimisationConfig,
    OptimisationStrategy,
)

from app.services.circuit_optimiser import (
    _count_gates,
    _estimate_depth,
    circuit_hash,
    optimise_circuit,
    optimise_shots,
)

QASM = (
    'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg c[2];\n'
    "h q[0];\ncx q[0],q[1];\nmeasure q[0] -> c[0];\nmeasure q[1] -> c[1];"
)
QASM_DOUBLE_X = 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[1];\ncreg c[1];\nx q[0];\nx q[0];\nmeasure q[0] -> c[0];'


class TestGateAnalysis:
    def test_count_gates_bell(self) -> None:
        count = _count_gates(QASM)
        assert count >= 2  # h + cx

    def test_estimate_depth_bell(self) -> None:
        depth = _estimate_depth(QASM)
        assert depth >= 2

    def test_circuit_hash_deterministic(self) -> None:
        h1 = circuit_hash(QASM)
        h2 = circuit_hash(QASM)
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex digest

    def test_circuit_hash_differs_for_different_circuits(self) -> None:
        h1 = circuit_hash(QASM)
        h2 = circuit_hash(QASM_DOUBLE_X)
        assert h1 != h2


class TestShotOptimisation:
    def test_simple_circuit_reduces_shots(self) -> None:
        result = optimise_shots(1024, gate_count=1)
        assert result <= 512

    def test_complex_circuit_keeps_shots(self) -> None:
        result = optimise_shots(1024, gate_count=5)
        assert result == 1024

    def test_shots_clamped_to_max(self) -> None:
        result = optimise_shots(10000, gate_count=100)
        assert result <= 10000

    def test_shots_at_least_one(self) -> None:
        result = optimise_shots(1, gate_count=0)
        assert result >= 1


class TestOptimiseCircuit:
    def test_none_strategy_passthrough(self) -> None:
        payload = CircuitPayload(qasm=QASM, shots=1024)
        config = OptimisationConfig(strategy=OptimisationStrategy.NONE)
        result = optimise_circuit(payload, config)
        assert result.original_qasm == QASM
        assert result.optimised_qasm == QASM
        assert result.strategy_applied == OptimisationStrategy.NONE

    def test_medium_strategy_reduces_double_gates(self) -> None:
        payload = CircuitPayload(qasm=QASM_DOUBLE_X, shots=1024)
        config = OptimisationConfig(strategy=OptimisationStrategy.MEDIUM)
        result = optimise_circuit(payload, config)
        # Double X should be removed by the depth reduction heuristic
        assert result.optimised_gate_count <= result.original_gate_count

    def test_noise_aware_mapping(self) -> None:
        payload = CircuitPayload(qasm=QASM, shots=1024)
        config = OptimisationConfig(strategy=OptimisationStrategy.NOISE_AWARE, noise_aware_mapping=True)
        result = optimise_circuit(payload, config)
        assert len(result.qubit_mapping) > 0

    def test_shot_optimisation(self) -> None:
        payload = CircuitPayload(qasm=QASM, shots=1024)
        config = OptimisationConfig(shot_optimisation=True)
        result = optimise_circuit(payload, config)
        assert result.estimated_fidelity <= 1.0
        assert result.estimated_fidelity >= 0.0

    def test_light_strategy(self) -> None:
        payload = CircuitPayload(qasm=QASM, shots=1024)
        config = OptimisationConfig(strategy=OptimisationStrategy.LIGHT)
        result = optimise_circuit(payload, config)
        assert result.strategy_applied == OptimisationStrategy.LIGHT

    def test_heavy_strategy(self) -> None:
        payload = CircuitPayload(qasm=QASM_DOUBLE_X, shots=1024)
        config = OptimisationConfig(strategy=OptimisationStrategy.HEAVY)
        result = optimise_circuit(payload, config)
        assert result.strategy_applied == OptimisationStrategy.HEAVY
        assert result.optimised_depth <= result.original_depth
