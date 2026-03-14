from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db_session
from app.repositories.api_keys import ApiKeyRepository

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db_session():
        yield session


async def get_redis() -> AsyncGenerator[Redis, None]:
    redis = Redis.from_url(settings.redis_url)
    try:
        yield redis
    finally:
        await redis.close()


async def require_api_key(
    api_key: str | None = Security(_api_key_header),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Dependency that validates the X-API-Key header against the database."""
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key")
    repo = ApiKeyRepository(session)
    model = await repo.get_by_raw_key(api_key)
    if model is None:
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")
    await repo.touch(model.id)
    await session.commit()

