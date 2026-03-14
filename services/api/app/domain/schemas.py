from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from quantum_contracts import (
    BenchmarkResult,
    Budget,
    CircuitPayload,
    ExecutionProvider,
    ExecutionResult,
    Experiment,
    ExperimentVersion,
    Job,
    OptimisationConfig,
    OptimisedCircuit,
    Organisation,
    Project,
    ResultComparison,
    RetryPolicy,
    Team,
    WorkflowDefinition,
    WorkflowRun,
)


class SubmitExperimentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    provider: ExecutionProvider = ExecutionProvider.LOCAL_SIMULATOR
    circuit: CircuitPayload
    retry_policy: RetryPolicy = RetryPolicy()
    optimisation: OptimisationConfig = OptimisationConfig()


class SubmitExperimentResponse(BaseModel):
    experiment: Experiment
    job: Job


class JobListResponse(BaseModel):
    jobs: list[Job]


class ExperimentListResponse(BaseModel):
    experiments: list[Experiment]


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


# ---------------------------------------------------------------------------
# Circuit optimisation
# ---------------------------------------------------------------------------


class OptimiseCircuitRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    circuit: CircuitPayload
    config: OptimisationConfig = OptimisationConfig()


class OptimiseCircuitResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result: OptimisedCircuit


# ---------------------------------------------------------------------------
# Experiment versioning
# ---------------------------------------------------------------------------


class CreateVersionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    circuit_qasm: str = Field(min_length=1)
    optimisation_params: dict[str, str | int | float | bool | None] = Field(default_factory=dict)
    provider: ExecutionProvider | None = None
    seed: int | None = None
    parent_version_id: UUID | None = None


class VersionListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    versions: list[ExperimentVersion]


# ---------------------------------------------------------------------------
# Workflow orchestration
# ---------------------------------------------------------------------------


class CreateWorkflowRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workflow: WorkflowDefinition


class WorkflowRunResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run: WorkflowRun


class WorkflowRunListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    runs: list[WorkflowRun]


# ---------------------------------------------------------------------------
# Result comparison
# ---------------------------------------------------------------------------


class CompareResultsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    experiment_name: str = Field(min_length=1)
    job_ids: list[UUID] = Field(min_length=1)
    reference_distribution: dict[str, float] | None = None


class CompareResultsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    comparison: ResultComparison


# ---------------------------------------------------------------------------
# Cost governance
# ---------------------------------------------------------------------------


class CreateBudgetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scope: str = Field(min_length=1, max_length=64)
    scope_id: str = Field(min_length=1, max_length=255)
    monthly_limit_usd: float = Field(ge=0.0)
    alert_threshold_pct: float = Field(default=80.0, ge=0.0, le=100.0)


class BudgetResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    budget: Budget


class BudgetListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    budgets: list[Budget]


# ---------------------------------------------------------------------------
# Multi-tenant platform
# ---------------------------------------------------------------------------


class CreateOrgRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)


class OrgResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    organisation: Organisation


class OrgListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    organisations: list[Organisation]


class CreateTeamRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)


class TeamResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    team: Team


class TeamListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    teams: list[Team]


class CreateProjectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project: Project


class ProjectListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    projects: list[Project]


# ---------------------------------------------------------------------------
# Benchmarking
# ---------------------------------------------------------------------------


class BenchmarkRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: ExecutionProvider
    fidelity: float = Field(default=0.98, ge=0.0, le=1.0)
    avg_gate_error: float = Field(default=0.002, ge=0.0)
    readout_error: float = Field(default=0.01, ge=0.0)
    queue_time_seconds: float = Field(default=0.0, ge=0.0)
    execution_time_ms: int = Field(default=50, ge=0)
    qubit_count: int = Field(default=2, ge=1)


class BenchmarkResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    benchmark: BenchmarkResult


class BenchmarkListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    benchmarks: list[BenchmarkResult]
