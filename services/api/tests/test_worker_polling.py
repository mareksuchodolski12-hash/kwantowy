from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import fakeredis.aioredis
import pytest
from quantum_contracts import CircuitPayload, ExecutionProvider, ExecutionResult, JobState
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.models import ResultModel
from app.domain.schemas import SubmitExperimentRequest
from app.queue.redis_queue import RedisQueue
from app.services.job_service import JobService
from app.services.worker_service import WorkerService
from app.simulation.providers import ProviderErrorClass, ProviderJobStatus, ProviderSubmitResult

TEST_DB = "sqlite+aiosqlite:///./test_worker_polling.db"
QASM = 'OPENQASM 2.0; include "qelib1.inc"; qreg q[1]; creg c[1]; h q[0]; measure q[0] -> c[0];'


@pytest.fixture(scope="module", autouse=True)
def cleanup_db() -> None:
    path = Path("test_worker_polling.db")
    if path.exists():
        path.unlink()


@pytest.mark.asyncio
async def test_polling_backoff_and_idempotent_result_ingestion(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = create_async_engine(TEST_DB, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    redis = fakeredis.aioredis.FakeRedis()
    queue = RedisQueue(redis)

    class PollingAdapter:
        def __init__(self) -> None:
            self.poll_calls = 0

        async def submit(self, payload: CircuitPayload, correlation_id: str) -> ProviderSubmitResult:
            return ProviderSubmitResult(remote_run_id=f"remote-{correlation_id}")

        async def poll_status(self, remote_run_id: str) -> ProviderJobStatus:
            _ = remote_run_id
            self.poll_calls += 1
            if self.poll_calls == 1:
                return ProviderJobStatus.QUEUED
            if self.poll_calls == 2:
                return ProviderJobStatus.RUNNING
            return ProviderJobStatus.SUCCEEDED

        async def fetch_result(
            self,
            remote_run_id: str,
            payload: CircuitPayload,
            timeout_seconds: int,
            job_id: str,
        ) -> ExecutionResult:
            _ = (remote_run_id, timeout_seconds)
            return ExecutionResult(
                job_id=job_id,
                provider=ExecutionProvider.IBM_RUNTIME,
                backend="ibm_qasm",
                counts={"0": payload.shots // 2, "1": payload.shots // 2},
                shots=payload.shots,
                duration_ms=42,
                completed_at=datetime.now(UTC),
            )

        def classify_error(self, exc: Exception) -> ProviderErrorClass:
            _ = exc
            return ProviderErrorClass.TRANSIENT

    adapter = PollingAdapter()
    monkeypatch.setattr("app.services.worker_service.get_provider", lambda _provider: adapter)

    backoffs: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        backoffs.append(seconds)

    monkeypatch.setattr("app.services.worker_service.asyncio.sleep", fake_sleep)

    async with session_factory() as session:
        service = JobService(session, queue)
        response = await service.submit(
            SubmitExperimentRequest(
                name="remote-success",
                provider=ExecutionProvider.IBM_RUNTIME,
                circuit=CircuitPayload(qasm=QASM, shots=16),
            ),
            idempotency_key=str(uuid4()),
        )

    item = await queue.dequeue(timeout=1)
    assert item is not None

    async with session_factory() as session:
        worker = WorkerService(session, queue)
        await worker.process_job(item[0], item[1])

    # duplicate processing should not duplicate result row
    async with session_factory() as session:
        worker = WorkerService(session, queue)
        await worker.process_job(item[0], item[1])

    async with session_factory() as session:
        service = JobService(session, queue)
        job = await service.get_job(response.job.id)
        assert job is not None
        assert job.status == JobState.SUCCEEDED
        assert job.remote_run_id is not None

        count_rows = await session.scalar(select(func.count()).select_from(ResultModel))
        assert count_rows == 1

    assert backoffs == [2.0, 4.0]


@pytest.mark.asyncio
async def test_transient_error_retries_and_fails_after_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = create_async_engine(TEST_DB, future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    redis = fakeredis.aioredis.FakeRedis()
    queue = RedisQueue(redis)

    class FailingAdapter:
        async def submit(self, payload: CircuitPayload, correlation_id: str) -> ProviderSubmitResult:
            _ = (payload, correlation_id)
            return ProviderSubmitResult(remote_run_id="r-fail")

        async def poll_status(self, remote_run_id: str) -> ProviderJobStatus:
            _ = remote_run_id
            raise TimeoutError("poll timeout")

        async def fetch_result(
            self,
            remote_run_id: str,
            payload: CircuitPayload,
            timeout_seconds: int,
            job_id: str,
        ) -> ExecutionResult:
            raise AssertionError("should not fetch result")

        def classify_error(self, exc: Exception) -> ProviderErrorClass:
            _ = exc
            return ProviderErrorClass.TRANSIENT

    monkeypatch.setattr("app.services.worker_service.get_provider", lambda _provider: FailingAdapter())

    async def fake_sleep(_seconds: float) -> None:
        return None

    monkeypatch.setattr("app.services.worker_service.asyncio.sleep", fake_sleep)

    async with session_factory() as session:
        service = JobService(session, queue)
        response = await service.submit(
            SubmitExperimentRequest(
                name="remote-fail",
                provider=ExecutionProvider.IBM_RUNTIME,
                circuit=CircuitPayload(qasm=QASM, shots=4),
                retry_policy={"max_attempts": 1, "timeout_seconds": 5},
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
