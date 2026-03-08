from abc import ABC, abstractmethod

from quantum_contracts import CircuitPayload, ExecutionProvider, ExecutionResult


class ExecutionProviderAdapter(ABC):
    provider: ExecutionProvider

    @abstractmethod
    async def run(self, payload: CircuitPayload, timeout_seconds: int, job_id: str) -> ExecutionResult:
        raise NotImplementedError

    async def poll(self, remote_run_id: str) -> tuple[bool, ExecutionResult | None]:
        return True, None
