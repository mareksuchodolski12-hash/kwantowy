from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException
from quantum_contracts import Job, ProviderCapabilities, ProviderRouteRequest, ProviderRouteResponse
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_redis, get_session, require_api_key
from app.core.correlation import get_correlation_id
from app.domain.schemas import (
    ApiKeyCreateRequest,
    ApiKeyCreateResponse,
    ApiKeyListItem,
    ApiKeyListResponse,
    JobListResponse,
    ResultResponse,
    SubmitExperimentRequest,
    SubmitExperimentResponse,
)
from app.queue.redis_queue import RedisQueue
from app.repositories.api_keys import ApiKeyRepository
from app.services.job_service import JobService, not_found
from app.services.provider_registry import get_provider_registry

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


# ---------------------------------------------------------------------------
# API key management
# ---------------------------------------------------------------------------


@router.post("/v1/api-keys", response_model=ApiKeyCreateResponse, status_code=201)
async def create_api_key(
    body: ApiKeyCreateRequest,
    session: AsyncSession = Depends(get_session),
) -> ApiKeyCreateResponse:
    """Generate a new API key. The raw key is returned once and cannot be retrieved again."""
    repo = ApiKeyRepository(session)
    raw, model = await repo.create(body.name)
    await session.commit()
    return ApiKeyCreateResponse(id=model.id, name=model.name, key=raw, created_at=model.created_at)


@router.get("/v1/api-keys", response_model=ApiKeyListResponse, dependencies=[Depends(require_api_key)])
async def list_api_keys(
    session: AsyncSession = Depends(get_session),
) -> ApiKeyListResponse:
    repo = ApiKeyRepository(session)
    models = await repo.list()
    return ApiKeyListResponse(
        keys=[
            ApiKeyListItem(
                id=m.id,
                name=m.name,
                is_active=m.is_active,
                created_at=m.created_at,
                last_used_at=m.last_used_at,
            )
            for m in models
        ]
    )


@router.delete("/v1/api-keys/{key_id}", status_code=204, dependencies=[Depends(require_api_key)])
async def revoke_api_key(
    key_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> None:
    repo = ApiKeyRepository(session)
    revoked = await repo.revoke(key_id)
    if not revoked:
        raise HTTPException(status_code=404, detail="API key not found")
    await session.commit()


# ---------------------------------------------------------------------------
# Experiments / Jobs
# ---------------------------------------------------------------------------


async def _submit(
    body: SubmitExperimentRequest,
    idempotency_key: str | None,
    session: AsyncSession,
    redis: Redis,
) -> SubmitExperimentResponse:
    service = JobService(session, RedisQueue(redis))
    return await service.submit(body, idempotency_key)


@router.post(
    "/v1/jobs",
    response_model=SubmitExperimentResponse,
    dependencies=[Depends(require_api_key)],
)
async def submit_job(
    body: SubmitExperimentRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
) -> SubmitExperimentResponse:
    return await _submit(body, idempotency_key, session, redis)


@router.post(
    "/v1/experiments",
    response_model=SubmitExperimentResponse,
    status_code=201,
    dependencies=[Depends(require_api_key)],
)
async def create_experiment(
    body: SubmitExperimentRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
) -> SubmitExperimentResponse:
    """Alias for POST /v1/jobs with 201 Created."""
    return await _submit(body, idempotency_key, session, redis)


@router.get("/v1/jobs/{job_id}", dependencies=[Depends(require_api_key)])
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


@router.get("/v1/jobs", response_model=JobListResponse, dependencies=[Depends(require_api_key)])
async def list_jobs(
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
) -> JobListResponse:
    service = JobService(session, RedisQueue(redis))
    return JobListResponse(jobs=await service.list_jobs())


async def _get_result(
    job_id: str,
    session: AsyncSession,
    redis: Redis,
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


@router.get(
    "/v1/jobs/{job_id}/result",
    response_model=ResultResponse,
    dependencies=[Depends(require_api_key)],
)
async def get_job_result(
    job_id: str,
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
) -> ResultResponse:
    return await _get_result(job_id, session, redis)


@router.get(
    "/v1/results/{job_id}",
    response_model=ResultResponse,
    dependencies=[Depends(require_api_key)],
)
async def get_result(
    job_id: str,
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
) -> ResultResponse:
    """Alias for GET /v1/jobs/{job_id}/result."""
    return await _get_result(job_id, session, redis)


# ---------------------------------------------------------------------------
# Provider Registry
# ---------------------------------------------------------------------------


@router.get(
    "/v1/providers",
    response_model=list[ProviderCapabilities],
    dependencies=[Depends(require_api_key)],
)
async def list_providers() -> list[ProviderCapabilities]:
    """List all registered quantum execution providers with capabilities."""
    registry = get_provider_registry()
    return registry.list_capabilities()


@router.post(
    "/v1/providers/select",
    response_model=ProviderRouteResponse,
    dependencies=[Depends(require_api_key)],
)
async def select_provider(body: ProviderRouteRequest) -> ProviderRouteResponse:
    """Select the best provider for the given circuit requirements."""
    registry = get_provider_registry()
    return registry.select(body)
