import asyncio
import logging
import signal

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings
from app.queue.redis_queue import RedisQueue
from app.services.worker_service import WorkerService

logger = logging.getLogger(__name__)

_shutdown = False


def _handle_signal(sig: int, frame: object) -> None:
    global _shutdown
    logger.info("Received signal %s – initiating graceful shutdown", sig)
    _shutdown = True


async def recover_stuck_jobs(session_factory: async_sessionmaker) -> None:  # type: ignore[type-arg]
    """Transition RUNNING jobs left over from a previous crash back to QUEUED."""
    from datetime import UTC, datetime, timedelta

    from sqlalchemy import select

    from app.db.models import JobModel
    from app.queue.redis_queue import RedisQueue as _RedisQueue

    redis = Redis.from_url(settings.redis_url)
    queue = _RedisQueue(redis)
    cutoff = datetime.now(UTC) - timedelta(seconds=settings.stuck_job_timeout_seconds)
    async with session_factory() as session:
        rows = await session.scalars(
            select(JobModel).where(
                JobModel.status == "running",
                JobModel.updated_at < cutoff,
            )
        )
        stuck = list(rows)
        for job in stuck:
            logger.warning("Recovering stuck job %s", job.id)
            job.status = "queued"
            from datetime import UTC

            job.updated_at = datetime.now(UTC)
            await queue.enqueue_job(job.id, job.correlation_id)
        if stuck:
            await session.commit()
    await redis.aclose()


async def run() -> None:
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    redis = Redis.from_url(settings.redis_url)
    queue = RedisQueue(redis)
    engine = create_async_engine(settings.database_url, future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    logger.info("Worker starting – recovering any stuck jobs")
    await recover_stuck_jobs(session_factory)

    logger.info("Worker ready – polling queue")
    while not _shutdown:
        item = await queue.dequeue(timeout=5)
        if not item:
            continue
        job_id, correlation_id = item
        async with session_factory() as session:
            worker = WorkerService(session, queue)
            await worker.process_job(job_id, correlation_id)

    logger.info("Worker shutdown complete")
    await redis.aclose()
    await engine.dispose()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())
