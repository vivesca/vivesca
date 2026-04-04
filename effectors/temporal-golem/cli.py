#!/usr/bin/env python3
"""CLI for submitting and inspecting golem Temporal workflows.

Usage:
    temporal-golem submit -p zhipu "Write tests for foo.py"
    temporal-golem submit -p volcano -f tasks.txt
    temporal-golem status <workflow-id>
    temporal-golem list [-n 10]
"""

from __future__ import annotations

import asyncio
import json
import sys
import uuid
from pathlib import Path

import click
from temporalio.client import Client
from workflow import GolemDispatchWorkflow


async def _get_client(target_host: str = "localhost:7233") -> Client:
    """Create a Temporal client connected to the given host."""
    return await Client.connect(target_host)


@click.group()
def main():
    """Temporal golem orchestrator CLI."""
    pass


@main.command()
@click.option("-p", "--provider", default="zhipu", help="Provider name")
@click.option("-w", "--workflow-id", default=None, help="Custom workflow ID")
@click.option("-f", "--file", "filepath", default=None, help="Read tasks from file")
@click.option("--max-turns", default=50, type=int, help="Max turns per task")
@click.argument("tasks", nargs=-1)
def submit(
    provider: str,
    workflow_id: str | None,
    filepath: str | None,
    max_turns: int,
    tasks: tuple[str, ...],
):
    """Submit one or more golem tasks as a Temporal workflow."""
    task_list = list(tasks)

    if filepath:
        lines = Path(filepath).read_text().splitlines()
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                task_list.append(stripped)

    if not task_list:
        click.echo(json.dumps({"error": "no tasks provided"}))
        sys.exit(1)

    specs = [{"task": t, "provider": provider, "max_turns": max_turns} for t in task_list]

    wf_id = workflow_id or f"golem-{provider}-{uuid.uuid4().hex[:8]}"

    async def _run():
        client = await _get_client()
        handle = await client.start_workflow(
            GolemDispatchWorkflow.run,
            args=[specs],
            id=wf_id,
            task_queue="golem-tasks",
        )
        return handle

    handle = asyncio.run(_run())
    click.echo(
        json.dumps(
            {
                "workflow_id": handle.id,
                "tasks_submitted": len(specs),
                "provider": provider,
            }
        )
    )


@main.command()
@click.argument("workflow_id")
def status(workflow_id: str):
    """Show the status of a golem workflow."""

    async def _run():
        client = await _get_client()
        handle = client.get_workflow_handle(workflow_id)
        desc = await handle.describe()
        result = None
        if desc.status.name == "COMPLETED":
            result = await handle.result()
        return {
            "workflow_id": workflow_id,
            "status": desc.status.name,
            "run_id": desc.run_id,
            "start_time": str(desc.start_time),
            "result": result,
        }

    output = asyncio.run(_run())
    click.echo(json.dumps(output, default=str))


@main.command(name="list")
@click.option("-n", "--limit", default=10, type=int, help="Max workflows to show")
def list_workflows(limit: int):
    """List recent golem workflows."""

    async def _run():
        client = await _get_client()
        results = []
        async for wf in client.list_workflows(
            query="WorkflowId STARTS_WITH 'golem-'",
            page_size=limit,
        ):
            results.append(
                {
                    "workflow_id": wf.id,
                    "status": wf.status.name,
                    "start_time": str(wf.start_time),
                }
            )
            if len(results) >= limit:
                break
        return results

    output = asyncio.run(_run())
    click.echo(json.dumps(output, default=str))


if __name__ == "__main__":
    main()
