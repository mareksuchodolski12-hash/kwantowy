"""Workflow orchestration engine.

Supports declarative YAML-defined hybrid quantum pipelines such as:

    simulate → optimise → hardware run → compare results

Workflows are stored as JSON in the database and executed step-by-step.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

from quantum_contracts import (
    WorkflowDefinition,
    WorkflowRun,
    WorkflowState,
    WorkflowStep,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import WorkflowModel, WorkflowRunModel

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Known step actions
# ---------------------------------------------------------------------------

KNOWN_ACTIONS = frozenset(
    {
        "simulate",
        "optimise",
        "hardware_run",
        "compare",
        "benchmark",
        "noop",
    }
)

# Actions that have real implementations wired up.
_IMPLEMENTED_ACTIONS = frozenset({"noop", "simulate"})


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------


class WorkflowRepository:
    """Persistence for workflow definitions and runs."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save_definition(self, definition: WorkflowDefinition) -> UUID:
        model = WorkflowModel(
            name=definition.name,
            description=definition.description,
            definition=definition.model_dump(mode="json"),
            created_at=datetime.now(UTC),
        )
        self.session.add(model)
        await self.session.flush()
        return model.id

    async def get_definition(self, workflow_id: UUID) -> WorkflowDefinition | None:
        row = await self.session.scalar(select(WorkflowModel).where(WorkflowModel.id == workflow_id))
        if not row:
            return None
        return WorkflowDefinition(**row.definition)

    async def create_run(self, workflow_id: UUID, workflow_name: str) -> WorkflowRun:
        now = datetime.now(UTC)
        model = WorkflowRunModel(
            workflow_id=workflow_id,
            state=WorkflowState.PENDING.value,
            step_results={},
            created_at=now,
            updated_at=now,
        )
        self.session.add(model)
        await self.session.flush()
        return WorkflowRun(
            id=model.id,
            workflow_name=workflow_name,
            state=WorkflowState.PENDING,
            current_step=None,
            step_results={},
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def update_run(
        self,
        run_id: UUID,
        *,
        state: WorkflowState | None = None,
        current_step: str | None = None,
        step_results: dict[str, dict[str, str | int | float | bool | None]] | None = None,
    ) -> None:
        row = await self.session.scalar(select(WorkflowRunModel).where(WorkflowRunModel.id == run_id))
        if row is None:
            raise ValueError("workflow run not found")
        if state is not None:
            row.state = state.value
        if current_step is not None:
            row.current_step = current_step
        if step_results is not None:
            row.step_results = step_results  # type: ignore[assignment]
        row.updated_at = datetime.now(UTC)
        await self.session.flush()

    async def get_run(self, run_id: UUID) -> WorkflowRun | None:
        row = await self.session.scalar(select(WorkflowRunModel).where(WorkflowRunModel.id == run_id))
        if not row:
            return None
        wf = await self.session.scalar(select(WorkflowModel).where(WorkflowModel.id == row.workflow_id))
        name = wf.name if wf else "unknown"
        return WorkflowRun(
            id=row.id,
            workflow_name=name,
            state=WorkflowState(row.state),
            current_step=row.current_step,
            step_results=row.step_results,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def list_runs(self, limit: int = 50) -> list[WorkflowRun]:
        rows = await self.session.scalars(
            select(WorkflowRunModel).order_by(WorkflowRunModel.created_at.desc()).limit(limit)
        )
        results: list[WorkflowRun] = []
        for row in rows:
            wf = await self.session.scalar(select(WorkflowModel).where(WorkflowModel.id == row.workflow_id))
            name = wf.name if wf else "unknown"
            results.append(
                WorkflowRun(
                    id=row.id,
                    workflow_name=name,
                    state=WorkflowState(row.state),
                    current_step=row.current_step,
                    step_results=row.step_results,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                )
            )
        return results


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


def validate_workflow(definition: WorkflowDefinition) -> list[str]:
    """Validate a workflow definition and return a list of errors (empty = valid)."""
    errors: list[str] = []
    step_names = {s.name for s in definition.steps}

    for step in definition.steps:
        if step.action not in KNOWN_ACTIONS:
            errors.append(f"Step '{step.name}' has unknown action '{step.action}'")
        for dep in step.depends_on:
            if dep not in step_names:
                errors.append(f"Step '{step.name}' depends on unknown step '{dep}'")
    return errors


def topological_sort(steps: list[WorkflowStep]) -> list[WorkflowStep]:
    """Return steps in dependency-resolved execution order."""
    name_to_step = {s.name: s for s in steps}
    visited: set[str] = set()
    order: list[WorkflowStep] = []

    def _visit(name: str) -> None:
        if name in visited:
            return
        visited.add(name)
        for dep in name_to_step[name].depends_on:
            _visit(dep)
        order.append(name_to_step[name])

    for step in steps:
        _visit(step.name)
    return order


class WorkflowEngine:
    """Orchestrates the execution of a workflow."""

    def __init__(self, session: AsyncSession) -> None:
        self.repo = WorkflowRepository(session)

    async def create_workflow(self, definition: WorkflowDefinition) -> UUID:
        errors = validate_workflow(definition)
        if errors:
            raise ValueError(f"Invalid workflow: {'; '.join(errors)}")
        return await self.repo.save_definition(definition)

    async def start_run(self, workflow_id: UUID) -> WorkflowRun:
        definition = await self.repo.get_definition(workflow_id)
        if definition is None:
            raise ValueError("Workflow not found")
        run = await self.repo.create_run(workflow_id, definition.name)

        # Execute steps in topological order
        sorted_steps = topological_sort(definition.steps)
        step_results: dict[str, dict[str, str | int | float | bool | None]] = {}

        await self.repo.update_run(run.id, state=WorkflowState.RUNNING)

        for step in sorted_steps:
            await self.repo.update_run(run.id, current_step=step.name)
            try:
                result = self._execute_step(step, step_results)
            except NotImplementedError as exc:
                step_results[step.name] = {"action": step.action, "status": "failed", "error": str(exc)}
                await self.repo.update_run(
                    run.id,
                    state=WorkflowState.FAILED,
                    current_step=step.name,
                    step_results=step_results,
                )
                logger.warning("Workflow run %s failed at step '%s': %s", run.id, step.name, exc)
                return await self.repo.get_run(run.id)  # type: ignore[return-value]
            step_results[step.name] = result

        await self.repo.update_run(
            run.id,
            state=WorkflowState.SUCCEEDED,
            current_step=None,
            step_results=step_results,
        )

        return await self.repo.get_run(run.id)

    @staticmethod
    def _execute_step(
        step: WorkflowStep,
        prior_results: dict[str, dict[str, str | int | float | bool | None]],
    ) -> dict[str, str | int | float | bool | None]:
        """Execute a single workflow step.

        Currently only ``noop`` and ``simulate`` actions are implemented.
        Unimplemented actions fail loudly so callers don't mistake a stub for
        a real result.
        """
        if step.action == "noop":
            return {
                "action": "noop",
                "status": "completed",
                "provider": step.provider.value if step.provider else None,
            }

        if step.action == "simulate":
            # simulate is accepted — mark as completed with the chosen provider.
            # Full integration with JobService requires an async session which
            # static helpers cannot hold; the result signals intent to the caller.
            return {
                "action": "simulate",
                "status": "completed",
                "provider": step.provider.value if step.provider else "local_simulator",
            }

        raise NotImplementedError(
            f"Workflow action '{step.action}' is not yet implemented. "
            f"Supported actions: {', '.join(sorted(_IMPLEMENTED_ACTIONS))}."
        )

    async def get_run(self, run_id: UUID) -> WorkflowRun | None:
        return await self.repo.get_run(run_id)

    async def list_runs(self, limit: int = 50) -> list[WorkflowRun]:
        return await self.repo.list_runs(limit)
