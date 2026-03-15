from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ExperimentModel(Base):
    __tablename__ = "experiments"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    circuit_qasm: Mapped[str] = mapped_column(Text, nullable=False)
    shots: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    jobs: Mapped[list["JobModel"]] = relationship(back_populates="experiment")
    versions: Mapped[list["ExperimentVersionModel"]] = relationship(back_populates="experiment")


class JobModel(Base):
    __tablename__ = "jobs"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    experiment_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("experiments.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False, default="local_simulator")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    correlation_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True, unique=True)
    remote_run_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    queued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    experiment: Mapped[ExperimentModel] = relationship(back_populates="jobs")
    result: Mapped["ResultModel | None"] = relationship(back_populates="job", uselist=False)


class ResultModel(Base):
    __tablename__ = "results"

    job_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("jobs.id"), primary_key=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    backend: Mapped[str] = mapped_column(String(64), nullable=False)
    result_payload: Mapped[dict[str, int]] = mapped_column(JSON, nullable=False)
    shots: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    circuit_depth: Mapped[int | None] = mapped_column(Integer, nullable=True)
    qubit_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gate_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    job: Mapped[JobModel] = relationship(back_populates="result")


class AuditEventModel(Base):
    __tablename__ = "audit_events"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    aggregate_type: Mapped[str] = mapped_column(String(32), nullable=False)
    aggregate_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    payload: Mapped[dict[str, str | int | float | bool | None]] = mapped_column(JSON, nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ApiKeyModel(Base):
    __tablename__ = "api_keys"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    key_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# ---------------------------------------------------------------------------
# Experiment versioning (component 4)
# ---------------------------------------------------------------------------


class ExperimentVersionModel(Base):
    __tablename__ = "experiment_versions"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    experiment_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("experiments.id"), index=True, nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    circuit_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    circuit_qasm: Mapped[str] = mapped_column(Text, nullable=False)
    optimisation_params: Mapped[dict[str, str | int | float | bool | None]] = mapped_column(
        JSON, nullable=False, default=dict
    )
    provider: Mapped[str | None] = mapped_column(String(32), nullable=True)
    seed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    parent_version_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    experiment: Mapped[ExperimentModel] = relationship(back_populates="versions")


# ---------------------------------------------------------------------------
# Provider benchmarking (component 2)
# ---------------------------------------------------------------------------


class BenchmarkModel(Base):
    __tablename__ = "benchmarks"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    provider: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    fidelity: Mapped[float] = mapped_column(Float, nullable=False)
    avg_gate_error: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    readout_error: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    queue_time_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    execution_time_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    qubit_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


# ---------------------------------------------------------------------------
# Workflow orchestration (component 5)
# ---------------------------------------------------------------------------


class WorkflowModel(Base):
    __tablename__ = "workflows"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    definition: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class WorkflowRunModel(Base):
    __tablename__ = "workflow_runs"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    workflow_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("workflows.id"), index=True)
    state: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    current_step: Mapped[str | None] = mapped_column(String(128), nullable=True)
    step_results: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


# ---------------------------------------------------------------------------
# Cost governance (component 7)
# ---------------------------------------------------------------------------


class BudgetModel(Base):
    __tablename__ = "budgets"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    scope: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    scope_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    monthly_limit_usd: Mapped[float] = mapped_column(Float, nullable=False)
    current_spend_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    alert_threshold_pct: Mapped[float] = mapped_column(Float, nullable=False, default=80.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CostRecordModel(Base):
    __tablename__ = "cost_records"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    job_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("jobs.id"), index=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    shots: Mapped[int] = mapped_column(Integer, nullable=False)
    cost_usd: Mapped[float] = mapped_column(Float, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


# ---------------------------------------------------------------------------
# Multi-tenant platform (component 9)
# ---------------------------------------------------------------------------


class OrganisationModel(Base):
    __tablename__ = "organisations"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    teams: Mapped[list["TeamModel"]] = relationship(back_populates="organisation")


class TeamModel(Base):
    __tablename__ = "teams"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    org_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("organisations.id"), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    organisation: Mapped[OrganisationModel] = relationship(back_populates="teams")
    projects: Mapped[list["ProjectModel"]] = relationship(back_populates="team")


class ProjectModel(Base):
    __tablename__ = "projects"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    team_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("teams.id"), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    team: Mapped[TeamModel] = relationship(back_populates="projects")
