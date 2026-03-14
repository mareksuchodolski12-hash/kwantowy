import asyncio
import time
from datetime import UTC, datetime

from qiskit.qasm2 import loads
from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit_ibm_runtime import SamplerV2 as Sampler
from quantum_contracts import CircuitPayload, ExecutionProvider, ExecutionResult

from app.core.config import settings
from app.simulation.providers import ExecutionProviderAdapter


class IbmRuntimeAdapter(ExecutionProviderAdapter):
    provider = ExecutionProvider.IBM_RUNTIME

    def __init__(self) -> None:
        if not settings.ibm_runtime_token:
            raise ValueError("IBM Runtime token is required when provider is enabled")
        self.service = QiskitRuntimeService(
            channel=settings.ibm_runtime_channel,
            token=settings.ibm_runtime_token,
            instance=settings.ibm_runtime_instance,
        )

    async def run(self, payload: CircuitPayload, timeout_seconds: int, job_id: str) -> ExecutionResult:
        started = time.monotonic()
        circuit = loads(payload.qasm)

        def _run() -> tuple[dict[str, int], str]:
            backend = self.service.backend(settings.ibm_runtime_backend)
            sampler = Sampler(mode=backend)
            job = sampler.run([circuit], shots=payload.shots)
            result = job.result(timeout=timeout_seconds)
            data = result[0].data.c.get_counts()
            return {str(k): int(v) for k, v in data.items()}, job.job_id()

        counts, remote_id = await asyncio.wait_for(asyncio.to_thread(_run), timeout=timeout_seconds)
        return ExecutionResult(
            job_id=job_id,
            provider=self.provider,
            backend=settings.ibm_runtime_backend,
            counts=counts,
            shots=payload.shots,
            duration_ms=int((time.monotonic() - started) * 1000),
            completed_at=datetime.now(UTC),
            remote_run_id=remote_id,
        )
