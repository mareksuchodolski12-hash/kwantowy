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


class OptimisationStrategy(str, Enum):
    """Circuit transpilation / optimisation strategies."""

    NONE = "none"
    LIGHT = "light"
    MEDIUM = "medium"
    HEAVY = "heavy"
    NOISE_AWARE = "noise_aware"


class WorkflowState(str, Enum):
    """Lifecycle states for a workflow run."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


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
    circuit_depth: int | None = None
    qubit_count: int | None = None
    gate_count: int | None = None


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
    estimated_fidelity: float = 1.0
    enabled: bool = True


class ProviderRouteRequest(BaseModel):
    """Request to select the best provider for a circuit."""

    model_config = ConfigDict(extra="forbid")

    qubit_count: int = Field(ge=1)
    shots: int = Field(default=1024, ge=1, le=10000)
    prefer_hardware: bool = False
    max_cost_usd: float | None = None
    min_fidelity: float | None = Field(default=None, ge=0.0, le=1.0)
    max_queue_seconds: float | None = None
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
    distribution_distances: dict[str, float] = Field(default_factory=dict)
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


# ---------------------------------------------------------------------------
# Circuit optimisation pipeline (component 1)
# ---------------------------------------------------------------------------


class OptimisationConfig(BaseModel):
    """Parameters controlling circuit optimisation before execution."""

    model_config = ConfigDict(extra="forbid")

    strategy: OptimisationStrategy = OptimisationStrategy.NONE
    target_backend: ExecutionProvider | None = None
    noise_aware_mapping: bool = False
    max_depth: int | None = Field(default=None, ge=1)
    shot_optimisation: bool = False
    seed: int | None = None


class OptimisedCircuit(BaseModel):
    """Result of circuit optimisation."""

    model_config = ConfigDict(extra="forbid")

    original_qasm: str
    optimised_qasm: str
    original_depth: int
    optimised_depth: int
    original_gate_count: int
    optimised_gate_count: int
    strategy_applied: OptimisationStrategy
    qubit_mapping: dict[int, int] = Field(default_factory=dict)
    estimated_fidelity: float = 1.0


# ---------------------------------------------------------------------------
# Provider benchmarking engine (component 2)
# ---------------------------------------------------------------------------


class BenchmarkResult(BaseModel):
    """Result of a single provider benchmark run."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    provider: ExecutionProvider
    fidelity: float = Field(ge=0.0, le=1.0)
    avg_gate_error: float = 0.0
    readout_error: float = 0.0
    queue_time_seconds: float = 0.0
    execution_time_ms: int = 0
    qubit_count: int = 0
    measured_at: datetime


# ---------------------------------------------------------------------------
# Experiment versioning (component 4)
# ---------------------------------------------------------------------------


class ExperimentVersion(BaseModel):
    """A single version within an experiment lineage."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    experiment_id: UUID
    version_number: int
    circuit_hash: str
    circuit_qasm: str
    optimisation_params: dict[str, str | int | float | bool | None] = Field(default_factory=dict)
    provider: ExecutionProvider | None = None
    seed: int | None = None
    parent_version_id: UUID | None = None
    created_at: datetime


# ---------------------------------------------------------------------------
# Workflow orchestration (component 5)
# ---------------------------------------------------------------------------


class WorkflowStep(BaseModel):
    """A single step in a workflow pipeline."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=128)
    action: str = Field(min_length=1, max_length=64)
    provider: ExecutionProvider | None = None
    params: dict[str, str | int | float | bool | None] = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list)


class WorkflowDefinition(BaseModel):
    """Declarative workflow definition."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    steps: list[WorkflowStep] = Field(min_length=1)
    circuit: CircuitPayload


class WorkflowRun(BaseModel):
    """Represents a running or completed workflow instance."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    workflow_name: str
    state: WorkflowState
    current_step: str | None = None
    step_results: dict[str, dict[str, str | int | float | bool | None]] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Cost governance (component 7)
# ---------------------------------------------------------------------------


class Budget(BaseModel):
    """Budget configuration for cost governance."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    scope: str = Field(min_length=1, max_length=64)
    scope_id: str = Field(min_length=1, max_length=255)
    monthly_limit_usd: float = Field(ge=0.0)
    current_spend_usd: float = Field(default=0.0, ge=0.0)
    alert_threshold_pct: float = Field(default=80.0, ge=0.0, le=100.0)
    created_at: datetime


class CostRecord(BaseModel):
    """A single cost entry for a job execution."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    job_id: UUID
    provider: ExecutionProvider
    shots: int
    cost_usd: float
    recorded_at: datetime


# ---------------------------------------------------------------------------
# Multi-tenant platform (component 9)
# ---------------------------------------------------------------------------


class Organisation(BaseModel):
    """Top-level tenant entity."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    name: str = Field(min_length=1, max_length=255)
    created_at: datetime


class Team(BaseModel):
    """Team within an organisation."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    org_id: UUID
    name: str = Field(min_length=1, max_length=255)
    created_at: datetime


class Project(BaseModel):
    """Project within a team."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    team_id: UUID
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    created_at: datetime
