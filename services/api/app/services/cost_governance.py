"""Cost governance – budget controls and cost tracking.

Provides per-experiment, per-team, and per-provider cost tracking with
monthly budget limits and alert thresholds.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

from quantum_contracts import Budget, CostRecord, ExecutionProvider
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import BudgetModel, CostRecordModel

logger = logging.getLogger(__name__)


class BudgetRepository:
    """CRUD for budget configurations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        scope: str,
        scope_id: str,
        monthly_limit_usd: float,
        alert_threshold_pct: float = 80.0,
    ) -> Budget:
        model = BudgetModel(
            scope=scope,
            scope_id=scope_id,
            monthly_limit_usd=monthly_limit_usd,
            current_spend_usd=0.0,
            alert_threshold_pct=alert_threshold_pct,
            created_at=datetime.now(UTC),
        )
        self.session.add(model)
        await self.session.flush()
        return self._to_contract(model)

    async def get(self, budget_id: UUID) -> Budget | None:
        row = await self.session.scalar(select(BudgetModel).where(BudgetModel.id == budget_id))
        return self._to_contract(row) if row else None

    async def get_by_scope(self, scope: str, scope_id: str) -> Budget | None:
        row = await self.session.scalar(
            select(BudgetModel).where(BudgetModel.scope == scope, BudgetModel.scope_id == scope_id)
        )
        return self._to_contract(row) if row else None

    async def list_all(self, limit: int = 100) -> list[Budget]:
        rows = await self.session.scalars(select(BudgetModel).order_by(BudgetModel.created_at.desc()).limit(limit))
        return [self._to_contract(r) for r in rows]

    async def add_spend(self, budget_id: UUID, amount_usd: float) -> Budget:
        row = await self.session.scalar(select(BudgetModel).where(BudgetModel.id == budget_id))
        if row is None:
            raise ValueError("budget not found")
        row.current_spend_usd += amount_usd
        await self.session.flush()
        return self._to_contract(row)

    @staticmethod
    def _to_contract(model: BudgetModel) -> Budget:
        return Budget(
            id=model.id,
            scope=model.scope,
            scope_id=model.scope_id,
            monthly_limit_usd=model.monthly_limit_usd,
            current_spend_usd=model.current_spend_usd,
            alert_threshold_pct=model.alert_threshold_pct,
            created_at=model.created_at,
        )


class CostRecordRepository:
    """CRUD for individual cost records."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record(
        self,
        job_id: UUID,
        provider: ExecutionProvider,
        shots: int,
        cost_usd: float,
    ) -> CostRecord:
        model = CostRecordModel(
            job_id=job_id,
            provider=provider.value,
            shots=shots,
            cost_usd=cost_usd,
            recorded_at=datetime.now(UTC),
        )
        self.session.add(model)
        await self.session.flush()
        return CostRecord(
            id=model.id,
            job_id=model.job_id,
            provider=ExecutionProvider(model.provider),
            shots=model.shots,
            cost_usd=model.cost_usd,
            recorded_at=model.recorded_at,
        )

    async def list_by_job(self, job_id: UUID) -> list[CostRecord]:
        rows = await self.session.scalars(select(CostRecordModel).where(CostRecordModel.job_id == job_id))
        return [
            CostRecord(
                id=r.id,
                job_id=r.job_id,
                provider=ExecutionProvider(r.provider),
                shots=r.shots,
                cost_usd=r.cost_usd,
                recorded_at=r.recorded_at,
            )
            for r in rows
        ]

    async def list_by_provider(self, provider: ExecutionProvider, limit: int = 100) -> list[CostRecord]:
        rows = await self.session.scalars(
            select(CostRecordModel)
            .where(CostRecordModel.provider == provider.value)
            .order_by(CostRecordModel.recorded_at.desc())
            .limit(limit)
        )
        return [
            CostRecord(
                id=r.id,
                job_id=r.job_id,
                provider=ExecutionProvider(r.provider),
                shots=r.shots,
                cost_usd=r.cost_usd,
                recorded_at=r.recorded_at,
            )
            for r in rows
        ]


class CostGovernanceService:
    """Enforces budget limits and records execution costs."""

    def __init__(self, session: AsyncSession) -> None:
        self.budgets = BudgetRepository(session)
        self.costs = CostRecordRepository(session)

    async def check_budget(self, scope: str, scope_id: str, estimated_cost: float) -> bool:
        """Return ``True`` if the estimated cost fits within the budget.

        Returns ``True`` when no budget is configured (open by default).
        """
        budget = await self.budgets.get_by_scope(scope, scope_id)
        if budget is None:
            return True
        remaining: float = budget.monthly_limit_usd - budget.current_spend_usd
        return bool(estimated_cost <= remaining)

    async def record_cost(
        self,
        job_id: UUID,
        provider: ExecutionProvider,
        shots: int,
        cost_per_shot: float,
        *,
        scope: str | None = None,
        scope_id: str | None = None,
    ) -> CostRecord:
        """Record a cost entry and optionally update the associated budget."""
        total = shots * cost_per_shot
        record = await self.costs.record(job_id, provider, shots, total)
        if scope and scope_id:
            budget = await self.budgets.get_by_scope(scope, scope_id)
            if budget:
                updated = await self.budgets.add_spend(budget.id, total)
                pct_used = (
                    (updated.current_spend_usd / updated.monthly_limit_usd) * 100
                    if updated.monthly_limit_usd > 0
                    else 0
                )
                if pct_used >= updated.alert_threshold_pct:
                    logger.warning(
                        "budget threshold exceeded",
                        extra={
                            "scope": scope,
                            "scope_id": scope_id,
                            "pct_used": round(pct_used, 1),
                        },
                    )
        return record

    async def create_budget(
        self,
        scope: str,
        scope_id: str,
        monthly_limit_usd: float,
        alert_threshold_pct: float = 80.0,
    ) -> Budget:
        return await self.budgets.create(scope, scope_id, monthly_limit_usd, alert_threshold_pct)

    async def get_budget(self, scope: str, scope_id: str) -> Budget | None:
        return await self.budgets.get_by_scope(scope, scope_id)

    async def list_budgets(self) -> list[Budget]:
        return await self.budgets.list_all()
