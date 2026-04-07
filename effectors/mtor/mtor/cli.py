"""mtor CLI — cyclopts app definition and command handlers.

Every response is a JSON envelope:
  ok:true   -> {"ok": true, "command": "...", "result": {...}, "next_actions": [...]}
  ok:false  -> {"ok": false, "command": "...", "error": {"message": "...", "code": "..."},
                "fix": "...", "next_actions": [...]}

Exit codes:
  0 - ok
  1 - error (generic, non-temporal)
  2 - usage error (missing required args)
  3 - temporal unreachable
  4 - workflow not found
"""

from __future__ import annotations

import asyncio
import contextlib
import subprocess
import sys
from typing import Annotated, Any, Literal

from cyclopts import App, Parameter
from porin import action as _action

from mtor import (
    LOG_TAIL_LINES,
    RIBOSOME_OUTPUTS_DIR,
    TEMPORAL_HOST,
    VERSION,
)
from mtor.client import _get_client
from mtor.dispatch import _dispatch_prompt
from mtor.doctor import doctor as _doctor
from mtor.envelope import _err, _extract_first_result, _ok
from mtor.tree import tree

# ---------------------------------------------------------------------------
# Cyclopts CLI
# ---------------------------------------------------------------------------

app = App(help_flags=[], version_flags=[])


@app.default
def default_handler(
    prompt: str | None = None,
    *,
    provider: Annotated[str, Parameter(name=["-p", "--provider"])] = "zhipu",
    experiment: Annotated[bool, Parameter(name=["-x", "--experiment"])] = False,
) -> None:
    """Bare invocation returns command tree; with a prompt, dispatches to Temporal."""
    if prompt is None:
        _ok("mtor", tree.to_dict(), version=VERSION)
    else:
        _dispatch_prompt(prompt, provider=provider, experiment=experiment)


@app.command(name="list")
def list_cmd(
    *,
    status: Literal["RUNNING", "COMPLETED", "FAILED", "CANCELED", "TERMINATED"] | None = None,
    count: int = 10,
) -> None:
    """List recent workflows."""
    cmd = "mtor list" + (f" --status {status}" if status else "") + f" --count {count}"

    client, err = _get_client()
    if err:
        sys.exit(
            _err(
                cmd,
                f"Cannot connect to Temporal at {TEMPORAL_HOST}: {err}",
                "TEMPORAL_UNREACHABLE",
                "Start Temporal worker on ganglion: ssh ganglion 'sudo systemctl start temporal-worker'",
                [_action("mtor doctor", "Run health check to diagnose connectivity")],
                exit_code=3,
            )
        )

    try:
        query_filter = ""
        if status:
            query_filter = f"ExecutionStatus = '{status}'"

        async def _list():
            results = []
            async for execution in client.list_workflows(
                query=query_filter if query_filter else None
            ):
                results.append(execution)
                if len(results) >= count:
                    break
            return results

        executions = asyncio.run(_list())
        workflows = []
        next_actions = []
        for ex in executions:
            wf_id = ex.id
            status_val = ex.status.name if ex.status else "UNKNOWN"
            start_time = ex.start_time.isoformat() if ex.start_time else None
            close_time = ex.close_time.isoformat() if ex.close_time else None
            workflows.append(
                {
                    "workflow_id": wf_id,
                    "status": status_val,
                    "start_time": start_time,
                    "close_time": close_time,
                }
            )
            next_actions.append(_action(f"mtor status {wf_id}", f"Get full status for {wf_id}"))

        _ok(cmd, {"workflows": workflows, "count": len(workflows)}, next_actions, version=VERSION)
    except Exception as exc:
        sys.exit(
            _err(
                cmd,
                str(exc),
                "LIST_ERROR",
                "Check Temporal server health with: mtor doctor",
                [_action("mtor doctor", "Run health check")],
            )
        )


