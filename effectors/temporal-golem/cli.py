"""CLI for submitting golem workflows to Temporal."""
from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import timedelta
from pathlib import Path

import click


TASK_QUEUE = "golem-tasks"


def _get_client():
    from temporalio.client import Client

    host = os.environ.get("TEMPORAL_HOST", "localhost:7233")
    namespace = os.environ.get("TEMPORAL_NAMESPACE", "default")
    return Client.connect(host, namespace=namespace)


@click.group()
def main() -> None:
    """temporal-golem — submit and inspect golem workflows via Temporal.io."""


# ---------------------------------------------------------------------------
# submit
# ---------------------------------------------------------------------------

@main.command()
@click.option("--provider", "-p", default="zhipu",
              type=click.Choice(["zhipu", "infini", "volcano"]),
              help="Provider for all tasks (default: zhipu).")
@click.option("--max-turns", "-t", default=50, type=int,
              help="Max turns per task (default: 50).")
@click.option("--file", "-f", "filepath", type=click.Path(exists=True),
              help="Read task list from a file (one task per line).")
@click.option("--workflow-id", "-w", default=None,
              help="Custom workflow ID (auto-generated if omitted).")
@click.argument("task", nargs=-1)
def submit(provider: str, max_turns: int, filepath: str | None,
           workflow_id: str | None, task: tuple[str, ...]) -> None:
    """Submit one or more golem tasks as a Temporal workflow.

    \b
    Examples:
      temporal-golem submit -p zhipu "Write tests for foo.py"
      temporal-golem submit -p infini -f tasks.txt
      temporal-golem submit -p volcano "task one" "task two" "task three"
    """
    tasks = list(task)
    if filepath:
        with open(filepath) as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#"):
                    tasks.append(line)

    if not tasks:
        click.echo("Error: no tasks provided. Use TASK args or --file.", err=True)
        raise SystemExit(1)

    specs = [{"task": t, "provider": provider, "max_turns": max_turns} for t in tasks]

    async def _run() -> str:
        from workflow import GolemDispatchWorkflow

        client = await _get_client()
        wid = workflow_id or f"golem-{provider}-{os.urandom(4).hex()}"
        handle = await client.start_workflow(
            GolemDispatchWorkflow.run,
            args=[specs],
            id=wid,
            task_queue=TASK_QUEUE,
            run_timeout=timedelta(hours=2),
        )
        return handle.id

    wf_id = asyncio.run(_run())
    click.echo(json.dumps({"workflow_id": wf_id, "tasks_submitted": len(tasks)}, indent=2))


# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------

@main.command()
@click.argument("workflow_id")
def status(workflow_id: str) -> None:
    """Show the status of a submitted workflow."""
    async def _run() -> dict:
        client = await _get_client()
        handle = client.get_workflow_handle(workflow_id)
        desc = await handle.describe()
        result = {
            "workflow_id": workflow_id,
            "status": desc.status.name,
            "run_id": desc.run_id,
            "start_time": str(desc.start_time) if desc.start_time else None,
        }
        if desc.status.name == "COMPLETED":
            try:
                raw = await handle.result()
                result["result"] = raw
            except Exception as exc:
                result["result_error"] = str(exc)
        return result

    data = asyncio.run(_run())
    click.echo(json.dumps(data, indent=2, default=str))


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------

@main.command("list")
@click.option("--limit", "-n", default=20, type=int, help="Max workflows to list.")
def list_workflows(limit: int) -> None:
    """List recent golem workflows."""
    async def _run() -> list[dict]:
        client = await _get_client()
        workflows = []
        async for wf in client.list_workflows(
            query="WorkflowType = 'GolemDispatchWorkflow'",
            page_size=limit,
        ):
            workflows.append({
                "workflow_id": wf.id,
                "status": wf.status.name,
                "start_time": str(wf.start_time) if wf.start_time else None,
            })
            if len(workflows) >= limit:
                break
        return workflows

    data = asyncio.run(_run())
    click.echo(json.dumps(data, indent=2, default=str))


if __name__ == "__main__":
    main()
