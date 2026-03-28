import logging
from uuid import UUID

from quantum_contracts import ErrorResponse, ExecutionResult, Experiment, Job, JobState
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.correlation import get_correlation_id
from app.core.observability import jobs_submitted_total
from app.domain.schemas import SubmitExperimentRequest, SubmitExperimentResponse
from app.queue.redis_queue import RedisQueue
from app.repositories.audit import AuditRepository
from app.repositories.experiments import ExperimentRepository
from app.repositories.jobs import JobRepository
from app.repositories.results import ResultRepository

logger = logging.getLogger(__name__)


class JobService:
    def __init__(self, session: AsyncSession, queue: RedisQueue):
        self.session = session
        self.queue = queue
        self.experiments = ExperimentRepository(session)
        self.jobs = JobRepository(session)
        self.results = ResultRepository(session)
        self.audit = AuditRepository(session)

    async def submit(
        self,
        request: SubmitExperimentRequest,
        idempotency_key: str | None,
    ) -> SubmitExperimentResponse:
        correlation_id = get_correlation_id()

        if idempotency_key:
            existing_job = await self.jobs.get_by_idempotency_key(idempotency_key)
            if existing_job:
                existing_experiment = await self.experiments.get(existing_job.experiment_id)
                if existing_experiment is None:
                    raise ValueError("inconsistent idempotent job state")
                return SubmitExperimentResponse(experiment=existing_experiment, job=existing_job)

        experiment = await self.experiments.create(
            name=request.name,
            description=request.description,
            circuit=request.circuit,
        )
        job = await self.jobs.create(
            experiment_id=experiment.id,
            provider=request.provider,
            correlation_id=correlation_id,
            max_attempts=request.retry_policy.max_attempts,
            timeout_seconds=request.retry_policy.timeout_seconds,
            idempotency_key=idempotency_key,
        )
        await self.jobs.transition(job.id, JobState.QUEUED)
        await self.audit.log(
            aggregate_type="job",
            aggregate_id=job.id,
            event_type="job.queued",
            payload={"experiment_id": str(experiment.id), "provider": request.provider.value},
            correlation_id=correlation_id,
        )
        await self.session.commit()
        # Enqueue AFTER commit so the worker always finds the job in the database.
        await self.queue.enqueue_job(job.id, correlation_id)
        jobs_submitted_total.labels(provider=request.provider.value).inc()
        logger.info(
            "job submitted",
            extra={"correlation_id": correlation_id, "job_id": str(job.id), "provider": request.provider.value},
        )
        queued_job = await self.jobs.get(job.id)
        if queued_job is None:
            raise ValueError("job disappeared after commit")
        return SubmitExperimentResponse(experiment=experiment, job=queued_job)

    async def get_job(self, job_id: UUID) -> Job | None:
        return await self.jobs.get(job_id)

    async def list_jobs(self, limit: int = 50, offset: int = 0) -> list[Job]:
        return await self.jobs.list(limit=limit, offset=offset)

    async def list_experiments(self, limit: int = 50, offset: int = 0) -> list[Experiment]:
        return await self.experiments.list(limit=limit, offset=offset)

    async def get_experiment(self, experiment_id: UUID) -> Experiment | None:
        return await self.experiments.get(experiment_id)

    async def get_result(self, job_id: UUID) -> ExecutionResult | None:
        return await self.results.get_by_job_id(job_id)


def not_found(correlation_id: str, entity: str) -> ErrorResponse:
    return ErrorResponse(code="not_found", message=f"{entity} not found", correlation_id=correlation_id)
