#!/usr/bin/env python3
"""Quickstart: submit a Bell-state circuit and retrieve results.

Prerequisites:
    pip install packages/sdk
    # API server running at http://localhost:8000

Usage:
    # 1. Generate an API key (one-time setup)
    python examples/quickstart.py --generate-key

    # 2. Run a circuit
    QCP_API_KEY=qcp_... python examples/quickstart.py
"""

import argparse
import json
import os
import sys

import httpx

BASE_URL = os.getenv("QCP_BASE_URL", "http://localhost:8000")

BELL_QASM = (
    'OPENQASM 2.0;\n'
    'include "qelib1.inc";\n'
    'qreg q[2];\n'
    'creg c[2];\n'
    'h q[0];\n'
    'cx q[0],q[1];\n'
    'measure q -> c;\n'
)


def generate_key(name: str) -> None:
    resp = httpx.post(f"{BASE_URL}/v1/api-keys", json={"name": name})
    resp.raise_for_status()
    data = resp.json()
    print(f"API key created!\n  ID:  {data['id']}\n  Key: {data['key']}")
    print("\nSet it as an environment variable:")
    print(f"  export QCP_API_KEY={data['key']}")


def run_circuit(api_key: str) -> None:
    try:
        from quantum_sdk import QCPClient
    except ImportError:
        print("SDK not installed. Run: pip install packages/sdk")
        sys.exit(1)

    client = QCPClient(api_key=api_key, base_url=BASE_URL)

    print("Submitting Bell-state circuit...")
    submission = client.run_circuit(
        name="bell-state-example",
        qasm=BELL_QASM,
        shots=1024,
        description="Quickstart Bell state circuit",
    )
    job_id = submission["job"]["id"]
    print(f"  Job ID: {job_id}  Status: {submission['job']['status']}")

    print("Waiting for result...")
    result = client.wait_for_result(job_id, poll_interval=0.5, max_wait=60)
    print("\nResult:")
    print(json.dumps(result, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Quantum Control Plane quickstart")
    parser.add_argument("--generate-key", metavar="NAME", help="Generate a new API key with the given name")
    args = parser.parse_args()

    if args.generate_key:
        generate_key(args.generate_key)
        return

    api_key = os.getenv("QCP_API_KEY")
    if not api_key:
        print("Error: QCP_API_KEY environment variable not set.")
        print("Run: python examples/quickstart.py --generate-key mykey")
        sys.exit(1)

    run_circuit(api_key)


if __name__ == "__main__":
    main()
