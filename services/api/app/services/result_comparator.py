"""Result comparison engine.

Compares execution results across providers using metrics such as:

• fidelity scores
• distribution distance (total variation distance)
• execution time
"""

from __future__ import annotations

import logging
import math

from quantum_contracts import ExecutionResult, ResultComparison

logger = logging.getLogger(__name__)


def _normalise_counts(counts: dict[str, int], shots: int) -> dict[str, float]:
    """Convert raw counts to a probability distribution."""
    if shots <= 0:
        return {}
    return {k: v / shots for k, v in counts.items()}


def total_variation_distance(dist_a: dict[str, float], dist_b: dict[str, float]) -> float:
    """Total variation distance between two discrete distributions.

    TVD = 0.5 * Σ |P(x) - Q(x)|
    """
    all_keys = set(dist_a.keys()) | set(dist_b.keys())
    return 0.5 * sum(abs(dist_a.get(k, 0.0) - dist_b.get(k, 0.0)) for k in all_keys)


def hellinger_fidelity(dist_a: dict[str, float], dist_b: dict[str, float]) -> float:
    """Compute fidelity as (1 - H²) where H is the Hellinger distance.

    Returns a value in [0, 1] where 1 means identical distributions.
    """
    all_keys = set(dist_a.keys()) | set(dist_b.keys())
    bc = sum(math.sqrt(dist_a.get(k, 0.0) * dist_b.get(k, 0.0)) for k in all_keys)
    h_sq = max(0.0, 1.0 - bc)
    return 1.0 - h_sq


def compare_results(
    experiment_name: str,
    results: list[ExecutionResult],
    reference: dict[str, float] | None = None,
) -> ResultComparison:
    """Compare a set of execution results.

    If *reference* is provided it is used as the ideal distribution for
    fidelity scoring.  Otherwise the first result's distribution is used
    as the reference.

    Returns a :class:`ResultComparison` with fidelity scores and
    distribution distances keyed by ``provider:backend``.
    """
    if not results:
        return ResultComparison(experiment_name=experiment_name, results=[])

    ref_dist: dict[str, float]
    if reference is not None:
        ref_dist = reference
    else:
        first = results[0]
        ref_dist = _normalise_counts(first.counts, first.shots)

    fidelity_scores: dict[str, float] = {}
    distribution_distances: dict[str, float] = {}
    total_duration = 0

    for r in results:
        key = f"{r.provider.value}:{r.backend}"
        dist = _normalise_counts(r.counts, r.shots)
        fidelity_scores[key] = round(hellinger_fidelity(ref_dist, dist), 6)
        distribution_distances[key] = round(total_variation_distance(ref_dist, dist), 6)
        total_duration += r.duration_ms

    return ResultComparison(
        experiment_name=experiment_name,
        results=results,
        fidelity_scores=fidelity_scores,
        distribution_distances=distribution_distances,
        total_duration_ms=total_duration,
    )
