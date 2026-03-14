"""Tests for RedisQueue queue_length and processing_count methods."""

import fakeredis.aioredis
import pytest

from app.queue.redis_queue import RedisQueue


@pytest.fixture
def redis() -> fakeredis.aioredis.FakeRedis:
    return fakeredis.aioredis.FakeRedis()


@pytest.fixture
def queue(redis: fakeredis.aioredis.FakeRedis) -> RedisQueue:
    return RedisQueue(redis)


@pytest.mark.asyncio
async def test_queue_length_empty(queue: RedisQueue) -> None:
    assert await queue.queue_length() == 0


@pytest.mark.asyncio
async def test_queue_length_after_enqueue(queue: RedisQueue) -> None:
    from uuid import uuid4

    await queue.enqueue_job(uuid4(), "corr-1")
    await queue.enqueue_job(uuid4(), "corr-2")
    assert await queue.queue_length() == 2


@pytest.mark.asyncio
async def test_processing_count_empty(queue: RedisQueue) -> None:
    assert await queue.processing_count() == 0


@pytest.mark.asyncio
async def test_processing_count_after_dequeue(queue: RedisQueue) -> None:
    from uuid import uuid4

    await queue.enqueue_job(uuid4(), "corr")
    assert await queue.processing_count() == 0

    await queue.dequeue(timeout=1)
    assert await queue.processing_count() == 1


@pytest.mark.asyncio
async def test_processing_count_decreases_after_ack(queue: RedisQueue) -> None:
    from uuid import uuid4

    job_id = uuid4()
    await queue.enqueue_job(job_id, "corr")
    await queue.dequeue(timeout=1)
    assert await queue.processing_count() == 1

    await queue.ack(str(job_id), "corr")
    assert await queue.processing_count() == 0
