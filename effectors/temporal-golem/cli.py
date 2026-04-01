"""temporal-golem CLI — submit workflows and check status."""
from __future__ import annotations

import asyncio
import json
import sys
from datetime import timedelta
from pathlib import Path
from typing import Optional

import click

# Add this directory to path for workflow imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

TASK_QUEUE = "golem-tasks"


async def _get_client():
    """Create and return a Temporal client connection."""
    from temporalio.client import Client
    return await Client.connect("localhost:7233")


@click.group()
def main():
    """temporal-golem — Temporal-based golem task orchestrator."""
    pass


@main.command()
@click.option("-p", "--provider", default="zhipu", help="Golem provider (zhipu, infini, volcano)")
@click.option("-f", "--file", "task_file", default=None, help="Read tasks from file (one per line)")
@click.option("-w", "--workflow-id", default=None, help="Custom workflow ID")
@click.argument("tasks", nargs=-1)
def submit(provider: str, task_file: Optional[str], workflow_id: Optional[str], tasks: tuple[str, ...]):
    """Submit golem tasks to the Temporal workflow."""
    # Collect tasks from args and/or file
    all_tasks = list(tasks)

    if task_file:
        try:
            with open(task_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        all_tasks.append(line)
        except FileNotFoundError:
            click.echo(json.dumps({"error": f"File not found: {task_file}"}))
            sys.exit(1)

    if not all_tasks:
        click.echo("Error: no tasks provided. Pass TASK args or use --file.")
        sys.exit(1)

    specs = [{"task": t, "provider": provider} for t in all_tasks]

    if workflow_id is None:
        import secrets
        workflow_id = f"golem-{provider}-{secrets.token_hex(4)}"

    async def _submit():
        client = await _get_client()
        from workflow import GolemDispatchWorkflow
        handle = await client.start_workflow(
            GolemDispatchWorkflow.run,
            specs,
            id=workflow_id,
            task_queue=TASK_QUEUE,
        )
        return handle

    handle = asyncio.get_event_loop().run_until_complete(_submit())

    output = {
        "workflow_id": handle.id,
        "tasks_submitted": len(specs),
        "provider": provider,
        "status": "STARTED",
    }
    click.echo(json.dumps(output))


@main.command()
@click.argument("workflow_id")
def status(workflow_id: str):
    """Check status of a submitted workflow."""
    async def _status():
        client = await _get_client()
        handle = client.get_workflow_handle(workflow_id)
        desc = await handle.describe()
        result = None
        if desc.status.name == "COMPLETED":
            result = await handle.result()
        return desc, result

    desc, result = asyncio.get_event_loop().run_until_complete(_status())

    output = {
        "workflow_id": workflow_id,
        "status": desc.status.name,
        "run_id": desc.run_id,
        "start_time": str(desc.start_time),
    }
    if result is not None:
        output["result"] = result

    click.echo(json.dumps(output))


@main.command(name="list")
@click.option("-n", "--limit", default=10, help="Max workflows to return")
def list_workflows(limit: int):
    """List recent golem workflows."""
    async def _list():
        client = await _get_client()
        results = []
        async for wf in client.list_workflows(
            query="WorkflowType = 'GolemDispatchWorkflow'",
            page_size=limit,
        ):
            results.append({
                "workflow_id": wf.id,
                "status": wf.status.name,
                "start_time": str(wf.start_time),
            })
            if len(results) >= limit:
                break
        return results

    results = asyncio.get_event_loop().run_until_complete(_list())
    click.echo(json.dumps(results))


if __name__ == "__main__":
    main()
