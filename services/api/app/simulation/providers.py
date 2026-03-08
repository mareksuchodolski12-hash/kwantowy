from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from quantum_contracts import CircuitPayload, ExecutionProvider, ExecutionResult


class ProviderJobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ProviderErrorClass(str, Enum):
    TRANSIENT = "transient"
    PERMANENT = "permanent"


@dataclass(slots=True)
class ProviderSubmitResult:
    remote_run_id: str


class ProviderExecutionError(Exception):
    def __init__(self, message: str, error_class: ProviderErrorClass):
        super().__init__(message)
        self.error_class = error_class


class ExecutionProviderAdapter(ABC):
    provider: ExecutionProvider

    @abstractmethod
    async def submit(self, payload: CircuitPayload, correlation_id: str) -> ProviderSubmitResult:
        raise NotImplementedError

    @abstractmethod
    async def poll_status(self, remote_run_id: str) -> ProviderJobStatus:
        raise NotImplementedError

    @abstractmethod
    async def fetch_result(
        self,
        remote_run_id: str,
        payload: CircuitPayload,
        timeout_seconds: int,
        job_id: str,
    ) -> ExecutionResult:
        raise NotImplementedError

    def classify_error(self, _: Exception) -> ProviderErrorClass:
        return ProviderErrorClass.PERMANENT
