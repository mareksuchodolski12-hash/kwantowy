"""Tests for idempotency key handling in job submission."""

from collections.abc import AsyncGenerator
from pathlib import Path

import fakeredis.aioredis
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_redis, get_session
from app.db.base import Base
from app.main import app

TEST_DB = "sqlite+aiosqlite:///./test_idempotency.db"


@pytest.fixture(scope="module", autouse=True)
def cleanup_db() -> None:
    path = Path("test_idempotency.db")
    if path.exists():
        path.unlink()


@pytest.fixture
def client() -> object:
    engine = create_async_engine(TEST_DB, future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    fake_redis = fakeredis.aioredis.FakeRedis()

    async def override_redis() -> AsyncGenerator[fakeredis.aioredis.FakeRedis, None]:
        yield fake_redis

    async def init_models() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    import asyncio

    asyncio.run(init_models())
    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_redis] = override_redis
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def api_key(client: TestClient) -> str:
    resp = client.post("/v1/api-keys", json={"name": "idem-key"})
    assert resp.status_code == 201
    return resp.json()["key"]  # type: ignore[no-any-return]


QASM = 'OPENQASM 2.0; include "qelib1.inc"; qreg q[1]; creg c[1]; x q[0]; measure q[0] -> c[0];'


def test_idempotency_key_returns_same_job(client: TestClient, api_key: str) -> None:
    """Submitting with the same Idempotency-Key should return the same job."""
    headers = {"X-API-Key": api_key, "Idempotency-Key": "dedup-123"}
    body = {"name": "exp-idem", "circuit": {"qasm": QASM, "shots": 4}}

    resp1 = client.post("/v1/jobs", json=body, headers=headers)
    assert resp1.status_code == 200
    job_id_1 = resp1.json()["job"]["id"]

    resp2 = client.post("/v1/jobs", json=body, headers=headers)
    assert resp2.status_code == 200
    job_id_2 = resp2.json()["job"]["id"]

    assert job_id_1 == job_id_2


def test_different_idempotency_keys_create_different_jobs(client: TestClient, api_key: str) -> None:
    headers1 = {"X-API-Key": api_key, "Idempotency-Key": "key-a"}
    headers2 = {"X-API-Key": api_key, "Idempotency-Key": "key-b"}
    body = {"name": "exp-diff", "circuit": {"qasm": QASM, "shots": 4}}

    resp1 = client.post("/v1/jobs", json=body, headers=headers1)
    resp2 = client.post("/v1/jobs", json=body, headers=headers2)

    assert resp1.json()["job"]["id"] != resp2.json()["job"]["id"]


def test_no_idempotency_key_creates_new_job_each_time(client: TestClient, api_key: str) -> None:
    headers = {"X-API-Key": api_key}
    body = {"name": "exp-no-key", "circuit": {"qasm": QASM, "shots": 4}}

    resp1 = client.post("/v1/jobs", json=body, headers=headers)
    resp2 = client.post("/v1/jobs", json=body, headers=headers)

    assert resp1.json()["job"]["id"] != resp2.json()["job"]["id"]
