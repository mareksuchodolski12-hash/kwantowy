import asyncio
from typing import Any, cast
from uuid import uuid4

import pytest
from quantum_contracts import CircuitPayload, JobState
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings
from app.db.base import Base
from app.domain.schemas import SubmitExperimentRequest
from app.queue.redis_queue import RedisQueue
from app.services.job_service import JobService
from app.services.worker_service import WorkerService


async def _is_ready() -> bool:
    try:
        redis = Redis.from_url(settings.redis_url)
        await cast(Any, redis.ping())
        await redis.close()
        engine = create_async_engine(settings.database_url, future=True)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        await engine.dispose()
        return True
    except Exception:
        return False


QASM = 'OPENQASM 2.0; include "qelib1.inc"; qreg q[1]; creg c[1]; h q[0]; measure q[0] -> c[0];'


@pytest.mark.integration
@pytest.mark.asyncio
async def test_end_to_end_async_execution() -> None:
    if not await _is_ready():
        pytest.skip("postgres/redis not available")
    engine = create_async_engine(settings.database_url, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    redis = Redis.from_url(settings.redis_url)
    queue = RedisQueue(redis)

    async with session_factory() as session:
        service = JobService(session, queue)
        response = await service.submit(
            SubmitExperimentRequest(name="it", circuit=CircuitPayload(qasm=QASM, shots=16)),
            idempotency_key=str(uuid4()),
        )
        job_id = response.job.id

    item = await queue.dequeue(timeout=1)
    assert item is not None

    async with session_factory() as session:
        worker = WorkerService(session, queue)
        await worker.process_job(item[0], item[1])

    async with session_factory() as session:
        service = JobService(session, queue)
        job = await service.get_job(job_id)
        result = await service.get_result(job_id)

    assert job is not None
    assert job.status == JobState.SUCCEEDED
    assert result is not None
    assert sum(result.counts.values()) == result.shots

    await redis.close()


@pytest.mark.asyncio
async def test_retry_to_failed(monkeypatch: pytest.MonkeyPatch) -> None:
    if not await _is_ready():
        pytest.skip("postgres/redis not available")
    engine = create_async_engine(settings.database_url, future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    redis = Redis.from_url(settings.redis_url)
    queue = RedisQueue(redis)

    class FailingAdapter:
        async def run(self, payload: CircuitPayload, timeout_seconds: int, job_id: str) -> object:
            raise TimeoutError("timeout")

    monkeypatch.setattr("app.services.worker_service.get_provider", lambda _provider: FailingAdapter())

    async with session_factory() as session:
        service = JobService(session, queue)
        response = await service.submit(
            SubmitExperimentRequest(
                name="fail",
                circuit=CircuitPayload(qasm=QASM, shots=4),
                retry_policy={"max_attempts": 1, "timeout_seconds": 1},
            ),
            idempotency_key=str(uuid4()),
        )

    item = await queue.dequeue(timeout=1)
    assert item is not None

    async with session_factory() as session:
        worker = WorkerService(session, queue)
        await worker.process_job(item[0], item[1])

    async with session_factory() as session:
        service = JobService(session, queue)
        job = await service.get_job(response.job.id)
        assert job is not None
        assert job.status == JobState.FAILED

    await redis.close()
    await asyncio.sleep(0)
