from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from quantum_contracts import (
    CircuitPayload,
    ExecutionProvider,
    ExecutionResult,
    Experiment,
    Job,
    RetryPolicy,
)


class SubmitExperimentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    provider: ExecutionProvider = ExecutionProvider.LOCAL_SIMULATOR
    circuit: CircuitPayload
    retry_policy: RetryPolicy = RetryPolicy()


class SubmitExperimentResponse(BaseModel):
    experiment: Experiment
    job: Job


class JobListResponse(BaseModel):
    jobs: list[Job]


class ResultResponse(BaseModel):
    result: ExecutionResult


class ApiKeyCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)


class ApiKeyCreateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    name: str
    key: str
    created_at: datetime


class ApiKeyListItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    name: str
    is_active: bool
    created_at: datetime
    last_used_at: datetime | None


class ApiKeyListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    keys: list[ApiKeyListItem]
