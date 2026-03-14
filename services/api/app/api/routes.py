from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException
from quantum_contracts import (
    Experiment,
    Job,
    ProviderCapabilities,
    ProviderRouteRequest,
    ProviderRouteResponse,
)
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_redis, get_session, require_api_key
from app.core.correlation import get_correlation_id
from app.domain.schemas import (
    ApiKeyCreateRequest,
    ApiKeyCreateResponse,
    ApiKeyListItem,
    ApiKeyListResponse,
    BenchmarkListResponse,
    BenchmarkResponse,
    BenchmarkRunRequest,
    BudgetListResponse,
    BudgetResponse,
    CompareResultsRequest,
    CompareResultsResponse,
    CreateBudgetRequest,
    CreateOrgRequest,
    CreateProjectRequest,
    CreateTeamRequest,
    CreateVersionRequest,
    CreateWorkflowRequest,
    ExperimentListResponse,
    JobListResponse,
    OptimiseCircuitRequest,
    OptimiseCircuitResponse,
    OrgListResponse,
    OrgResponse,
    ProjectListResponse,
    ProjectResponse,
    ResultResponse,
    SubmitExperimentRequest,
    SubmitExperimentResponse,
    TeamListResponse,
    TeamResponse,
    VersionListResponse,
    WorkflowRunListResponse,
    WorkflowRunResponse,
)
from app.queue.redis_queue import RedisQueue
from app.repositories.api_keys import ApiKeyRepository
from app.services.benchmarking import BenchmarkingService
from app.services.circuit_optimiser import optimise_circuit
from app.services.cost_governance import CostGovernanceService
from app.services.experiment_versioning import ExperimentVersionRepository
from app.services.job_service import JobService, not_found
from app.services.provider_registry import get_provider_registry
from app.services.result_comparator import compare_results
from app.services.tenant import TenantRepository
from app.services.workflow_engine import WorkflowEngine

router = APIRouter()


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readyz")
async def readyz(
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
) -> dict[str, str]:
    await session.execute(text("SELECT 1"))
    from typing import Any, cast

    await cast(Any, redis.ping())
    return {"status": "ready"}


# ---------------------------------------------------------------------------
# API key management
# ---------------------------------------------------------------------------


@router.post("/v1/api-keys", response_model=ApiKeyCreateResponse, status_code=201)
async def create_api_key(
    body: ApiKeyCreateRequest,
    session: AsyncSession = Depends(get_session),
) -> ApiKeyCreateResponse:
    """Generate a new API key. The raw key is returned once and cannot be retrieved again."""
    repo = ApiKeyRepository(session)
    raw, model = await repo.create(body.name)
    await session.commit()
    return ApiKeyCreateResponse(id=model.id, name=model.name, key=raw, created_at=model.created_at)


@router.get("/v1/api-keys", response_model=ApiKeyListResponse, dependencies=[Depends(require_api_key)])
async def list_api_keys(
    session: AsyncSession = Depends(get_session),
) -> ApiKeyListResponse:
    repo = ApiKeyRepository(session)
    models = await repo.list()
    return ApiKeyListResponse(
        keys=[
            ApiKeyListItem(
                id=m.id,
                name=m.name,
                is_active=m.is_active,
                created_at=m.created_at,
                last_used_at=m.last_used_at,
            )
            for m in models
        ]
    )


