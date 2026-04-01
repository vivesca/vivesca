from __future__ import annotations

"""CLI for submitting golem workflows and checking status.

Usage::

    temporal-golem submit --provider zhipu --task "Write tests for foo.py"
    temporal-golem submit --file tasks.txt          # one task per line
    temporal-golem status <workflow-id>
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import List, Optional

import click

from temporalio.client import Client, WorkflowExecution, WorkflowFailureError

# Local imports — these work when invoked as a module from the project dir.
from worker import TASK_QUEUE
from workflow import (
    GolemDispatchInput,
    GolemDispatchOutput,
    GolemDispatchWorkflow,
    GolemTaskSpec,
)

TEMPORAL_ADDRESS_DEFAULT = "localhost:7233"


async def _connect(address: str) -> Client:
    return await Client.connect(address)


def _parse_task_file(path: str) -> List[GolemTaskSpec]:
    """Parse a task file: each non-empty line is ``provider|task``."""
    specs: list[GolemTaskSpec] = []
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "|" in line:
            provider, task = line.split("|", 1)
        else:
            provider, task = "zhipu", line
        specs.append(GolemTaskSpec(provider=provider.strip(), task=task.strip()))
    return specs


@click.group()
@click.option(
    "--address",
    envvar="TEMPORAL_ADDRESS",
    default=TEMPORAL_ADDRESS_DEFAULT,
    help="Temporal server gRPC address",
)
@click.pass_context
def cli(ctx: click.Context, address: str) -> None:
    """temporal-golem — submit and inspect golem dispatch workflows."""
    ctx.ensure_object(dict)
    ctx.obj["address"] = address


@cli.command()
@click.option("--provider", "-p", required=True, help="Provider name (zhipu, infini, volcano)")
@click.option("--task", "-t", "tasks", multiple=True, help="Task string (repeatable)")
@click.option("--file", "-f", "task_file", help="File with provider|task lines")
@click.option("--workflow-id", "-w", help="Custom workflow ID")
@click.pass_context
def submit(
    ctx: click.Context,
    provider: str,
    tasks: tuple[str, ...],
    task_file: Optional[str],
    workflow_id: Optional[str],
) -> None:
    """Submit a batch of golem tasks as a Temporal workflow."""
    specs: list[GolemTaskSpec] = []
    for t in tasks:
        specs.append(GolemTaskSpec(provider=provider, task=t))
    if task_file:
        specs.extend(_parse_task_file(task_file))

    if not specs:
        click.echo("No tasks provided. Use --task or --file.", err=True)
        raise SystemExit(1)

    address = ctx.obj["address"]
    input_data = GolemDispatchInput(tasks=specs)
    if not workflow_id:
        import datetime
        workflow_id = (
            f"golem-{provider}-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
        )

    async def _run() -> None:
        client = await _connect(address)
        handle = await client.start_workflow(
            GolemDispatchWorkflow.run,
            input_data,
            id=workflow_id,
            task_queue=TASK_QUEUE,
        )
        click.echo(f"Workflow started: {handle.id}")
        click.echo(f"  Task queue: {TASK_QUEUE}")
        click.echo(f"  Tasks: {len(specs)}")

    asyncio.run(_run())


@cli.command()
@click.argument("workflow_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def status(ctx: click.Context, workflow_id: str, as_json: bool) -> None:
    """Check the status of a dispatched workflow."""
    address = ctx.obj["address"]

    async def _run() -> None:
        client = await _connect(address)
        handle = client.get_workflow_handle(workflow_id)
        desc = await handle.describe()
        click.echo(f"Workflow:  {desc.id}")
        click.echo(f"Status:    {desc.status.name}")
        click.echo(f"Started:   {desc.start_time}")
        if desc.close_time:
            click.echo(f"Finished:  {desc.close_time}")

        if desc.status.name == "COMPLETED":
            try:
                result = await handle.result()
                if isinstance(result, GolemDispatchOutput):
                    if as_json:
                        click.echo(json.dumps({
                            "total": result.total,
                            "succeeded": result.succeeded,
                            "failed": result.failed,
                            "results": [
                                {
                                    "provider": r.provider,
                                    "task": r.task,
                                    "exit_code": r.exit_code,
                                    "ok": r.ok,
                                }
                                for r in result.results
                            ],
                        }, indent=2))
                    else:
                        click.echo(str(result))
                else:
                    click.echo(json.dumps(result, indent=2, default=str))
            except WorkflowFailureError as exc:
                click.echo(f"Workflow failed: {exc}", err=True)

    asyncio.run(_run())


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
