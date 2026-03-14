from quantum_contracts import ExecutionProvider

from app.core.config import settings
from app.simulation.ibm_runtime_adapter import IbmRuntimeAdapter
from app.simulation.ionq_adapter import IonqAdapter
from app.simulation.providers import ExecutionProviderAdapter
from app.simulation.qiskit_adapter import LocalQiskitSimulator
from app.simulation.rigetti_adapter import RigettiAdapter


def get_provider(provider: ExecutionProvider) -> ExecutionProviderAdapter:
    if provider == ExecutionProvider.IBM_RUNTIME:
        if not settings.ibm_runtime_enabled:
            raise ValueError("IBM Runtime provider is disabled")
        return IbmRuntimeAdapter()
    if provider == ExecutionProvider.IONQ:
        return IonqAdapter()
    if provider == ExecutionProvider.RIGETTI:
        return RigettiAdapter()
    # LOCAL_SIMULATOR and SIMULATOR_AER both use the local Qiskit backend.
    return LocalQiskitSimulator()
