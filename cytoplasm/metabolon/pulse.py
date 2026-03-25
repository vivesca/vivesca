"""pulse — the organism's heartbeat.

Each wave is a heartbeat: respiration regulates the rate, pulse is the
beat. Runs waves, manages the cardiac log, detects stalls/churn, handles
autophagy and vital signs reporting.

Safety nets:
1. Vital capacity check (respiration)
2. Per-wave respiratory status check
3. --stop-after circadian deadline (default 07:00 overnight)
4. Max waves cap (3 overnight, 1 daytime per cycle)
5. Circuit breaker (3 consecutive failures)
6. Wave timeout with stall/churn detection
7. Cardiac lock prevents concurrent instances
"""

import atexit
import datetime
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

from metabolon.respiration import (
    EVENT_LOG,
    check_vital_capacity,
    get_respiratory_status,
    increment_daily_wave_count,
    is_apneic,
    log,
    log_event,
    measure_respiration,
    read_respiratory_genome,
    respiration_snapshot,
    resume_breathing,
    send_distress_signal,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
CARDIAC_LOG = Path.home() / "tmp" / "pulse-manifest.md"
CARDIAC_LOCK = Path.home() / "tmp" / "pulse.lock"
LOG_DIR = Path.home() / "logs"
REPORT_DIR = Path.home() / "notes" / "Pulse Reports"
VITAL_SIGNS_FILE = Path.home() / "tmp" / "pulse-status.json"

# ---------------------------------------------------------------------------
# Wave defaults
# ---------------------------------------------------------------------------
CIRCADIAN_DEADLINE = "07:00"
MAX_WAVES = 3  # overnight waves per cycle
DAYTIME_WAVES = 1  # daytime waves per cycle

SATURATION_PHRASES = [
    "no new work",
    "diminishing returns",
    "all items covered",
    "nothing remaining",
    "saturated",
    "exhausted",
    "no further",
]

WAVE_PROMPT = """One heartbeat. ONE wave per session — the shell loop handles iteration.

You already have ~/CLAUDE.md (How to Think, meta-rules) and MEMORY.md loaded. Use them — especially "Map is dark" and "bet, review, bet". Don't duplicate what's already in your context.

## Steps

1. **Load session state.** Read ~/tmp/pulse-manifest.md (memory of prior waves), ~/code/vivesca-terry/chromatin/North Star.md (includes meta goal), ~/code/vivesca-terry/chromatin/Praxis.md (head 80), ~/code/vivesca-terry/chromatin/Tonus.md. Run `date`.
2. **Scout.** What do the north stars need? What did prior waves reveal? Any `agent:claude` items in TODO? Any deadlines within 14 days? Pick the north star with least coverage. Allocate ~30% of agents to the meta goal (system improvement) while the system is young.
3. **Dispatch 15-20 agents** with `run_in_background: true`, `mode: bypassPermissions`. Model routing: research/collection -> sonnet, synthesis/judgment -> opus. Each prompt starts: "Read ~/tmp/pulse-manifest.md. Do not duplicate completed work." When outputs naturally chain (research -> synthesis -> brief), dispatch as a pipeline.
4. **Wait** for all agents. Process results.
5. **Update** ~/tmp/pulse-manifest.md manifest. Route: self-sufficient -> archive from TODO. Needs Terry -> add to Praxis.md with `agent:terry`.
6. **Post to ACTA** for any results that need inter-skill coordination or Terry's attention:
   - `acta post "Brief: [title] ready at [path]" --from pulse --to terry --severity info`
   - `acta post "Action needed: [description]" --from pulse --to terry --severity action`
   Use the CLI — it is at vivesca/effectors/efferens. Post sparingly: only actionable items or significant deliverables.
7. **Observe** (append to manifest): which north stars got zero coverage? Any external signals? Any patterns?
8. **Exit.** Output summary and stop. Do NOT run another wave.

## Taste rules
- **No duplicates.** Check ~/code/vivesca-terry/chromatin/ for existing files. Update, don't create "v2."
- **Diminishing returns.** 0-5 files on a topic = good. 5-10 = only if novel. 10+ = move to a different star.
- **Stance > deadline.** "if it fails, it fails" = deprioritized. Read context, not just the due date.
- **Fix factual errors directly.** Typos, wrong acronyms, wrong dates = bugs. Fix them.
- **No sends, no pushes** to shared repos. Draft only for external comms.
- **Commit atomically.** If you modify a tracked file, `git add` + `git commit` before exiting. No dirty state left behind.
- **Only Automated tasks.** Presence/Sharpening/Collaborative = skip.
- **Quality gate** for client-facing or published content: dispatch a verification agent.
- **Never give up scouting.** Budget is the only stop.
"""


# ---------------------------------------------------------------------------
# Cardiac lock
# ---------------------------------------------------------------------------


def acquire_cardiac_lock():
    """Acquire cardiac lock — ensures only one heartbeat runs at a time."""
    if CARDIAC_LOCK.exists():
        try:
            existing_pid = int(CARDIAC_LOCK.read_text().strip())
        except (ValueError, OSError):
            existing_pid = None

        if existing_pid is not None:
            try:
                os.kill(existing_pid, 0)
                print(
                    f"Pulse already running (PID {existing_pid}). Exiting.",
                    flush=True,
                )
                sys.exit(1)
            except ProcessLookupError:
                print(
                    f"Removing stale lock (PID {existing_pid} no longer running).",
                    flush=True,
                )
            except PermissionError:
                print(
                    f"Pulse already running (PID {existing_pid}). Exiting.",
                    flush=True,
                )
                sys.exit(1)

        CARDIAC_LOCK.unlink(missing_ok=True)

    CARDIAC_LOCK.write_text(str(os.getpid()))
    atexit.register(release_cardiac_lock)


def release_cardiac_lock():
    """Release cardiac lock if it still belongs to this process."""
    try:
        if CARDIAC_LOCK.exists() and CARDIAC_LOCK.read_text().strip() == str(os.getpid()):
            CARDIAC_LOCK.unlink()
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Cardiac log
# ---------------------------------------------------------------------------


def init_cardiac_log():
    if not CARDIAC_LOG.exists():
        today = datetime.date.today().isoformat()
        CARDIAC_LOG.write_text(f"# Pulse Manifest -- {today}\n\n## Completed\n\n## In Progress\n")


def compact_cardiac_log():
    """Keep cardiac log under 100 lines so fresh session context stays small."""
    if not CARDIAC_LOG.exists():
        return
    lines = CARDIAC_LOG.read_text().splitlines()
    if len(lines) <= 100:
        return
    header = lines[:3]
    recent = lines[-80:]
    compacted = [*header, f"\n(... {len(lines) - 83} earlier lines compacted ...)\n", *recent]
    CARDIAC_LOG.write_text("\n".join(compacted))
    log_event("manifest_compacted", from_lines=len(lines), to_lines=len(compacted))


# ---------------------------------------------------------------------------
# Autonomic disk pressure relief
# ---------------------------------------------------------------------------

DISK_FLOOR_GB = 5  # below this, refuse to start a wave (ENOSPC risk)
DISK_CLEAN_GB = 15  # below this, run lysosome before wave


def check_disk_pressure() -> bool:
    """Sense disk pressure, auto-clean if needed. Returns True if safe to proceed."""
    try:
        free_gb = shutil.disk_usage("/").free / (1024**3)
    except Exception:
        return True  # can't measure → don't block

    if free_gb >= DISK_CLEAN_GB:
        return True

    log(f"Disk pressure: {free_gb:.1f}GB free (threshold {DISK_CLEAN_GB}GB). Running lysosome.")
    log_event("disk_pressure", free_gb=round(free_gb, 1), action="lysosome")

    try:
        from metabolon.tools.checkpoint import lysosome_digest

        result = lysosome_digest()
        log(f"Lysosome: freed {result.freed_gb}GB ({result.before_gb}→{result.after_gb}GB)")
        log_event(
            "disk_lysosome_complete",
            before_gb=result.before_gb,
            after_gb=result.after_gb,
            freed_gb=result.freed_gb,
        )
        free_gb = result.after_gb
    except Exception as e:
        log(f"Lysosome failed: {e}")
        log_event("disk_lysosome_failed", error=str(e))

    if free_gb < DISK_FLOOR_GB:
        log(f"Disk critically low ({free_gb:.1f}GB < {DISK_FLOOR_GB}GB). Refusing wave.")
        log_event("disk_critical", free_gb=round(free_gb, 1))
        return False

    return True


# ---------------------------------------------------------------------------
# Wave execution
# ---------------------------------------------------------------------------

SECRETION_DIRS = [
    Path.home() / "tmp",
    Path.home() / "docs" / "pulse",
]


def _count_recent_secretions(dirs: list, since: float) -> int:
    """Count recent secretions (files produced) after `since` timestamp."""
    count = 0
    for d in dirs:
        if not d.exists():
            continue
        for f in d.iterdir():
            if f.is_file() and f.stat().st_mtime > since:
                count += 1
    return count


def run_wave(wave_num: int, model: str, focus: str | None = None) -> tuple[bool, str]:
    """Run a single wave (one heartbeat). Returns (success, output_tail)."""
    log_file = LOG_DIR / "pulse-waves.log"

    prompt = WAVE_PROMPT
    if focus:
        prompt += f"\n\n## FOCUS RESTRICTION\nThis loop instance ONLY works on: {focus}. Ignore all other north stars. Another loop handles the rest."

    cmd = [
        "max20",
        model,
        "-p",
        "--dangerously-skip-permissions",
        "--no-session-persistence",
        prompt,
    ]

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = f"\n{'=' * 60}\n=== Wave {wave_num} -- {timestamp} ===\n{'=' * 60}\n"

    log_event("wave_start", wave=wave_num, model=model)
    start = time.time()

    with open(log_file, "a") as lf:
        lf.write(header)

    genome = read_respiratory_genome()
    max_wave_seconds = genome.get("max_wave_seconds", 1800)
    stall_seconds = genome.get("stall_seconds", 300)

    def write_status(**kwargs):
        """Write current wave vitals for external observers."""
        VITAL_SIGNS_FILE.write_text(
            json.dumps(
                {
                    "wave": wave_num,
                    "model": model,
                    "started": datetime.datetime.now().isoformat(),
                    **kwargs,
                },
                indent=2,
            )
        )

    log_fh = open(log_file, "a")
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=log_fh,
            stderr=subprocess.STDOUT,
            text=True,
        )
        last_log_size = os.path.getsize(log_file)
        last_growth_time = time.time()
        last_deliverable_time = time.time()
        last_deliverable_count = 0
        churn_seconds = genome.get("churn_seconds", 600)

        stall_warned = False
        churn_warned = False
        last_print_time = start

        while True:
            time.sleep(30)
            elapsed_so_far = round(time.time() - start)

            ret = proc.poll()
            if ret is not None:
                elapsed = round(time.time() - start, 1)
                try:
                    with open(log_file) as f:
                        f.seek(max(0, os.path.getsize(log_file) - 300))
                        tail = f.read().strip()[-200:]
                except Exception:
                    tail = "(unreadable)"
                recent_count = _count_recent_secretions(SECRETION_DIRS, start)
                log_event(
                    "wave_yield",
                    wave=wave_num,
                    secretion_count=recent_count,
                )
                log_event(
                    "wave_end",
                    wave=wave_num,
                    exit_code=ret,
                    elapsed_s=elapsed,
                    output_tail=tail,
                )
                write_status(state="completed", elapsed_s=elapsed)
                return ret == 0, tail

            current_log_size = os.path.getsize(log_file)
            if current_log_size > last_log_size:
                last_log_size = current_log_size
                last_growth_time = time.time()

            stall_duration = round(time.time() - last_growth_time)

            if stall_duration > stall_seconds:
                if not stall_warned:
                    log_event(
                        "wave_stall_warning",
                        wave=wave_num,
                        elapsed_s=elapsed_so_far,
                        stall_s=stall_duration,
                    )
                    stall_warned = True
            else:
                if stall_warned:
                    log_event(
                        "wave_stall_resolved",
                        wave=wave_num,
                        elapsed_s=elapsed_so_far,
                        stall_s=stall_duration,
                    )
                stall_warned = False

            recent_count = _count_recent_secretions(SECRETION_DIRS, start)
            if recent_count > last_deliverable_count:
                last_deliverable_time = time.time()
                last_deliverable_count = recent_count

            churn_duration = round(time.time() - last_deliverable_time)

            if churn_duration > churn_seconds and elapsed_so_far > churn_seconds:
                if not churn_warned:
                    log_event(
                        "wave_churn_warning",
                        wave=wave_num,
                        elapsed_s=elapsed_so_far,
                        churn_s=churn_duration,
                    )
                    churn_warned = True
            else:
                if churn_warned:
                    log_event(
                        "wave_churn_resolved",
                        wave=wave_num,
                        elapsed_s=elapsed_so_far,
                        churn_s=churn_duration,
                    )
                churn_warned = False

            if elapsed_so_far > max_wave_seconds:
                proc.kill()
                proc.wait()
                log_fh.write(f"\n--- KILLED after {elapsed_so_far}s ---\n")
                log_event(
                    "wave_killed",
                    wave=wave_num,
                    elapsed_s=elapsed_so_far,
                    reason="timeout",
                )
                print(f"  ! Killed wave {wave_num} at {elapsed_so_far}s", flush=True)
                return True, ""

            try:
                cpu = subprocess.run(
                    ["ps", "-p", str(proc.pid), "-o", "cputime="],
                    capture_output=True,
                    text=True,
                    timeout=2,
                ).stdout.strip()
            except Exception:
                cpu = "?"
            stall_status = f"stall={stall_duration}s" if stall_duration > 60 else "log=active"
            churn_status = f"churn={churn_duration}s" if churn_duration > 120 else "files=ok"
            now = time.time()
            if now - last_print_time >= 60:
                print(
                    f"  ... {elapsed_so_far}s elapsed, cpu={cpu}, {stall_status}, {churn_status}",
                    flush=True,
                )
                last_print_time = now
            write_status(
                elapsed_s=elapsed_so_far,
                stall_s=stall_duration,
                churn_s=churn_duration,
                cpu=cpu,
                new_deliverables=recent_count,
                log_active=stall_duration < 60,
                producing_files=churn_duration < 120,
            )

    except Exception as e:
        elapsed = round(time.time() - start, 1)
        log_event("wave_error", wave=wave_num, error=str(e), elapsed_s=elapsed)
        return False, ""
    finally:
        log_fh.close()


