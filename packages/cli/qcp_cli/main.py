"""Quantum Control Plane CLI.

Usage:
    qcp login
    qcp experiment run <file> --provider <provider>
    qcp experiment list
    qcp run status <job_id>
    qcp result show <job_id>
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from qcp_cli.config import get_api_key, get_base_url, save_config

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="qcp")
def cli() -> None:
    """Quantum Control Plane CLI — run quantum experiments from your terminal."""


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


@cli.command()
@click.option("--api-key", prompt="API Key", hide_input=True, help="Your QCP API key")
@click.option("--url", default="http://localhost:8000", help="QCP API base URL")
def login(api_key: str, url: str) -> None:
    """Store API credentials for future commands."""
    save_config(api_key=api_key, base_url=url)
    console.print("[green]✓[/green] Credentials saved.")


# ---------------------------------------------------------------------------
# Experiment commands
# ---------------------------------------------------------------------------


@cli.group()
def experiment() -> None:
    """Manage experiments."""


@experiment.command("run")
@click.argument("file", type=click.Path(exists=True))
@click.option("--provider", default="local_simulator", help="Execution provider")
@click.option("--shots", default=1024, type=int, help="Number of shots")
@click.option("--name", default=None, help="Experiment name (defaults to filename)")
@click.option("--wait/--no-wait", default=False, help="Wait for result")
def experiment_run(file: str, provider: str, shots: int, name: str | None, wait: bool) -> None:
    """Submit a QASM circuit for execution."""
    from quantum_sdk import QCPClient

    qasm = Path(file).read_text()
    exp_name = name or Path(file).stem

    client = QCPClient(api_key=get_api_key(), base_url=get_base_url())
    with console.status("Submitting experiment…"):
        resp = client.run_circuit(name=exp_name, qasm=qasm, shots=shots, provider=provider)

    job_id = resp["job"]["id"]
    console.print(f"[green]✓[/green] Experiment submitted")
    console.print(f"  Job ID:  {job_id}")
    console.print(f"  Status:  {resp['job']['status']}")

    if wait:
        with console.status("Waiting for result…"):
            result = client.wait_for_result(job_id, poll_interval=1.0, max_wait=120)
        console.print("\n[bold]Result:[/bold]")
        console.print_json(json.dumps(result, indent=2, default=str))


@experiment.command("list")
def experiment_list() -> None:
    """List all experiments."""
    import httpx

    resp = httpx.get(
        f"{get_base_url()}/v1/experiments",
        headers={"X-API-Key": get_api_key()},
        timeout=30.0,
    )
    resp.raise_for_status()
    experiments = resp.json().get("experiments", [])

    table = Table(title="Experiments")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="bold")
    table.add_column("Shots", justify="right")
    table.add_column("Created")

    for exp in experiments:
        table.add_row(
            exp["id"][:8],
            exp["name"],
            str(exp["circuit"]["shots"]),
            exp["created_at"][:19],
        )

    console.print(table)


# ---------------------------------------------------------------------------
# Run commands
# ---------------------------------------------------------------------------


@cli.group("run")
def run_group() -> None:
    """Inspect job runs."""


@run_group.command("status")
@click.argument("job_id")
def run_status(job_id: str) -> None:
    """Show the status of a job."""
    from quantum_sdk import QCPClient

    client = QCPClient(api_key=get_api_key(), base_url=get_base_url())
    job = client.get_job(job_id)

    console.print(f"[bold]Job {job_id[:8]}[/bold]")
    console.print(f"  Status:   {job['status']}")
    console.print(f"  Provider: {job['provider']}")
    console.print(f"  Attempts: {job['attempts']}")
    console.print(f"  Updated:  {job['updated_at']}")


# ---------------------------------------------------------------------------
# Result commands
# ---------------------------------------------------------------------------


@cli.group()
def result() -> None:
    """View execution results."""


@result.command("show")
@click.argument("job_id")
def result_show(job_id: str) -> None:
    """Display results for a completed job."""
    from quantum_sdk import QCPClient

    client = QCPClient(api_key=get_api_key(), base_url=get_base_url())
    res = client.get_results(job_id)

    if res is None:
        console.print("[yellow]No results available yet.[/yellow]")
        sys.exit(1)

    result_data = res.get("result", res)
    console.print(f"[bold]Results for job {job_id[:8]}[/bold]")
    console.print(f"  Provider: {result_data.get('provider', 'N/A')}")
    console.print(f"  Backend:  {result_data.get('backend', 'N/A')}")
    console.print(f"  Shots:    {result_data.get('shots', 'N/A')}")
    console.print(f"  Duration: {result_data.get('duration_ms', 'N/A')}ms")
    console.print("\n[bold]Counts:[/bold]")
    counts = result_data.get("counts", {})
    for state, count in sorted(counts.items()):
        console.print(f"  |{state}⟩  {count}")


def main() -> None:
    """Entry point."""
    cli()


if __name__ == "__main__":
    main()
