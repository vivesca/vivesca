#!/usr/bin/env python3
"""Temporal worker for golem task orchestration.

Polls the 'golem-tasks' task queue and executes golem commands as activities.
Each activity runs `bash effectors/golem --provider X task`, heartbeats every
30s, has a 30min timeout, and a retry policy (3 attempts, exponential backoff).

Usage:
    python worker.py                # Start worker
    python worker.py --help         # Show this help
"""
from __future__ import annotations

import asyncio
import os
import sys
from datetime import timedelta
from pathlib import Path

from temporalio import activity
from temporalio.client import Client
from temporalio.worker import Worker

TASK_QUEUE = "golem-tasks"
GOLEM_SCRIPT = Path(__file__).resolve().parent.parent / "golem"
REVIEW_LOG = Path.home() / "germline" / "loci" / "golem-reviews.jsonl"
OUTPUT_DIR = Path.home() / "germline" / "loci" / "golem-outputs"

# Per-provider concurrency limits (matching golem-daemon config)
PROVIDER_LIMITS = {
    "zhipu": 8,
    "infini": 8,
    "volcano": 16,
    "gemini": 4,
    "codex": 4,
}

# How long we wait between heartbeats
_HEARTBEAT_INTERVAL = 30.0
# Maximum time a single golem invocation may run
_ACTIVITY_TIMEOUT = timedelta(minutes=30)


def _git_snapshot() -> dict:
    """Capture git diff stat + numstat for before/after comparison."""
    try:
        stat = _subprocess.run(
            ["git", "diff", "--stat", "HEAD"],
            capture_output=True, text=True, timeout=10,
            cwd=str(Path.home()),
        )
        # numstat gives per-file +/- line counts for shrinkage detection
        numstat = _subprocess.run(
            ["git", "diff", "--numstat", "HEAD"],
            capture_output=True, text=True, timeout=10,
            cwd=str(Path.home()),
        )
        return {
            "stat": stat.stdout[:2000],
            "numstat": numstat.stdout[:2000],
        }
    except Exception:
        return {"stat": "", "numstat": ""}


@activity.defn
async def run_golem_task(task: str, provider: str, max_turns: int = 50) -> dict:
    """Execute a single golem task as a subprocess."""
    # #1: Idempotency — if output file from prior attempt exists, return cached
    task_id_match = _re.search(r'\[t-([0-9a-fA-F]+)\]', task)
    tid_str = task_id_match.group(1) if task_id_match else ""
    if tid_str:
        cached = OUTPUT_DIR / f"{_time.strftime('%Y%m%d')}-{tid_str}.txt"
        if cached.exists():
            content = cached.read_text()
            rc = 0 if "Exit: 0" in content[:200] else 1
            return {
                "success": rc == 0,
                "exit_code": rc,
                "provider": provider,
                "task": task[:200],
                "stdout": "(cached from prior attempt)",
                "stderr": "",
                "pre_diff": {"stat": "", "numstat": ""},
                "post_diff": {"stat": "", "numstat": ""},
                "cost_info": "",
                "output_path": str(cached),
            }

    # Snapshot before golem runs
    pre_diff = await asyncio.to_thread(_git_snapshot)

    cmd = [
        "bash", str(GOLEM_SCRIPT),
        "--provider", provider,
        "--max-turns", str(max_turns),
        task,
    ]
    # Run golem from repo root, not temporal-golem subdir
    repo_root = str(Path.home() / "germline")
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=repo_root,
        env={**os.environ, "GOLEM_PROVIDER": provider},
    )

    # Heartbeat while subprocess runs
    async def _heartbeat():
        n = 0
        while True:
            await asyncio.sleep(_HEARTBEAT_INTERVAL)
            n += 1
            try:
                activity.heartbeat(f"{provider}:{task[:60]} tick:{n}")
            except Exception:
                pass

    hb_task = asyncio.create_task(_heartbeat())
    try:
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(),
                timeout=_ACTIVITY_TIMEOUT.total_seconds(),
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.communicate()
            return {
                "success": False,
                "exit_code": -1,
                "provider": provider,
                "task": task[:200],
                "stdout": "",
                "stderr": "timeout after 30m",
            }
    finally:
        hb_task.cancel()
        try:
            await hb_task
        except asyncio.CancelledError:
            pass

    rc = proc.returncode or 0
    stdout = stdout_bytes.decode(errors="replace")
    stderr = stderr_bytes.decode(errors="replace")

    # Snapshot after golem runs
    post_diff = await asyncio.to_thread(_git_snapshot)

    # #5: Extract token/cost info from golem output
    cost_info = ""
    for line in stdout.splitlines()[-10:]:
        if any(k in line.lower() for k in ["token", "cost", "usage", "input:", "output:"]):
            cost_info += line + "\n"

    # #8: Save full output to per-task file; #4: return path, not payload
    task_id_match = _re.search(r'\[t-([0-9a-fA-F]+)\]', task)
    tid_str = task_id_match.group(1) if task_id_match else _time.strftime("%H%M%S")
    out_path = ""
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        out_file = OUTPUT_DIR / f"{_time.strftime('%Y%m%d')}-{tid_str}.txt"
        out_file.write_text(f"Task: {task}\nProvider: {provider}\nExit: {rc}\n\n--- stdout ---\n{stdout}\n\n--- stderr ---\n{stderr}\n\n--- diff ---\n{post_diff.get('stat', '')}\n")
        out_path = str(out_file)
    except OSError:
        pass

    return {
        "success": rc == 0,
        "exit_code": rc,
        "provider": provider,
        "task": task[:200],
        "stdout": stdout[:1000],  # slim: just enough for review patterns
        "stderr": stderr[:500],
        "pre_diff": pre_diff,
        "post_diff": post_diff,
        "cost_info": cost_info[:500],
        "output_path": out_path,
    }


