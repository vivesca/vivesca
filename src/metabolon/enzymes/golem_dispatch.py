"""golem_dispatch — MCP tool for direct Temporal workflow dispatch.

Actions: dispatch|batch|status|list|cancel

Connects to a Temporal server (default ganglion:7233) and manages
golem workflows directly — no markdown queue, no poller layer.
"""

import asyncio
import json
import os
import sys
import uuid
from typing import Any

from fastmcp.tools.function_tool import tool
from mcp.types import ToolAnnotations
from pydantic import Field

from metabolon.morphology import EffectorResult, Secretion

# Temporal host — override via TEMPORAL_HOST env var
TEMPORAL_HOST: str = os.environ.get("TEMPORAL_HOST", "100.120.158.22:7233")

# Allow import of GolemDispatchWorkflow from effectors/temporal-golem
sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "..", "..", "effectors", "temporal-golem"),
)


class QueueResult(Secretion):
    """Structured result for golem-dispatch operations."""

    output: str
    data: dict[str, Any] = Field(default_factory=dict)


# ── async helpers ─────────────────────────────────────────────────────────────


async def _get_client():
    """Create a Temporal client connected to TEMPORAL_HOST."""
    from temporalio.client import Client

    return await Client.connect(TEMPORAL_HOST)


async def _start_workflow(specs: list[dict]) -> dict[str, Any]:
    """Start a single Temporal workflow with the given task specs."""
    from workflow import GolemDispatchWorkflow

    client = await _get_client()
    provider = specs[0].get("provider", "zhipu") if specs else "zhipu"
    wf_id = f"golem-{provider}-{uuid.uuid4().hex[:8]}"

    handle = await client.start_workflow(
        GolemDispatchWorkflow.run,
        args=[specs],
        id=wf_id,
        task_queue="golem-tasks",
    )
    return {
        "workflow_id": handle.id,
        "tasks_submitted": len(specs),
    }


async def _get_workflow_status(workflow_id: str) -> dict[str, Any]:
    """Query a workflow by ID and return its current state."""
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


async def _list_workflows(
    limit: int = 10,
    status: str = "",
    provider: str = "",
) -> list[dict[str, Any]]:
    """List recent golem workflows, optionally filtered by status/provider."""
    client = await _get_client()
    clauses = ['WorkflowId STARTS_WITH "golem-"']
    if status:
        clauses.append(f'ExecutionStatus = "{status.capitalize()}"')
    if provider:
        clauses.append(f'GolemProvider = "{provider}"')
    query = " AND ".join(clauses)
    results: list[dict[str, Any]] = []
    async for wf in client.list_workflows(query=query, page_size=limit):
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


async def _get_workflow_result(workflow_id: str) -> dict[str, Any]:
    """Get the full result of a completed workflow."""
    client = await _get_client()
    handle = client.get_workflow_handle(workflow_id)
    desc = await handle.describe()
    if desc.status.name != "COMPLETED":
        return {"workflow_id": workflow_id, "status": desc.status.name, "result": None}
    result = await handle.result()
    return {"workflow_id": workflow_id, "status": "COMPLETED", "result": result}


async def _signal_workflow(workflow_id: str, signal: str) -> bool:
    """Send approve or reject signal to a workflow."""
    client = await _get_client()
    handle = client.get_workflow_handle(workflow_id)
    if signal == "approve":
        await handle.signal("approve_task", workflow_id)
    else:
        await handle.signal("reject_task", workflow_id)
    return True


async def _cancel_workflow(workflow_id: str) -> bool:
    """Cancel a running workflow. Returns True on success."""
    client = await _get_client()
    handle = client.get_workflow_handle(workflow_id)
    await handle.cancel()
    return True


# ── MCP tool ──────────────────────────────────────────────────────────────────


