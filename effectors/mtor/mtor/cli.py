"""mtor — agent-first translation controller Temporal dispatch CLI.

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

import contextlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import click

TEMPORAL_HOST = os.environ.get("TEMPORAL_HOST", "ganglion:7233")
TASK_QUEUE = "translation-queue"
WORKFLOW_TYPE = "TranslationWorkflow"
COACHING_PATH = Path.home() / "epigenome/marks/feedback_ribosome_coaching.md"

LOG_TAIL_LINES = 30
RIBOSOME_OUTPUTS_DIR = "~/germline/loci/ribosome-outputs"


def _extract_first_result(wf_result: dict) -> dict | None:
    """Extract the first task result from the batch envelope."""
    results = wf_result.get("results")
    if isinstance(results, list) and results:
        return results[0]
    # Flat result (direct task output, not batch envelope)
    if "exit_code" in wf_result:
        return wf_result
    return None


# ---------------------------------------------------------------------------
# JSON envelope helpers
# ---------------------------------------------------------------------------


def _ok(command: str, result: dict[str, Any], next_actions: list[dict] | None = None) -> None:
    payload = {
        "ok": True,
        "command": command,
        "result": result,
        "next_actions": next_actions or [],
    }
    sys.stdout.write(json.dumps(payload) + "\n")
    sys.stdout.flush()


def _err(
    command: str,
    message: str,
    code: str,
    fix: str,
    next_actions: list[dict] | None = None,
    exit_code: int = 1,
) -> int:
    payload = {
        "ok": False,
        "command": command,
        "error": {"message": message, "code": code},
        "fix": fix,
        "next_actions": next_actions or [],
    }
    sys.stdout.write(json.dumps(payload) + "\n")
    sys.stdout.flush()
    return exit_code


def _action(command: str, description: str) -> dict:
    return {"command": command, "description": description}


# ---------------------------------------------------------------------------
# Temporal client helpers
# ---------------------------------------------------------------------------


def _get_client():
    """Connect to Temporal server. Returns (client, None) or (None, error_msg)."""
    try:
        import asyncio

        from temporalio.client import Client

        async def _connect():
            return await Client.connect(TEMPORAL_HOST)

        client = asyncio.run(_connect())
        return client, None
    except ImportError:
        return None, "temporalio SDK not installed"
    except Exception as exc:
        return None, str(exc)


def _load_coaching() -> str:
    """Load coaching content from feedback_ribosome_coaching.md. Empty string if missing."""
    if COACHING_PATH.exists():
        try:
            return COACHING_PATH.read_text(encoding="utf-8")
        except OSError:
            pass
    return ""


# ---------------------------------------------------------------------------
# Command tree (bare invocation)
# ---------------------------------------------------------------------------

COMMAND_TREE = {
    "commands": [
        {
            "name": "mtor",
            "description": "Bare invocation — returns this JSON command tree for agent self-discovery",
            "params": [],
        },
        {
            "name": "mtor <prompt>",
            "description": "Dispatch a task prompt to Temporal. Prepends coaching content before sending.",
            "params": [
                {
                    "name": "prompt",
                    "type": "string",
                    "required": True,
                    "description": "Task instruction for the ribosome worker",
                },
            ],
        },
        {
            "name": "mtor list",
            "description": "List recent workflows",
            "params": [
                {
                    "name": "--status",
                    "type": "enum",
                    "enum": ["RUNNING", "COMPLETED", "FAILED", "CANCELED", "TERMINATED"],
                    "required": False,
                    "default": None,
                    "description": "Filter by execution status",
                },
                {
                    "name": "--count",
                    "type": "integer",
                    "required": False,
                    "default": 10,
                    "description": "Maximum workflows to return",
                },
            ],
        },
        {
            "name": "mtor status <workflow_id>",
            "description": "Query status of a single workflow",
            "params": [
                {
                    "name": "workflow_id",
                    "type": "string",
                    "required": True,
                    "description": "Temporal workflow ID",
                },
            ],
        },
        {
            "name": "mtor logs <workflow_id>",
            "description": f"Last {LOG_TAIL_LINES} lines of workflow stdout + path to full log on ganglion",
            "params": [
                {
                    "name": "workflow_id",
                    "type": "string",
                    "required": True,
                    "description": "Temporal workflow ID",
                },
            ],
        },
        {
            "name": "mtor cancel <workflow_id>",
            "description": "Cancel a running workflow. Idempotent — cancelling an already-cancelled workflow is ok.",
            "params": [
                {
                    "name": "workflow_id",
                    "type": "string",
                    "required": True,
                    "description": "Temporal workflow ID",
                },
            ],
        },
        {
            "name": "mtor doctor",
            "description": "Health check: Temporal server reachability, worker liveness, provider info",
            "params": [],
        },
        {
            "name": "mtor schema",
            "description": "Emit full JSON schema of all commands with params, types, enums, defaults",
            "params": [],
        },
    ],
    "exit_codes": {
        "0": "ok",
        "1": "error (generic)",
        "2": "usage error (missing required argument)",
        "3": "temporal unreachable",
        "4": "workflow not found",
    },
    "temporal_host": TEMPORAL_HOST,
    "task_queue": TASK_QUEUE,
}

FULL_SCHEMA = {
    "schema_version": "1",
    "commands": [
        {
            "name": "mtor",
            "description": "Returns command tree (this schema)",
            "params": [],
            "returns": {
                "ok": "boolean",
                "command": "string",
                "result": {"commands": "array"},
                "next_actions": "array",
            },
        },
        {
            "name": "mtor <prompt>",
            "description": "Dispatch task to Temporal workflow",
            "params": [
                {
                    "name": "prompt",
                    "type": "string",
                    "required": True,
                    "positional": True,
                    "description": "Task instruction. Coaching content is prepended automatically.",
                },
            ],
            "returns": {
                "ok": "boolean",
                "command": "string",
                "result": {
                    "workflow_id": "string",
                    "status": "string",
                    "prompt_preview": "string (first 100 chars of full prompt after coaching injection)",
                },
                "next_actions": "array",
            },
        },
        {
            "name": "mtor list",
            "description": "List recent workflows with optional filters",
            "params": [
                {
                    "name": "--status",
                    "type": "enum",
                    "enum": ["RUNNING", "COMPLETED", "FAILED", "CANCELED", "TERMINATED"],
                    "required": False,
                    "default": None,
                    "description": "Filter workflows by execution status",
                },
                {
                    "name": "--count",
                    "type": "integer",
                    "required": False,
                    "default": 10,
                    "min": 1,
                    "max": 100,
                    "description": "Maximum number of workflows to return",
                },
            ],
            "returns": {
                "ok": "boolean",
                "command": "string",
                "result": {
                    "workflows": "array of {workflow_id, status, start_time, close_time}",
                    "count": "integer",
                },
                "next_actions": "array (one mtor status per workflow)",
            },
        },
        {
            "name": "mtor status <workflow_id>",
            "description": "Get detailed status of a single workflow",
            "params": [
                {
                    "name": "workflow_id",
                    "type": "string",
                    "required": True,
                    "positional": True,
                    "description": "Temporal workflow ID",
                },
            ],
            "returns": {
                "ok": "boolean",
                "command": "string",
                "result": {
                    "workflow_id": "string",
                    "status": "string",
                    "start_time": "string (ISO8601)",
                    "close_time": "string or null",
                },
                "next_actions": "array",
            },
            "errors": [
                {
                    "code": "WORKFLOW_NOT_FOUND",
                    "exit_code": 4,
                    "message": "No workflow with that ID",
                },
                {
                    "code": "TEMPORAL_UNREACHABLE",
                    "exit_code": 3,
                    "message": "Cannot connect to Temporal server",
                },
            ],
        },
        {
            "name": "mtor logs <workflow_id>",
            "description": f"Fetch last {LOG_TAIL_LINES} lines of workflow output from ganglion",
            "params": [
                {
                    "name": "workflow_id",
                    "type": "string",
                    "required": True,
                    "positional": True,
                    "description": "Temporal workflow ID",
                },
            ],
            "returns": {
                "ok": "boolean",
                "command": "string",
                "result": {
                    "lines": "array of strings",
                    "log_path": "string (full path on ganglion)",
                    "truncated": "boolean",
                },
                "next_actions": "array",
            },
        },
        {
            "name": "mtor cancel <workflow_id>",
            "description": "Cancel a workflow. Idempotent.",
            "params": [
                {
                    "name": "workflow_id",
                    "type": "string",
                    "required": True,
                    "positional": True,
                    "description": "Temporal workflow ID",
                },
            ],
            "returns": {
                "ok": "boolean",
                "command": "string",
                "result": {"workflow_id": "string", "cancelled": "boolean"},
                "next_actions": "array",
            },
        },
        {
            "name": "mtor doctor",
            "description": "Health check for Temporal server and worker",
            "params": [],
            "returns": {
                "ok": "boolean",
                "command": "string",
                "result": {
                    "temporal_reachable": "boolean",
                    "temporal_host": "string",
                    "worker_alive": "boolean",
                    "checks": "array of {name, ok, detail}",
                },
                "next_actions": "array",
            },
        },
        {
            "name": "mtor schema",
            "description": "Full JSON schema of all commands",
            "params": [],
            "returns": {"schema_version": "string", "commands": "array"},
        },
    ],
    "exit_codes": {
        "0": "ok",
        "1": "error (generic, non-temporal)",
        "2": "usage error (missing required argument)",
        "3": "temporal unreachable",
        "4": "workflow not found",
    },
}


# ---------------------------------------------------------------------------
# Click CLI
# ---------------------------------------------------------------------------


@click.group(invoke_without_command=True, add_help_option=False)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """mtor — agent-first translation controller Temporal dispatch CLI. Bare invocation returns command tree."""
    if ctx.invoked_subcommand is None:
        _ok("mtor", COMMAND_TREE)


@cli.command(name="list", add_help_option=False)
@click.option(
    "--status",
    type=click.Choice(["RUNNING", "COMPLETED", "FAILED", "CANCELED", "TERMINATED"]),
    default=None,
)
@click.option("--count", type=int, default=10)
def list_cmd(status: str | None, count: int) -> None:
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
        import asyncio

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

        _ok(cmd, {"workflows": workflows, "count": len(workflows)}, next_actions)
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


@cli.command(add_help_option=False)
@click.argument("workflow_id")
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
        import asyncio

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


@cli.command(add_help_option=False)
@click.argument("workflow_id")
def logs(workflow_id: str) -> None:
    """Fetch last 30 lines of workflow output from ganglion."""
    cmd = f"mtor logs {workflow_id}"

    # Step 1: Query Temporal for the workflow result to get output_path
    log_path = ""
    client, client_err = _get_client()
    if client and not client_err:
        try:
            import asyncio

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
        except subprocess.TimeoutExpired, OSError:
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


@cli.command(add_help_option=False)
@click.argument("workflow_id")
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
        import asyncio

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


@cli.command(add_help_option=False)
def doctor() -> None:
    """Health check: Temporal reachability, worker liveness, provider info."""
    cmd = "mtor doctor"
    checks = []
    all_ok = True

    # Check 1: Temporal server reachable
    client, err = _get_client()
    temporal_ok = err is None
    if not temporal_ok:
        all_ok = False
    checks.append(
        {
            "name": "temporal_reachable",
            "ok": temporal_ok,
            "detail": f"Connected to {TEMPORAL_HOST}" if temporal_ok else f"Cannot connect: {err}",
        }
    )

    # Check 2: Worker alive (query for recent RUNNING workflows as a proxy)
    worker_ok = False
    worker_detail = "Skipped (Temporal unreachable)"
    if temporal_ok and client is not None:
        try:
            import asyncio

            async def _probe():
                count = 0
                async for _ in client.list_workflows():
                    count += 1
                    if count >= 1:
                        break
                return count

            asyncio.run(_probe())
            worker_ok = True
            worker_detail = "Worker service responsive (list_workflows succeeded)"
        except Exception as probe_exc:
            worker_detail = f"Worker probe failed: {probe_exc}"
            all_ok = False
    else:
        all_ok = False

    checks.append(
        {
            "name": "worker_alive",
            "ok": worker_ok,
            "detail": worker_detail,
        }
    )

    # Check 3: Coaching file present
    coaching_ok = COACHING_PATH.exists()
    checks.append(
        {
            "name": "coaching_file",
            "ok": coaching_ok,
            "detail": str(COACHING_PATH) if coaching_ok else f"Missing: {COACHING_PATH}",
        }
    )

    result = {
        "temporal_reachable": temporal_ok,
        "temporal_host": TEMPORAL_HOST,
        "worker_alive": worker_ok,
        "task_queue": TASK_QUEUE,
        "checks": checks,
    }

    if all_ok:
        _ok(cmd, result, [])
    else:
        payload = {
            "ok": False,
            "command": cmd,
            "error": {
                "message": "One or more health checks failed",
                "code": "HEALTH_CHECK_FAILED",
            },
            "fix": "Start Temporal worker on ganglion: ssh ganglion 'sudo systemctl start temporal-worker'",
            "result": result,
            "next_actions": [
                _action(
                    "ssh ganglion 'sudo systemctl status temporal-worker'",
                    "Check worker service status",
                ),
                _action("ssh ganglion 'sudo systemctl start temporal-worker'", "Start the worker"),
            ],
        }
        sys.stdout.write(json.dumps(payload) + "\n")
        sys.stdout.flush()
        sys.exit(3)


@cli.command(add_help_option=False)
def schema() -> None:
    """Emit full JSON schema of all commands."""
    _ok("mtor schema", FULL_SCHEMA)


# ---------------------------------------------------------------------------
# Dispatch subcommand (bare positional prompt)
# The Click group handles bare invocation (no args = command tree).
# A positional prompt that doesn't match a subcommand name goes here.
# We implement this as a special case in the group's result_callback.
# ---------------------------------------------------------------------------


@cli.command(name="dispatch", add_help_option=False, hidden=True)
@click.argument("prompt")
def dispatch(prompt: str) -> None:
    """Internal: dispatch a prompt to Temporal. Use 'mtor <prompt>' directly."""
    _dispatch_prompt(prompt)


def _dispatch_prompt(prompt: str) -> None:
    """Core dispatch logic — shared by the group's bare-prompt handler."""
    cmd = f"mtor {prompt[:60]}{'...' if len(prompt) > 60 else ''}"

    if not prompt.strip():
        sys.exit(
            _err(
                "mtor",
                "Prompt is required",
                "MISSING_PROMPT",
                'Provide a task description: mtor "Write tests for metabolon/foo.py"',
                [_action("mtor", "Show command tree")],
                exit_code=2,
            )
        )

    # Prepend coaching content
    coaching = _load_coaching()
    if coaching:
        full_prompt = f"<coaching-notes>\n{coaching}\n</coaching-notes>\n\n{prompt}"
    else:
        full_prompt = prompt

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
        import asyncio
        import uuid

        workflow_id = f"ribosome-{uuid.uuid4().hex[:8]}"
        spec = {
            "task": full_prompt,
            "provider": "zhipu",
            "max_turns": 25,
            "mode": "build",
        }

        async def _start():
            handle = await client.start_workflow(
                WORKFLOW_TYPE,
                args=[[spec]],
                id=workflow_id,
                task_queue=TASK_QUEUE,
            )
            return handle.id

        started_id = asyncio.run(_start())
        _ok(
            cmd,
            {
                "workflow_id": started_id,
                "status": "RUNNING",
                "prompt_preview": prompt[:100],
            },
            [
                _action(f"mtor status {started_id}", "Poll workflow status"),
                _action(f"mtor logs {started_id}", "Fetch output when complete"),
                _action(f"mtor cancel {started_id}", "Cancel if needed"),
            ],
        )
    except Exception as exc:
        sys.exit(
            _err(
                cmd,
                f"Failed to start workflow: {exc}",
                "DISPATCH_ERROR",
                "Check Temporal server health: mtor doctor",
                [_action("mtor doctor", "Run health check")],
            )
        )


# ---------------------------------------------------------------------------
# Allow bare positional: `mtor "some task prompt"`
# Click dispatches unknown subcommand names as errors by default.
# We override result_callback to handle any non-subcommand first argument
# as a prompt dispatch.
# ---------------------------------------------------------------------------


@cli.result_callback()
def _process_result(*args: Any, **kwargs: Any) -> None:
    pass


# Monkey-patch the group to treat unknown subcommands as prompts
_original_make_context = cli.make_context


def _patched_make_context(info_name, args, **kwargs):
    # If the first arg looks like a dispatch prompt (not a known subcommand),
    # rewrite args to use the 'dispatch' subcommand
    if args and not args[0].startswith("-"):
        known = {cmd_obj.name for cmd_obj in cli.commands.values()}
        if args[0] not in known:
            args = ["dispatch", *args]
    return _original_make_context(info_name, args, **kwargs)


cli.make_context = _patched_make_context
