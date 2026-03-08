import json
from typing import Any, cast
from uuid import UUID

from redis.asyncio import Redis

from app.core.config import settings
from app.core.observability import queue_depth_gauge


class RedisQueue:
    def __init__(self, redis: Redis):
        self.redis = redis

    async def enqueue_job(self, job_id: UUID, correlation_id: str) -> None:
        message = json.dumps({"job_id": str(job_id), "correlation_id": correlation_id})
        await cast(Any, self.redis.rpush(settings.queue_name, message))
        await self.observe_depth()

    async def dequeue(self, timeout: int = 5) -> tuple[str, str] | None:
        payload = await cast(Any, self.redis.blpop(settings.queue_name, timeout=timeout))
        await self.observe_depth()
        if not payload:
            return None
        raw = payload[1].decode("utf-8")
        message = json.loads(raw)
        return message["job_id"], message["correlation_id"]

    async def observe_depth(self) -> None:
        depth = await cast(Any, self.redis.llen(settings.queue_name))
        queue_depth_gauge.set(float(depth))
