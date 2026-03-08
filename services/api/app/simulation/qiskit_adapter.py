import asyncio
import time
from datetime import UTC, datetime

from qiskit import transpile
from qiskit.providers.basic_provider import BasicProvider
from qiskit.qasm2 import loads
from quantum_contracts import CircuitPayload, ExecutionProvider, ExecutionResult

from app.simulation.providers import ExecutionProviderAdapter, ProviderJobStatus, ProviderSubmitResult


class LocalQiskitSimulator(ExecutionProviderAdapter):
    provider = ExecutionProvider.LOCAL_SIMULATOR

    async def submit(self, payload: CircuitPayload, correlation_id: str) -> ProviderSubmitResult:
        return ProviderSubmitResult(remote_run_id=f"local:{correlation_id}:{payload.shots}")

    async def poll_status(self, remote_run_id: str) -> ProviderJobStatus:
        _ = remote_run_id
        return ProviderJobStatus.SUCCEEDED

    async def fetch_result(
        self,
        remote_run_id: str,
        payload: CircuitPayload,
        timeout_seconds: int,
        job_id: str,
    ) -> ExecutionResult:
        _ = remote_run_id
        started = time.monotonic()
        circuit = loads(payload.qasm)
        backend = BasicProvider().get_backend("basic_simulator")
        compiled = transpile(circuit, backend)

        result = await asyncio.wait_for(
            asyncio.to_thread(lambda: backend.run(compiled, shots=payload.shots).result()),
            timeout=timeout_seconds,
        )
        counts = result.get_counts()
        duration_ms = int((time.monotonic() - started) * 1000)
        return ExecutionResult(
            job_id=job_id,
            provider=self.provider,
            backend="qiskit_basic_simulator",
            counts={str(k): int(v) for k, v in counts.items()},
            shots=payload.shots,
            duration_ms=duration_ms,
            completed_at=datetime.now(UTC),
        )
