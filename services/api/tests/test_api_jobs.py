from collections.abc import AsyncGenerator
from pathlib import Path

import fakeredis.aioredis
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_redis, get_session
from app.db.base import Base
from app.main import app

TEST_DB = "sqlite+aiosqlite:///./test_api.db"


@pytest.fixture(scope="module", autouse=True)
def cleanup_db() -> None:
    path = Path("test_api.db")
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


QASM = 'OPENQASM 2.0; include "qelib1.inc"; qreg q[1]; creg c[1]; x q[0]; measure q[0] -> c[0];'


def test_submit_and_get_job(client: TestClient) -> None:
    response = client.post(
        "/v1/jobs",
        json={"name": "exp-1", "description": "d", "circuit": {"qasm": QASM, "shots": 8}},
    )
    assert response.status_code == 200
    body = response.json()
    job_id = body["job"]["id"]

    job_response = client.get(f"/v1/jobs/{job_id}")
    assert job_response.status_code == 200
    assert job_response.json()["status"] in {"queued", "submitted"}
