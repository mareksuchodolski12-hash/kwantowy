import asyncio
import logging
import time
from datetime import UTC, datetime
from uuid import UUID

from quantum_contracts import CircuitPayload, ExecutionProvider, JobState
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.observability import (
    execution_duration_seconds,
    job_retries_total,
    jobs_failed_total,
    jobs_succeeded_total,
    poll_backoff_seconds,
    poll_cycles_total,
    poll_latency_seconds,
    provider_errors_total,
    queue_latency_seconds,
)
from app.db.models import ExperimentModel, JobModel
from app.domain.state_machine import InvalidStateTransition
from app.queue.redis_queue import RedisQueue
from app.repositories.audit import AuditRepository
from app.repositories.jobs import JobRepository
from app.repositories.results import ResultRepository
from app.services.provider_factory import get_provider
from app.simulation.providers import (
    ExecutionProviderAdapter,
    ProviderErrorClass,
    ProviderJobStatus,
)

logger = logging.getLogger(__name__)


class WorkerService:
    def __init__(self, session: AsyncSession, queue: RedisQueue):
        self.session = session
        self.jobs = JobRepository(session)
        self.results = ResultRepository(session)
        self.audit = AuditRepository(session)
        self.queue = queue

    async def process_job(self, job_id: str, correlation_id: str) -> None:
        parsed_job_id = UUID(job_id)
        job_model = await self.session.scalar(select(JobModel).where(JobModel.id == parsed_job_id))
        if job_model is None:
            return

        provider = ExecutionProvider(job_model.provider)
        try:
            await self.jobs.transition(job_model.id, JobState.RUNNING)
        except InvalidStateTransition:
            return

        await self.jobs.increment_attempt(job_model.id)
        if job_model.queued_at:
            queued_at = job_model.queued_at
            if queued_at.tzinfo is None:
                queued_at = queued_at.replace(tzinfo=UTC)
            queue_latency_seconds.labels(provider=provider.value).observe(
                max((datetime.now(UTC) - queued_at).total_seconds(), 0)
            )

        exp = await self.session.scalar(select(ExperimentModel).where(ExperimentModel.id == job_model.experiment_id))
        if exp is None:
            await self.jobs.transition(job_model.id, JobState.FAILED)
            await self.session.commit()
            return

        payload = CircuitPayload(qasm=exp.circuit_qasm, shots=exp.shots)
        adapter = get_provider(provider)

        try:
            remote_run_id = job_model.remote_run_id
            if not remote_run_id:
                submit = await adapter.submit(payload, correlation_id)
                remote_run_id = submit.remote_run_id
                await self.jobs.set_remote_run_id(job_model.id, remote_run_id)
                await self.audit.log(
                    aggregate_type="job",
                    aggregate_id=job_model.id,
                    event_type="provider.submitted",
                    payload={"provider": provider.value, "remote_run_id": remote_run_id},
                    correlation_id=correlation_id,
                )

            status = await self._poll_until_terminal(adapter, remote_run_id, provider, correlation_id, job_model.id)
            if status != ProviderJobStatus.SUCCEEDED:
                raise RuntimeError(f"provider terminal status: {status.value}")

            result = await self.results.get_by_job_id(job_model.id)
            if result is None:
                fetched = await adapter.fetch_result(
                    remote_run_id,
                    payload,
                    job_model.timeout_seconds,
                    str(job_model.id),
                )
                result = await self.results.save(fetched)

            await self.jobs.transition(job_model.id, JobState.SUCCEEDED)
            await self.audit.log(
                aggregate_type="job",
                aggregate_id=job_model.id,
                event_type="job.succeeded",
                payload={"duration_ms": result.duration_ms, "provider": provider.value},
                correlation_id=correlation_id,
            )
            await self.session.commit()
            execution_duration_seconds.labels(provider=provider.value).observe(result.duration_ms / 1000)
            jobs_succeeded_total.labels(provider=provider.value).inc()
            logger.info("job succeeded", extra={"correlation_id": correlation_id, "job_id": str(job_id)})
        except Exception as exc:  # noqa: BLE001
            error_class = adapter.classify_error(exc)
            provider_errors_total.labels(provider=provider.value, error_class=error_class.value).inc()
            await self._handle_failure(job_model, correlation_id, provider, str(exc), error_class)

    async def _poll_until_terminal(
        self,
        adapter: ExecutionProviderAdapter,
        remote_run_id: str,
        provider: ExecutionProvider,
        correlation_id: str,
        job_id: UUID,
    ) -> ProviderJobStatus:
        delay = settings.ibm_poll_initial_delay_seconds
        started = time.monotonic()
        previous_status: ProviderJobStatus | None = None

        while True:
            if time.monotonic() - started > settings.ibm_poll_timeout_seconds:
                raise TimeoutError("provider poll timeout budget exceeded")

            poll_started = time.monotonic()
            status = await adapter.poll_status(remote_run_id)
            poll_latency_seconds.labels(provider=provider.value).observe(time.monotonic() - poll_started)
            poll_cycles_total.labels(provider=provider.value).inc()

            if previous_status != status:
                await self.audit.log(
                    aggregate_type="job",
                    aggregate_id=job_id,
                    event_type="provider.status",
                    payload={"provider": provider.value, "status": status.value, "remote_run_id": remote_run_id},
                    correlation_id=correlation_id,
                )
                previous_status = status

            if status in {ProviderJobStatus.SUCCEEDED, ProviderJobStatus.FAILED}:
                return status

            poll_backoff_seconds.labels(provider=provider.value).observe(delay)
            await asyncio.sleep(delay)
            delay = min(delay * 2, settings.ibm_poll_max_delay_seconds)

    async def _handle_failure(
        self,
        job_model: JobModel,
        correlation_id: str,
        provider: ExecutionProvider,
        reason: str,
        error_class: ProviderErrorClass,
    ) -> None:
        refreshed = await self.session.get(JobModel, job_model.id)
        if refreshed is None:
            return

        should_retry = error_class == ProviderErrorClass.TRANSIENT and refreshed.attempts < refreshed.max_attempts
        if should_retry:
            await self.jobs.transition(refreshed.id, JobState.FAILED)
            await self.jobs.transition(refreshed.id, JobState.QUEUED)
            await self.queue.enqueue_job(refreshed.id, correlation_id)
            await self.audit.log(
                aggregate_type="job",
                aggregate_id=refreshed.id,
                event_type="job.retry_scheduled",
                payload={
                    "attempts": refreshed.attempts,
                    "reason": reason,
                    "provider": provider.value,
                    "error_class": error_class.value,
                },
                correlation_id=correlation_id,
            )
            job_retries_total.labels(provider=provider.value).inc()
        else:
            await self.jobs.transition(refreshed.id, JobState.FAILED)
            await self.audit.log(
                aggregate_type="job",
                aggregate_id=refreshed.id,
                event_type="job.failed",
                payload={
                    "attempts": refreshed.attempts,
                    "reason": reason,
                    "provider": provider.value,
                    "error_class": error_class.value,
                },
                correlation_id=correlation_id,
            )
            jobs_failed_total.labels(provider=provider.value).inc()

        await self.session.commit()
