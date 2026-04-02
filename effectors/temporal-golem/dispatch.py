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
import fcntl
import json
import random
import re
import sys
import time
import uuid
from pathlib import Path

from temporalio.client import Client

QUEUE_FILE = Path.home() / "germline" / "loci" / "golem-queue.md"
LOG_FILE = Path.home() / ".local" / "share" / "vivesca" / "temporal-dispatch.log"

# ---------------------------------------------------------------------------
# QueueLock — file-based mutex shared with golem-daemon
# ---------------------------------------------------------------------------

class QueueLock:
    """Exclusive file lock on the same lock file golem-daemon uses."""
    _lock_path = Path.home() / ".local" / "share" / "vivesca" / "golem-queue.lock"

    def __enter__(self):
        self._lock_path.parent.mkdir(parents=True, exist_ok=True)
        self._fd = open(self._lock_path, "w")
        fcntl.flock(self._fd, fcntl.LOCK_EX)
        return self

    def __exit__(self, *args):
        fcntl.flock(self._fd, fcntl.LOCK_UN)
        self._fd.close()


# ---------------------------------------------------------------------------
# Task-ID format (same as golem-daemon)
# ---------------------------------------------------------------------------

TASK_ID_RE = re.compile(r"\[t-([0-9a-f]{6})\]")

# ---------------------------------------------------------------------------
# Per-provider concurrency limits (mirrors golem-daemon)
# ---------------------------------------------------------------------------

PROVIDER_LIMITS: dict[str, int] = {
    "zhipu": 8,
    "infini": 2,
    "volcano": 16,
    "gemini": 4,
    "codex": 4,
}
DEFAULT_LIMIT = 4
MAX_TOTAL_CONCURRENT = 24

# Provider fallback chain — ordered by pass rate.
PROVIDER_FALLBACK: dict[str, list[str]] = {
    "codex": ["gemini", "zhipu"],
    "gemini": ["codex", "zhipu"],
    "zhipu": ["codex", "gemini"],
    "infini": ["codex", "gemini"],
    "volcano": ["codex", "gemini"],
}

# ---------------------------------------------------------------------------
# Rate-limit cooldown tracking
# ---------------------------------------------------------------------------

RATE_LIMIT_COOLDOWN_SECONDS = 18000  # 5-hour cooldown for quota exhaustion
PROVIDER_COOLDOWN_SECONDS = 600      # 10 min cooldown after excessive failures

COOLDOWN_LOG = Path.home() / ".local" / "share" / "vivesca" / "golem-cooldowns.json"

# Runtime state: provider -> timestamp when cooldown expires
_provider_cooldown_until: dict[str, float] = {}

# Runtime state: provider -> count of currently dispatched (in-flight) tasks
_provider_running: dict[str, int] = {}


def _log_cooldown(provider: str, cooldown_until: float, reason: str = "") -> None:
    """Append cooldown event to persistent log for visibility."""
    entry = {
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "event": "burnout",
        "provider": provider,
        "resets_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(cooldown_until)),
        "reason": reason[:100],
    }
    try:
        entries = json.loads(COOLDOWN_LOG.read_text()) if COOLDOWN_LOG.exists() else []
    except (json.JSONDecodeError, OSError):
        entries = []
    if entries:
        last_for_provider = [
            e for e in entries
            if e.get("provider") == provider and e.get("event") == "burnout"
        ]
        if last_for_provider and last_for_provider[-1].get("resets_at") == entry.get("resets_at"):
            return
    entries.append(entry)
    entries = entries[-100:]
    COOLDOWN_LOG.write_text(json.dumps(entries, indent=2) + "\n")


def _generate_task_id() -> str:
    """Generate a task ID in t-XXXXXX format (6 hex chars, same as golem-daemon)."""
    return f"t-{random.randint(0, 0xFFFFFF):06x}"


def _is_on_cooldown(provider: str) -> bool:
    """Return True if *provider* is still within its cooldown window."""
    deadline = _provider_cooldown_until.get(provider, 0)
    if deadline <= time.time():
        _provider_cooldown_until.pop(provider, None)
        return False
    return True


def _set_cooldown(provider: str, seconds: float, reason: str = "") -> None:
    """Put *provider* on cooldown for *seconds* from now."""
    cooldown_end = time.time() + seconds
    # Only extend, never shorten
    if _provider_cooldown_until.get(provider, 0) < cooldown_end:
        _provider_cooldown_until[provider] = cooldown_end
        _log_cooldown(provider, cooldown_end, reason)


def _pick_dispatch_provider(provider: str) -> str | None:
    """Pick the runtime provider, falling back if the preferred one is on cooldown."""
    if not _is_on_cooldown(provider):
        return provider
    for candidate in PROVIDER_FALLBACK.get(provider, []):
        if _is_on_cooldown(candidate):
            continue
        current = _provider_running.get(candidate, 0)
        limit = PROVIDER_LIMITS.get(candidate, DEFAULT_LIMIT)
        if current < limit:
            return candidate
    return None


