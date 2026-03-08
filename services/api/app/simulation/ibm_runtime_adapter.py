import asyncio
import time
from datetime import UTC, datetime
from typing import cast

from qiskit.qasm2 import loads
from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit_ibm_runtime import SamplerV2 as Sampler
from qiskit_ibm_runtime.exceptions import IBMRuntimeError
from quantum_contracts import CircuitPayload, ExecutionProvider, ExecutionResult

from app.core.config import settings
from app.simulation.providers import (
    ExecutionProviderAdapter,
    ProviderErrorClass,
    ProviderJobStatus,
    ProviderSubmitResult,
)


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

    async def submit(self, payload: CircuitPayload, correlation_id: str) -> ProviderSubmitResult:
        _ = correlation_id
        circuit = loads(payload.qasm)

        def _submit() -> str:
            backend = self.service.backend(settings.ibm_runtime_backend)
            sampler = Sampler(mode=backend)
            job = sampler.run([circuit], shots=payload.shots)
            return cast(str, job.job_id())

        remote_run_id = await asyncio.to_thread(_submit)
        return ProviderSubmitResult(remote_run_id=remote_run_id)

    async def poll_status(self, remote_run_id: str) -> ProviderJobStatus:
        def _status() -> str:
            job = self.service.job(remote_run_id)
            return str(job.status()).upper()

        raw = await asyncio.to_thread(_status)
        if raw in {"QUEUED", "INITIALIZING", "VALIDATING"}:
            return ProviderJobStatus.QUEUED
        if raw in {"RUNNING"}:
            return ProviderJobStatus.RUNNING
        if raw in {"DONE", "COMPLETED"}:
            return ProviderJobStatus.SUCCEEDED
        return ProviderJobStatus.FAILED

    async def fetch_result(
        self,
        remote_run_id: str,
        payload: CircuitPayload,
        timeout_seconds: int,
        job_id: str,
    ) -> ExecutionResult:
        started = time.monotonic()

        def _fetch() -> dict[str, int]:
            job = self.service.job(remote_run_id)
            result = job.result(timeout=timeout_seconds)
            data = result[0].data.c.get_counts()
            return {str(k): int(v) for k, v in data.items()}

        counts = await asyncio.wait_for(asyncio.to_thread(_fetch), timeout=timeout_seconds)
        return ExecutionResult(
            job_id=job_id,
            provider=self.provider,
            backend=settings.ibm_runtime_backend,
            counts=counts,
            shots=payload.shots,
            duration_ms=int((time.monotonic() - started) * 1000),
            completed_at=datetime.now(UTC),
        )

    def classify_error(self, exc: Exception) -> ProviderErrorClass:
        if isinstance(exc, TimeoutError | IBMRuntimeError | ConnectionError):
            return ProviderErrorClass.TRANSIENT
        return ProviderErrorClass.PERMANENT
