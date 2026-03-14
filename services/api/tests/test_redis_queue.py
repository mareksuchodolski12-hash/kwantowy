"""Tests for RedisQueue ack, dlq, and visibility timeout operations."""

import json
from typing import Any, cast

import fakeredis.aioredis
import pytest

from app.core.config import settings
from app.queue.redis_queue import RedisQueue


@pytest.fixture
def redis() -> fakeredis.aioredis.FakeRedis:
    return fakeredis.aioredis.FakeRedis()


@pytest.fixture
def queue(redis: fakeredis.aioredis.FakeRedis) -> RedisQueue:
    return RedisQueue(redis)


@pytest.mark.asyncio
async def test_enqueue_dequeue_roundtrip(queue: RedisQueue) -> None:
    from uuid import uuid4

    job_id = uuid4()
    correlation_id = "corr-1"
    await queue.enqueue_job(job_id, correlation_id)

    item = await queue.dequeue(timeout=1)
    assert item is not None
    assert item[0] == str(job_id)
    assert item[1] == correlation_id


@pytest.mark.asyncio
async def test_dequeue_returns_none_when_empty(queue: RedisQueue) -> None:
    item = await queue.dequeue(timeout=1)
    assert item is None


@pytest.mark.asyncio
async def test_ack_removes_from_processing_set(queue: RedisQueue, redis: fakeredis.aioredis.FakeRedis) -> None:
    from uuid import uuid4

    job_id = uuid4()
    correlation_id = "corr-ack"
    await queue.enqueue_job(job_id, correlation_id)
    item = await queue.dequeue(timeout=1)
    assert item is not None

    # Item should be in the processing set
    processing_key = settings.queue_name + ".processing"
    size_before = await redis.zcard(processing_key)
    assert size_before == 1

    await queue.ack(str(job_id), correlation_id)

    size_after = await redis.zcard(processing_key)
    assert size_after == 0


@pytest.mark.asyncio
async def test_move_to_dlq(queue: RedisQueue, redis: fakeredis.aioredis.FakeRedis) -> None:
    from uuid import uuid4

    job_id = uuid4()
    correlation_id = "corr-dlq"
    await queue.enqueue_job(job_id, correlation_id)
    await queue.dequeue(timeout=1)

    await queue.move_to_dlq(str(job_id), correlation_id, "permanent failure")

    # Should be removed from processing set
    processing_key = settings.queue_name + ".processing"
    assert await redis.zcard(processing_key) == 0

    # Should be in DLQ
    dlq_key = settings.queue_name + ".dlq"
    dlq_len = cast(int, await cast(Any, redis.llen(dlq_key)))
    assert dlq_len == 1

    raw = await cast(Any, redis.lpop(dlq_key))
    assert raw is not None
    entry = json.loads(raw)
    assert entry["job_id"] == str(job_id)
    assert entry["reason"] == "permanent failure"


@pytest.mark.asyncio
async def test_dlq_length(queue: RedisQueue) -> None:
    from uuid import uuid4

    assert await queue.dlq_length() == 0

    job_id = uuid4()
    await queue.enqueue_job(job_id, "corr")
    await queue.dequeue(timeout=1)
    await queue.move_to_dlq(str(job_id), "corr", "error")

    assert await queue.dlq_length() == 1


@pytest.mark.asyncio
async def test_requeue_timed_out(queue: RedisQueue, redis: fakeredis.aioredis.FakeRedis) -> None:
    from uuid import uuid4

    job_id = uuid4()
    correlation_id = "corr-timeout"
    await queue.enqueue_job(job_id, correlation_id)
    await queue.dequeue(timeout=1)

    # Manually backdate the processing set score so the item appears stale.
    processing_key = settings.queue_name + ".processing"
    members = await redis.zrange(processing_key, 0, -1)
    assert len(members) == 1
    # Set score to 0 (epoch) so it's definitely past cutoff
    await redis.zadd(processing_key, {members[0]: 0})

    count = await queue.requeue_timed_out(visibility_timeout_seconds=1)
    assert count == 1

    # Processing set should be empty
    assert await redis.zcard(processing_key) == 0

    # Should be back in the main queue
    item = await queue.dequeue(timeout=1)
    assert item is not None
    assert item[0] == str(job_id)
