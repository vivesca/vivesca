"""Core dispatch logic — send a task prompt to Temporal."""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

from porin import action as _action

from mtor import TASK_QUEUE, TEMPORAL_HOST, VERSION, WORKFLOW_TYPE
from mtor.client import _get_client
from mtor.envelope import _err, _ok


def decompose_spec(prompt: str) -> list[str] | None:
    """Split a multi-task spec into individual task prompts.

    Returns None if the prompt is a single task (no ## Task sections).
    """
    task_pattern = re.compile(r'^## Task \d+', re.MULTILINE)
    matches = list(task_pattern.finditer(prompt))

    if len(matches) < 2:
        return None  # Single task or no task sections

    preamble_end = matches[0].start()
    preamble = prompt[:preamble_end].strip()

    tasks = []
    for idx, match in enumerate(matches):
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(prompt)
        task_text = prompt[start:end].strip()
        # Prepend preamble to each task
        if preamble:
            tasks.append(f"{preamble}\n\n{task_text}")
        else:
            tasks.append(task_text)

    return tasks


# ---------------------------------------------------------------------------
# Task risk classification
# ---------------------------------------------------------------------------

RISK_PATTERNS: dict[str, list[str]] = {
    "high": ["delete", "remove", "drop", "config", "infra", "deploy", "migrate", "rename"],
    "low": ["test", "doc", "readme", "comment", "add test", "write test", "new file"],
}
# Default: "medium"


def classify_risk(prompt: str) -> str:
    """Classify a task prompt by risk level for merge gating."""
    lower = prompt.lower()
    for level, patterns in RISK_PATTERNS.items():
        if any(p in lower for p in patterns):
            return level
    return "medium"


# ---------------------------------------------------------------------------
# Task-type routing
# ---------------------------------------------------------------------------

ROUTE_PATTERNS: dict[str, list[str]] = {
    "explore": ["how does", "find ", "search ", "what is", "explain", "where is", "list all", "show me"],
    "bugfix": ["fix ", "bug", "broken", "error ", "failing", "crash", "regression"],
    "test": ["write test", "add test", "test for", "coverage"],
}

ROUTE_TO_PROVIDER: dict[str, str] = {
    "explore": "droid",
    "bugfix": "goose",
    "build": "zhipu",
    "test": "zhipu",
}


def detect_task_type(prompt: str) -> str:
    """Classify a prompt into a task type for routing."""
    lower = prompt.lower()
    for task_type, patterns in ROUTE_PATTERNS.items():
        if any(p in lower for p in patterns):
            return task_type
    return "build"


def _dispatch_prompt(prompt: str, *, provider: str | None = None, experiment: bool = False) -> None:
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
            "mode": "experiment" if experiment else "build",
            "risk": classify_risk(full_prompt),
        }
        if experiment:
            spec["experiment"] = True

        async def _start():
            from temporalio.common import WorkflowIDConflictPolicy, WorkflowIDReusePolicy

            handle = await client.start_workflow(
                WORKFLOW_TYPE,
                args=[[spec]],
                id=workflow_id,
                task_queue=TASK_QUEUE,
                id_reuse_policy=WorkflowIDReusePolicy.ALLOW_DUPLICATE_FAILED_ONLY,
                id_conflict_policy=WorkflowIDConflictPolicy.USE_EXISTING,
            )
            return handle.id

        started_id = asyncio.run(_start())
        result_envelope: dict = {
            "workflow_id": started_id,
            "status": "RUNNING",
            "prompt_preview": prompt[:100],
            "risk": classify_risk(full_prompt),
        }
        if experiment:
            result_envelope["experiment"] = True

        next_actions = [
            _action(f"mtor status {started_id}", "Poll workflow status"),
            _action(f"mtor logs {started_id}", "Fetch output when complete"),
            _action(f"mtor cancel {started_id}", "Cancel if needed"),
        ]
        if experiment:
            next_actions.append(
                _action(f"mtor status {started_id}", "Experiment mode — will NOT auto-merge to main")
            )

        _ok(
            cmd,
            result_envelope,
            next_actions,
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
