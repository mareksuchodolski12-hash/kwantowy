from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException
from quantum_contracts import Job
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_redis, get_session
from app.core.correlation import get_correlation_id
from app.domain.schemas import (
    JobListResponse,
    ResultResponse,
    SubmitExperimentRequest,
    SubmitExperimentResponse,
)
from app.queue.redis_queue import RedisQueue
from app.services.job_service import JobService, not_found

router = APIRouter()


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readyz")
async def readyz(
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
) -> dict[str, str]:
    await session.execute(text("SELECT 1"))
    from typing import Any, cast

    await cast(Any, redis.ping())
    return {"status": "ready"}


@router.post("/v1/jobs", response_model=SubmitExperimentResponse)
async def submit_job(
    body: SubmitExperimentRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
) -> SubmitExperimentResponse:
    service = JobService(session, RedisQueue(redis))
    return await service.submit(body, idempotency_key)


@router.get("/v1/jobs/{job_id}")
async def get_job(
    job_id: str,
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
) -> Job:
    service = JobService(session, RedisQueue(redis))
    job = await service.get_job(UUID(job_id))
    if job is None:
        correlation_id = get_correlation_id()
        raise HTTPException(status_code=404, detail=not_found(correlation_id, "job").model_dump())
    return job


@router.get("/v1/jobs", response_model=JobListResponse)
async def list_jobs(
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
) -> JobListResponse:
    service = JobService(session, RedisQueue(redis))
    return JobListResponse(jobs=await service.list_jobs())


@router.get("/v1/jobs/{job_id}/result", response_model=ResultResponse)
async def get_job_result(
    job_id: str,
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
) -> ResultResponse:
    service = JobService(session, RedisQueue(redis))
    result = await service.get_result(UUID(job_id))
    if result is None:
        correlation_id = get_correlation_id()
        raise HTTPException(
            status_code=404,
            detail=not_found(correlation_id, "result").model_dump(),
        )
    return ResultResponse(result=result)
