from datetime import UTC, datetime
from uuid import UUID

from quantum_contracts import ExecutionProvider, Job, JobState
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import JobModel
from app.domain.state_machine import ensure_transition


class JobRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        experiment_id: UUID,
        provider: ExecutionProvider,
        correlation_id: str,
        max_attempts: int,
        timeout_seconds: int,
        idempotency_key: str | None,
    ) -> Job:
        now = datetime.now(UTC)
        model = JobModel(
            experiment_id=experiment_id,
            status=JobState.SUBMITTED.value,
            provider=provider.value,
            attempts=0,
            max_attempts=max_attempts,
            timeout_seconds=timeout_seconds,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
            submitted_at=now,
            created_at=now,
            updated_at=now,
        )
        self.session.add(model)
        await self.session.flush()
        return self._to_contract(model)

    async def get(self, job_id: UUID) -> Job | None:
        model = await self.session.scalar(select(JobModel).where(JobModel.id == job_id))
        return self._to_contract(model) if model else None

    async def get_by_idempotency_key(self, key: str) -> Job | None:
        model = await self.session.scalar(select(JobModel).where(JobModel.idempotency_key == key))
        return self._to_contract(model) if model else None

    async def list(self, limit: int = 50, offset: int = 0) -> list[Job]:
        rows = await self.session.scalars(
            select(JobModel).order_by(JobModel.created_at.desc()).offset(offset).limit(limit)
        )
        return [self._to_contract(m) for m in rows]

    async def transition(self, job_id: UUID, next_state: JobState) -> Job:
        model = await self.session.scalar(
            select(JobModel).where(JobModel.id == job_id).with_for_update()
        )
        if model is None:
            raise ValueError("job not found")
        ensure_transition(JobState(model.status), next_state)
        model.status = next_state.value
        if next_state == JobState.QUEUED:
            model.queued_at = datetime.now(UTC)
        if next_state == JobState.RUNNING:
            model.started_at = datetime.now(UTC)
        model.updated_at = datetime.now(UTC)
        await self.session.flush()
        return self._to_contract(model)

    async def increment_attempt(self, job_id: UUID) -> Job:
        model = await self.session.scalar(
            select(JobModel).where(JobModel.id == job_id).with_for_update()
        )
        if model is None:
            raise ValueError("job not found")
        model.attempts += 1
        model.updated_at = datetime.now(UTC)
        await self.session.flush()
        return self._to_contract(model)

    async def set_remote_run_id(self, job_id: UUID, remote_run_id: str) -> None:
        model = await self.session.scalar(
            select(JobModel).where(JobModel.id == job_id).with_for_update()
        )
        if model is None:
            raise ValueError("job not found")
        model.remote_run_id = remote_run_id
        model.updated_at = datetime.now(UTC)
        await self.session.flush()

    def _to_contract(self, model: JobModel) -> Job:
        return Job(
            id=model.id,
            experiment_id=model.experiment_id,
            status=JobState(model.status),
            provider=ExecutionProvider(model.provider),
            attempts=model.attempts,
            correlation_id=model.correlation_id,
            idempotency_key=model.idempotency_key,
            remote_run_id=model.remote_run_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
