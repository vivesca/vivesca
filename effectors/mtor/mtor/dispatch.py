"""Core dispatch logic — send a task prompt to Temporal."""

from __future__ import annotations

import sys
from pathlib import Path

from porin import action as _action

from mtor import TASK_QUEUE, TEMPORAL_HOST, VERSION, WORKFLOW_TYPE
from mtor.client import _get_client
from mtor.envelope import _err, _ok


def _dispatch_prompt(prompt: str, *, provider: str = "zhipu") -> None:
    """Core dispatch logic."""
    # If prompt is a file path, read it as the spec
    prompt_path = Path(prompt).expanduser()
    if prompt_path.is_file():
        prompt = prompt_path.read_text(encoding="utf-8").strip()
        # Strip YAML frontmatter (--- ... ---) — confuses GLM into treating spec as document
        import re
        prompt = re.sub(r"\A---\n.*?\n---\n*", "", prompt, count=1, flags=re.DOTALL).strip()

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

    # Coaching injection is handled by the ribosome executor per provider:
    # CC: prepended to prompt; goose: MOIM file; droid: --append-system-prompt-file.
    # Do NOT prepend here — it causes double injection.
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

        # Deterministic ID from prompt hash — Temporal rejects if already running (dedup)
        import hashlib
        prompt_hash = hashlib.sha256(full_prompt.encode()).hexdigest()[:8]
        workflow_id = f"ribosome-{provider}-{prompt_hash}"
        spec = {
            "task": full_prompt,
            "provider": provider,
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

        try:
            started_id = asyncio.run(_start())
        except Exception as exc:
            if "already started" in str(exc).lower() or "already running" in str(exc).lower():
                _ok(
                    cmd,
                    {
                        "workflow_id": workflow_id,
                        "status": "ALREADY_RUNNING",
                        "prompt_preview": prompt[:100],
                    },
                    [
                        _action(f"mtor status {workflow_id}", "Check existing run"),
                        _action(f"mtor cancel {workflow_id}", "Cancel to re-dispatch"),
                    ],
                    version=VERSION,
                )
                return
            raise
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
            version=VERSION,
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
