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
import os
import re
import secrets
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

# Only zhipu confirmed working on ganglion. Others exit 127.
# Re-enable when provider configs are fixed on ganglion.
PROVIDER_LIMITS: dict[str, int] = {
    "zhipu": 8,
    # "infini": 2,
    # "volcano": 16,
    # "gemini": 4,
    # "codex": 4,
}
DEFAULT_LIMIT = 4
MAX_TOTAL_CONCURRENT = 24

# Provider fallback chain — disabled until non-zhipu providers work on ganglion.
PROVIDER_FALLBACK: dict[str, list[str]] = {
    "zhipu": [],
}

# ---------------------------------------------------------------------------
# Rate-limit detection (mirrors golem-daemon)
# ---------------------------------------------------------------------------

RATE_LIMIT_PATTERNS = re.compile(
    r'429|AccountQuotaExceeded|rate.?limit|quota.?exceeded|20013|'
    r'request.?limit.?exceeded|API Error.*429|too many requests|TooManyRequests|'
    r'usage.?limit|hit your.*limit|quota will reset',
    re.IGNORECASE,
)

# Per-provider rate-limit windows (seconds) — used when provider is known to
# have strict quotas and fast-exit patterns suggest rate-limiting.
PROVIDER_RATE_WINDOWS: dict[str, int] = {
    "infini": 18000,   # 1000 req / 5 hours
    "volcano": 18000,  # 5-hour quota window
    "codex": 3600,     # ~hourly resets
    "gemini": 1200,    # ~20 min resets
}


def parse_rate_limit_window(text: str) -> int | None:
    """Extract rate-limit window in seconds from error message.

    Priority:
    1. Exact reset timestamp (e.g. "reset at 2026-04-01 21:09:32")
    2. "try again at H:MM PM" (Codex format)
    3. "quota will reset after NmNs" (Gemini format)
    4. Duration patterns ("5-hour", "30-minute")
    Returns seconds until reset, or None if not parseable.
    """
    from datetime import datetime

    # 1. Exact reset timestamp
    m = re.search(r'reset at (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', text)
    if m:
        try:
            reset_time = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
            delta = (reset_time - datetime.now()).total_seconds()
            if delta > 0:
                return int(delta)
        except (ValueError, OverflowError):
            pass

    # 2. "try again at H:MM PM"
    m = re.search(r'try again at (\d{1,2}):(\d{2})\s*([AP]M)', text, re.IGNORECASE)
    if m:
        try:
            hour = int(m.group(1))
            minute = int(m.group(2))
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

    # 3. "quota will reset after NmNs"
    m = re.search(r'quota will reset after (\d+)m(\d+)s', text)
    if m:
        return int(m.group(1)) * 60 + int(m.group(2))

    # 4. Duration patterns
    m = re.search(r'(\d+)[- ]hour', text)
    if m:
        return int(m.group(1)) * 3600
    m = re.search(r'(\d+)[- ]minute', text)
    if m:
        return int(m.group(1)) * 60
    return None


def is_rate_limited(text: str) -> bool:
    """Check if text contains rate-limit/quota-exhaustion indicators."""
    return bool(RATE_LIMIT_PATTERNS.search(text))


# ---------------------------------------------------------------------------
# Rate-limit cooldown tracking
# ---------------------------------------------------------------------------

RATE_LIMIT_COOLDOWN_SECONDS = 18000  # 5-hour cooldown for quota exhaustion
PROVIDER_COOLDOWN_SECONDS = 600      # 10 min cooldown after excessive failures
PROVIDER_FAILURE_WINDOW = 600   # 10 min sliding window for failure counting
PROVIDER_FAILURE_THRESHOLD = 3  # cooldown after N failures within the window

COOLDOWN_LOG = Path.home() / ".local" / "share" / "vivesca" / "golem-cooldowns.json"

# Runtime state: provider -> timestamp when cooldown expires
_provider_cooldown_until: dict[str, float] = {}

# Runtime state: provider -> count of currently dispatched (in-flight) tasks
_provider_running: dict[str, int] = {}
# Runtime state: provider -> temporary concurrency reduction (adaptive throttle)
_provider_throttle: dict[str, int] = {}
# Runtime state: provider -> list of failure timestamps (sliding window)
_provider_failure_times: dict[str, list[float]] = {}


