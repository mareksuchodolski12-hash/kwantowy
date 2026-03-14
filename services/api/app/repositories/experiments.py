from datetime import UTC, datetime
from uuid import UUID

from quantum_contracts import CircuitPayload, Experiment
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ExperimentModel


class ExperimentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        name: str,
        description: str | None,
        circuit: CircuitPayload,
    ) -> Experiment:
        now = datetime.now(UTC)
        model = ExperimentModel(
            name=name,
            description=description,
            circuit_qasm=circuit.qasm,
            shots=circuit.shots,
            created_at=now,
        )
        self.session.add(model)
        await self.session.flush()
        return self._to_contract(model)

    async def get(self, experiment_id: UUID) -> Experiment | None:
        model = await self.session.scalar(select(ExperimentModel).where(ExperimentModel.id == experiment_id))
        if model is None:
            return None
        return self._to_contract(model)

    async def list(self, limit: int = 100) -> list[Experiment]:
        rows = await self.session.scalars(
            select(ExperimentModel).order_by(ExperimentModel.created_at.desc()).limit(limit)
        )
        return [self._to_contract(m) for m in rows]

    def _to_contract(self, model: ExperimentModel) -> Experiment:
        return Experiment(
            id=model.id,
            name=model.name,
            description=model.description,
            circuit=CircuitPayload(qasm=model.circuit_qasm, shots=model.shots),
            created_at=model.created_at,
        )