@app.command
def status(workflow_id: str) -> None:
    """Query status of a single workflow."""
    cmd = f"mtor status {workflow_id}"

    client, err = _get_client()
    if err:
        sys.exit(
            _err(
                cmd,
                f"Cannot connect to Temporal at {TEMPORAL_HOST}: {err}",
                "TEMPORAL_UNREACHABLE",
                "Start Temporal worker on ganglion: ssh ganglion 'sudo systemctl start temporal-worker'",
                [_action("mtor doctor", "Run health check to diagnose connectivity")],
                exit_code=3,
            )
        )

    try:

        async def _status():
            handle = client.get_workflow_handle(workflow_id)
            desc = await handle.describe()
            wf_result = None
            if desc.status and desc.status.name == "COMPLETED":
                with contextlib.suppress(Exception):
                    wf_result = await handle.result()
            return desc, wf_result

        desc, wf_result = asyncio.run(_status())
        status_val = desc.status.name if desc.status else "UNKNOWN"
        start_time = desc.start_time.isoformat() if desc.start_time else None
        close_time = desc.close_time.isoformat() if desc.close_time else None

        result_payload: dict[str, Any] = {
            "workflow_id": workflow_id,
            "status": status_val,
            "start_time": start_time,
            "close_time": close_time,
        }
        if wf_result and isinstance(wf_result, dict):
            task_result = _extract_first_result(wf_result)
            if task_result:
                result_payload["success"] = task_result.get("success")
                result_payload["exit_code"] = task_result.get("exit_code")
                result_payload["provider"] = task_result.get("provider")
                result_payload["task_preview"] = task_result.get("task", "")[:120]
                result_payload["output_path"] = task_result.get("review", {}).get(
                    "output_path", ""
                )
                result_payload["merged"] = task_result.get("merged")
                result_payload["verdict"] = task_result.get("review", {}).get("verdict")

        _ok(
            cmd,
            result_payload,
            [
                _action(f"mtor logs {workflow_id}", "Fetch last 30 lines of output"),
                _action(f"mtor cancel {workflow_id}", "Cancel this workflow"),
            ],
            version=VERSION,
        )
    except Exception as exc:
        exc_str = str(exc)
        if "not found" in exc_str.lower() or "workflow_not_found" in exc_str.lower():
            sys.exit(
                _err(
                    cmd,
                    f"Workflow {workflow_id} not found",
                    "WORKFLOW_NOT_FOUND",
                    "Verify the workflow ID with: mtor list",
                    [_action("mtor list", "List all recent workflows")],
                    exit_code=4,
                )
            )
        sys.exit(
            _err(
                cmd,
                exc_str,
                "STATUS_ERROR",
                "Check Temporal server health with: mtor doctor",
                [_action("mtor doctor", "Run health check")],
            )
        )


