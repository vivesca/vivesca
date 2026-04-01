#!/usr/bin/env python3
"""hatchet-dispatch — read golem-queue.md and dispatch tasks via Hatchet.

Replacement for golem-daemon's direct subprocess dispatch. Reads the same
queue file format, submits tasks through Hatchet with per-provider
concurrency, and marks tasks done/failed in the queue.

Usage:
    python3 dispatch.py                  # One-shot: dispatch all pending
    python3 dispatch.py --poll           # Poll mode: watch queue like daemon
    python3 dispatch.py --poll --interval 30  # Custom poll interval (seconds)
    python3 dispatch.py --dry-run        # Show what would be dispatched
    python3 dispatch.py --status         # Show running Hatchet workflows
    python3 dispatch.py --dry-run --json # Pending tasks as JSON
    python3 dispatch.py --status --json  # Workflow runs as JSON
    python3 dispatch.py --json           # Dispatch results as JSON
"""
from __future__ import annotations

import asyncio
import json
import re
import sys
import time
from pathlib import Path

from hatchet_sdk import Hatchet

# Import the task references from worker
sys.path.insert(0, str(Path(__file__).resolve().parent))
from worker import golem_zhipu, golem_infini, golem_volcano, golem_gemini

QUEUE_FILE = Path.home() / "germline" / "loci" / "golem-queue.md"
LOG_FILE = Path.home() / ".local" / "share" / "vivesca" / "hatchet-dispatch.log"

PROVIDER_TASKS = {
    "zhipu": golem_zhipu,
    "infini": golem_infini,
    "volcano": golem_volcano,
    "gemini": golem_gemini,
}

_json_mode = False
_dispatch_results: list[dict] = []


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


def parse_queue() -> list[tuple[int, str, str, str]]:
    """Parse queue file. Returns [(line_num, command, provider, task_id)]."""
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

        # Extract provider
        provider_match = re.search(r'--provider\s+(\w+)', cmd)
        provider = provider_match.group(1) if provider_match else "zhipu"

        # Extract task ID
        tid_match = re.search(r'\[t-([0-9a-fA-F]+)\]', cmd)
        task_id = f"t-{tid_match.group(1)}" if tid_match else f"t-{i:04x}"

        # Extract the actual task prompt (everything after the flags)
        prompt_match = re.search(r'"([^"]+)"', cmd)
        prompt = prompt_match.group(1) if prompt_match else cmd

        # Extract max-turns
        turns_match = re.search(r'--max-turns\s+(\d+)', cmd)
        max_turns = int(turns_match.group(1)) if turns_match else 50

        pending.append((i, prompt, provider, task_id, max_turns))

    return pending


def mark_done(line_num: int, result: str = "") -> None:
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


def mark_failed(line_num: int, result: str = "") -> None:
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


async def _run_one(task_ref, line_num, prompt, provider, task_id, max_turns):
    """Run a single task and handle result."""
    info = {"task_id": task_id, "provider": provider, "prompt": prompt[:200], "status": "pending"}
    try:
        run_ref = await task_ref.aio_run_no_wait({
            "task": prompt,
            "max_turns": max_turns,
        })
        mark_done(line_num, f"hatchet:dispatched:{run_ref.workflow_run_id}")
        log(f"[DISPATCHED] [{task_id}] {provider}: {prompt[:60]}...")
        info["status"] = "dispatched"
        info["workflow_run_id"] = run_ref.workflow_run_id
    except Exception as e:
        mark_failed(line_num, str(e)[:100])
        log(f"[ERROR] [{task_id}] {provider}: {e}")
        info["status"] = "error"
        info["error"] = str(e)[:200]
    _dispatch_results.append(info)


async def dispatch_all(dry_run: bool = False) -> int:
    """Dispatch all pending tasks via Hatchet concurrently. Returns count dispatched."""
    pending = parse_queue()
    if not pending:
        log("No pending tasks in queue")
        return 0

    log(f"Found {len(pending)} pending tasks")

    if dry_run:
        for line_num, prompt, provider, task_id, max_turns in pending:
            log(f"[DRY] [{task_id}] {provider}: {prompt[:60]}...")
        return len(pending)

    # Fire all tasks concurrently — Hatchet handles per-provider concurrency
    coros = []
    for line_num, prompt, provider, task_id, max_turns in pending:
        task_ref = PROVIDER_TASKS.get(provider)
        if not task_ref:
            log(f"[{task_id}] Unknown provider '{provider}', skipping")
            continue
        log(f"[DISPATCH] [{task_id}] {provider}: {prompt[:60]}...")
        coros.append(_run_one(task_ref, line_num, prompt, provider, task_id, max_turns))

    # Run all concurrently — Hatchet's concurrency limits handle the throttling
    await asyncio.gather(*coros, return_exceptions=True)

    log(f"Dispatched {len(coros)}/{len(pending)} tasks")
    return len(coros)


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


def show_status(json_output: bool = False) -> None:
    """Show current Hatchet workflow runs."""
    h = Hatchet()
    result = h.runs.list(limit=20)
    rows = result.rows if hasattr(result, "rows") else []
    if json_output:
        data = [
            {
                "task_id": r.task_id,
                "workflow_name": r.workflow_name,
                "status": str(r.status),
                "started_at": str(r.started_at),
            }
            for r in rows
        ]
        print(json.dumps(data, indent=2))
    else:
        for r in rows:
            print(f"  {r.task_id}  {r.workflow_name}  {r.status}  {r.started_at}")


def main() -> None:
    global _json_mode

    args = sys.argv[1:]

    if "--help" in args or "-h" in args:
        print(__doc__)
        return

    json_mode = "--json" in args
    if json_mode:
        _json_mode = True

    if "--status" in args:
        show_status(json_output=json_mode)
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
    elif dry_run and json_mode:
        pending = parse_queue()
        tasks = [
            {"task_id": tid, "provider": p, "prompt": prompt[:200], "max_turns": mt, "line": ln}
            for ln, prompt, p, tid, mt in pending
        ]
        print(json.dumps({"total": len(tasks), "tasks": tasks}, indent=2))
    elif json_mode:
        count = asyncio.run(dispatch_all(dry_run=dry_run))
        print(json.dumps({"dispatched": count, "total": count, "tasks": _dispatch_results}, indent=2))
    else:
        asyncio.run(dispatch_all(dry_run=dry_run))


if __name__ == "__main__":
    main()
