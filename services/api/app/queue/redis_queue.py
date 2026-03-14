import json
import time
from typing import Any, cast
from uuid import UUID

from redis.asyncio import Redis

from app.core.config import settings

_DLQ_SUFFIX = ".dlq"
_PROCESSING_SUFFIX = ".processing"


class RedisQueue:
    def __init__(self, redis: Redis):
        self.redis = redis

    @property
    def _processing_key(self) -> str:
        return settings.queue_name + _PROCESSING_SUFFIX

    @property
    def _dlq_key(self) -> str:
        return settings.queue_name + _DLQ_SUFFIX

    async def enqueue_job(self, job_id: UUID, correlation_id: str) -> None:
        message = json.dumps({"job_id": str(job_id), "correlation_id": correlation_id})
        await cast(Any, self.redis.rpush(settings.queue_name, message))

    async def dequeue(self, timeout: int = 5) -> tuple[str, str] | None:
        """Dequeue with visibility timeout using a processing sorted set."""
        payload = await cast(Any, self.redis.blpop(settings.queue_name, timeout=timeout))
        if not payload:
            return None
        raw = payload[1].decode("utf-8")
        # Track the item in the processing set with a timestamp for visibility timeout
        score = time.time()
        await cast(Any, self.redis.zadd(self._processing_key, {raw: score}))
        message = json.loads(raw)
        return message["job_id"], message["correlation_id"]

    async def ack(self, job_id: str, correlation_id: str) -> None:
        """Remove a successfully processed message from the processing set."""
        raw = json.dumps({"job_id": job_id, "correlation_id": correlation_id})
        await cast(Any, self.redis.zrem(self._processing_key, raw))

    async def move_to_dlq(self, job_id: str, correlation_id: str, reason: str) -> None:
        """Move a permanently-failed message to the dead-letter queue."""
        raw = json.dumps({"job_id": job_id, "correlation_id": correlation_id})
        dlq_entry = json.dumps({"job_id": job_id, "correlation_id": correlation_id, "reason": reason})
        await cast(Any, self.redis.zrem(self._processing_key, raw))
        await cast(Any, self.redis.rpush(self._dlq_key, dlq_entry))

    async def requeue_timed_out(self, visibility_timeout_seconds: int = 300) -> int:
        """Re-enqueue messages that have been in the processing set longer than the visibility timeout.

        Returns the number of messages re-enqueued.
        """
        cutoff = time.time() - visibility_timeout_seconds
        stale: list[bytes] = await cast(
            Any,
            self.redis.zrangebyscore(self._processing_key, "-inf", cutoff),
        )
        count = 0
        for raw in stale:
            await cast(Any, self.redis.zrem(self._processing_key, raw))
            await cast(Any, self.redis.rpush(settings.queue_name, raw))
            count += 1
        return count

    async def dlq_length(self) -> int:
        return cast(int, await cast(Any, self.redis.llen(self._dlq_key)))

