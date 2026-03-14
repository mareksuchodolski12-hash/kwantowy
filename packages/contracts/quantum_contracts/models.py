from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class JobState(str, Enum):
    SUBMITTED = "submitted"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ExecutionProvider(str, Enum):
    LOCAL_SIMULATOR = "local_simulator"
    IBM_RUNTIME = "ibm_runtime"
    IONQ = "ionq"
    RIGETTI = "rigetti"
    SIMULATOR_AER = "simulator_aer"


class CircuitPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    qasm: str = Field(min_length=1)
    shots: int = Field(default=1024, ge=1, le=10000)


class RetryPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_attempts: int = Field(default=3, ge=1, le=10)
    timeout_seconds: int = Field(default=30, ge=1, le=600)


class Experiment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    circuit: CircuitPayload
    created_at: datetime


class Job(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    experiment_id: UUID
    status: JobState
    provider: ExecutionProvider
    attempts: int = 0
    correlation_id: str
    idempotency_key: str | None = None
    remote_run_id: str | None = None
    created_at: datetime
    updated_at: datetime


class ExecutionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: UUID
    provider: ExecutionProvider
    backend: str
    counts: dict[str, int]
    shots: int
    duration_ms: int
    completed_at: datetime
    remote_run_id: str | None = None


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    correlation_id: str


class ProviderCapabilities(BaseModel):
    """Metadata describing a provider's capabilities and constraints."""

    model_config = ConfigDict(extra="forbid")

    provider: ExecutionProvider
    display_name: str
    max_qubits: int
    max_shots: int = 10000
    supports_mid_circuit_measurement: bool = False
    supports_dynamic_circuits: bool = False
    is_simulator: bool = True
    estimated_cost_per_shot_usd: float = 0.0
    avg_queue_time_seconds: float = 0.0
    enabled: bool = True


class ProviderRouteRequest(BaseModel):
    """Request to select the best provider for a circuit."""

    model_config = ConfigDict(extra="forbid")

    qubit_count: int = Field(ge=1)
    shots: int = Field(default=1024, ge=1, le=10000)
    prefer_hardware: bool = False
    max_cost_usd: float | None = None
    exclude_providers: list[ExecutionProvider] = Field(default_factory=list)


class ProviderRouteResponse(BaseModel):
    """Ranked list of providers suitable for a circuit."""

    model_config = ConfigDict(extra="forbid")

    recommended: ExecutionProvider
    alternatives: list[ExecutionProvider]
    reason: str


class ResultComparison(BaseModel):
    """Side-by-side comparison of execution results across providers."""

    model_config = ConfigDict(extra="forbid")

    experiment_name: str
    results: list[ExecutionResult]
    fidelity_scores: dict[str, float] = Field(default_factory=dict)
    total_duration_ms: int = 0


class AuditEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    aggregate_type: str
    aggregate_id: UUID
    event_type: str
    payload: dict[str, str | int | float | bool | None]
    correlation_id: str
    created_at: datetime
