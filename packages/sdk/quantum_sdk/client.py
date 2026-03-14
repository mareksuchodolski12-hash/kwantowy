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
