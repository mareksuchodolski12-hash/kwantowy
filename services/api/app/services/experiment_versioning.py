"""Experiment versioning – lineage tracking for experiment iterations.

Each version captures the circuit hash, optimisation parameters, provider,
result reference, and optional seed so that experiment evolution is fully
reproducible.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime
from uuid import UUID

from quantum_contracts import ExecutionProvider, ExperimentVersion
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ExperimentVersionModel

logger = logging.getLogger(__name__)


def _circuit_hash(qasm: str) -> str:
    return hashlib.sha256(qasm.encode()).hexdigest()


class ExperimentVersionRepository:
    """CRUD for experiment version lineage."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        experiment_id: UUID,
        circuit_qasm: str,
        *,
        optimisation_params: dict[str, str | int | float | bool | None] | None = None,
        provider: ExecutionProvider | None = None,
        seed: int | None = None,
        parent_version_id: UUID | None = None,
    ) -> ExperimentVersion:
        # Determine the next version number for this experiment.
        max_ver = await self.session.scalar(
            select(func.max(ExperimentVersionModel.version_number)).where(
                ExperimentVersionModel.experiment_id == experiment_id
            )
        )
        next_version = (max_ver or 0) + 1

        model = ExperimentVersionModel(
            experiment_id=experiment_id,
            version_number=next_version,
            circuit_hash=_circuit_hash(circuit_qasm),
            circuit_qasm=circuit_qasm,
            optimisation_params=optimisation_params or {},
            provider=provider.value if provider else None,
            seed=seed,
            parent_version_id=parent_version_id,
            created_at=datetime.now(UTC),
        )
        self.session.add(model)
        await self.session.flush()
        return self._to_contract(model)

    async def list_versions(self, experiment_id: UUID) -> list[ExperimentVersion]:
        rows = await self.session.scalars(
            select(ExperimentVersionModel)
            .where(ExperimentVersionModel.experiment_id == experiment_id)
            .order_by(ExperimentVersionModel.version_number.asc())
        )
        return [self._to_contract(r) for r in rows]

    async def get(self, version_id: UUID) -> ExperimentVersion | None:
        row = await self.session.scalar(select(ExperimentVersionModel).where(ExperimentVersionModel.id == version_id))
        return self._to_contract(row) if row else None

    @staticmethod
    def _to_contract(model: ExperimentVersionModel) -> ExperimentVersion:
        return ExperimentVersion(
            id=model.id,
            experiment_id=model.experiment_id,
            version_number=model.version_number,
            circuit_hash=model.circuit_hash,
            circuit_qasm=model.circuit_qasm,
            optimisation_params=model.optimisation_params,
            provider=ExecutionProvider(model.provider) if model.provider else None,
            seed=model.seed,
            parent_version_id=model.parent_version_id,
            created_at=model.created_at,
        )
