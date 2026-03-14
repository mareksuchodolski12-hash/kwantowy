"""Unit tests for WorkerService process_job and _handle_failure."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast
from uuid import UUID, uuid4

import fakeredis.aioredis
import pytest
from quantum_contracts import CircuitPayload, ExecutionProvider, ExecutionResult
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.models import ExperimentModel, JobModel
from app.queue.redis_queue import RedisQueue
from app.services.worker_service import WorkerService

TEST_DB = "sqlite+aiosqlite:///./test_worker.db"

QASM = 'OPENQASM 2.0; include "qelib1.inc"; qreg q[1]; creg c[1]; x q[0]; measure q[0] -> c[0];'


@pytest.fixture(scope="module", autouse=True)
def cleanup_db() -> None:
    path = Path("test_worker.db")
    if path.exists():
        path.unlink()


@pytest.fixture
async def engine() -> Any:
    eng = create_async_engine(TEST_DB, future=True)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest.fixture
def session_factory(engine: Any) -> Any:
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest.fixture
def fake_redis() -> fakeredis.aioredis.FakeRedis:
    return fakeredis.aioredis.FakeRedis()


@pytest.fixture
def queue(fake_redis: fakeredis.aioredis.FakeRedis) -> RedisQueue:
    return RedisQueue(fake_redis)


async def _seed_job(
    session: AsyncSession,
    *,
    status: str = "queued",
    max_attempts: int = 3,
    provider: str = "local_simulator",
) -> tuple[ExperimentModel, JobModel]:
    """Insert an experiment + job row for testing.

    Note: queued_at is left as None to avoid timezone-naive datetime issues
    with SQLite (which strips tzinfo).  In production PostgreSQL preserves it.
    """
    from datetime import UTC, datetime

    now = datetime.now(UTC)
    exp = ExperimentModel(
        name="test-exp",
        circuit_qasm=QASM,
        shots=8,
        created_at=now,
    )
    session.add(exp)
    await session.flush()

    job = JobModel(
        experiment_id=exp.id,
        status=status,
        provider=provider,
        attempts=0,
        max_attempts=max_attempts,
        timeout_seconds=30,
        correlation_id="corr-test",
        submitted_at=now,
        queued_at=None,
        created_at=now,
        updated_at=now,
    )
    session.add(job)
    await session.flush()
    await session.commit()
    return exp, job


# ---------------------------------------------------------------------------
# process_job: missing job → ack
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_process_missing_job_acks(session_factory: Any, queue: RedisQueue, fake_redis: Any) -> None:
    """If the job row is missing, the worker should ack the message."""
    missing_id = str(uuid4())
    # Enqueue + dequeue to populate the processing set with the correct key.
    await queue.enqueue_job(UUID(missing_id), "corr")
    await queue.dequeue(timeout=1)

    async with session_factory() as session:
        worker = WorkerService(session, queue)
        await worker.process_job(missing_id, "corr")

    # Processing set should be empty after ack
    from app.core.config import settings

    assert await fake_redis.zcard(settings.queue_name + ".processing") == 0


# ---------------------------------------------------------------------------
# process_job: commits RUNNING before execution
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_running_state_committed_before_execution(
    session_factory: Any, queue: RedisQueue, monkeypatch: pytest.MonkeyPatch
) -> None:
    """RUNNING state must be committed so it's visible to other queries."""
    observed_statuses: list[str] = []

    from datetime import UTC, datetime

    class SpyAdapter:
        async def run(self, payload: CircuitPayload, timeout_seconds: int, job_id: str) -> ExecutionResult:
            # During execution, query the job in a separate session to check committed status.
            async with session_factory() as check_session:
                from sqlalchemy import select

                row = await check_session.scalar(select(JobModel).where(JobModel.id == UUID(job_id)))
                if row:
                    observed_statuses.append(row.status)
            return ExecutionResult(
                job_id=job_id,
                provider=ExecutionProvider.LOCAL_SIMULATOR,
                backend="test",
                counts={"1": 8},
                shots=8,
                duration_ms=1,
                completed_at=datetime.now(UTC),
            )

    monkeypatch.setattr("app.services.worker_service.get_provider", lambda _: SpyAdapter())

    async with session_factory() as session:
        exp, job = await _seed_job(session, status="queued")
        job_id = str(job.id)
        await queue.enqueue_job(job.id, "corr")
        await queue.dequeue(timeout=1)

    async with session_factory() as session:
        worker = WorkerService(session, queue)
        await worker.process_job(job_id, "corr")

    assert observed_statuses == ["running"], f"Expected RUNNING committed during execution, got {observed_statuses}"


# ---------------------------------------------------------------------------
# _handle_failure: retry commits before enqueue
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_retry_commits_before_enqueue(
    session_factory: Any, queue: RedisQueue, fake_redis: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """On retriable failure the DB must be committed to QUEUED before the message is enqueued."""

    class FailingAdapter:
        async def run(self, payload: CircuitPayload, timeout_seconds: int, job_id: str) -> ExecutionResult:
            raise RuntimeError("boom")

    monkeypatch.setattr("app.services.worker_service.get_provider", lambda _: FailingAdapter())

    async with session_factory() as session:
        exp, job = await _seed_job(session, status="queued", max_attempts=2)
        job_id = str(job.id)
        await queue.enqueue_job(job.id, "corr")
        await queue.dequeue(timeout=1)

    async with session_factory() as session:
        worker = WorkerService(session, queue)
        await worker.process_job(job_id, "corr")

    # Job should now be in QUEUED state in the DB (committed)
    async with session_factory() as session:
        from sqlalchemy import select

        row = await session.scalar(select(JobModel).where(JobModel.id == UUID(job_id)))
        assert row is not None
        assert row.status == "queued"

    # A new message should be in the queue
    from app.core.config import settings

    queue_len = cast(int, await cast(Any, fake_redis.llen(settings.queue_name)))
    assert queue_len >= 1


# ---------------------------------------------------------------------------
# _handle_failure: permanent failure goes to DLQ
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_permanent_failure_goes_to_dlq(
    session_factory: Any, queue: RedisQueue, fake_redis: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    class FailingAdapter:
        async def run(self, payload: CircuitPayload, timeout_seconds: int, job_id: str) -> ExecutionResult:
            raise RuntimeError("permanent")

    monkeypatch.setattr("app.services.worker_service.get_provider", lambda _: FailingAdapter())

    async with session_factory() as session:
        exp, job = await _seed_job(session, status="queued", max_attempts=1)
        job_id = str(job.id)
        await queue.enqueue_job(job.id, "corr")
        await queue.dequeue(timeout=1)

    async with session_factory() as session:
        worker = WorkerService(session, queue)
        await worker.process_job(job_id, "corr")

    # Job should be permanently FAILED
    async with session_factory() as session:
        from sqlalchemy import select

        row = await session.scalar(select(JobModel).where(JobModel.id == UUID(job_id)))
        assert row is not None
        assert row.status == "failed"

    # Should be in DLQ
    assert await queue.dlq_length() >= 1
