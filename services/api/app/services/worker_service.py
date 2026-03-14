import logging
from datetime import UTC, datetime

from quantum_contracts import CircuitPayload, ExecutionProvider, JobState
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.observability import (
    execution_duration_seconds,
    job_retries_total,
    jobs_failed_total,
    jobs_succeeded_total,
    queue_latency_seconds,
)
from app.db.models import ExperimentModel, JobModel
from app.domain.state_machine import InvalidStateTransition
from app.queue.redis_queue import RedisQueue
from app.repositories.audit import AuditRepository
from app.repositories.jobs import JobRepository
from app.repositories.results import ResultRepository
from app.services.provider_factory import get_provider

logger = logging.getLogger(__name__)


class WorkerService:
    def __init__(self, session: AsyncSession, queue: RedisQueue):
        self.session = session
        self.jobs = JobRepository(session)
        self.results = ResultRepository(session)
        self.audit = AuditRepository(session)
        self.queue = queue

    async def process_job(self, job_id: str, correlation_id: str) -> None:
        job_model = await self.session.scalar(select(JobModel).where(JobModel.id == job_id))
        if job_model is None:
            await self.queue.ack(job_id, correlation_id)
            return
        provider = ExecutionProvider(job_model.provider)
        try:
            await self.jobs.transition(job_model.id, JobState.RUNNING)
        except InvalidStateTransition:
            await self.queue.ack(job_id, correlation_id)
            return

        await self.jobs.increment_attempt(job_model.id)
        if job_model.queued_at:
            queue_latency_seconds.labels(provider=provider.value).observe(
                max((datetime.now(UTC) - job_model.queued_at).total_seconds(), 0)
            )

        exp = await self.session.scalar(select(ExperimentModel).where(ExperimentModel.id == job_model.experiment_id))
        if exp is None:
            await self.jobs.transition(job_model.id, JobState.FAILED)
            await self.session.commit()
            await self.queue.ack(job_id, correlation_id)
            return

        payload = CircuitPayload(qasm=exp.circuit_qasm, shots=exp.shots)
        adapter = get_provider(provider)
        try:
            result = await adapter.run(payload, job_model.timeout_seconds, str(job_model.id))
            if result.remote_run_id:
                await self.jobs.set_remote_run_id(job_model.id, result.remote_run_id)
            await self.results.save(result)
            await self.jobs.transition(job_model.id, JobState.SUCCEEDED)
            await self.audit.log(
                aggregate_type="job",
                aggregate_id=job_model.id,
                event_type="job.succeeded",
                payload={"duration_ms": result.duration_ms, "provider": provider.value},
                correlation_id=correlation_id,
            )
            await self.session.commit()
            await self.queue.ack(job_id, correlation_id)
            execution_duration_seconds.labels(provider=provider.value).observe(result.duration_ms / 1000)
            jobs_succeeded_total.labels(provider=provider.value).inc()
            logger.info(
                "job succeeded",
                extra={"correlation_id": correlation_id, "job_id": str(job_id), "provider": provider.value},
            )
        except TimeoutError:
            await self._handle_failure(job_model, correlation_id, provider, "timeout")
        except Exception as exc:  # noqa: BLE001
            await self._handle_failure(job_model, correlation_id, provider, str(exc))

    async def _handle_failure(
        self,
        job_model: JobModel,
        correlation_id: str,
        provider: ExecutionProvider,
        reason: str,
    ) -> None:
        refreshed = await self.session.get(JobModel, job_model.id)
        if refreshed is None:
            await self.queue.ack(str(job_model.id), correlation_id)
            return
        if refreshed.attempts < refreshed.max_attempts:
            await self.jobs.transition(refreshed.id, JobState.FAILED)
            await self.jobs.transition(refreshed.id, JobState.QUEUED)
            await self.queue.enqueue_job(refreshed.id, correlation_id)
            await self.audit.log(
                aggregate_type="job",
                aggregate_id=refreshed.id,
                event_type="job.retry_scheduled",
                payload={"attempts": refreshed.attempts, "reason": reason, "provider": provider.value},
                correlation_id=correlation_id,
            )
            await self.session.commit()
            await self.queue.ack(str(job_model.id), correlation_id)
            job_retries_total.labels(provider=provider.value).inc()
            logger.warning(
                "job retry scheduled",
                extra={"correlation_id": correlation_id, "job_id": str(job_model.id), "provider": provider.value},
            )
        else:
            await self.jobs.transition(refreshed.id, JobState.FAILED)
            await self.audit.log(
                aggregate_type="job",
                aggregate_id=refreshed.id,
                event_type="job.failed",
                payload={"attempts": refreshed.attempts, "reason": reason, "provider": provider.value},
                correlation_id=correlation_id,
            )
            await self.session.commit()
            await self.queue.move_to_dlq(str(job_model.id), correlation_id, reason)
            jobs_failed_total.labels(provider=provider.value).inc()
            logger.error(
                "job failed permanently",
                extra={"correlation_id": correlation_id, "job_id": str(job_model.id), "provider": provider.value},
            )
