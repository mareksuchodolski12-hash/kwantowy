"""Tests for ProviderRegistry and provider-selection API endpoints."""

from collections.abc import AsyncGenerator
from pathlib import Path

import fakeredis.aioredis
import pytest
from fastapi.testclient import TestClient
from quantum_contracts import ExecutionProvider, ProviderRouteRequest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_redis, get_session
from app.db.base import Base
from app.main import app
from app.services.provider_registry import ProviderRegistry

# ---------------------------------------------------------------------------
# Unit tests – ProviderRegistry
# ---------------------------------------------------------------------------

TEST_DB = "sqlite+aiosqlite:///./test_providers.db"


@pytest.fixture(scope="module", autouse=True)
def cleanup_db() -> None:
    path = Path("test_providers.db")
    if path.exists():
        path.unlink()


class TestProviderRegistryUnit:
    """Pure-unit tests for the registry, no HTTP layer."""

    def test_list_capabilities_returns_all_providers(self) -> None:
        registry = ProviderRegistry()
        caps = registry.list_capabilities()
        providers = {c.provider for c in caps}
        assert ExecutionProvider.LOCAL_SIMULATOR in providers
        assert ExecutionProvider.IBM_RUNTIME in providers
        assert ExecutionProvider.IONQ in providers
        assert ExecutionProvider.RIGETTI in providers
        assert ExecutionProvider.SIMULATOR_AER in providers

    def test_get_capabilities_for_known_provider(self) -> None:
        registry = ProviderRegistry()
        cap = registry.get_capabilities(ExecutionProvider.LOCAL_SIMULATOR)
        assert cap is not None
        assert cap.display_name == "Qiskit BasicProvider (local)"
        assert cap.is_simulator is True

    def test_select_prefers_simulator_by_default(self) -> None:
        registry = ProviderRegistry()
        request = ProviderRouteRequest(qubit_count=2, shots=1024)
        result = registry.select(request)
        # Local simulators are enabled and cheapest – should be recommended.
        assert result.recommended in {ExecutionProvider.LOCAL_SIMULATOR, ExecutionProvider.SIMULATOR_AER}

    def test_select_excludes_providers(self) -> None:
        registry = ProviderRegistry()
        request = ProviderRouteRequest(
            qubit_count=2,
            shots=1024,
            exclude_providers=[ExecutionProvider.LOCAL_SIMULATOR],
        )
        result = registry.select(request)
        assert result.recommended != ExecutionProvider.LOCAL_SIMULATOR
        assert ExecutionProvider.LOCAL_SIMULATOR not in result.alternatives

    def test_select_respects_qubit_limit(self) -> None:
        registry = ProviderRegistry()
        # Request more qubits than the local simulator supports (24).
        request = ProviderRouteRequest(qubit_count=25, shots=1024)
        result = registry.select(request)
        # LOCAL_SIMULATOR (24 max) should NOT appear in recommended or alternatives.
        all_choices = [result.recommended, *result.alternatives]
        assert ExecutionProvider.LOCAL_SIMULATOR not in all_choices

    def test_select_fallback_when_no_candidates(self) -> None:
        registry = ProviderRegistry()
        # Require 500 qubits – no provider can satisfy that.
        request = ProviderRouteRequest(qubit_count=500, shots=1024)
        result = registry.select(request)
        assert result.recommended == ExecutionProvider.LOCAL_SIMULATOR
        assert "No suitable provider" in result.reason


# ---------------------------------------------------------------------------
# API integration tests
# ---------------------------------------------------------------------------


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
    resp = client.post("/v1/api-keys", json={"name": "provider-test-key"})
    assert resp.status_code == 201
    return resp.json()["key"]  # type: ignore[no-any-return]


def test_list_providers_endpoint(client: TestClient, api_key: str) -> None:
    headers = {"X-API-Key": api_key}
    resp = client.get("/v1/providers", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    providers = {p["provider"] for p in data}
    assert "local_simulator" in providers
    assert "ionq" in providers
    assert "rigetti" in providers


def test_select_provider_endpoint(client: TestClient, api_key: str) -> None:
    headers = {"X-API-Key": api_key}
    resp = client.post(
        "/v1/providers/select",
        json={"qubit_count": 2, "shots": 1024},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "recommended" in data
    assert "alternatives" in data
    assert "reason" in data


def test_select_provider_prefer_hardware(client: TestClient, api_key: str) -> None:
    headers = {"X-API-Key": api_key}
    resp = client.post(
        "/v1/providers/select",
        json={"qubit_count": 2, "shots": 1024, "prefer_hardware": True},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    # Even with hardware preference, if no hardware is enabled the result
    # should still return a valid recommendation.
    assert data["recommended"] is not None


def test_providers_endpoint_requires_auth(client: TestClient) -> None:
    resp = client.get("/v1/providers")
    assert resp.status_code == 401
