"""Auto-benchmark worker.

Periodically runs calibration circuits against every registered provider,
stores results, and updates provider ranking metrics.

Usage:
    PYTHONPATH=services/api python workers/benchmark-runner/benchmark_worker.py
"""

from __future__ import annotations

import asyncio
import logging
import signal

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings
from app.services.benchmarking import BenchmarkingService, update_benchmark_metrics
from quantum_contracts import ExecutionProvider

logger = logging.getLogger(__name__)

_shutdown = False

# Run benchmarks every 5 minutes by default.
_INTERVAL_SECONDS = int(__import__("os").environ.get("QCP_BENCHMARK_INTERVAL", "300"))

# Simulated calibration parameters per provider.
_PROVIDER_PARAMS: dict[str, dict[str, float | int]] = {
    ExecutionProvider.LOCAL_SIMULATOR.value: {
        "fidelity": 0.99,
        "gate_error": 0.001,
        "readout_error": 0.005,
        "queue_time": 0.0,
        "execution_time_ms": 30,
        "qubit_count": 2,
    },
    ExecutionProvider.SIMULATOR_AER.value: {
        "fidelity": 0.98,
        "gate_error": 0.002,
        "readout_error": 0.01,
        "queue_time": 0.5,
        "execution_time_ms": 45,
        "qubit_count": 2,
    },
    ExecutionProvider.IBM_RUNTIME.value: {
        "fidelity": 0.95,
        "gate_error": 0.005,
        "readout_error": 0.02,
        "queue_time": 15.0,
        "execution_time_ms": 200,
        "qubit_count": 2,
    },
    ExecutionProvider.IONQ.value: {
        "fidelity": 0.96,
        "gate_error": 0.004,
        "readout_error": 0.015,
        "queue_time": 30.0,
        "execution_time_ms": 350,
        "qubit_count": 2,
    },
    ExecutionProvider.RIGETTI.value: {
        "fidelity": 0.93,
        "gate_error": 0.008,
        "readout_error": 0.025,
        "queue_time": 20.0,
        "execution_time_ms": 280,
        "qubit_count": 2,
    },
}


def _handle_signal(sig: int, frame: object) -> None:
    global _shutdown
    logger.info("Received signal %s – shutting down benchmark worker", sig)
    _shutdown = True


async def run_calibration_cycle(session_factory: async_sessionmaker) -> None:  # type: ignore[type-arg]
    """Execute one calibration cycle for all providers."""
    async with session_factory() as session:
        svc = BenchmarkingService(session)
        for provider in ExecutionProvider:
            params = _PROVIDER_PARAMS.get(provider.value, {})
            if not params:
                continue
            try:
                await svc.run_calibration(
                    provider,
                    fidelity=float(params.get("fidelity", 0.95)),
                    gate_error=float(params.get("gate_error", 0.005)),
                    readout_error=float(params.get("readout_error", 0.01)),
                    queue_time=float(params.get("queue_time", 0.0)),
                    execution_time_ms=int(params.get("execution_time_ms", 100)),
                    qubit_count=int(params.get("qubit_count", 2)),
                )
            except Exception:
                logger.exception("Benchmark failed for %s", provider.value)
        await session.commit()

        benchmarks = await svc.get_all_latest()
        update_benchmark_metrics(benchmarks)
        logger.info("Benchmark cycle complete – %d providers updated", len(benchmarks))


async def run() -> None:
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    engine = create_async_engine(settings.database_url, future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    logger.info("Benchmark worker starting – interval=%ds", _INTERVAL_SECONDS)
    while not _shutdown:
        try:
            await run_calibration_cycle(session_factory)
        except Exception:
            logger.exception("Error in benchmark cycle")
        for _ in range(_INTERVAL_SECONDS):
            if _shutdown:
                break
            await asyncio.sleep(1)

    logger.info("Benchmark worker shutdown complete")
    await engine.dispose()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())
