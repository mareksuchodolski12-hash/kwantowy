import json
from typing import Any, cast
from uuid import UUID

from redis.asyncio import Redis

from app.core.config import settings


class RedisQueue:
    def __init__(self, redis: Redis):
        self.redis = redis

    async def enqueue_job(self, job_id: UUID, correlation_id: str) -> None:
        message = json.dumps({"job_id": str(job_id), "correlation_id": correlation_id})
        await cast(Any, self.redis.rpush(settings.queue_name, message))

    async def dequeue(self, timeout: int = 5) -> tuple[str, str] | None:
        payload = await cast(Any, self.redis.blpop(settings.queue_name, timeout=timeout))
        if not payload:
            return None
        raw = payload[1].decode("utf-8")
        message = json.loads(raw)
        return message["job_id"], message["correlation_id"]
