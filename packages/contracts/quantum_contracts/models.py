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


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    correlation_id: str


class AuditEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    aggregate_type: str
    aggregate_id: UUID
    event_type: str
    payload: dict[str, str | int | float | bool | None]
    correlation_id: str
    created_at: datetime
