import asyncio
import logging
import signal
import time
from datetime import UTC, datetime, timedelta

from quantum_contracts import JobState
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings
from app.db.models import JobModel
from app.domain.state_machine import InvalidStateTransition
from app.queue.redis_queue import RedisQueue
from app.repositories.jobs import JobRepository
from app.services.worker_service import WorkerService

logger = logging.getLogger(__name__)

_shutdown = False

# How often (seconds) the worker checks for timed-out messages in the processing set.
_REQUEUE_INTERVAL_SECONDS = 60


def _handle_signal(sig: int, frame: object) -> None:
    global _shutdown
    logger.info("Received signal %s – initiating graceful shutdown", sig)
    _shutdown = True


async def recover_stuck_jobs(session_factory: async_sessionmaker, queue: RedisQueue) -> None:  # type: ignore[type-arg]
    """Transition RUNNING jobs left over from a previous crash back to QUEUED.

    Also re-enqueues any messages stuck in the processing set beyond the
    visibility timeout (covers crashes that happened after dequeue but
    before ack).
    """
    cutoff = datetime.now(UTC) - timedelta(seconds=settings.stuck_job_timeout_seconds)
    async with session_factory() as session:
        rows = await session.scalars(
            select(JobModel).where(
                JobModel.status == "running",
                JobModel.updated_at < cutoff,
            )
        )
        stuck = list(rows)
        jobs_repo = JobRepository(session)
        for job in stuck:
            logger.warning("Recovering stuck job %s", job.id)
            try:
                await jobs_repo.transition(job.id, JobState.FAILED)
                await jobs_repo.transition(job.id, JobState.QUEUED)
            except InvalidStateTransition:
                logger.error("Cannot recover job %s – invalid state %s", job.id, job.status)
                continue
            # Commit before enqueue so the worker always finds the updated row.
            await session.commit()
            await queue.enqueue_job(job.id, job.correlation_id)

    # Re-enqueue messages stuck in the processing sorted set.
    requeued = await queue.requeue_timed_out(settings.stuck_job_timeout_seconds)
    if requeued:
        logger.info("Re-enqueued %d timed-out messages from processing set", requeued)


async def run() -> None:
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    redis = Redis.from_url(settings.redis_url)
    queue = RedisQueue(redis)
    engine = create_async_engine(settings.database_url, future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    logger.info("Worker starting – recovering any stuck jobs")
    await recover_stuck_jobs(session_factory, queue)

    logger.info("Worker ready – polling queue")
    last_requeue_check = time.monotonic()
    while not _shutdown:
        item = await queue.dequeue(timeout=5)
        if not item:
            # Periodically re-enqueue timed-out messages from the processing set.
            if time.monotonic() - last_requeue_check >= _REQUEUE_INTERVAL_SECONDS:
                try:
                    requeued = await queue.requeue_timed_out(settings.stuck_job_timeout_seconds)
                    if requeued:
                        logger.info("Re-enqueued %d timed-out messages", requeued)
                except Exception:
                    logger.exception("Error during requeue_timed_out")
                last_requeue_check = time.monotonic()
            continue
        job_id, correlation_id = item
        try:
            async with session_factory() as session:
                worker = WorkerService(session, queue)
                await worker.process_job(job_id, correlation_id)
        except Exception:
            logger.exception("Unhandled error processing job %s", job_id)

    logger.info("Worker shutdown complete")
    await redis.aclose()
    await engine.dispose()


if __name__ == "__main__":
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
    )
    asyncio.run(run())