@tool(
    name="golem_dispatch",
    description="dispatch|batch|status|result|list|running|failed|approve|reject|cancel — Temporal golem dispatch",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def golem_dispatch(
    action: str,
    prompt: str = "",
    provider: str = "zhipu",
    max_turns: int = 15,
    workflow_id: str = "",
    specs: str = "",
    limit: int = 10,
    status_filter: str = "",
) -> QueueResult | EffectorResult:
    """Direct Temporal dispatch for golem tasks.

    Parameters
    ----------
    action : str
        One of: dispatch, batch, status, list, running, failed, cancel.
    prompt : str
        Task prompt (dispatch only).
    provider : str
        Provider name (default zhipu; also filters list/running/failed).
    max_turns : int
        Max agent turns (default 15, dispatch only).
    workflow_id : str
        Workflow identifier (status / cancel).
    specs : str
        JSON array of task specs (batch).
    limit : int
        Max workflows to return (list, default 10).
    status_filter : str
        Filter by workflow status: Running, Completed, Failed, etc. (list only).
    """
    action = action.lower().strip()

    # ── dispatch ───────────────────────────────────────────────────────────
    if action == "dispatch":
        if not prompt:
            return EffectorResult(
                success=False,
                message="dispatch requires: prompt",
            )
        task_specs = [{"task": prompt, "provider": provider, "max_turns": max_turns}]
        result = asyncio.run(_start_workflow(task_specs))
        return QueueResult(
            output=f"Dispatched workflow {result['workflow_id']}",
            data=result,
        )

    # ── batch ──────────────────────────────────────────────────────────────
    if action == "batch":
        try:
            parsed: list[dict] = json.loads(specs) if specs else []
        except json.JSONDecodeError:
            return EffectorResult(
                success=False,
                message="specs must be valid JSON",
            )
        if not parsed:
            return EffectorResult(
                success=False,
                message="batch requires non-empty specs",
            )
        result = asyncio.run(_start_workflow(parsed))
        return QueueResult(
            output=f"Dispatched batch workflow {result['workflow_id']}",
            data=result,
        )

    # ── status ─────────────────────────────────────────────────────────────
    if action == "status":
        if not workflow_id:
            return EffectorResult(
                success=False,
                message="status requires: workflow_id",
            )
        result = asyncio.run(_get_workflow_status(workflow_id))
        return QueueResult(
            output=f"Workflow {workflow_id}: {result['status']}",
            data=result,
        )

    # ── list ───────────────────────────────────────────────────────────────
    if action == "list":
        filter_provider = provider if provider != "zhipu" else ""
        workflows = asyncio.run(
            _list_workflows(limit=limit, status=status_filter, provider=filter_provider)
        )
        return QueueResult(
            output=f"Found {len(workflows)} workflow(s)",
            data={"workflows": workflows},
        )

    # ── running ───────────────────────────────────────────────────────────
    if action == "running":
        workflows = asyncio.run(_list_workflows(limit=limit, status="Running"))
        return QueueResult(
            output=f"{len(workflows)} running",
            data={"workflows": workflows},
        )

    # ── failed ────────────────────────────────────────────────────────────
    if action == "failed":
        workflows = asyncio.run(_list_workflows(limit=limit, status="Failed"))
        return QueueResult(
            output=f"{len(workflows)} failed",
            data={"workflows": workflows},
        )

    # ── result ─────────────────────────────────────────────────────────────
    if action == "result":
        if not workflow_id:
            return EffectorResult(success=False, message="result requires: workflow_id")
        data = asyncio.run(_get_workflow_result(workflow_id))
        if data["result"] is None:
            return QueueResult(
                output=f"{workflow_id} is {data['status']} (no result yet)",
                data=data,
            )
        return QueueResult(output=f"{workflow_id}: completed", data=data)

    # ── approve / reject ──────────────────────────────────────────────────
    if action in ("approve", "reject"):
        if not workflow_id:
            return EffectorResult(success=False, message=f"{action} requires: workflow_id")
        asyncio.run(_signal_workflow(workflow_id, action))
        return QueueResult(
            output=f"Sent {action} signal to {workflow_id}",
            data={"workflow_id": workflow_id, "signal": action},
        )

    # ── cancel ─────────────────────────────────────────────────────────────
    if action == "cancel":
        if not workflow_id:
            return EffectorResult(success=False, message="cancel requires: workflow_id")
        cancelled = asyncio.run(_cancel_workflow(workflow_id))
        if cancelled:
            return QueueResult(
                output=f"Cancelled workflow {workflow_id}",
                data={"workflow_id": workflow_id, "cancelled": True},
            )
        return EffectorResult(success=False, message=f"Failed to cancel {workflow_id}")

    return EffectorResult(
        success=False,
        message="Unknown action. Valid: dispatch, batch, status, result, list, running, failed, approve, reject, cancel",
    )
