"""Integration tests for the new platform API endpoints.

Tests circuit optimisation, benchmarking, experiment versioning, workflows,
result comparison, cost governance, and multi-tenant endpoints.
"""

from collections.abc import AsyncGenerator
from pathlib import Path

import fakeredis.aioredis
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_redis, get_session
from app.db.base import Base
from app.main import app

TEST_DB = "sqlite+aiosqlite:///./test_platform.db"

QASM = (
    'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg c[2];\n'
    "h q[0];\ncx q[0],q[1];\nmeasure q[0] -> c[0];\nmeasure q[1] -> c[1];"
)
QASM_DOUBLE = 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[1];\ncreg c[1];\nx q[0];\nx q[0];\nmeasure q[0] -> c[0];'


@pytest.fixture(scope="module", autouse=True)
def cleanup_db() -> None:
    path = Path("test_platform.db")
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
    resp = client.post("/v1/api-keys", json={"name": "platform-test-key"})
    assert resp.status_code == 201
    return resp.json()["key"]  # type: ignore[no-any-return]


# ---------------------------------------------------------------------------
# Circuit Optimisation (component 1)
# ---------------------------------------------------------------------------


def test_optimise_circuit_none_strategy(client: TestClient, api_key: str) -> None:
    headers = {"X-API-Key": api_key}
    resp = client.post(
        "/v1/circuits/optimise",
        json={"circuit": {"qasm": QASM, "shots": 1024}, "config": {"strategy": "none"}},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()["result"]
    assert data["strategy_applied"] == "none"
    assert data["original_qasm"] == QASM


def test_optimise_circuit_medium_strategy(client: TestClient, api_key: str) -> None:
    headers = {"X-API-Key": api_key}
    resp = client.post(
        "/v1/circuits/optimise",
        json={
            "circuit": {"qasm": QASM_DOUBLE, "shots": 1024},
            "config": {"strategy": "medium"},
        },
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()["result"]
    assert data["optimised_gate_count"] <= data["original_gate_count"]


def test_optimise_circuit_noise_aware(client: TestClient, api_key: str) -> None:
    headers = {"X-API-Key": api_key}
    resp = client.post(
        "/v1/circuits/optimise",
        json={
            "circuit": {"qasm": QASM, "shots": 1024},
            "config": {"strategy": "noise_aware", "noise_aware_mapping": True},
        },
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()["result"]
    assert len(data["qubit_mapping"]) > 0


# ---------------------------------------------------------------------------
# Provider Benchmarking (component 2)
# ---------------------------------------------------------------------------


def test_run_and_list_benchmark(client: TestClient, api_key: str) -> None:
    headers = {"X-API-Key": api_key}
    resp = client.post(
        "/v1/benchmarks",
        json={"provider": "local_simulator", "fidelity": 0.99, "qubit_count": 2},
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()["benchmark"]
    assert data["provider"] == "local_simulator"
    assert data["fidelity"] == 0.99

    resp2 = client.get("/v1/benchmarks", headers=headers)
    assert resp2.status_code == 200
    benchmarks = resp2.json()["benchmarks"]
    assert len(benchmarks) >= 1


# ---------------------------------------------------------------------------
# Smart Provider Routing (component 3) - enhanced selection
# ---------------------------------------------------------------------------


def test_select_provider_with_fidelity_filter(client: TestClient, api_key: str) -> None:
    headers = {"X-API-Key": api_key}
    resp = client.post(
        "/v1/providers/select",
        json={"qubit_count": 2, "shots": 1024, "min_fidelity": 0.99},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["recommended"] is not None


def test_select_provider_with_queue_limit(client: TestClient, api_key: str) -> None:
    headers = {"X-API-Key": api_key}
    resp = client.post(
        "/v1/providers/select",
        json={"qubit_count": 2, "shots": 1024, "max_queue_seconds": 1.0},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    # Local simulators have 0 queue time, should be selected
    assert data["recommended"] in {"local_simulator", "simulator_aer"}


# ---------------------------------------------------------------------------
# Experiment Versioning (component 4)
# ---------------------------------------------------------------------------


def test_create_and_list_experiment_versions(client: TestClient, api_key: str) -> None:
    headers = {"X-API-Key": api_key}
    # First create an experiment
    exp_resp = client.post(
        "/v1/experiments",
        json={"name": "version-test", "circuit": {"qasm": QASM, "shots": 8}},
        headers=headers,
    )
    assert exp_resp.status_code == 201
    experiment_id = exp_resp.json()["experiment"]["id"]

    # Create version 1
    v1_resp = client.post(
        f"/v1/experiments/{experiment_id}/versions",
        json={"circuit_qasm": QASM, "provider": "local_simulator", "seed": 42},
        headers=headers,
    )
    assert v1_resp.status_code == 201
    versions = v1_resp.json()["versions"]
    assert len(versions) == 1
    assert versions[0]["version_number"] == 1
    assert versions[0]["seed"] == 42

    # Create version 2
    v2_resp = client.post(
        f"/v1/experiments/{experiment_id}/versions",
        json={"circuit_qasm": QASM_DOUBLE, "provider": "local_simulator"},
        headers=headers,
    )
    assert v2_resp.status_code == 201
    versions = v2_resp.json()["versions"]
    assert len(versions) == 2
    assert versions[1]["version_number"] == 2

    # List versions
    list_resp = client.get(f"/v1/experiments/{experiment_id}/versions", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()["versions"]) == 2


# ---------------------------------------------------------------------------
# Workflow Orchestration (component 5)
# ---------------------------------------------------------------------------


def test_create_and_run_workflow(client: TestClient, api_key: str) -> None:
    headers = {"X-API-Key": api_key}
    resp = client.post(
        "/v1/workflows",
        json={
            "workflow": {
                "name": "test-pipeline",
                "description": "simulate then optimise",
                "steps": [
                    {"name": "simulate", "action": "simulate"},
                    {"name": "optimise", "action": "optimise", "depends_on": ["simulate"]},
                    {"name": "run", "action": "hardware_run", "depends_on": ["optimise"]},
                ],
                "circuit": {"qasm": QASM, "shots": 100},
            }
        },
        headers=headers,
    )
    assert resp.status_code == 201
    run = resp.json()["run"]
    assert run["state"] == "succeeded"
    assert run["workflow_name"] == "test-pipeline"
    assert "simulate" in run["step_results"]
    assert "optimise" in run["step_results"]
    assert "run" in run["step_results"]


def test_list_workflow_runs(client: TestClient, api_key: str) -> None:
    headers = {"X-API-Key": api_key}
    # Create a workflow run first
    client.post(
        "/v1/workflows",
        json={
            "workflow": {
                "name": "list-test",
                "steps": [{"name": "s1", "action": "noop"}],
                "circuit": {"qasm": QASM, "shots": 10},
            }
        },
        headers=headers,
    )
    resp = client.get("/v1/workflows/runs", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()["runs"]) >= 1


def test_invalid_workflow_returns_error(client: TestClient, api_key: str) -> None:
    headers = {"X-API-Key": api_key}
    resp = client.post(
        "/v1/workflows",
        json={
            "workflow": {
                "name": "bad-wf",
                "steps": [{"name": "s1", "action": "nonexistent_action"}],
                "circuit": {"qasm": QASM, "shots": 10},
            }
        },
        headers=headers,
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Cost Governance (component 7)
# ---------------------------------------------------------------------------


def test_create_and_list_budgets(client: TestClient, api_key: str) -> None:
    headers = {"X-API-Key": api_key}
    resp = client.post(
        "/v1/budgets",
        json={"scope": "team", "scope_id": "team-alpha", "monthly_limit_usd": 100.0},
        headers=headers,
    )
    assert resp.status_code == 201
    budget = resp.json()["budget"]
    assert budget["scope"] == "team"
    assert budget["monthly_limit_usd"] == 100.0
    assert budget["current_spend_usd"] == 0.0

    resp2 = client.get("/v1/budgets", headers=headers)
    assert resp2.status_code == 200
    assert len(resp2.json()["budgets"]) >= 1


# ---------------------------------------------------------------------------
# Multi-tenant Platform (component 9)
# ---------------------------------------------------------------------------


def test_tenant_hierarchy(client: TestClient, api_key: str) -> None:
    headers = {"X-API-Key": api_key}

    # Create org
    org_resp = client.post("/v1/orgs", json={"name": "Acme Corp"}, headers=headers)
    assert org_resp.status_code == 201
    org_id = org_resp.json()["organisation"]["id"]

    # List orgs
    list_orgs = client.get("/v1/orgs", headers=headers)
    assert list_orgs.status_code == 200
    assert len(list_orgs.json()["organisations"]) >= 1

    # Create team
    team_resp = client.post(f"/v1/orgs/{org_id}/teams", json={"name": "Quantum Team"}, headers=headers)
    assert team_resp.status_code == 201
    team_id = team_resp.json()["team"]["id"]

    # List teams
    list_teams = client.get(f"/v1/orgs/{org_id}/teams", headers=headers)
    assert list_teams.status_code == 200
    assert len(list_teams.json()["teams"]) >= 1

    # Create project
    proj_resp = client.post(
        f"/v1/teams/{team_id}/projects",
        json={"name": "Bell State Study", "description": "Testing entanglement"},
        headers=headers,
    )
    assert proj_resp.status_code == 201
    proj = proj_resp.json()["project"]
    assert proj["name"] == "Bell State Study"

    # List projects
    list_projects = client.get(f"/v1/teams/{team_id}/projects", headers=headers)
    assert list_projects.status_code == 200
    assert len(list_projects.json()["projects"]) >= 1


# ---------------------------------------------------------------------------
# Auth required for new endpoints
# ---------------------------------------------------------------------------


def test_new_endpoints_require_auth(client: TestClient) -> None:
    """All new endpoints should require an API key."""
    endpoints = [
        ("POST", "/v1/circuits/optimise"),
        ("POST", "/v1/benchmarks"),
        ("GET", "/v1/benchmarks"),
        ("POST", "/v1/workflows"),
        ("GET", "/v1/workflows/runs"),
        ("POST", "/v1/budgets"),
        ("GET", "/v1/budgets"),
        ("POST", "/v1/orgs"),
        ("GET", "/v1/orgs"),
    ]
    for method, path in endpoints:
        if method == "POST":
            resp = client.post(path, json={})
        else:
            resp = client.get(path)
        assert resp.status_code == 401, f"{method} {path} should require auth, got {resp.status_code}"
