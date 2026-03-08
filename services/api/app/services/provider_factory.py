from quantum_contracts import ExecutionProvider

from app.core.config import settings
from app.simulation.ibm_runtime_adapter import IbmRuntimeAdapter
from app.simulation.providers import ExecutionProviderAdapter
from app.simulation.qiskit_adapter import LocalQiskitSimulator


def get_provider(provider: ExecutionProvider) -> ExecutionProviderAdapter:
    if provider == ExecutionProvider.IBM_RUNTIME:
        if not settings.ibm_runtime_enabled:
            raise ValueError("IBM Runtime provider is disabled")
        return IbmRuntimeAdapter()
    return LocalQiskitSimulator()
