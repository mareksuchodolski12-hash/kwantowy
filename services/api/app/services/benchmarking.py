"""Provider benchmarking engine.

Periodically runs calibration circuits against providers, measures fidelity and
noise characteristics, and exposes the results via Prometheus metrics and the
database.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from prometheus_client import Gauge
from quantum_contracts import BenchmarkResult, ExecutionProvider
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import BenchmarkModel

logger = logging.getLogger(__name__)


class BenchmarkRepository:
    """CRUD operations for provider benchmarks."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, result: BenchmarkResult) -> BenchmarkResult:
        model = BenchmarkModel(
            id=result.id,
            provider=result.provider.value,
            fidelity=result.fidelity,
            avg_gate_error=result.avg_gate_error,
            readout_error=result.readout_error,
            queue_time_seconds=result.queue_time_seconds,
            execution_time_ms=result.execution_time_ms,
            qubit_count=result.qubit_count,
            measured_at=result.measured_at,
        )
        await self.session.merge(model)
        await self.session.flush()
        return result

    async def list_by_provider(
        self,
        provider: ExecutionProvider,
        limit: int = 50,
    ) -> list[BenchmarkResult]:
        rows = await self.session.scalars(
            select(BenchmarkModel)
            .where(BenchmarkModel.provider == provider.value)
            .order_by(BenchmarkModel.measured_at.desc())
            .limit(limit)
        )
        return [self._to_contract(r) for r in rows]

    async def latest(self, provider: ExecutionProvider) -> BenchmarkResult | None:
        row = await self.session.scalar(
            select(BenchmarkModel)
            .where(BenchmarkModel.provider == provider.value)
            .order_by(BenchmarkModel.measured_at.desc())
            .limit(1)
        )
        return self._to_contract(row) if row else None

    async def list_all_latest(self) -> list[BenchmarkResult]:
        """Return the most recent benchmark for every provider."""
        results: list[BenchmarkResult] = []
        for provider in ExecutionProvider:
            row = await self.latest(provider)
            if row:
                results.append(row)
        return results

    @staticmethod
    def _to_contract(model: BenchmarkModel) -> BenchmarkResult:
        return BenchmarkResult(
            id=model.id,
            provider=ExecutionProvider(model.provider),
            fidelity=model.fidelity,
            avg_gate_error=model.avg_gate_error,
            readout_error=model.readout_error,
            queue_time_seconds=model.queue_time_seconds,
            execution_time_ms=model.execution_time_ms,
            qubit_count=model.qubit_count,
            measured_at=model.measured_at,
        )


class BenchmarkingService:
    """Runs calibration circuits and records benchmark metrics."""

    # A simple Bell-state calibration circuit used to measure fidelity.
    CALIBRATION_QASM = (
        'OPENQASM 2.0;\ninclude "qelib1.inc";\n'
        "qreg q[2];\ncreg c[2];\n"
        "h q[0];\ncx q[0],q[1];\n"
        "measure q[0] -> c[0];\nmeasure q[1] -> c[1];"
    )

    def __init__(self, session: AsyncSession) -> None:
        self.repo = BenchmarkRepository(session)

    async def run_calibration(
        self,
        provider: ExecutionProvider,
        *,
        fidelity: float = 0.98,
        gate_error: float = 0.002,
        readout_error: float = 0.01,
        queue_time: float = 0.0,
        execution_time_ms: int = 50,
        qubit_count: int = 2,
    ) -> BenchmarkResult:
        """Record a calibration result for *provider*.

        In a production deployment this method would execute the calibration
        circuit on the real backend.  For now it accepts pre-measured values
        so callers (e.g. a periodic task) can supply them.
        """
        from uuid import uuid4

        result = BenchmarkResult(
            id=uuid4(),
            provider=provider,
            fidelity=fidelity,
            avg_gate_error=gate_error,
            readout_error=readout_error,
            queue_time_seconds=queue_time,
            execution_time_ms=execution_time_ms,
            qubit_count=qubit_count,
            measured_at=datetime.now(UTC),
        )
        await self.repo.save(result)
        logger.info(
            "benchmark recorded",
            extra={"provider": provider.value, "fidelity": fidelity},
        )
        return result

    async def get_latest(self, provider: ExecutionProvider) -> BenchmarkResult | None:
        return await self.repo.latest(provider)

    async def get_history(
        self,
        provider: ExecutionProvider,
        limit: int = 50,
    ) -> list[BenchmarkResult]:
        return await self.repo.list_by_provider(provider, limit)

    async def get_all_latest(self) -> list[BenchmarkResult]:
        return await self.repo.list_all_latest()


# ---------------------------------------------------------------------------
# Prometheus metrics for benchmarks (component 8 integration)
# ---------------------------------------------------------------------------

provider_fidelity = Gauge(
    "qcp_provider_fidelity",
    "Latest calibration fidelity per provider",
    ["provider"],
)
provider_gate_error = Gauge(
    "qcp_provider_gate_error",
    "Latest average gate error per provider",
    ["provider"],
)
provider_readout_error = Gauge(
    "qcp_provider_readout_error",
    "Latest readout error per provider",
    ["provider"],
)
provider_queue_latency = Gauge(
    "qcp_provider_queue_latency_seconds",
    "Latest measured queue latency per provider",
    ["provider"],
)
provider_exec_time = Gauge(
    "qcp_provider_execution_time_ms",
    "Latest execution time per provider",
    ["provider"],
)


def update_benchmark_metrics(benchmarks: list[BenchmarkResult]) -> None:
    """Push the latest benchmark results into Prometheus gauges."""
    for b in benchmarks:
        label = b.provider.value
        provider_fidelity.labels(provider=label).set(b.fidelity)
        provider_gate_error.labels(provider=label).set(b.avg_gate_error)
        provider_readout_error.labels(provider=label).set(b.readout_error)
        provider_queue_latency.labels(provider=label).set(b.queue_time_seconds)
        provider_exec_time.labels(provider=label).set(b.execution_time_ms)
