"""Synchronous and asynchronous clients for the Quantum Control Plane API."""

from __future__ import annotations

from typing import Any

import httpx

DEFAULT_BASE_URL = "http://localhost:8000"


class QCPClient:
    """Simple synchronous client for the Quantum Control Plane API.

    Example::

        from quantum_sdk import QCPClient

        client = QCPClient(api_key="qcp_...", base_url="http://localhost:8000")
        resp = client.run_circuit(
            name="my-bell-circuit",
            qasm='OPENQASM 2.0; include "qelib1.inc"; qreg q[2]; creg c[2]; h q[0]; cx q[0],q[1]; measure q -> c;',
            shots=1024,
        )
        job_id = resp["job"]["id"]
        result = client.get_results(job_id)
        print(result)
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json",
        }
        self._timeout = timeout

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def run_circuit(
        self,
        name: str,
        qasm: str,
        shots: int = 1024,
        provider: str = "local_simulator",
        description: str | None = None,
        max_attempts: int = 3,
        timeout_seconds: int = 30,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Submit a quantum circuit for execution.

        Returns the response dict containing ``experiment`` and ``job`` keys.
        """
        payload: dict[str, Any] = {
            "name": name,
            "provider": provider,
            "circuit": {"qasm": qasm, "shots": shots},
            "retry_policy": {"max_attempts": max_attempts, "timeout_seconds": timeout_seconds},
        }
        if description is not None:
            payload["description"] = description
        headers = dict(self._headers)
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        resp = httpx.post(
            f"{self._base}/v1/experiments",
            json=payload,
            headers=headers,
            timeout=self._timeout,
        )
        resp.raise_for_status()
        return resp.json()  # type: ignore[no-any-return]

    def get_job(self, job_id: str) -> dict[str, Any]:
        """Retrieve job status by ID."""
        resp = httpx.get(
            f"{self._base}/v1/jobs/{job_id}",
            headers=self._headers,
            timeout=self._timeout,
        )
        resp.raise_for_status()
        return resp.json()  # type: ignore[no-any-return]

    def get_results(self, job_id: str) -> dict[str, Any] | None:
        """Retrieve execution results for a job. Returns None if not ready yet."""
        resp = httpx.get(
            f"{self._base}/v1/results/{job_id}",
            headers=self._headers,
            timeout=self._timeout,
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()  # type: ignore[no-any-return]

    def run_experiment(
        self,
        name: str,
        qasm: str,
        shots: int = 1024,
        provider: str = "local_simulator",
        description: str | None = None,
    ) -> dict[str, Any]:
        """High-level helper that mirrors the SDK example in the docs.

        Returns the full response dict (with ``experiment`` and ``job`` keys).
        """
        return self.run_circuit(name=name, qasm=qasm, shots=shots, provider=provider, description=description)

    def list_experiments(self) -> list[dict[str, Any]]:
        """List all experiments."""
        resp = httpx.get(
            f"{self._base}/v1/experiments",
            headers=self._headers,
            timeout=self._timeout,
        )
        resp.raise_for_status()
        return resp.json()["experiments"]  # type: ignore[no-any-return]

    def list_jobs(self) -> list[dict[str, Any]]:
        """List all jobs."""
        resp = httpx.get(
            f"{self._base}/v1/jobs",
            headers=self._headers,
            timeout=self._timeout,
        )
        resp.raise_for_status()
        return resp.json()["jobs"]  # type: ignore[no-any-return]

    def wait_for_result(
        self,
        job_id: str,
        poll_interval: float = 1.0,
        max_wait: float = 120.0,
    ) -> dict[str, Any]:
        """Poll until the job succeeds or fails, then return the result."""
        import time

        deadline = time.monotonic() + max_wait
        while time.monotonic() < deadline:
            job = self.get_job(job_id)
            status = job.get("status")
            if status == "succeeded":
                result = self.get_results(job_id)
                if result:
                    return result
            elif status == "failed":
                raise RuntimeError(f"Job {job_id} failed after {job.get('attempts')} attempts")
            time.sleep(poll_interval)
        raise TimeoutError(f"Job {job_id} did not complete within {max_wait}s")

    # ------------------------------------------------------------------
    # Providers
    # ------------------------------------------------------------------

    def list_providers(self) -> list[dict[str, Any]]:
        """List all registered quantum execution providers with capabilities."""
        resp = httpx.get(
            f"{self._base}/v1/providers",
            headers=self._headers,
            timeout=self._timeout,
        )
        resp.raise_for_status()
        return resp.json()  # type: ignore[no-any-return]

    def select_provider(
        self,
        qubit_count: int,
        circuit_depth: int,
        priority: str = "fidelity",
    ) -> dict[str, Any]:
        """Select the best provider for given circuit requirements."""
        resp = httpx.post(
            f"{self._base}/v1/providers/select",
            json={
                "qubit_count": qubit_count,
                "circuit_depth": circuit_depth,
                "priority": priority,
            },
            headers=self._headers,
            timeout=self._timeout,
        )
        resp.raise_for_status()
        return resp.json()  # type: ignore[no-any-return]

    # ------------------------------------------------------------------
    # Circuit Optimisation
    # ------------------------------------------------------------------

    def optimise_circuit(
        self,
        qasm: str,
        strategy: str = "light",
    ) -> dict[str, Any]:
        """Optimise a quantum circuit before execution."""
        resp = httpx.post(
            f"{self._base}/v1/circuits/optimise",
            json={
                "circuit": {"qasm": qasm},
                "config": {"strategy": strategy},
            },
            headers=self._headers,
            timeout=self._timeout,
        )
        resp.raise_for_status()
        return resp.json()  # type: ignore[no-any-return]

    # ------------------------------------------------------------------
    # Benchmarks
    # ------------------------------------------------------------------

    def list_benchmarks(self) -> list[dict[str, Any]]:
        """Return the latest benchmark for every provider."""
        resp = httpx.get(
            f"{self._base}/v1/benchmarks",
            headers=self._headers,
            timeout=self._timeout,
        )
        resp.raise_for_status()
        return resp.json().get("benchmarks", [])  # type: ignore[no-any-return]

    # ------------------------------------------------------------------
    # Result Comparison
    # ------------------------------------------------------------------

    def compare_results(
        self,
        experiment_name: str,
        job_ids: list[str],
        reference_distribution: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        """Compare execution results across providers."""
        payload: dict[str, Any] = {
            "experiment_name": experiment_name,
            "job_ids": job_ids,
        }
        if reference_distribution is not None:
            payload["reference_distribution"] = reference_distribution
        resp = httpx.post(
            f"{self._base}/v1/results/compare",
            json=payload,
            headers=self._headers,
            timeout=self._timeout,
        )
        resp.raise_for_status()
        return resp.json()  # type: ignore[no-any-return]

    # ------------------------------------------------------------------
    # Experiment Versioning
    # ------------------------------------------------------------------

    def create_experiment_version(
        self,
        experiment_id: str,
        circuit_qasm: str,
        provider: str | None = None,
        optimisation_params: dict[str, Any] | None = None,
        seed: int | None = None,
        parent_version_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a new version for an experiment."""
        payload: dict[str, Any] = {"circuit_qasm": circuit_qasm}
        if provider is not None:
            payload["provider"] = provider
        if optimisation_params is not None:
            payload["optimisation_params"] = optimisation_params
        if seed is not None:
            payload["seed"] = seed
        if parent_version_id is not None:
            payload["parent_version_id"] = parent_version_id
        resp = httpx.post(
            f"{self._base}/v1/experiments/{experiment_id}/versions",
            json=payload,
            headers=self._headers,
            timeout=self._timeout,
        )
        resp.raise_for_status()
        return resp.json()  # type: ignore[no-any-return]

    def list_experiment_versions(self, experiment_id: str) -> list[dict[str, Any]]:
        """List all versions of an experiment."""
        resp = httpx.get(
            f"{self._base}/v1/experiments/{experiment_id}/versions",
            headers=self._headers,
            timeout=self._timeout,
        )
        resp.raise_for_status()
        return resp.json().get("versions", [])  # type: ignore[no-any-return]
