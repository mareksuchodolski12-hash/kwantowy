"""Tests for result comparison engine (component 6)."""

from datetime import UTC, datetime
from uuid import uuid4

from quantum_contracts import ExecutionProvider, ExecutionResult

from app.services.result_comparator import (
    compare_results,
    hellinger_fidelity,
    total_variation_distance,
)


class TestTotalVariationDistance:
    def test_identical_distributions(self) -> None:
        dist = {"00": 0.5, "11": 0.5}
        assert total_variation_distance(dist, dist) == 0.0

    def test_disjoint_distributions(self) -> None:
        a = {"00": 1.0}
        b = {"11": 1.0}
        assert total_variation_distance(a, b) == 1.0

    def test_partial_overlap(self) -> None:
        a = {"00": 0.5, "01": 0.5}
        b = {"00": 0.5, "11": 0.5}
        tvd = total_variation_distance(a, b)
        assert 0.0 < tvd < 1.0


class TestHellingerFidelity:
    def test_identical_distributions(self) -> None:
        dist = {"00": 0.5, "11": 0.5}
        assert hellinger_fidelity(dist, dist) == 1.0

    def test_disjoint_distributions(self) -> None:
        a = {"00": 1.0}
        b = {"11": 1.0}
        f = hellinger_fidelity(a, b)
        assert f == 0.0

    def test_partial_overlap(self) -> None:
        a = {"00": 0.8, "11": 0.2}
        b = {"00": 0.6, "11": 0.4}
        f = hellinger_fidelity(a, b)
        assert 0.0 < f < 1.0


class TestCompareResults:
    def _make_result(
        self, provider: ExecutionProvider, backend: str, counts: dict[str, int], shots: int
    ) -> ExecutionResult:
        return ExecutionResult(
            job_id=uuid4(),
            provider=provider,
            backend=backend,
            counts=counts,
            shots=shots,
            duration_ms=100,
            completed_at=datetime.now(UTC),
        )

    def test_compare_two_results(self) -> None:
        r1 = self._make_result(ExecutionProvider.LOCAL_SIMULATOR, "sim", {"00": 500, "11": 500}, 1000)
        r2 = self._make_result(ExecutionProvider.IBM_RUNTIME, "ibm", {"00": 480, "11": 520}, 1000)
        comparison = compare_results("test-exp", [r1, r2])
        assert len(comparison.fidelity_scores) == 2
        assert len(comparison.distribution_distances) == 2
        assert comparison.total_duration_ms == 200
        assert comparison.experiment_name == "test-exp"

    def test_compare_single_result(self) -> None:
        r1 = self._make_result(ExecutionProvider.LOCAL_SIMULATOR, "sim", {"0": 1024}, 1024)
        comparison = compare_results("single", [r1])
        assert comparison.fidelity_scores["local_simulator:sim"] == 1.0
        assert comparison.distribution_distances["local_simulator:sim"] == 0.0

    def test_compare_with_reference(self) -> None:
        r1 = self._make_result(ExecutionProvider.LOCAL_SIMULATOR, "sim", {"00": 500, "11": 500}, 1000)
        ref = {"00": 0.5, "11": 0.5}
        comparison = compare_results("ref-test", [r1], reference=ref)
        assert comparison.fidelity_scores["local_simulator:sim"] == 1.0

    def test_empty_results(self) -> None:
        comparison = compare_results("empty", [])
        assert len(comparison.results) == 0
        assert comparison.total_duration_ms == 0
