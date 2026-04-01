#!/usr/bin/env python3
from __future__ import annotations

"""temporal-golem CLI — submit workflows and check status.

Usage:
    temporal-golem submit --provider zhipu --task "Write tests"
    temporal-golem submit --provider zhipu --file tasks.txt
    temporal-golem status <workflow-id>
    temporal-golem status <workflow-id> --json
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import click
from temporalio.client import Client, WorkflowFailureError

# Re-export models for convenience
from models import GolemDispatchInput, GolemDispatchOutput, GolemResult, GolemTaskSpec  # noqa: F401


async def _connect() -> Client:
    """Connect to the local Temporal server."""
    return await Client.connect("localhost:7233")


def _parse_task_file(path: str) -> List[GolemTaskSpec]:
    """Parse a task file into a list of GolemTaskSpec.

    Each line is either ``provider|task`` (pipe-separated) or bare task text
    (defaults to provider ``zhipu``).  Blank lines and lines starting with
    ``#`` are skipped.
    """
    specs: List[GolemTaskSpec] = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "|" in line:
                provider, task = line.split("|", 1)
                specs.append(GolemTaskSpec(provider=provider.strip(), task=task.strip()))
            else:
                specs.append(GolemTaskSpec(provider="zhipu", task=line))
    return specs


@click.group()
def cli() -> None:
    """Temporal Golem — submit and monitor golem workflows."""


@cli.command()
@click.option("--provider", "-p", required=True, help="Golem provider (zhipu|infini|volcano)")
@click.option("--task", "-t", "tasks", multiple=True, help="Task description (repeatable)")
@click.option("--file", "-f", "task_file", default=None, help="File with tasks (provider|task per line)")
@click.option("--workflow-id", default=None, help="Custom workflow ID")
def submit(provider: str, tasks: tuple[str, ...], task_file: Optional[str], workflow_id: Optional[str]) -> None:
    """Submit a golem dispatch workflow."""
    specs: List[GolemTaskSpec] = []

    for t in tasks:
        specs.append(GolemTaskSpec(provider=provider, task=t))

    if task_file:
        file_specs = _parse_task_file(task_file)
        specs.extend(file_specs)

    if not specs:
        click.echo("Error: no tasks provided. Use --task or --file.", err=True)
        sys.exit(1)

    inp = GolemDispatchInput(tasks=specs)

    async def _do_submit() -> None:
        client = await _connect()
        if workflow_id:
            wid = workflow_id
        else:
            timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
            wid = f"golem-{provider}-{timestamp}"

        handle = await client.start_workflow(
            "GolemDispatchWorkflow",
            inp,
            id=wid,
            task_queue="golem-tasks",
        )
        click.echo(f"Workflow started: {handle.id}")

    asyncio.run(_do_submit())


@cli.command()
@click.argument("workflow_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def status(workflow_id: str, as_json: bool) -> None:
    """Check the status of a golem dispatch workflow."""
    async def _do_status() -> None:
        client = await _connect()
        handle = client.get_workflow_handle(workflow_id)
        desc = await handle.describe()

        status_name = desc.status.name
        click.echo(f"Workflow: {desc.id}")
        click.echo(f"Status:   {status_name}")
        click.echo(f"Started:  {desc.start_time}")

        if desc.close_time:
            click.echo(f"Finished: {desc.close_time}")

        if status_name == "COMPLETED":
            result = await handle.result()
            if as_json:
                data = {
                    "total": result.total,
                    "succeeded": result.succeeded,
                    "failed": result.failed,
                    "results": [
                        {
                            "provider": r.provider,
                            "task": r.task,
                            "exit_code": r.exit_code,
                            "ok": r.ok,
                            "timed_out": r.timed_out,
                        }
                        for r in result.results
                    ],
                }
                click.echo(json.dumps(data, indent=2))
            else:
                click.echo(str(result))

    asyncio.run(_do_status())


if __name__ == "__main__":
    cli()