@router.delete("/v1/api-keys/{key_id}", status_code=204, dependencies=[Depends(require_api_key)])
async def revoke_api_key(
    key_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> None:
    repo = ApiKeyRepository(session)
    revoked = await repo.revoke(key_id)
    if not revoked:
        raise HTTPException(status_code=404, detail="API key not found")
    await session.commit()


# ---------------------------------------------------------------------------
# Experiments / Jobs
# ---------------------------------------------------------------------------


async def _submit(
    body: SubmitExperimentRequest,
    idempotency_key: str | None,
    session: AsyncSession,
    redis: Redis,
) -> SubmitExperimentResponse:
    service = JobService(session, RedisQueue(redis))
    return await service.submit(body, idempotency_key)


@router.post(
    "/v1/jobs",
    response_model=SubmitExperimentResponse,
    dependencies=[Depends(require_api_key)],
)
async def submit_job(
    body: SubmitExperimentRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
) -> SubmitExperimentResponse:
    return await _submit(body, idempotency_key, session, redis)


@router.post(
    "/v1/experiments",
    response_model=SubmitExperimentResponse,
    status_code=201,
    dependencies=[Depends(require_api_key)],
)
async def create_experiment(
    body: SubmitExperimentRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
) -> SubmitExperimentResponse:
    """Alias for POST /v1/jobs with 201 Created."""
    return await _submit(body, idempotency_key, session, redis)


@router.get(
    "/v1/experiments",
    response_model=ExperimentListResponse,
    dependencies=[Depends(require_api_key)],
)
async def list_experiments(
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
) -> ExperimentListResponse:
    """List all experiments."""
    service = JobService(session, RedisQueue(redis))
    return ExperimentListResponse(experiments=await service.list_experiments())


@router.get(
    "/v1/experiments/{experiment_id}",
    response_model=Experiment,
    dependencies=[Depends(require_api_key)],
)
async def get_experiment(
    experiment_id: UUID,
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
) -> Experiment:
    """Get a single experiment by ID."""
    service = JobService(session, RedisQueue(redis))
    experiment = await service.get_experiment(experiment_id)
    if experiment is None:
        correlation_id = get_correlation_id()
        raise HTTPException(status_code=404, detail=not_found(correlation_id, "experiment").model_dump())
    return experiment


@router.get("/v1/jobs/{job_id}", dependencies=[Depends(require_api_key)])
async def get_job(
    job_id: str,
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
) -> Job:
    service = JobService(session, RedisQueue(redis))
    job = await service.get_job(UUID(job_id))
    if job is None:
        correlation_id = get_correlation_id()
        raise HTTPException(status_code=404, detail=not_found(correlation_id, "job").model_dump())
    return job


@router.get("/v1/jobs", response_model=JobListResponse, dependencies=[Depends(require_api_key)])
async def list_jobs(
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
) -> JobListResponse:
    service = JobService(session, RedisQueue(redis))
    return JobListResponse(jobs=await service.list_jobs())


async def _get_result(
    job_id: str,
    session: AsyncSession,
    redis: Redis,
) -> ResultResponse:
    service = JobService(session, RedisQueue(redis))
    result = await service.get_result(UUID(job_id))
    if result is None:
        correlation_id = get_correlation_id()
        raise HTTPException(
            status_code=404,
            detail=not_found(correlation_id, "result").model_dump(),
        )
    return ResultResponse(result=result)


@router.get(
    "/v1/jobs/{job_id}/result",
    response_model=ResultResponse,
    dependencies=[Depends(require_api_key)],
)
async def get_job_result(
    job_id: str,
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
) -> ResultResponse:
    return await _get_result(job_id, session, redis)


@router.get(
    "/v1/results/{job_id}",
    response_model=ResultResponse,
    dependencies=[Depends(require_api_key)],
)
async def get_result(
    job_id: str,
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
) -> ResultResponse:
    """Alias for GET /v1/jobs/{job_id}/result."""
    return await _get_result(job_id, session, redis)


# ---------------------------------------------------------------------------
# Provider Registry
# ---------------------------------------------------------------------------


@router.get(
    "/v1/providers",
    response_model=list[ProviderCapabilities],
    dependencies=[Depends(require_api_key)],
)
async def list_providers() -> list[ProviderCapabilities]:
    """List all registered quantum execution providers with capabilities."""
    registry = get_provider_registry()
    return registry.list_capabilities()


@router.post(
    "/v1/providers/select",
    response_model=ProviderRouteResponse,
    dependencies=[Depends(require_api_key)],
)
async def select_provider(body: ProviderRouteRequest) -> ProviderRouteResponse:
    """Select the best provider for the given circuit requirements."""
    registry = get_provider_registry()
    return registry.select(body)


# ---------------------------------------------------------------------------
# Circuit Optimisation (component 1)
# ---------------------------------------------------------------------------


@router.post(
    "/v1/circuits/optimise",
    response_model=OptimiseCircuitResponse,
    dependencies=[Depends(require_api_key)],
)
async def optimise_circuit_endpoint(body: OptimiseCircuitRequest) -> OptimiseCircuitResponse:
    """Optimise a quantum circuit before execution."""
    result = optimise_circuit(body.circuit, body.config)
    return OptimiseCircuitResponse(result=result)


# ---------------------------------------------------------------------------
# Provider Benchmarking (component 2)
# ---------------------------------------------------------------------------


@router.post(
    "/v1/benchmarks",
    response_model=BenchmarkResponse,
    status_code=201,
    dependencies=[Depends(require_api_key)],
)
async def run_benchmark(
    body: BenchmarkRunRequest,
    session: AsyncSession = Depends(get_session),
) -> BenchmarkResponse:
    """Record a provider benchmark calibration result."""
    svc = BenchmarkingService(session)
    result = await svc.run_calibration(
        body.provider,
        fidelity=body.fidelity,
        gate_error=body.avg_gate_error,
        readout_error=body.readout_error,
        queue_time=body.queue_time_seconds,
        execution_time_ms=body.execution_time_ms,
        qubit_count=body.qubit_count,
    )
    await session.commit()
    return BenchmarkResponse(benchmark=result)


@router.get(
    "/v1/benchmarks",
    response_model=BenchmarkListResponse,
    dependencies=[Depends(require_api_key)],
)
async def list_benchmarks(
    session: AsyncSession = Depends(get_session),
) -> BenchmarkListResponse:
    """Return the latest benchmark for every provider."""
    svc = BenchmarkingService(session)
    benchmarks = await svc.get_all_latest()
    return BenchmarkListResponse(benchmarks=benchmarks)


# ---------------------------------------------------------------------------
# Experiment Versioning (component 4)
# ---------------------------------------------------------------------------


@router.post(
    "/v1/experiments/{experiment_id}/versions",
    response_model=VersionListResponse,
    status_code=201,
    dependencies=[Depends(require_api_key)],
)
async def create_experiment_version(
    experiment_id: UUID,
    body: CreateVersionRequest,
    session: AsyncSession = Depends(get_session),
) -> VersionListResponse:
    """Create a new version for an experiment."""
    repo = ExperimentVersionRepository(session)
    await repo.create(
        experiment_id=experiment_id,
        circuit_qasm=body.circuit_qasm,
        optimisation_params=body.optimisation_params,
        provider=body.provider,
        seed=body.seed,
        parent_version_id=body.parent_version_id,
    )
    await session.commit()
    versions = await repo.list_versions(experiment_id)
    return VersionListResponse(versions=versions)


@router.get(
    "/v1/experiments/{experiment_id}/versions",
    response_model=VersionListResponse,
    dependencies=[Depends(require_api_key)],
)
async def list_experiment_versions(
    experiment_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> VersionListResponse:
    """List all versions of an experiment."""
    repo = ExperimentVersionRepository(session)
    versions = await repo.list_versions(experiment_id)
    return VersionListResponse(versions=versions)


# ---------------------------------------------------------------------------
# Workflow Orchestration (component 5)
# ---------------------------------------------------------------------------


@router.post(
    "/v1/workflows",
    response_model=WorkflowRunResponse,
    status_code=201,
    dependencies=[Depends(require_api_key)],
)
async def create_and_run_workflow(
    body: CreateWorkflowRequest,
    session: AsyncSession = Depends(get_session),
) -> WorkflowRunResponse:
    """Create a workflow definition and immediately start a run."""
    engine = WorkflowEngine(session)
    try:
        workflow_id = await engine.create_workflow(body.workflow)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    run = await engine.start_run(workflow_id)
    await session.commit()
    return WorkflowRunResponse(run=run)


@router.get(
    "/v1/workflows/runs",
    response_model=WorkflowRunListResponse,
    dependencies=[Depends(require_api_key)],
)
async def list_workflow_runs(
    session: AsyncSession = Depends(get_session),
) -> WorkflowRunListResponse:
    """List recent workflow runs."""
    engine = WorkflowEngine(session)
    runs = await engine.list_runs()
    return WorkflowRunListResponse(runs=runs)


@router.get(
    "/v1/workflows/runs/{run_id}",
    response_model=WorkflowRunResponse,
    dependencies=[Depends(require_api_key)],
)
async def get_workflow_run(
    run_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> WorkflowRunResponse:
    """Get a specific workflow run."""
    engine = WorkflowEngine(session)
    run = await engine.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Workflow run not found")
    return WorkflowRunResponse(run=run)


# ---------------------------------------------------------------------------
# Result Comparison (component 6)
# ---------------------------------------------------------------------------


@router.post(
    "/v1/results/compare",
    response_model=CompareResultsResponse,
    dependencies=[Depends(require_api_key)],
)
async def compare_results_endpoint(
    body: CompareResultsRequest,
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
) -> CompareResultsResponse:
    """Compare execution results across providers."""
    from app.repositories.results import ResultRepository

    result_repo = ResultRepository(session)
    results = []
    for jid in body.job_ids:
        r = await result_repo.get_by_job_id(jid)
        if r is not None:
            results.append(r)
    if not results:
        raise HTTPException(status_code=404, detail="No results found for the given job IDs")
    comparison = compare_results(body.experiment_name, results, body.reference_distribution)
    return CompareResultsResponse(comparison=comparison)


# ---------------------------------------------------------------------------
# Cost Governance (component 7)
# ---------------------------------------------------------------------------


@router.post(
    "/v1/budgets",
    response_model=BudgetResponse,
    status_code=201,
    dependencies=[Depends(require_api_key)],
)
async def create_budget(
    body: CreateBudgetRequest,
    session: AsyncSession = Depends(get_session),
) -> BudgetResponse:
    """Create a budget for cost governance."""
    svc = CostGovernanceService(session)
    budget = await svc.create_budget(
        scope=body.scope,
        scope_id=body.scope_id,
        monthly_limit_usd=body.monthly_limit_usd,
        alert_threshold_pct=body.alert_threshold_pct,
    )
    await session.commit()
    return BudgetResponse(budget=budget)


@router.get(
    "/v1/budgets",
    response_model=BudgetListResponse,
    dependencies=[Depends(require_api_key)],
)
async def list_budgets(
    session: AsyncSession = Depends(get_session),
) -> BudgetListResponse:
    """List all budgets."""
    svc = CostGovernanceService(session)
    budgets = await svc.list_budgets()
    return BudgetListResponse(budgets=budgets)


# ---------------------------------------------------------------------------
# Multi-tenant Platform (component 9)
# ---------------------------------------------------------------------------


@router.post(
    "/v1/orgs",
    response_model=OrgResponse,
    status_code=201,
    dependencies=[Depends(require_api_key)],
)
async def create_org(
    body: CreateOrgRequest,
    session: AsyncSession = Depends(get_session),
) -> OrgResponse:
    """Create a new organisation."""
    repo = TenantRepository(session)
    org = await repo.create_org(body.name)
    await session.commit()
    return OrgResponse(organisation=org)


@router.get(
    "/v1/orgs",
    response_model=OrgListResponse,
    dependencies=[Depends(require_api_key)],
)
async def list_orgs(
    session: AsyncSession = Depends(get_session),
) -> OrgListResponse:
    """List all organisations."""
    repo = TenantRepository(session)
    orgs = await repo.list_orgs()
    return OrgListResponse(organisations=orgs)


@router.post(
    "/v1/orgs/{org_id}/teams",
    response_model=TeamResponse,
    status_code=201,
    dependencies=[Depends(require_api_key)],
)
async def create_team(
    org_id: UUID,
    body: CreateTeamRequest,
    session: AsyncSession = Depends(get_session),
) -> TeamResponse:
    """Create a team within an organisation."""
    repo = TenantRepository(session)
    team = await repo.create_team(org_id, body.name)
    await session.commit()
    return TeamResponse(team=team)


@router.get(
    "/v1/orgs/{org_id}/teams",
    response_model=TeamListResponse,
    dependencies=[Depends(require_api_key)],
)
async def list_teams(
    org_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> TeamListResponse:
    """List teams in an organisation."""
    repo = TenantRepository(session)
    teams = await repo.list_teams(org_id)
    return TeamListResponse(teams=teams)


@router.post(
    "/v1/teams/{team_id}/projects",
    response_model=ProjectResponse,
    status_code=201,
    dependencies=[Depends(require_api_key)],
)
async def create_project(
    team_id: UUID,
    body: CreateProjectRequest,
    session: AsyncSession = Depends(get_session),
) -> ProjectResponse:
    """Create a project within a team."""
    repo = TenantRepository(session)
    project = await repo.create_project(team_id, body.name, body.description)
    await session.commit()
    return ProjectResponse(project=project)


@router.get(
    "/v1/teams/{team_id}/projects",
    response_model=ProjectListResponse,
    dependencies=[Depends(require_api_key)],
)
async def list_projects(
    team_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> ProjectListResponse:
    """List projects in a team."""
    repo = TenantRepository(session)
    projects = await repo.list_projects(team_id)
    return ProjectListResponse(projects=projects)
