from datetime import UTC, datetime

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
        return Experiment(
            id=model.id,
            name=model.name,
            description=model.description,
            circuit=CircuitPayload(qasm=model.circuit_qasm, shots=model.shots),
            created_at=model.created_at,
        )

    async def get(self, experiment_id: object) -> Experiment | None:
        model = await self.session.scalar(select(ExperimentModel).where(ExperimentModel.id == experiment_id))
        if model is None:
            return None
        return Experiment(
            id=model.id,
            name=model.name,
            description=model.description,
            circuit=CircuitPayload(qasm=model.circuit_qasm, shots=model.shots),
            created_at=model.created_at,
        )