def get_provider_limit(provider: str) -> int:
    """Return concurrency limit for a provider."""
    return PROVIDER_LIMITS.get(provider, DEFAULT_LIMIT)

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
    """Parse queue file under QueueLock.

    Returns [(line_num, prompt, provider, task_id, max_turns)].
    """
    with QueueLock():
        if not QUEUE_FILE.exists():
            return []

        lines = QUEUE_FILE.read_text().splitlines()

    pending = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not (stripped.startswith("- [ ] ") or stripped.startswith("- [!!] ")):
            continue

        cmd_match = re.search(r"`([^`]+)`", line)
        if not cmd_match:
            continue

        cmd = cmd_match.group(1)

        provider_match = re.search(r"--provider\s+(\w+)", cmd)
        provider = provider_match.group(1) if provider_match else "zhipu"

        tid_match = TASK_ID_RE.search(cmd)
        task_id = f"t-{tid_match.group(1)}" if tid_match else _generate_task_id()

        prompt_match = re.search(r'"([^"]+)"', cmd)
        prompt = prompt_match.group(1) if prompt_match else cmd

        turns_match = re.search(r"--max-turns\s+(\d+)", cmd)
        max_turns = int(turns_match.group(1)) if turns_match else 50

        pending.append((i, prompt, provider, task_id, max_turns))

    return pending


def mark_done(line_num: int) -> None:
    """Mark a task as done in the queue file (under QueueLock)."""
    with QueueLock():
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
    """Mark a task as failed in the queue file (under QueueLock)."""
    with QueueLock():
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
    """Dispatch all pending tasks as a single Temporal workflow.

    Skips providers currently on cooldown, falling back through
    PROVIDER_FALLBACK.  Tracks per-provider concurrency so we never
    exceed PROVIDER_LIMITS.
    """
    pending = parse_queue()
    if not pending:
        log("No pending tasks in queue")
        return 0

    log(f"Found {len(pending)} pending tasks")

    if dry_run:
        for line_num, prompt, provider, task_id, max_turns in pending:
            log(f"[DRY] [{task_id}] {provider}: {prompt[:60]}...")
        return len(pending)

    # Build specs for Temporal workflow, respecting cooldowns & limits
    specs = []
    line_nums = []
    skipped = 0
    for line_num, prompt, provider, task_id, max_turns in pending:
        dispatch_provider = _pick_dispatch_provider(provider)
        if dispatch_provider is None:
            skipped += 1
            log(f"[SKIP] [{task_id}] {provider} on cooldown, no fallback available")
            continue

        # Enforce per-provider concurrency limit
        current_running = _provider_running.get(dispatch_provider, 0)
        limit = get_provider_limit(dispatch_provider)
        total_running = sum(_provider_running.values())
        if current_running >= limit or total_running >= MAX_TOTAL_CONCURRENT:
            skipped += 1
            log(f"[SKIP] [{task_id}] {dispatch_provider} at concurrency limit ({current_running}/{limit})")
            continue

        specs.append({
            "task": prompt,
            "provider": dispatch_provider,
            "max_turns": max_turns,
        })
        line_nums.append(line_num)
        _provider_running[dispatch_provider] = current_running + 1
        label = provider if dispatch_provider == provider else f"{provider}->{dispatch_provider}"
        log(f"[QUEUE] [{task_id}] {label}: {prompt[:60]}...")

    if not specs:
        log(f"All {len(pending)} tasks skipped (cooldowns/limits)")
        return 0

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
    log(f"Dispatched {len(specs)} tasks as workflow {wf_id}" + (f", skipped {skipped}" if skipped else ""))
    return len(specs)


async def poll_loop(interval: int = 30) -> None:
    """Continuously poll the queue and dispatch tasks.

    On rate-limit errors (HTTP 429 / quota messages), sets a cooldown
    on the offending provider so subsequent poll cycles skip it until
    the cooldown expires.
    """
    log(f"Starting poll loop (interval={interval}s)")
    while True:
        try:
            count = await dispatch_all()
            if count == 0:
                log("Queue empty, waiting...")
        except Exception as e:
            err_msg = str(e).lower()
            # Detect rate-limit / quota errors and set cooldowns
            if any(kw in err_msg for kw in ("429", "rate limit", "quota", "resource exhausted")):
                # Try to identify the provider from the error
                for prov in PROVIDER_LIMITS:
                    if prov in err_msg:
                        _set_cooldown(prov, RATE_LIMIT_COOLDOWN_SECONDS, reason=err_msg[:100])
                        log(f"RATE-LIMIT detected for {prov}, cooldown {RATE_LIMIT_COOLDOWN_SECONDS}s")
                        break
                else:
                    # Unknown provider — apply cooldown to all low-limit providers
                    for prov, lim in PROVIDER_LIMITS.items():
                        if lim <= 2:
                            _set_cooldown(prov, RATE_LIMIT_COOLDOWN_SECONDS, reason=err_msg[:100])
                    log(f"RATE-LIMIT detected (unknown provider), cooldown applied to low-limit providers")
            else:
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