import json
import re as _re
import subprocess as _subprocess
import time as _time

# ── LangGraph golem activity ──


@activity.defn
async def run_golem_graph_task(task: str, provider: str, max_turns: int = 50) -> dict:
    """Execute a golem task via LangGraph agent graph (plan→execute→verify→review)."""
    from golem_graph import run_golem_graph
    # Run synchronously in a thread to avoid blocking the event loop
    import asyncio
    result = await asyncio.to_thread(run_golem_graph, task, provider)
    return result

# ── Red-flag patterns that indicate golem may have done damage ──

_DESTRUCTION_PATTERNS = _re.compile(
    r'rm -rf|rmdir|replaced entire|overwrote|deleted all|'
    r'file is now empty|wrote 0 bytes|No such file',
    _re.IGNORECASE,
)

_ERROR_PATTERNS = _re.compile(
    r'SyntaxError|ImportError|ModuleNotFoundError|PermissionError|'
    r'Traceback \(most recent|FAILED|panic:|fatal:',
    _re.IGNORECASE,
)



@activity.defn
async def review_golem_result(result: dict) -> dict:
    """Review a golem task result for quality signals.

    Checks for destruction patterns, errors, suspiciously short output,
    and writes a review entry to golem-reviews.jsonl.

    Returns {"approved": bool, "flags": [...], "verdict": str}.
    """
    task = result.get("task", "")
    provider = result.get("provider", "")
    stdout = result.get("stdout", "")
    stderr = result.get("stderr", "")
    exit_code = result.get("exit_code", -1)
    combined = f"{stdout}\n{stderr}"

    flags: list[str] = []

    # 1. Exit code
    if exit_code != 0:
        flags.append(f"exit_code={exit_code}")

    # 2. Destruction patterns in output
    destruction_hits = _DESTRUCTION_PATTERNS.findall(combined)
    if destruction_hits:
        flags.append(f"destruction: {', '.join(list(set(destruction_hits))[:3])}")

    # 3. Error patterns
    error_hits = _ERROR_PATTERNS.findall(combined)
    if error_hits:
        flags.append(f"errors: {', '.join(list(set(error_hits))[:3])}")

    # 4. Suspiciously short output for complex tasks
    task_words = len(task.split())
    output_words = len(stdout.split())
    if task_words > 20 and output_words < 10 and exit_code == 0:
        flags.append(f"thin_output: {output_words} words for {task_words}-word task")

    # 5. Empty stdout with success (golem should always produce output)
    if exit_code == 0 and len(stdout.strip()) < 5:
        flags.append("empty_stdout_on_success")

    # 6. Git diff — per-file line count analysis from numstat
    pre_diff = result.get("pre_diff", {})
    post_diff = result.get("post_diff", {})
    pre_numstat = pre_diff.get("numstat", "") if isinstance(pre_diff, dict) else ""
    post_numstat = post_diff.get("numstat", "") if isinstance(post_diff, dict) else ""
    post_stat = post_diff.get("stat", "") if isinstance(post_diff, dict) else str(post_diff)

    if post_numstat and post_numstat != pre_numstat:
        for line in post_numstat.splitlines():
            parts = line.split("\t")
            if len(parts) == 3:
                added, removed, fname = parts
                try:
                    a, r = int(added), int(removed)
                    if r > a * 3 and r > 10:
                        flags.append(f"file_shrunk: {fname} +{a}/-{r}")
                    if a == 0 and r > 5:
                        flags.append(f"pure_deletion: {fname} -{r}")
                except ValueError:
                    pass

    # Verdict
    approved = exit_code == 0 and not any(
        f.startswith("destruction") for f in flags
    )
    verdict = "approved" if approved else "rejected"
    if flags and approved:
        verdict = "approved_with_flags"

    review = {
        "ts": _time.strftime("%Y-%m-%dT%H:%M:%S"),
        "task": task[:200],
        "provider": provider,
        "exit_code": exit_code,
        "flags": flags,
        "verdict": verdict,
        "stdout_len": len(stdout),
        "stderr_len": len(stderr),
        "diff": post_stat[:500] if post_stat else "",
        "cost_info": result.get("cost_info", ""),
    }

    # Persist review
    try:
        REVIEW_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(REVIEW_LOG, "a") as f:
            f.write(json.dumps(review) + "\n")
    except OSError:
        pass

    # #9: Auto-requeue rejected thin_output with coaching prompt
    requeue_prompt = ""
    if verdict == "rejected" and any("thin_output" in f for f in flags):
        requeue_prompt = task[:200] + " — Be thorough. Read files before editing. Show your work."
    elif verdict == "rejected" and any("file_shrunk" in f for f in flags):
        requeue_prompt = task[:200] + " — IMPORTANT: Read the entire file before modifying. Preserve ALL existing content."

    return {"approved": approved, "flags": flags, "verdict": verdict, "requeue_prompt": requeue_prompt}


async def main() -> None:
    """Start the Temporal worker."""
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        sys.exit(0)

    # Import workflow here to avoid circular import at module level
    from workflow import GolemDispatchWorkflow

    host = os.getenv("TEMPORAL_HOST", "ganglion:7233")
    client = await Client.connect(host)

    # Total concurrent activities across all providers
    max_concurrent = sum(PROVIDER_LIMITS.values())

    worker = Worker(
        client=client,
        task_queue=TASK_QUEUE,
        workflows=[GolemDispatchWorkflow],
        activities=[run_golem_task, run_golem_graph_task, review_golem_result],
        max_concurrent_activities=max_concurrent,
    )
    print(f"Temporal golem worker started on queue '{TASK_QUEUE}' (max_concurrent={max_concurrent})")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
