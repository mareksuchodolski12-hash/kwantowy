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


@pytest.fixture
def api_key(client: TestClient) -> str:
    """Create a fresh API key for test use."""
    resp = client.post("/v1/api-keys", json={"name": "test-key"})
    assert resp.status_code == 201
    return resp.json()["key"]  # type: ignore[no-any-return]


QASM = 'OPENQASM 2.0; include "qelib1.inc"; qreg q[1]; creg c[1]; x q[0]; measure q[0] -> c[0];'


def test_submit_and_get_job(client: TestClient, api_key: str) -> None:
    headers = {"X-API-Key": api_key}
    response = client.post(
        "/v1/jobs",
        json={"name": "exp-1", "description": "d", "circuit": {"qasm": QASM, "shots": 8}},
        headers=headers,
    )
    assert response.status_code == 200
    body = response.json()
    job_id = body["job"]["id"]

    job_response = client.get(f"/v1/jobs/{job_id}", headers=headers)
    assert job_response.status_code == 200
    assert job_response.json()["status"] in {"queued", "submitted"}


def test_submit_experiments_endpoint(client: TestClient, api_key: str) -> None:
    headers = {"X-API-Key": api_key}
    response = client.post(
        "/v1/experiments",
        json={"name": "exp-alias", "circuit": {"qasm": QASM, "shots": 4}},
        headers=headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert "experiment" in body
    assert "job" in body


def test_results_alias_endpoint(client: TestClient, api_key: str) -> None:
    headers = {"X-API-Key": api_key}
    submit = client.post(
        "/v1/jobs",
        json={"name": "exp-result-alias", "circuit": {"qasm": QASM, "shots": 4}},
        headers=headers,
    )
    job_id = submit.json()["job"]["id"]
    # result not ready yet (worker not running in tests) – expect 404
    result_response = client.get(f"/v1/results/{job_id}", headers=headers)
    assert result_response.status_code == 404


def test_unauthorized_request(client: TestClient) -> None:
    response = client.post(
        "/v1/jobs",
        json={"name": "no-key", "circuit": {"qasm": QASM, "shots": 4}},
    )
    assert response.status_code == 401


def test_invalid_api_key(client: TestClient) -> None:
    response = client.get("/v1/jobs", headers={"X-API-Key": "qcp_invalid"})
    assert response.status_code == 401
