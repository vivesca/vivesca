#!/usr/bin/env python3
"""temporal-dispatch — read golem-queue.md and dispatch tasks via Temporal.

Reads the same queue file format as golem-daemon and hatchet-dispatch,
submits tasks through Temporal workflows, marks tasks done/failed.

Usage:
    python3 dispatch.py                  # One-shot: dispatch all pending
    python3 dispatch.py --poll           # Poll mode: watch queue like daemon
    python3 dispatch.py --poll --interval 30
    python3 dispatch.py --dry-run        # Show what would be dispatched
    python3 dispatch.py --status         # Show running workflows
    python3 dispatch.py --json           # JSON output mode
"""
from __future__ import annotations

import asyncio
import json
import re
import sys
import time
import uuid
from pathlib import Path

from temporalio.client import Client

QUEUE_FILE = Path.home() / "germline" / "loci" / "golem-queue.md"
LOG_FILE = Path.home() / ".local" / "share" / "vivesca" / "temporal-dispatch.log"

_json_mode = False


def log(msg: str) -> None:
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    if not _json_mode:
        print(line)
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except OSError:
        pass


def parse_queue() -> list[tuple[int, str, str, str, int]]:
    """Parse queue file. Returns [(line_num, prompt, provider, task_id, max_turns)]."""
    if not QUEUE_FILE.exists():
        return []

    lines = QUEUE_FILE.read_text().splitlines()
    pending = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not (stripped.startswith("- [ ] ") or stripped.startswith("- [!!] ")):
            continue

        cmd_match = re.search(r'`([^`]+)`', line)
        if not cmd_match:
            continue

        cmd = cmd_match.group(1)

        provider_match = re.search(r'--provider\s+(\w+)', cmd)
        provider = provider_match.group(1) if provider_match else "zhipu"

        tid_match = re.search(r'\[t-([0-9a-fA-F]+)\]', cmd)
        task_id = f"t-{tid_match.group(1)}" if tid_match else f"t-{i:04x}"

        prompt_match = re.search(r'"([^"]+)"', cmd)
        prompt = prompt_match.group(1) if prompt_match else cmd

        turns_match = re.search(r'--max-turns\s+(\d+)', cmd)
        max_turns = int(turns_match.group(1)) if turns_match else 50

        pending.append((i, prompt, provider, task_id, max_turns))

    return pending


def mark_done(line_num: int) -> None:
    """Mark a task as done in the queue file."""
    lines = QUEUE_FILE.read_text().splitlines()
    if line_num >= len(lines):
        return
    line = lines[line_num]
    if "- [!!] " in line:
        lines[line_num] = line.replace("- [!!] ", "- [x] ", 1)
    elif "- [ ] " in line:
        lines[line_num] = line.replace("- [ ] ", "- [x] ", 1)
    QUEUE_FILE.write_text("\n".join(lines) + "\n")


def mark_failed(line_num: int) -> None:
    """Mark a task as failed in the queue file."""
    lines = QUEUE_FILE.read_text().splitlines()
    if line_num >= len(lines):
        return
    line = lines[line_num]
    if "- [!!] " in line:
        lines[line_num] = line.replace("- [!!] ", "- [!] ", 1)
    elif "- [ ] " in line:
        lines[line_num] = line.replace("- [ ] ", "- [!] ", 1)
    QUEUE_FILE.write_text("\n".join(lines) + "\n")


async def dispatch_all(dry_run: bool = False) -> int:
    """Dispatch all pending tasks as a single Temporal workflow."""
    pending = parse_queue()
    if not pending:
        log("No pending tasks in queue")
        return 0

    log(f"Found {len(pending)} pending tasks")

    if dry_run:
        for line_num, prompt, provider, task_id, max_turns in pending:
            log(f"[DRY] [{task_id}] {provider}: {prompt[:60]}...")
        return len(pending)

    # Build specs for Temporal workflow
    specs = []
    line_nums = []
    for line_num, prompt, provider, task_id, max_turns in pending:
        specs.append({
            "task": prompt,
            "provider": provider,
            "max_turns": max_turns,
        })
        line_nums.append(line_num)
        log(f"[QUEUE] [{task_id}] {provider}: {prompt[:60]}...")

    # Mark all as dispatched (done) in queue - Temporal handles retries
    for ln in line_nums:
        mark_done(ln)

    # Submit as a single batch workflow
    from workflow import GolemDispatchWorkflow

    client = await Client.connect("localhost:7233")
    wf_id = f"golem-batch-{uuid.uuid4().hex[:8]}"

    handle = await client.start_workflow(
        GolemDispatchWorkflow.run,
        args=[specs],
        id=wf_id,
        task_queue="golem-tasks",
    )
    log(f"Dispatched {len(specs)} tasks as workflow {wf_id}")
    return len(specs)


async def poll_loop(interval: int = 30) -> None:
    """Continuously poll the queue and dispatch tasks."""
    log(f"Starting poll loop (interval={interval}s)")
    while True:
        try:
            count = await dispatch_all()
            if count == 0:
                log("Queue empty, waiting...")
        except Exception as e:
            log(f"Error in poll loop: {e}")
        await asyncio.sleep(interval)


async def show_status(json_output: bool = False) -> None:
    """Show recent Temporal workflow runs."""
    client = await Client.connect("localhost:7233")
    results = []
    async for wf in client.list_workflows(
        query="WorkflowType = 'GolemDispatchWorkflow'",
        page_size=20,
    ):
        results.append({
            "workflow_id": wf.id,
            "status": wf.status.name if wf.status else "UNKNOWN",
            "start_time": str(wf.start_time),
        })
        if len(results) >= 20:
            break

    if json_output:
        print(json.dumps(results, indent=2))
    else:
        for r in results:
            print(f"  {r['workflow_id']}  {r['status']}  {r['start_time']}")


def main() -> None:
    global _json_mode

    args = sys.argv[1:]
    json_mode = "--json" in args
    if json_mode:
        _json_mode = True

    if "--help" in args or "-h" in args:
        print(__doc__)
        sys.exit(0)

    if "--status" in args:
        asyncio.run(show_status(json_output=json_mode))
        return

    dry_run = "--dry-run" in args
    poll = "--poll" in args

    interval = 30
    if "--interval" in args:
        idx = args.index("--interval")
        if idx + 1 < len(args):
            interval = int(args[idx + 1])

    if poll:
        asyncio.run(poll_loop(interval))
    else:
        asyncio.run(dispatch_all(dry_run=dry_run))


if __name__ == "__main__":
    main()