# ---------------------------------------------------------------------------
# Autophagy (cellular self-recycling)
# ---------------------------------------------------------------------------


def write_vital_signs(total_waves: int, stop_reason: str):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
    report_path = REPORT_DIR / f"{ts}-pulse.md"

    manifest_content = CARDIAC_LOG.read_text() if CARDIAC_LOG.exists() else "(no manifest)"

    report_path.write_text(f"""---
title: "Pulse Report -- {ts}"
date: {datetime.date.today().isoformat()}
tags: [pulse, report]
waves: {total_waves}
stop_reason: {stop_reason}
---

# Pulse Report -- {ts}

## Summary
- Waves completed: {total_waves}
- Stop reason: {stop_reason}

## Manifest (final state)
{manifest_content}
""")
    print(f"Report written to {report_path}")


def run_cross_model_review(manifest_path: Path):
    """Run cross-model quality check in background."""
    try:
        subprocess.Popen(
            ["pulse-review", str(manifest_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        log_event("cross_model_review", manifest=str(manifest_path))
        print(f"Cross-model review dispatched for {manifest_path.name}")
    except FileNotFoundError:
        print("pulse-review not found -- skipping cross-model review")


def post_acta_summary(total_waves: int, stop_reason: str):
    """Post a summary to ACTA board so Terry sees results in his inbox."""
    try:
        from metabolon.cytosol import VIVESCA_ROOT

        import acta

        acta.post(
            f"Pulse completed {total_waves} wave(s). Stop reason: {stop_reason}. "
            f"Check ~/code/vivesca-terry/chromatin/Pulse Reports/ for details.",
            sender="pulse",
            to="terry",
            severity="info",
            subject=f"pulse-{total_waves}w-{stop_reason}",
        )
    except Exception as e:
        log(f"ACTA post failed: {e}")


def autophagy(wave: int, stop_reason: str):
    """Autophagy — recycle the cardiac cycle: write vital signs, archive log, review."""
    write_vital_signs(wave, stop_reason)
    post_acta_summary(wave, stop_reason)
    if CARDIAC_LOG.exists():
        ts = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
        archive = CARDIAC_LOG.with_name(f"pulse-{ts}.md")
        CARDIAC_LOG.rename(archive)
        print(f"Manifest archived to {archive.name}")
        run_cross_model_review(archive)


# ---------------------------------------------------------------------------
# Event log rotation
# ---------------------------------------------------------------------------


def rotate_event_log():
    """Rotate event log if it exceeds 1MB."""
    if not EVENT_LOG.exists():
        return
    try:
        if EVENT_LOG.stat().st_size > 1_000_000:
            rotated = EVENT_LOG.with_suffix(".jsonl.1")
            if rotated.exists():
                rotated.unlink()
            EVENT_LOG.rename(rotated)
            log("Event log rotated (>1MB)")
    except Exception as e:
        log(f"Event log rotation failed: {e}")


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def main(waves=None, model="opus", retry=1, focus=None, stop_after=None, dry_run=False):
    """Main pulse loop."""
    log("=== Pulse starting ===")

    # Respiration: skip-until check (avoids respirometry call when pacing already blocked)
    skip, skip_reason = is_apneic()
    if skip:
        log(f"Skipping: {skip_reason}")
        return

    acquire_cardiac_lock()
    rotate_event_log()

    # Respiration: budget headroom (coarse gate)
    has_headroom, reason = check_vital_capacity()
    if not has_headroom:
        log(f"No headroom: {reason}. Exiting.")
        return
    log(f"Headroom confirmed: {reason}")

    hour = datetime.datetime.now().hour
    is_overnight = hour >= 22 or hour < 7

    max_waves = waves if waves is not None else (MAX_WAVES if is_overnight else DAYTIME_WAVES)
    stop_after_str = stop_after or (CIRCADIAN_DEADLINE if is_overnight else None)

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    init_cardiac_log()

    log_event("run_start", max_waves=max_waves, model=model, overnight=is_overnight)

    stop_reason = "completed"
    wave = 0
    consecutive_fails = 0
    consecutive_saturation = 0

    def sigint_handler(sig, frame):
        nonlocal stop_reason, wave
        log_event("interrupted", wave=wave)
        stop_reason = "interrupted"
        autophagy(wave, stop_reason)
        sys.exit(0)

    signal.signal(signal.SIGINT, sigint_handler)

    stop_after_time = None
    if stop_after_str:
        h, m = map(int, stop_after_str.split(":"))
        stop_after_time = datetime.time(h, m)
        log_event("deadline_set", stop_after=stop_after_str)

    for wave in range(1, max_waves + 1):
        if stop_after_time and datetime.datetime.now().time() >= stop_after_time:
            stop_reason = f"deadline_{stop_after_str}"
            log_event("deadline_reached", wave=wave, deadline=stop_after_str)
            print(f"  Past {stop_after_str} -- no new waves.", flush=True)
            break

        # Respiration: fine budget gate (per-wave)
        budget = get_respiratory_status()
        log_event("budget_check", wave=wave, status=budget)
        if budget in ("yellow", "red", "unknown"):
            stop_reason = f"budget_{budget}"
            log_event("budget_stop", wave=wave, status=budget)
            if budget == "unknown":
                print(
                    "  Budget unknown (live + cached both failed). Stopping as precaution.",
                    flush=True,
                )
            break

        # Autonomic: disk pressure relief
        if not check_disk_pressure():
            stop_reason = "disk_critical"
            break

        if dry_run:
            log_event("dry_run", wave=wave)
            stop_reason = "dry_run"
            break

        compact_cardiac_log()

        # Run wave with retry
        usage_before = respiration_snapshot()
        success = False
        wave_tail = ""
        for attempt in range(1, retry + 2):
            success, wave_tail = run_wave(wave, model, focus)
            if success:
                consecutive_fails = 0
                resume_breathing()
                break
            if attempt <= retry:
                log_event("retry", wave=wave, attempt=attempt)
                time.sleep(5)

        # Log per-wave usage delta
        wave_delta = 0.0
        usage_after = respiration_snapshot()
        if usage_before and usage_after:
            wave_delta = round(usage_after["weekly"] - usage_before["weekly"], 2)
            log_event(
                "wave_usage",
                wave=wave,
                weekly_before=usage_before["weekly"],
                weekly_after=usage_after["weekly"],
                weekly_delta=wave_delta,
                sonnet_before=usage_before["sonnet"],
                sonnet_after=usage_after["sonnet"],
                sonnet_delta=round(usage_after["sonnet"] - usage_before["sonnet"], 2),
            )

        # Saturation gate
        is_saturated = False
        if success and wave_tail:
            tail_lower = wave_tail.lower()
            matched = [p for p in SATURATION_PHRASES if p in tail_lower]
            if matched:
                is_saturated = True
                consecutive_saturation += 1
                log_event(
                    "saturation_detected",
                    wave=wave,
                    consecutive=consecutive_saturation,
                    phrases=matched,
                    tail=wave_tail[-120:],
                )
                print(
                    f"  ~ Saturation signal ({', '.join(matched)}). "
                    f"Consecutive: {consecutive_saturation}.",
                    flush=True,
                )
                if consecutive_saturation >= 2:
                    stop_reason = f"saturation_{consecutive_saturation}_consecutive_waves"
                    log_event("saturation_stop", wave=wave, consecutive=consecutive_saturation)
                    print(
                        f"  Saturation confirmed over {consecutive_saturation} waves. Stopping.",
                        flush=True,
                    )
                    break
            else:
                consecutive_saturation = 0

        if success:
            daily_count = increment_daily_wave_count(saturated=is_saturated, wave_delta=wave_delta)
            log_event(
                "daily_wave_count",
                wave=wave,
                daily_total=daily_count,
                saturated=is_saturated,
                wave_delta=wave_delta,
            )

        if not success:
            consecutive_fails += 1
            log_file = LOG_DIR / "pulse-waves.log"
            try:
                with open(log_file) as f:
                    f.seek(max(0, os.path.getsize(log_file) - 200))
                    fail_tail = f.read().strip()
            except Exception:
                fail_tail = ""

            is_killed = "KILLED" in fail_tail
            backoff = 120 if is_killed else 30
            log_event(
                "wave_failed_backoff",
                wave=wave,
                consecutive=consecutive_fails,
                backoff_s=backoff,
                killed=is_killed,
                tail=fail_tail[-100:],
            )
            print(
                f"  ! Fail #{consecutive_fails} ({'killed' if is_killed else 'error'}). Backoff {backoff}s.",
                flush=True,
            )
            if consecutive_fails >= 3:
                stop_reason = f"circuit_breaker_{consecutive_fails}_consecutive_fails"
                log_event("circuit_breaker", wave=wave, consecutive=consecutive_fails)
                print(
                    f"  Circuit breaker: {consecutive_fails} consecutive failures. Stopping.",
                    flush=True,
                )
                break
            time.sleep(backoff)
    else:
        stop_reason = f"max_waves_{max_waves}"

    log_event("run_end", waves=wave, reason=stop_reason)
    autophagy(wave, stop_reason)

    if stop_reason.startswith("circuit_breaker"):
        send_distress_signal("Pulse: circuit breaker fired. Check ~/logs/vivesca-events.jsonl")

    post_usage = measure_respiration()
    if post_usage:
        weekly = post_usage.get("seven_day", {}).get("utilization", 0)
        sonnet = post_usage.get("seven_day_sonnet", {}).get("utilization", 0)
        log(f"Final budget: weekly={weekly}%, sonnet={sonnet}%")

    log(f"=== Pulse finished. {wave} waves. Reason: {stop_reason} ===")
