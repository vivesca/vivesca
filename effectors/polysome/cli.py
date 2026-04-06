#!/usr/bin/env python3
"""CLI for submitting and inspecting polysome Temporal workflows.

Usage:
    polysome submit -p zhipu "Write tests for foo.py"
    polysome submit -p volcano -f tasks.txt
    polysome status <workflow-id>
    polysome list [-n 10]
"""

from __future__ import annotations

import asyncio
import json
import sys
import uuid
from pathlib import Path

import click
from temporalio.client import Client
from workflow import TranslationWorkflow


async def _get_client(target_host: str = "localhost:7233") -> Client:
    """Create a Temporal client connected to the given host."""
    return await Client.connect(target_host)


@click.group()
def main():
    """Polysome translation orchestrator CLI."""
    pass


@main.command()
@click.option("-p", "--provider", default="zhipu", help="Provider name")
@click.option("-w", "--workflow-id", default=None, help="Custom workflow ID")
@click.option("-f", "--file", "filepath", default=None, help="Read tasks from file")
@click.argument("tasks", nargs=-1)
def submit(
    provider: str,
    workflow_id: str | None,
    filepath: str | None,
    tasks: tuple[str, ...],
):
    """Submit one or more translation tasks as a Temporal workflow."""
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

    specs = [{"task": t, "provider": provider} for t in task_list]

    wf_id = workflow_id or f"ribosome-{provider}-{uuid.uuid4().hex[:8]}"

    async def _run():
        client = await _get_client()
        handle = await client.start_workflow(
            TranslationWorkflow.run,
            args=[specs],
            id=wf_id,
            task_queue="translation-queue",
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
    """Show the status of a translation workflow."""

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
    """List recent translation workflows."""

    async def _run():
        client = await _get_client()
        results = []
        async for wf in client.list_workflows(
            query="WorkflowId STARTS_WITH 'ribosome-'",
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