def _log_cooldown(provider: str, cooldown_until: float, reason: str = "", event: str = "burnout") -> None:
    """Append cooldown event to persistent log for visibility."""
    entry = {
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "event": event,
        "provider": provider,
        "resets_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(cooldown_until)) if event == "burnout" else None,
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
    return f"t-{secrets.token_hex(3)}"


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


def _dispatch_candidates(provider: str) -> list[str]:
    """Return providers to try for migrated work, preserving preferred order first."""
    ordered: list[str] = []
    seen = {provider}
    for candidate in PROVIDER_FALLBACK.get(provider, []):
        if candidate not in seen:
            ordered.append(candidate)
            seen.add(candidate)
    for candidate in PROVIDER_LIMITS:
        if candidate not in seen:
            ordered.append(candidate)
            seen.add(candidate)
    return ordered



def _pick_dispatch_provider(provider: str) -> str | None:
    """Pick the runtime provider, falling back if the preferred one is on cooldown."""
    if not _is_on_cooldown(provider):
        return provider
    for candidate in _dispatch_candidates(provider):
        if _is_on_cooldown(candidate):
            continue
        current = _provider_running.get(candidate, 0)
        limit = get_provider_limit(candidate)
        if current < limit:
            return candidate
    return None


def get_provider_limit(provider: str) -> int:
    """Return concurrency limit for a provider, reduced by adaptive throttle."""
    base = PROVIDER_LIMITS.get(provider, DEFAULT_LIMIT)
    throttle = _provider_throttle.get(provider, 0)
    return max(1, base - throttle)


def _throttle_provider(provider: str) -> None:
    """Reduce provider concurrency by 1 after a failure (adaptive back-pressure)."""
    base = PROVIDER_LIMITS.get(provider, DEFAULT_LIMIT)
    current = _provider_throttle.get(provider, 0)
    if current < base - 1:
        _provider_throttle[provider] = current + 1


def _unthrottle_provider(provider: str) -> None:
    """Restore 1 slot of provider concurrency after a success."""
    current = _provider_throttle.get(provider, 0)
    if current > 0:
        _provider_throttle[provider] = current - 1

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
    Generates a unique task ID (t-xxxxxx) for each task that doesn't have one,
    and writes it back into the queue file inside the backtick (like golem-daemon).
    High-priority [!!] tasks are sorted before normal [ ] tasks.
    """
    with QueueLock():
        if not QUEUE_FILE.exists():
            return []

        lines = QUEUE_FILE.read_text().splitlines()

    pending = []
    modified = False
    priority_map: dict[int, int] = {}  # line_num -> priority (0=high, 1=normal)

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not (stripped.startswith("- [ ] ") or stripped.startswith("- [!!] ")):
            continue

        # Match outermost backtick pair (greedy — handles backticks inside prompts)
        cmd_match = re.search(r"`(.+)`", line)
        if not cmd_match:
            continue

        cmd = cmd_match.group(1)

        provider_match = re.search(r"(?:--provider|-b)\s+(\w+)", cmd)
        provider = provider_match.group(1) if provider_match else "zhipu"

        tid_match = TASK_ID_RE.search(cmd)
        if tid_match:
            task_id = f"t-{tid_match.group(1)}"
        else:
            task_id = _generate_task_id()
            # Inject task ID after "golem " in the command, matching golem-daemon
            new_cmd = cmd.replace("golem ", f"golem [{task_id}] ", 1)
            lines[i] = line.replace(f"`{cmd}`", f"`{new_cmd}`", 1)
            cmd = new_cmd
            modified = True

        prompt_match = re.search(r'"([^"]+)"', cmd)
        if prompt_match:
            prompt = prompt_match.group(1)
        else:
            # Strip golem prefix, task IDs, and known flags only
            prompt = re.sub(r'^golem\s+', '', cmd)
            prompt = re.sub(r'\[t-[0-9a-fA-F]+\]\s*', '', prompt)
            prompt = re.sub(r'(?:--provider|-b)\s+\S+\s*', '', prompt)
            prompt = re.sub(r'--max-turns\s+\d+\s*', '', prompt)
            prompt = prompt.strip() or cmd

        turns_match = re.search(r"--max-turns\s+(\d+)", cmd)
        max_turns = int(turns_match.group(1)) if turns_match else 50

        is_high = stripped.startswith("- [!!] ")
        priority_map[i] = 0 if is_high else 1
        pending.append((i, prompt, provider, task_id, max_turns))

    # Write back if any IDs were generated
    if modified:
        try:
            with QueueLock():
                QUEUE_FILE.write_text("\n".join(lines) + "\n")
        except (PermissionError, OSError):
            pass

    # Sort: high priority (0) first, then normal (1); stable sort preserves file order
    pending.sort(key=lambda x: priority_map.get(x[0], 1))
    return pending


_PENDING_PREFIXES = ("- [ ] ", "- [!!] ", "- [!] ")


def _find_task_line(lines: list[str], line_num: int, task_id: str) -> int:
    """Find task line by task_id, falling back to line_num.

    External edits to the queue file can shift line numbers. When the line at
    line_num doesn't match, scan for the task_id to find the correct line.
    Returns -1 if not found.
    """
    def _is_task(s: str) -> bool:
        return any(s.startswith(p) for p in _PENDING_PREFIXES)

    # Fast path: line_num is still correct
    if 0 <= line_num < len(lines):
        line = lines[line_num].strip()
        if task_id and f"[{task_id}]" in line and _is_task(line):
            return line_num
    # Slow path: scan by task_id
    if task_id:
        for i, line in enumerate(lines):
            stripped = line.strip()
            if f"[{task_id}]" in stripped and _is_task(stripped):
                return i
    # Final fallback: original line_num if it's a pending task
    if 0 <= line_num < len(lines):
        stripped = lines[line_num].strip()
        if _is_task(stripped):
            return line_num
    return -1


def mark_done(line_num: int, task_id: str = "") -> None:
    """Mark a task as done in the queue file (under QueueLock)."""
    with QueueLock():
        if not QUEUE_FILE.exists():
            return
        try:
            lines = QUEUE_FILE.read_text().splitlines()
        except (PermissionError, OSError, UnicodeDecodeError):
            return
        actual_line = _find_task_line(lines, line_num, task_id)
        if actual_line < 0:
            return
        original = lines[actual_line]
        stripped = original.strip()
        if stripped.startswith("- [!!] "):
            lines[actual_line] = original.replace("- [!!] ", "- [x] ", 1)
        elif stripped.startswith("- [ ] "):
            lines[actual_line] = original.replace("- [ ] ", "- [x] ", 1)
        else:
            return
        try:
            QUEUE_FILE.write_text("\n".join(lines) + "\n")
        except (PermissionError, OSError):
            return


def mark_failed(line_num: int, task_id: str = "", reason: str = "") -> dict:
    """Mark a task as failed in the queue file (under QueueLock).

    Supports retry: if the command hasn't been retried yet, re-queue it
    with a (retry) tag.  Otherwise mark as permanently failed [!].

    Returns {"retried": bool, "rate_limited": bool}.
    """
    rate_limited = is_rate_limited(reason) if reason else False
    with QueueLock():
        if not QUEUE_FILE.exists():
            return {"retried": False, "rate_limited": rate_limited}
        try:
            lines = QUEUE_FILE.read_text().splitlines()
        except (PermissionError, OSError, UnicodeDecodeError):
            return {"retried": False, "rate_limited": rate_limited}
        actual_line = _find_task_line(lines, line_num, task_id)
        if actual_line < 0:
            return {"retried": False, "rate_limited": rate_limited}
        original = lines[actual_line]
        stripped = original.strip()
        is_high = stripped.startswith("- [!!] ")
        if not is_high and not stripped.startswith("- [ ] "):
            return {"retried": False, "rate_limited": rate_limited}

        cmd_match = re.search(r'`([^`]+)`', original)
        retried = False

        def _to_failed(line: str) -> str:
            if "- [!!] " in line:
                return line.replace("- [!!] ", "- [!] ", 1)
            return line.replace("- [ ] ", "- [!] ", 1)

        if not cmd_match:
            lines[actual_line] = _to_failed(original)
        elif '(retry)' not in cmd_match.group(1):
            old_cmd = cmd_match.group(1)
            if old_cmd.rstrip().endswith('"'):
                new_cmd = old_cmd.rstrip()[:-1] + ' (retry)"'
            else:
                new_cmd = old_cmd + ' (retry)'
            lines[actual_line] = original.replace(f'`{old_cmd}`', f'`{new_cmd}`', 1)
            retried = True
        else:
            lines[actual_line] = _to_failed(original)

        try:
            QUEUE_FILE.write_text("\n".join(lines) + "\n")
        except (PermissionError, OSError):
            return {"retried": False, "rate_limited": rate_limited}

        return {"retried": retried, "rate_limited": rate_limited}


async def dispatch_all(dry_run: bool = False, mode: str = "raw") -> int:
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
    dispatched = []  # list of (line_num, task_id) for mark_done
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
            "mode": mode,
        })
        dispatched.append((line_num, task_id))
        _provider_running[dispatch_provider] = current_running + 1
        label = provider if dispatch_provider == provider else f"{provider}->{dispatch_provider}"
        log(f"[QUEUE] [{task_id}] {label}: {prompt[:60]}...")

    if not specs:
        log(f"All {len(pending)} tasks skipped (cooldowns/limits)")
        return 0

    # #2: One workflow per task — independent completion, no batch blocking
    from workflow import GolemDispatchWorkflow

    host = os.getenv("TEMPORAL_HOST", "ganglion:7233")
    client = await Client.connect(host)

    # Start all workflows
    handles = []
    for spec, (ln, tid) in zip(specs, dispatched):
        wf_id = f"golem-{tid}-{uuid.uuid4().hex[:4]}"
        handle = await client.start_workflow(
            GolemDispatchWorkflow.run,
            args=[[spec]],  # single-element list (workflow expects list)
            id=wf_id,
            task_queue="golem-tasks",
        )
        handles.append((handle, ln, tid, spec))
        log(f"Dispatched [{tid}] as workflow {wf_id}")

    # Await all results independently
    approved_count = 0
    flagged_count = 0
    rejected_count = 0
    for handle, ln, tid, spec in handles:
        try:
            result = await handle.result()
            task_results = result.get("results", [])
            tr = task_results[0] if task_results else {}
            review = tr.get("review", {})
            verdict = review.get("verdict", "unknown")
            flags = review.get("flags", [])

            if verdict == "approved":
                mark_done(ln, task_id=tid)
                output_path = review.get("output_path", "")
                extra = f" → {output_path}" if output_path else ""
                log(f"[DONE] [{tid}] {tr.get('provider', '?')}{extra}")
                approved_count += 1
            elif verdict == "approved_with_flags":
                log(f"[HOLD] [{tid}] {tr.get('provider', '?')} — flags: {', '.join(flags)}")
                flagged_count += 1
            else:
                requeue_prompt = tr.get("requeue_prompt", "")
                if requeue_prompt:
                    _auto_requeue(requeue_prompt, tr.get("provider", "zhipu"))
                    log(f"[REQUEUE] [{tid}] {tr.get('provider', '?')} — auto-requeued with coaching")
                elif tr.get("exit_code", 0) != 0:
                    orig_provider = tr.get("provider", "zhipu")
                    fallback_list = PROVIDER_FALLBACK.get(orig_provider, [])
                    fallback = next((f for f in fallback_list if not _is_on_cooldown(f)), None)
                    if fallback:
                        _auto_requeue(spec.get("task", ""), fallback)
                        log(f"[FALLBACK] [{tid}] {orig_provider}->{fallback} — requeued on fallback")
                reason = f"review rejected: {', '.join(flags)}" if flags else "review rejected"
                mark_failed(ln, task_id=tid, reason=reason)
                log(f"[FAIL] [{tid}] {tr.get('provider', '?')} — {reason}")
                rejected_count += 1
        except Exception as e:
            log(f"[FAIL] [{tid}] workflow error: {e}")
            mark_failed(ln, task_id=tid, reason=f"workflow error: {str(e)[:100]}")
            rejected_count += 1

    log(f"Complete: {approved_count} approved, {flagged_count} flagged, {rejected_count} rejected")
    _sync_reviews()
    return len(specs)


def _auto_requeue(prompt: str, provider: str) -> None:
    """#9: Append a coached retry task to the queue."""
    import secrets as _secrets
    tid = f"t-{_secrets.token_hex(3)}"
    entry = f'- [ ] `golem --provider {provider} [{tid}] {prompt}`\n'
    with QueueLock():
        lines = QUEUE_FILE.read_text().splitlines() if QUEUE_FILE.exists() else ["### Pending"]
        # Insert after "### Pending" line
        for i, line in enumerate(lines):
            if line.strip().startswith("### Pending"):
                lines.insert(i + 1, entry.rstrip())
                break
        else:
            lines.append(entry.rstrip())
        QUEUE_FILE.write_text("\n".join(lines) + "\n")


def _sync_reviews() -> None:
    """Pull golem-reviews.jsonl from ganglion; sync germline via git."""
    import subprocess
    # Pull review log (not in git — ephemeral)
    review_src = "ganglion:~/germline/loci/golem-reviews.jsonl"
    review_dst = str(Path.home() / "germline" / "loci" / "golem-reviews.jsonl")
    try:
        subprocess.run(["rsync", "-az", review_src, review_dst], timeout=30, capture_output=True)
    except Exception:
        pass
    # Git pull on ganglion to sync skills + temporal-golem code
    try:
        subprocess.run(
            ["ssh", "ganglion", "cd ~/germline && git pull --ff-only 2>&1"],
            timeout=30, capture_output=True,
        )
        log("[SYNC] reviews pulled, ganglion git pulled")
    except Exception as e:
        log(f"[SYNC] failed: {e}")


async def poll_loop(interval: int = 30) -> None:
    """Continuously poll the queue and dispatch tasks.

    On rate-limit errors (HTTP 429 / quota messages), sets a cooldown
    on the offending provider so subsequent poll cycles skip it until
    the cooldown expires.  Tracks non-rate-limit failures in a sliding
    window and triggers cooldown when PROVIDER_FAILURE_THRESHOLD is hit.
    Uses adaptive throttle to reduce per-provider concurrency on failure.
    """
    log(f"Starting poll loop (interval={interval}s)")
    while True:
        try:
            count = await dispatch_all()
            if count == 0:
                log("Queue empty, waiting...")
            else:
                # Success — unthrottle all providers
                for prov in list(_provider_throttle):
                    _unthrottle_provider(prov)
        except Exception as e:
            err_msg = str(e)
            # Detect rate-limit / quota errors using compiled regex
            if is_rate_limited(err_msg) or "resource exhausted" in err_msg.lower():
                # Try to extract a precise cooldown window from the error text
                window = parse_rate_limit_window(err_msg)
                # Try to identify the provider from the error
                cooldown_applied = False
                for prov in PROVIDER_LIMITS:
                    if prov in err_msg.lower():
                        cooldown = window or PROVIDER_RATE_WINDOWS.get(prov, RATE_LIMIT_COOLDOWN_SECONDS)
                        _set_cooldown(prov, cooldown, reason=err_msg[:100])
                        _throttle_provider(prov)
                        log(f"RATE-LIMIT detected for {prov}, cooldown {cooldown}s")
                        cooldown_applied = True
                        break
                if not cooldown_applied:
                    # Unknown provider — apply cooldown to all low-limit providers
                    cooldown = window or RATE_LIMIT_COOLDOWN_SECONDS
                    for prov, lim in PROVIDER_LIMITS.items():
                        if lim <= 2:
                            _set_cooldown(prov, cooldown, reason=err_msg[:100])
                    log(f"RATE-LIMIT detected (unknown provider), cooldown applied to low-limit providers")
            else:
                log(f"Error in poll loop: {e}")
                # Track non-rate-limit failures in sliding window per provider
                failed_prov = None
                for prov in PROVIDER_LIMITS:
                    if prov in err_msg.lower():
                        failed_prov = prov
                        break
                if failed_prov:
                    _throttle_provider(failed_prov)
                    now = time.time()
                    if failed_prov not in _provider_failure_times:
                        _provider_failure_times[failed_prov] = []
                    times = _provider_failure_times[failed_prov]
                    times.append(now)
                    window_start = now - PROVIDER_FAILURE_WINDOW
                    _provider_failure_times[failed_prov] = [t for t in times if t >= window_start]
                    recent_fails = len(_provider_failure_times[failed_prov])
                    if recent_fails >= PROVIDER_FAILURE_THRESHOLD:
                        cooldown_end = now + PROVIDER_COOLDOWN_SECONDS
                        _provider_cooldown_until[failed_prov] = cooldown_end
                        _log_cooldown(failed_prov, cooldown_end, f"failure window {recent_fails} in {PROVIDER_FAILURE_WINDOW//60}min")
                        log(f"COOLDOWN: {failed_prov} hit {recent_fails} failures in {PROVIDER_FAILURE_WINDOW//60}min window")
        await asyncio.sleep(interval)


async def show_status(json_output: bool = False) -> None:
    """Show recent Temporal workflow runs."""
    host = os.getenv("TEMPORAL_HOST", "ganglion:7233")
    client = await Client.connect(host)
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
    mode = "graph" if "--graph" in args else "raw"

    interval = 30
    if "--interval" in args:
        idx = args.index("--interval")
        if idx + 1 < len(args):
            interval = int(args[idx + 1])

    if poll:
        asyncio.run(poll_loop(interval))
    else:
        asyncio.run(dispatch_all(dry_run=dry_run, mode=mode))


if __name__ == "__main__":
    main()