@app.command
def logs(workflow_id: str) -> None:
    """Fetch last 30 lines of workflow output from ganglion."""
    cmd = f"mtor logs {workflow_id}"

    # Step 1: Query Temporal for the workflow result to get output_path
    log_path = ""
    client, client_err = _get_client()
    if client and not client_err:
        try:

            async def _get_output_path():
                handle = client.get_workflow_handle(workflow_id)
                wf_result = await handle.result()
                if isinstance(wf_result, dict):
                    task_result = _extract_first_result(wf_result)
                    if task_result:
                        return task_result.get("review", {}).get("output_path", "")
                return ""

            log_path = asyncio.run(_get_output_path())
        except Exception:
            pass

    # Step 2: If no output_path from result, fall back to ls + grep
    if not log_path:
        try:
            find_result = subprocess.run(
                ["ssh", "ganglion", f"ls -t {RIBOSOME_OUTPUTS_DIR}/*.txt 2>/dev/null | head -20"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if find_result.returncode == 0:
                # Extract the hex suffix from workflow_id (e.g. ribosome-zhipu-af3c43d1 -> af3c43d1)
                wf_suffix = workflow_id.rsplit("-", 1)[-1] if "-" in workflow_id else workflow_id
                for line in find_result.stdout.strip().splitlines():
                    fname = line.strip().rsplit("/", 1)[-1]
                    if wf_suffix in fname:
                        log_path = line.strip()
                        break
        except (subprocess.TimeoutExpired, OSError):
            pass

    if not log_path:
        sys.exit(
            _err(
                cmd,
                f"No log file found for workflow {workflow_id}",
                "LOG_NOT_FOUND",
                f"Verify the workflow ID with: mtor status {workflow_id}",
                [_action(f"mtor status {workflow_id}", "Check if workflow exists")],
                exit_code=4,
            )
        )

    try:
        result = subprocess.run(
            ["ssh", "ganglion", f"tail -{LOG_TAIL_LINES} {log_path}"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            stderr_msg = result.stderr.strip()
            if "no such file" in stderr_msg.lower() or "not found" in stderr_msg.lower():
                sys.exit(
                    _err(
                        cmd,
                        f"Log file not found on ganglion: {log_path}",
                        "LOG_NOT_FOUND",
                        f"Verify the workflow ID with: mtor status {workflow_id}",
                        [_action(f"mtor status {workflow_id}", "Check if workflow exists")],
                        exit_code=4,
                    )
                )
            sys.exit(
                _err(
                    cmd,
                    f"SSH command failed: {stderr_msg}",
                    "SSH_ERROR",
                    "Verify ganglion is reachable via Tailscale: ping ganglion",
                    [_action("mtor doctor", "Run health check")],
                )
            )

        lines = result.stdout.splitlines()
        _ok(
            cmd,
            {
                "lines": lines,
                "log_path": log_path,
                "truncated": len(lines) == LOG_TAIL_LINES,
            },
            [
                _action(f"mtor status {workflow_id}", "Check workflow status"),
                _action(f"mtor cancel {workflow_id}", "Cancel if still running"),
            ],
            version=VERSION,
        )
    except subprocess.TimeoutExpired:
        sys.exit(
            _err(
                cmd,
                "SSH to ganglion timed out after 30s",
                "SSH_TIMEOUT",
                "Check Tailscale connectivity: ping ganglion",
                [_action("mtor doctor", "Run health check")],
            )
        )
    except FileNotFoundError:
        sys.exit(
            _err(
                cmd,
                "ssh binary not found",
                "SSH_NOT_FOUND",
                "Install openssh-client",
                [],
            )
        )


@app.command
def cancel(workflow_id: str) -> None:
    """Cancel a running workflow. Idempotent."""
    cmd = f"mtor cancel {workflow_id}"

    client, err = _get_client()
    if err:
        sys.exit(
            _err(
                cmd,
                f"Cannot connect to Temporal at {TEMPORAL_HOST}: {err}",
                "TEMPORAL_UNREACHABLE",
                "Start Temporal worker on ganglion: ssh ganglion 'sudo systemctl start temporal-worker'",
                [_action("mtor doctor", "Run health check to diagnose connectivity")],
                exit_code=3,
            )
        )

    try:

        async def _cancel():
            handle = client.get_workflow_handle(workflow_id)
            await handle.cancel()

        asyncio.run(_cancel())
        _ok(
            cmd,
            {"workflow_id": workflow_id, "cancelled": True},
            [
                _action(f"mtor status {workflow_id}", "Verify cancellation status"),
            ],
            version=VERSION,
        )
    except Exception as exc:
        exc_str = str(exc)
        # Idempotent: already cancelled/completed = ok
        if any(phrase in exc_str.lower() for phrase in ["not found", "workflow_not_found"]):
            sys.exit(
                _err(
                    cmd,
                    f"Workflow {workflow_id} not found",
                    "WORKFLOW_NOT_FOUND",
                    "Verify the workflow ID with: mtor list",
                    [_action("mtor list", "List all recent workflows")],
                    exit_code=4,
                )
            )
        # Already terminated/cancelled — treat as idempotent success
        if any(
            phrase in exc_str.lower()
            for phrase in ["already", "terminated", "cancelled", "canceled", "completed"]
        ):
            _ok(
                cmd,
                {
                    "workflow_id": workflow_id,
                    "cancelled": True,
                    "note": "Workflow was already in terminal state",
                },
                [
                    _action(f"mtor status {workflow_id}", "Verify final status"),
                ],
                version=VERSION,
            )
            return
        sys.exit(
            _err(
                cmd,
                exc_str,
                "CANCEL_ERROR",
                "Check Temporal server health with: mtor doctor",
                [_action("mtor doctor", "Run health check")],
            )
        )


@app.command
def doctor() -> None:
    """Health check: Temporal reachability, worker liveness, provider info."""
    _doctor()


@app.command
def schema() -> None:
    """Emit full JSON schema of all commands."""
    _ok("mtor schema", tree.to_schema(), version=VERSION)


@app.command
def approve(workflow_id: str) -> None:
    """Approve a deferred (SRP-paused) ribosome task."""
    client, err = _get_client()
    if err:
        sys.exit(
            _err(
                "mtor approve",
                f"Cannot connect to Temporal at {TEMPORAL_HOST}: {err}",
                "TEMPORAL_UNREACHABLE",
                "Check Temporal connectivity",
                exit_code=3,
            )
        )

    async def _signal():
        handle = client.get_workflow_handle(workflow_id)
        await handle.signal("approve_task", workflow_id)

    asyncio.run(_signal())
    _ok("mtor approve", {"workflow_id": workflow_id, "decision": "approved"}, version=VERSION)


@app.command
def deny(workflow_id: str) -> None:
    """Deny a deferred (SRP-paused) ribosome task."""
    client, err = _get_client()
    if err:
        sys.exit(
            _err(
                "mtor deny",
                f"Cannot connect to Temporal at {TEMPORAL_HOST}: {err}",
                "TEMPORAL_UNREACHABLE",
                "Check Temporal connectivity",
                exit_code=3,
            )
        )

    async def _signal():
        handle = client.get_workflow_handle(workflow_id)
        await handle.signal("reject_task", workflow_id)

    asyncio.run(_signal())
    _ok("mtor deny", {"workflow_id": workflow_id, "decision": "denied"}, version=VERSION)
