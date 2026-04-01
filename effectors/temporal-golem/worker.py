#!/usr/bin/env python3
"""Temporal worker for golem task orchestration.

Polls the 'golem-tasks' task queue and executes golem commands as activities.
Each activity runs `bash effectors/golem --provider X task`, heartbeats every
30s, has a 30min timeout, and a retry policy (3 attempts, exponential backoff).

Ported from golem-daemon: rate-limit detection, adaptive throttling,
per-provider concurrency, smart retry.

Usage:
    python worker.py                # Start worker
    python worker.py --help         # Show this help
"""
from __future__ import annotations

import asyncio
import os
import re
import sys
from datetime import timedelta
from pathlib import Path

from temporalio import activity
from temporalio.client import Client
from temporalio.exceptions import ApplicationError
from temporalio.worker import Worker

TASK_QUEUE = "golem-tasks"
GOLEM_SCRIPT = Path(__file__).resolve().parent.parent / "golem"

# Per-provider concurrency limits (matching golem-daemon config)
PROVIDER_LIMITS = {
    "zhipu": 8,
    "infini": 4,   # 1000 req/5hr — conservative
    "volcano": 16,
    "gemini": 4,
    "codex": 4,
}
DEFAULT_LIMIT = 4

# Rate-limit detection (from golem-daemon)
RATE_LIMIT_PATTERNS = re.compile(
    r'429|AccountQuotaExceeded|rate.?limit|quota.?exceeded|20013|'
    r'request.?limit.?exceeded|API Error.*429|too many requests|TooManyRequests|'
    r'usage.?limit|hit your.*limit|quota will reset',
    re.IGNORECASE,
)

# Per-provider rate limit cooldown windows (seconds)
PROVIDER_RATE_WINDOWS = {
    "infini": 18000,  # 5 hours
    "volcano": 18000,
    "codex": 3600,    # 1 hour
    "gemini": 1200,   # 20 min
}

# How long we wait between heartbeats
_HEARTBEAT_INTERVAL = 30.0
# Maximum time a single golem invocation may run
_ACTIVITY_TIMEOUT = timedelta(minutes=30)


def is_rate_limited(output: str) -> bool:
    """Check if output contains rate-limit/quota-exhaustion indicators."""
    return bool(RATE_LIMIT_PATTERNS.search(output))


def parse_rate_limit_window(output: str) -> int | None:
    """Extract rate-limit reset window in seconds from error output."""
    # Exact reset timestamp (Volcano: "reset at YYYY-MM-DD HH:MM:SS")
    from datetime import datetime
    m = re.search(r'reset at (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', output)
    if m:
        try:
            reset_time = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
            delta = (reset_time - datetime.now()).total_seconds()
            if delta > 0:
                return int(delta)
        except (ValueError, OverflowError):
            pass

    # Codex: "try again at 9:01 PM"
    m = re.search(r'try again at (\d{1,2}):(\d{2})\s*([AP]M)', output, re.IGNORECASE)
    if m:
        try:
            hour, minute = int(m.group(1)), int(m.group(2))
            if m.group(3).upper() == "PM" and hour != 12:
                hour += 12
            elif m.group(3).upper() == "AM" and hour == 12:
                hour = 0
            now = datetime.now()
            reset_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if reset_time <= now:
                reset_time = reset_time.replace(day=now.day + 1)
            delta = (reset_time - now).total_seconds()
            if 0 < delta < 86400:
                return int(delta)
        except (ValueError, OverflowError):
            pass

    # Gemini: "quota will reset after 18m38s"
    m = re.search(r'quota will reset after (\d+)m(\d+)s', output)
    if m:
        return int(m.group(1)) * 60 + int(m.group(2))

    # Duration patterns
    m = re.search(r'(\d+)[- ]hour', output)
    if m:
        return int(m.group(1)) * 3600
    m = re.search(r'(\d+)[- ]minute', output)
    if m:
        return int(m.group(1)) * 60
    return None


@activity.defn
async def run_golem_task(task: str, provider: str, max_turns: int = 50) -> dict:
    """Execute a single golem task as a subprocess.

    Raises ApplicationError (retryable) on rate limits so Temporal retries.
    Returns result dict on success or permanent failure.
    """
    cmd = [
        "bash", str(GOLEM_SCRIPT),
        "--provider", provider,
        "--max-turns", str(max_turns),
        task,
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
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
                "rate_limited": False,
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
    combined = stdout + stderr

    # Rate-limit detection — raise retryable error so Temporal backs off
    rate_limited = is_rate_limited(combined) or (rc != 0 and not combined.strip())
    if rate_limited:
        window = parse_rate_limit_window(combined)
        window_str = f" (reset in {window}s)" if window else ""
        raise ApplicationError(
            f"Rate limited: {provider}{window_str} — {combined[:500]}",
            type="RATE_LIMITED",
            non_retryable=False,  # Temporal will retry with backoff
        )

    return {
        "success": rc == 0,
        "exit_code": rc,
        "provider": provider,
        "task": task[:200],
        "stdout": stdout[:4000],
        "stderr": stderr[:2000],
        "rate_limited": False,
    }


async def main() -> None:
    """Start the Temporal worker."""
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        sys.exit(0)

    # Import workflow here to avoid circular import at module level
    from workflow import GolemDispatchWorkflow

    host = os.getenv("TEMPORAL_HOST", "localhost:7233")
    client = await Client.connect(host)

    # Total concurrent activities across all providers
    max_concurrent = sum(PROVIDER_LIMITS.values())

    worker = Worker(
        client=client,
        task_queue=TASK_QUEUE,
        workflows=[GolemDispatchWorkflow],
        activities=[run_golem_task],
        max_concurrent_activities=max_concurrent,
    )
    print(f"Temporal golem worker started on queue '{TASK_QUEUE}' (max_concurrent={max_concurrent})")
    print(f"Provider limits: {PROVIDER_LIMITS}")
    print(f"Rate-limit detection: enabled")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
