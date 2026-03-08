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
