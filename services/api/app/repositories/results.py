from uuid import UUID

from quantum_contracts import ExecutionResult
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ResultModel


class ResultRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, result: ExecutionResult) -> ExecutionResult:
        model = ResultModel(
            job_id=result.job_id,
            provider=result.provider.value,
            backend=result.backend,
            result_payload=result.counts,
            shots=result.shots,
            duration_ms=result.duration_ms,
            completed_at=result.completed_at,
            circuit_depth=result.circuit_depth,
            qubit_count=result.qubit_count,
            gate_count=result.gate_count,
        )
        await self.session.merge(model)
        await self.session.flush()
        return result

    async def get_by_job_id(self, job_id: UUID) -> ExecutionResult | None:
        model = await self.session.scalar(select(ResultModel).where(ResultModel.job_id == job_id))
        if model is None:
            return None
        return ExecutionResult(
            job_id=model.job_id,
            provider=model.provider,
            backend=model.backend,
            counts=model.result_payload,
            shots=model.shots,
            duration_ms=model.duration_ms,
            completed_at=model.completed_at,
            circuit_depth=model.circuit_depth,
            qubit_count=model.qubit_count,
            gate_count=model.gate_count,
        )
