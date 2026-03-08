import asyncio

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings
from app.queue.redis_queue import RedisQueue
from app.services.worker_service import WorkerService


async def run() -> None:
    redis = Redis.from_url(settings.redis_url)
    queue = RedisQueue(redis)
    engine = create_async_engine(settings.database_url, future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    while True:
        item = await queue.dequeue(timeout=5)
        if not item:
            continue
        job_id, correlation_id = item
        async with session_factory() as session:
            worker = WorkerService(session, queue)
            await worker.process_job(job_id, correlation_id)


if __name__ == "__main__":
    asyncio.run(run())
