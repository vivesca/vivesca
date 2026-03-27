"""pulse — the organism's heartbeat.

Each systole is a heartbeat: respiration regulates the rate, pulse is the
beat. Runs systoles, manages the cardiac log, detects stalls/churn, handles
autophagy and vital signs reporting.

Safety nets:
1. Vital capacity check (respiration)
2. Per-systole respiratory status check
3. --stop-after circadian deadline (default 07:00 overnight)
4. Max systoles cap (3 overnight, 1 daytime per cycle)
5. Circuit breaker (3 consecutive failures)
6. Systole timeout with stall/churn detection
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

from metabolon.vasomotor import (
    EVENT_LOG,
    MAX_DAILY_SYSTOLES,
    _fetch_telemetry,
    _hours_to_reset,
    adapt,
    assess_vital_capacity,
    breathe,
    emit_distress_signal,
    is_apneic,
    log,
    measure_vasomotor_tone,
    measured_cost_per_systole,
    oxygen_debt,
    record_event,
    resume_breathing,
    set_recovery_interval,
    vasomotor_genome,
    vasomotor_snapshot,
    vasomotor_status,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
CARDIAC_LOG = Path.home() / "tmp" / "pulse-manifest.md"
CARDIAC_LOCK = Path.home() / "tmp" / "pulse.lock"
TOPIC_LOCK = Path.home() / "tmp" / "pulse-topics-done.txt"
LOG_DIR = Path.home() / "logs"
REPORT_DIR = Path.home() / "epigenome" / "chromatin" / "Pulse Reports"
VITAL_SIGNS_FILE = Path.home() / "tmp" / "pulse-status.json"

# ---------------------------------------------------------------------------
# Systole defaults
# ---------------------------------------------------------------------------
CIRCADIAN_DEADLINE = "07:00"
MAX_SYSTOLES = 5  # overnight systoles per cycle
DAYTIME_SYSTOLES = 1  # daytime systoles per cycle

SATURATION_PHRASES = [
    "no new work",
    "diminishing returns",
    "all items covered",
    "nothing remaining",
    "saturated",
    "exhausted",
    "no further",
]

SYSTOLE_PROMPT_TEMPLATE = """One heartbeat. ONE systole per session — the shell loop handles iteration.

You already have ~/CLAUDE.md (How to Think, meta-rules) and MEMORY.md loaded. Use them — especially "Map is dark" and "bet, review, bet". Don't duplicate what's already in your context.

## Steps

1. **Load session state.** Read ~/tmp/pulse-manifest.md (memory of prior systoles), ~/epigenome/chromatin/North Star.md (includes meta goal), ~/epigenome/chromatin/Praxis.md (head 80), ~/epigenome/chromatin/Tonus.md. Run `date`.
2. **Scout.** What do the north stars need? What did prior systoles reveal? Any `agent:claude` items in TODO? Any deadlines within 14 days? Pick the north star with least coverage. Allocate ~{infra_pct}% of agents to the meta goal (system improvement) while the system is young.{focus_line}
3. **Dispatch 15-20 agents** with `run_in_background: true`, `mode: bypassPermissions`. Model routing: research/collection -> sonnet, synthesis/judgment -> opus. Each prompt starts: "Read ~/tmp/pulse-manifest.md. Do not duplicate completed work." When outputs naturally chain (research -> synthesis -> brief), dispatch as a pipeline.
4. **Wait** for all agents. Process results.
5. **Update** ~/tmp/pulse-manifest.md manifest. Route results by ejection gate:
   - **Self-resolving** (research completed, file created, status verified) -> mark done in manifest. Do NOT add to Praxis.
   - **Needs physical action** (go somewhere, call someone, sign something) -> add to Praxis with `agent:terry`.
   - **Needs a decision** (trade-off with no obvious winner) -> add to Praxis with `agent:terry`.
   - **Info-only** (status update, confirmation, FYI) -> manifest only. NOT Praxis.
   Most outputs are self-resolving or info-only. If in doubt, it's NOT an `agent:terry` item. Target: ≤3 new Praxis items per systole.

   **Dispatch gate (mandatory before tagging agent:terry):** Pass ALL three checks or drop the tag:
   (a) Sourced — did Terry or a Terry-approved task explicitly request this? If not and it creates an obligation: SKIP.
   (b) Automated — is this Automated per division-of-labour.md? Presence/Sharpening/Collaborative tasks: SKIP.
   (c) Not phantom — does this require Terry's name/voice/presence for something he never asked about? If yes: SKIP (archive instead).
   Banned phantom patterns: conference abstracts, LinkedIn/bio drafts, self-audits of the system, rescue reports for routing errors, task chains built on unverified premises.
6. **Post to ACTA** for any results that need inter-skill coordination or Terry's attention:
   - `efferens post "Brief: [title] ready at [path]" --from pulse --to terry --severity info`
   - `efferens post "Action needed: [description]" --from pulse --to terry --severity action`
   Use the CLI — it is at vivesca/effectors/efferens. Post sparingly: only actionable items or significant deliverables.
7. **Observe** (append to manifest): which north stars got zero coverage? Any external signals? Any patterns?
8. **Log topics.** Append one line per completed topic to ~/tmp/pulse-topics-done.txt (short key, e.g. "garp-m3-cards", "hsbc-stakeholder-map"). This prevents the next systole from redoing your work.
9. **Exit.** Output summary and stop. Do NOT run another systole.

## Taste rules
- **No duplicates.** Check ~/epigenome/chromatin/ for existing files. Update, don't create "v2."
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


def seed_cardiac_log():
    if not CARDIAC_LOG.exists():
        today = datetime.date.today().isoformat()
        CARDIAC_LOG.write_text(f"# Pulse Manifest -- {today}\n\n## Completed\n\n## In Progress\n")
    # Reset topic lock at start of new run
    if TOPIC_LOCK.exists():
        TOPIC_LOCK.unlink()


def read_topics_done() -> str:
    """Read completed topic keys for dedup injection into systole prompts."""
    if not TOPIC_LOCK.exists():
        return ""
    return TOPIC_LOCK.read_text().strip()


def append_topics_done(topics: str):
    """Append completed topic keys after a systole."""
    with TOPIC_LOCK.open("a") as f:
        f.write(topics.strip() + "\n")


# ---------------------------------------------------------------------------
# Cardiac phases
# ---------------------------------------------------------------------------

PRAXIS_FILE = Path.home() / "epigenome" / "chromatin" / "Praxis.md"
FOCUS_DIRECTIVE_FILE = Path.home() / "tmp" / "pulse-focus-directive.txt"


def atrial_systole() -> dict:
    """Late diastole: active pre-fill before the next systole fires.

    Fetches fresh budget, checks for Praxis changes, identifies the
    least-covered north star, and writes a focus directive file.
    Returns context dict for the systole.
    """
    context: dict = {}

    # Fresh budget
    usage = measure_vasomotor_tone()
    if usage:
        context["weekly"] = usage.get("seven_day", {}).get("utilization", 0)
        context["sonnet"] = usage.get("seven_day_sonnet", {}).get("utilization", 0)

    # Perfusion check: which north stars are ischaemic?
    from metabolon.perfusion import perfusion_report

    perf = perfusion_report()
    context["focus_star"] = perf.get("focus_star")
    context["coverage"] = perf.get("coverage", {})
    context["ischaemic"] = perf.get("ischaemic", [])

    # Praxis deadline scan (next 7 days)
    urgent_items: list[str] = []
    if PRAXIS_FILE.exists():
        today = datetime.date.today()
        for line in PRAXIS_FILE.read_text().splitlines()[:80]:
            # Look for date patterns in TODO-style lines
            for fmt in ("%Y-%m-%d", "%b %d", "%d %b"):
                try:
                    if fmt == "%Y-%m-%d":
                        import re

                        match = re.search(r"\d{4}-\d{2}-\d{2}", line)
                        if match:
                            d = datetime.datetime.strptime(match.group(), fmt).date()
                            if 0 <= (d - today).days <= 7:
                                urgent_items.append(line.strip())
                except (ValueError, AttributeError):
                    pass
    context["urgent"] = urgent_items[:10]

    # Write focus directive for isovolumic contraction to consume
    directive_parts = []
    if context.get("focus_star"):
        directive_parts.append(f"FOCUS: {context['focus_star']} (least coverage)")
    if urgent_items:
        directive_parts.append(f"URGENT ({len(urgent_items)}): {'; '.join(urgent_items[:3])}")
    done = read_topics_done()
    if done:
        directive_parts.append(f"DONE: {done}")

    FOCUS_DIRECTIVE_FILE.write_text("\n".join(directive_parts) if directive_parts else "")
    record_event("atrial_systole", focus=context.get("focus_star"), urgent=len(urgent_items))

    return context


def isovolumic_contraction(genome: dict, focus: str | None, context: dict) -> str:
    """Build systole prompt with deterministic pre-planning injected.

    Reads focus directive, topic lockfile, and coverage data to produce
    a more targeted prompt than the LLM would build from raw file reads.
    """
    prompt = _build_systole_prompt(genome, focus)

    # Inject focus directive from atrial systole
    directive = ""
    if FOCUS_DIRECTIVE_FILE.exists():
        directive = FOCUS_DIRECTIVE_FILE.read_text().strip()

    injections = []

    if directive:
        injections.append(f"## PRE-COMPUTED DIRECTIVES\n{directive}")

    # Coverage map so the LLM doesn't need to compute it
    coverage = context.get("coverage")
    if coverage:
        lines = [
            f"- {star}: {count} mentions"
            for star, count in sorted(coverage.items(), key=lambda x: x[1])
        ]
        injections.append("## NORTH STAR COVERAGE (this run)\n" + "\n".join(lines))

    # Completed topics (dedup)
    done = read_topics_done()
    if done:
        injections.append(
            f"## COMPLETED TOPICS (DO NOT REDO)\n{done}\nSkip these entirely. Work on NEW topics only."
        )

    if injections:
        prompt += "\n\n" + "\n\n".join(injections)

    return prompt


def diastole(systole_num: int):
    """Active recovery between systoles: compact, extract, prepare.

    Unlike passive set_recovery_interval(), diastole does filling work:
    1. Compact cardiac log
    2. Extract topic keys from manifest to lockfile
    3. Log the diastole event
    """
    # 1. Compact
    compact_cardiac_log()

    # 2. Extract completed topics from manifest
    if CARDIAC_LOG.exists():
        manifest = CARDIAC_LOG.read_text()
        # Extract [x] items as topic keys
        new_topics = []
        for line in manifest.splitlines():
            if "[x]" in line.lower():
                # Strip markdown, extract a short key
                key = line.split("**")
                if len(key) >= 2:
                    topic = key[1].strip().lower()
                    # Slugify
                    topic = topic.replace(" ", "-").replace(".", "")[:60]
                    new_topics.append(topic)
        if new_topics:
            append_topics_done("\n".join(new_topics))
            record_event("diastole_topics_extracted", count=len(new_topics), systole=systole_num)

    # 3. Auto-convert confirmation items (raise ejection fraction)
    from metabolon.respiration import auto_convert, phantom_sweep

    result = auto_convert()
    if result["converted"] > 0:
        record_event("diastole_auto_convert", count=result["converted"], systole=systole_num)

    # 4. Phantom obligation sweep — flag invented agent:terry items
    phantom_result = phantom_sweep()
    if phantom_result["phantom_count"] > 0:
        record_event(
            "diastole_phantoms_detected",
            count=phantom_result["phantom_count"],
            systole=systole_num,
        )
        log(
            f"Diastole: {phantom_result['phantom_count']} phantom agent:terry "
            "item(s) detected in Praxis — systole should have filtered these"
        )

    # 4. Log
    record_event("diastole", systole=systole_num)


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
    record_event("manifest_compacted", from_lines=len(lines), to_lines=len(compacted))


# ---------------------------------------------------------------------------
# Autonomic disk pressure relief
# ---------------------------------------------------------------------------

DISK_FLOOR_GB = 5  # below this, refuse to start a systole (ENOSPC risk)
DISK_CLEAN_GB = 15  # below this, run lysosome before systole


def sense_disk_pressure() -> bool:
    """Sense disk pressure, auto-clean if needed. Returns True if safe to proceed."""
    try:
        free_gb = shutil.disk_usage("/").free / (1024**3)
    except Exception:
        return True  # can't measure → don't block

    if free_gb >= DISK_CLEAN_GB:
        return True

    log(f"Disk pressure: {free_gb:.1f}GB free (threshold {DISK_CLEAN_GB}GB). Running lysosome.")
    record_event("disk_pressure", free_gb=round(free_gb, 1), action="lysosome")

    try:
        from metabolon.enzymes.interoception import lysosome_digest

        result = lysosome_digest()
        log(f"Lysosome: freed {result.freed_gb}GB ({result.before_gb}→{result.after_gb}GB)")
        record_event(
            "disk_lysosome_complete",
            before_gb=result.before_gb,
            after_gb=result.after_gb,
            freed_gb=result.freed_gb,
        )
        free_gb = result.after_gb
    except Exception as e:
        log(f"Lysosome failed: {e}")
        record_event("disk_lysosome_failed", error=str(e))

    if free_gb < DISK_FLOOR_GB:
        log(f"Disk critically low ({free_gb:.1f}GB < {DISK_FLOOR_GB}GB). Refusing systole.")
        record_event("disk_critical", free_gb=round(free_gb, 1))
        return False

    return True


# ---------------------------------------------------------------------------
# Systole execution
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


def _build_systole_prompt(genome: dict, focus: str | None = None) -> str:
    """Build systole prompt from template + conf-driven parameters."""
    infra_pct = genome.get("infra_pct", 30)
    focus_star = focus or genome.get("focus_star")
    focus_line = ""
    if focus_star:
        focus_line = f"\n   **FOCUS:** Prioritize '{focus_star}' this systole. Other stars get remaining capacity."
    prompt = SYSTOLE_PROMPT_TEMPLATE.format(infra_pct=infra_pct, focus_line=focus_line)
    if focus and not focus_star:
        prompt += f"\n\n## FOCUS RESTRICTION\nThis loop instance ONLY works on: {focus}. Ignore all other north stars. Another loop handles the rest."
    return prompt


def fire_systole(
    systole_num: int, model: str, focus: str | None = None, prompt: str | None = None
) -> tuple[bool, str]:
    """Run a single systole (one heartbeat). Returns (success, output_tail).

    If prompt is provided (from isovolumic_contraction), uses it directly.
    Otherwise falls back to building its own prompt.
    """
    log_file = LOG_DIR / "pulse-systoles.log"

    if prompt is None:
        genome = vasomotor_genome()
        prompt = _build_systole_prompt(genome, focus)

    cmd = [
        "channel",
        model,
        "-p",
        "--dangerously-skip-permissions",
        "--no-session-persistence",
        prompt,
    ]

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = f"\n{'=' * 60}\n=== Systole {systole_num} -- {timestamp} ===\n{'=' * 60}\n"

    record_event("systole_start", systole=systole_num, model=model)
    start = time.time()

    with open(log_file, "a") as lf:
        lf.write(header)

    genome = vasomotor_genome()
    max_systole_seconds = genome.get("max_systole_seconds", 1800)
    stall_seconds = genome.get("stall_seconds", 300)

    def record_status(**kwargs):
        """Write current systole vitals for external observers."""
        VITAL_SIGNS_FILE.write_text(
            json.dumps(
                {
                    "systole": systole_num,
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
                record_event(
                    "systole_yield",
                    systole=systole_num,
                    secretion_count=recent_count,
                )
                record_event(
                    "systole_end",
                    systole=systole_num,
                    exit_code=ret,
                    elapsed_s=elapsed,
                    output_tail=tail,
                )
                record_status(state="completed", elapsed_s=elapsed)
                return ret == 0, tail

            current_log_size = os.path.getsize(log_file)
            if current_log_size > last_log_size:
                last_log_size = current_log_size
                last_growth_time = time.time()

            stall_duration = round(time.time() - last_growth_time)

            if stall_duration > stall_seconds:
                if not stall_warned:
                    record_event(
                        "systole_stall_warning",
                        systole=systole_num,
                        elapsed_s=elapsed_so_far,
                        stall_s=stall_duration,
                    )
                    stall_warned = True
            else:
                if stall_warned:
                    record_event(
                        "systole_stall_resolved",
                        systole=systole_num,
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
                    record_event(
                        "systole_churn_warning",
                        systole=systole_num,
                        elapsed_s=elapsed_so_far,
                        churn_s=churn_duration,
                    )
                    churn_warned = True
                # Reduced ejection: if churning 2x the threshold, soft-stop
                if churn_duration > churn_seconds * 2:
                    proc.terminate()
                    proc.wait(timeout=30)
                    log_fh.write(
                        f"\n--- REDUCED EJECTION after {elapsed_so_far}s (churn {churn_duration}s) ---\n"
                    )
                    record_event(
                        "reduced_ejection",
                        systole=systole_num,
                        elapsed_s=elapsed_so_far,
                        churn_s=churn_duration,
                    )
                    print(
                        f"  ~ Reduced ejection: systole {systole_num} soft-stopped at {elapsed_so_far}s (no output for {churn_duration}s)",
                        flush=True,
                    )
                    return True, ""
            else:
                if churn_warned:
                    record_event(
                        "systole_churn_resolved",
                        systole=systole_num,
                        elapsed_s=elapsed_so_far,
                        churn_s=churn_duration,
                    )
                churn_warned = False

            if elapsed_so_far > max_systole_seconds:
                proc.kill()
                proc.wait()
                log_fh.write(f"\n--- KILLED after {elapsed_so_far}s ---\n")
                record_event(
                    "systole_killed",
                    systole=systole_num,
                    elapsed_s=elapsed_so_far,
                    reason="timeout",
                )
                print(f"  ! Killed systole {systole_num} at {elapsed_so_far}s", flush=True)
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
            record_status(
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
        record_event("systole_error", systole=systole_num, error=str(e), elapsed_s=elapsed)
        return False, ""
    finally:
        log_fh.close()


# ---------------------------------------------------------------------------
# Autophagy (cellular self-recycling)
# ---------------------------------------------------------------------------


def record_vital_signs(total_systoles: int, stop_reason: str):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
    report_path = REPORT_DIR / f"{ts}-pulse.md"

    manifest_content = CARDIAC_LOG.read_text() if CARDIAC_LOG.exists() else "(no manifest)"

    report_path.write_text(f"""---
title: "Pulse Report -- {ts}"
date: {datetime.date.today().isoformat()}
tags: [pulse, report]
systoles: {total_systoles}
stop_reason: {stop_reason}
---

# Pulse Report -- {ts}

## Summary
- Systoles completed: {total_systoles}
- Stop reason: {stop_reason}

## Manifest (final state)
{manifest_content}
""")
    print(f"Report written to {report_path}")


def cross_model_review(manifest_path: Path):
    """Run cross-model quality check in background."""
    try:
        subprocess.Popen(
            ["pulse-review", str(manifest_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        record_event("cross_model_review", manifest=str(manifest_path))
        print(f"Cross-model review dispatched for {manifest_path.name}")
    except FileNotFoundError:
        print("pulse-review not found -- skipping cross-model review")


def post_efferens_summary(total_systoles: int, stop_reason: str):
    """Post a summary to efferens board so Terry sees results in his inbox."""
    try:
        import acta

        acta.post(
            f"Pulse completed {total_systoles} systole(s). Stop reason: {stop_reason}. "
            f"Check ~/epigenome/chromatin/Pulse Reports/ for details.",
            sender="pulse",
            to="terry",
            severity="info",
            subject=f"pulse-{total_systoles}w-{stop_reason}",
        )
    except Exception as e:
        log(f"ACTA post failed: {e}")


def _auto_commit_germline():
    """Commit any dirty pulse output so germline stays clean between sessions."""
    germline = Path.home() / "germline"
    try:
        status = subprocess.run(
            ["git", "status", "--porcelain", "loci/pulse/"],
            capture_output=True,
            text=True,
            cwd=germline,
            timeout=10,
        )
        if not status.stdout.strip():
            return
        subprocess.run(
            ["git", "add", "loci/pulse/"],
            cwd=germline,
            capture_output=True,
            timeout=10,
        )
        subprocess.run(
            [
                "git",
                "commit",
                "-m",
                f"pulse: auto-commit {datetime.datetime.now():%Y-%m-%d %H:%M}",
            ],
            cwd=germline,
            capture_output=True,
            timeout=10,
        )
        log("Auto-committed pulse output to germline")
    except Exception as e:
        log(f"Auto-commit failed: {e}")


def autophagy(systoles: int, stop_reason: str):
    """Autophagy — recycle the cardiac cycle: write vital signs, archive log, review."""
    record_vital_signs(systoles, stop_reason)
    post_efferens_summary(systoles, stop_reason)
    if CARDIAC_LOG.exists():
        ts = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
        archive = CARDIAC_LOG.with_name(f"pulse-{ts}.md")
        CARDIAC_LOG.rename(archive)
        print(f"Manifest archived to {archive.name}")
        cross_model_review(archive)
    _auto_commit_germline()


# ---------------------------------------------------------------------------
# Event log rotation
# ---------------------------------------------------------------------------


def cycle_event_log():
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


def _check_entrainment() -> tuple[bool, str]:
    """Check circadian entrainment recommendations before firing a pulse cycle.

    Returns (suppress, reason). Fast path: <1s. Never raises — if entrainment
    is unavailable, returns (False, "entrainment_unavailable") so pulse proceeds.
    """
    try:
        from metabolon.organelles import entrainment as _ent
        from metabolon.vasomotor import SKIP_UNTIL_FILE

        signals = _ent.zeitgebers()
        sched = _ent.optimal_schedule(signals)
        pulse_rec = sched.get("recommendations", {}).get("pulse", {})
        action = pulse_rec.get("action", "normal")
        reason = pulse_rec.get("reason", "nominal")

        record_event(
            "entrainment_check",
            action=action,
            reason=reason,
            hkt_hour=signals.get("hkt_hour"),
            budget_status=signals.get("budget_status"),
            readiness=signals.get("readiness"),
        )

        if action == "suppress":
            # Write skip-until so is_apneic() gates the next invocation too.
            # Duration: night → skip to 06:00; budget_red → 1-hour recheck.
            import datetime as _dt

            HKT = _dt.timezone(_dt.timedelta(hours=8))
            now = _dt.datetime.now(tz=HKT)
            if reason == "night_hours":
                # Skip until 06:00 HKT today (or tomorrow if already past 06:00)
                wake = now.replace(hour=6, minute=0, second=0, microsecond=0)
                if wake <= now:
                    wake += _dt.timedelta(days=1)
            else:
                # Budget red or other: recheck in 1 hour
                wake = now + _dt.timedelta(hours=1)
            SKIP_UNTIL_FILE.parent.mkdir(parents=True, exist_ok=True)
            SKIP_UNTIL_FILE.write_text(wake.isoformat())
            log(f"Entrainment: suppress ({reason}). Skip until {wake.strftime('%H:%M HKT')}.")
            return True, f"entrainment_suppress_{reason}"

        if action == "accelerate":
            log(f"Entrainment: accelerate signal ({reason}) — proceeding normally.")

        return False, action

    except Exception as e:
        record_event("entrainment_check_failed", error=str(e))
        return False, "entrainment_unavailable"


def main(systoles=None, model=None, retry=1, focus=None, stop_after=None, dry_run=False):
    """Main pulse loop."""
    log("=== Pulse starting ===")

    # Respiration: skip-until check (avoids respirometry call when pacing already blocked)
    skip, skip_reason = is_apneic()
    if skip:
        log(f"Skipping: {skip_reason}")
        return

    # Circadian entrainment: check schedule recommendations before firing
    suppress, ent_reason = _check_entrainment()
    if suppress:
        log(f"Entrainment suppressed pulse: {ent_reason}")
        return

    acquire_cardiac_lock()
    cycle_event_log()

    # Read model from conf if not explicitly passed
    genome = vasomotor_genome()
    if model is None:
        conf_model = genome.get("systole_model", "sonnet")
        # Consult tissue routing as an advisory override (advisory — falls back to conf on failure).
        try:
            import sys as _sys

            _germline = str(Path.home() / "germline")
            if _germline not in _sys.path:
                _sys.path.insert(0, _germline)
            from metabolon.organelles.tissue_routing import route as _tr_route

            routed_model = _tr_route("poiesis_dispatch")
            if routed_model != conf_model:
                log(f"tissue routing: poiesis_dispatch -> {routed_model} (conf had {conf_model})")
            model = routed_model
        except Exception:
            model = conf_model

    # Respiration: budget headroom (coarse gate)
    has_headroom, reason = assess_vital_capacity()
    if not has_headroom:
        log(f"No headroom: {reason}. Exiting.")
        return
    log(f"Headroom confirmed: {reason}")

    hour = datetime.datetime.now().hour
    is_overnight = hour >= 22 or hour < 7

    # Adaptive cadence: budget-driven systole count
    if systoles is not None:
        max_systoles = systoles
    else:
        telemetry = _fetch_telemetry()
        hours = _hours_to_reset(telemetry)
        debt = oxygen_debt(hours) if hours is not None else 0.0
        weekly_util = (telemetry or {}).get("seven_day", {}).get("utilization", 50)
        remaining_pct = max(0, 100 - weekly_util - 5)  # 5% sympathetic floor
        cost = measured_cost_per_systole()
        budget_systoles = max(1, int(remaining_pct / cost)) if cost > 0 else DAYTIME_SYSTOLES
        if is_overnight:
            max_systoles = min(budget_systoles, MAX_DAILY_SYSTOLES)
        else:
            # Scale by debt: low debt = conservative, high debt = burn what's left
            scaled = max(
                DAYTIME_SYSTOLES,
                round(DAYTIME_SYSTOLES + debt * (budget_systoles - DAYTIME_SYSTOLES)),
            )
            max_systoles = min(scaled, MAX_SYSTOLES, MAX_DAILY_SYSTOLES)
        if debt > 0 or budget_systoles != DAYTIME_SYSTOLES:
            record_event(
                "adaptive_cadence",
                debt=round(debt, 2),
                max_systoles=max_systoles,
                budget_systoles=budget_systoles,
                remaining_pct=round(remaining_pct, 1),
            )
    stop_after_str = stop_after or (CIRCADIAN_DEADLINE if is_overnight else None)

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    seed_cardiac_log()

    record_event("run_start", max_systoles=max_systoles, model=model, overnight=is_overnight)

    stop_reason = "completed"
    systole_num = 0
    consecutive_fails = 0
    consecutive_saturation = 0
    total_saturated = 0
    total_failed = 0

    def sigint_handler(sig, frame):
        nonlocal stop_reason, systole_num
        record_event("interrupted", systole=systole_num)
        stop_reason = "interrupted"
        autophagy(systole_num, stop_reason)
        sys.exit(0)

    signal.signal(signal.SIGINT, sigint_handler)

    stop_after_time = None
    if stop_after_str:
        h, m = map(int, stop_after_str.split(":"))
        stop_after_time = datetime.time(h, m)
        record_event("deadline_set", stop_after=stop_after_str)

    for systole_num in range(1, max_systoles + 1):
        if stop_after_time and datetime.datetime.now().time() >= stop_after_time:
            stop_reason = f"deadline_{stop_after_str}"
            record_event("deadline_reached", systole=systole_num, deadline=stop_after_str)
            print(f"  Past {stop_after_str} -- no new systoles.", flush=True)
            break

        # Respiration: fine budget gate (per-systole)
        budget = vasomotor_status()
        record_event("budget_check", systole=systole_num, status=budget)
        if budget in ("yellow", "red", "unknown"):
            stop_reason = f"budget_{budget}"
            record_event("budget_stop", systole=systole_num, status=budget)
            if budget == "unknown":
                print(
                    "  Budget unknown (live + cached both failed). Stopping as precaution.",
                    flush=True,
                )
            break

        # Autonomic: disk pressure relief
        if not sense_disk_pressure():
            stop_reason = "disk_critical"
            break

        if dry_run:
            record_event("dry_run", systole=systole_num)
            stop_reason = "dry_run"
            break

        # Atrial systole: active pre-fill (late diastole)
        prefill_context = atrial_systole()

        # Isovolumic contraction: deterministic dispatch planning
        genome = vasomotor_genome()
        systole_prompt = isovolumic_contraction(genome, focus, prefill_context)

        # Ejection: run systole with retry
        usage_before = vasomotor_snapshot()
        success = False
        systole_tail = ""
        for attempt in range(1, retry + 2):
            success, systole_tail = fire_systole(systole_num, model, focus, prompt=systole_prompt)
            if success:
                consecutive_fails = 0
                resume_breathing()
                break
            if attempt <= retry:
                record_event("retry", systole=systole_num, attempt=attempt)
                time.sleep(5)

        # Log per-systole usage delta
        systole_delta = 0.0
        usage_after = vasomotor_snapshot()
        if usage_before and usage_after:
            systole_delta = round(usage_after["weekly"] - usage_before["weekly"], 2)
            record_event(
                "systole_usage",
                systole=systole_num,
                weekly_before=usage_before["weekly"],
                weekly_after=usage_after["weekly"],
                weekly_delta=systole_delta,
                sonnet_before=usage_before["sonnet"],
                sonnet_after=usage_after["sonnet"],
                sonnet_delta=round(usage_after["sonnet"] - usage_before["sonnet"], 2),
            )

        # Saturation gate
        is_saturated = False
        if success and systole_tail:
            tail_lower = systole_tail.lower()
            matched = [p for p in SATURATION_PHRASES if p in tail_lower]
            if matched:
                is_saturated = True
                consecutive_saturation += 1
                total_saturated += 1
                record_event(
                    "saturation_detected",
                    systole=systole_num,
                    consecutive=consecutive_saturation,
                    phrases=matched,
                    tail=systole_tail[-120:],
                )
                print(
                    f"  ~ Saturation signal ({', '.join(matched)}). "
                    f"Consecutive: {consecutive_saturation}.",
                    flush=True,
                )
                patience = vasomotor_genome().get("saturation_patience", 2)
                if consecutive_saturation >= patience:
                    # Parasympathetic response: idle, don't die.
                    # Set max recovery interval so the organism rests but
                    # the pacemaker keeps ticking on the LaunchAgent schedule.
                    from metabolon.vasomotor import SKIP_UNTIL_FILE

                    idle_until = datetime.datetime.now() + datetime.timedelta(hours=3)
                    SKIP_UNTIL_FILE.write_text(idle_until.isoformat())
                    stop_reason = f"saturation_idle_{consecutive_saturation}_systoles"
                    record_event(
                        "saturation_idle",
                        systole=systole_num,
                        consecutive=consecutive_saturation,
                        idle_until=idle_until.isoformat(),
                    )
                    print(
                        f"  Saturation confirmed. Idling until {idle_until.strftime('%H:%M')}.",
                        flush=True,
                    )
                    break
            else:
                consecutive_saturation = 0

        if success:
            daily_count = breathe(saturated=is_saturated, systole_delta=systole_delta)
            record_event(
                "daily_systole_count",
                systole=systole_num,
                daily_total=daily_count,
                saturated=is_saturated,
                systole_delta=systole_delta,
            )
            # Diastole: active recovery — compact, extract topics, prepare
            diastole(systole_num)

        if not success:
            consecutive_fails += 1
            total_failed += 1
            log_file = LOG_DIR / "pulse-systoles.log"
            try:
                with open(log_file) as f:
                    f.seek(max(0, os.path.getsize(log_file) - 200))
                    fail_tail = f.read().strip()
            except Exception:
                fail_tail = ""

            is_killed = "KILLED" in fail_tail
            backoff = 120 if is_killed else 30
            record_event(
                "systole_failed_backoff",
                systole=systole_num,
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
                record_event("circuit_breaker", systole=systole_num, consecutive=consecutive_fails)
                print(
                    f"  Circuit breaker: {consecutive_fails} consecutive failures. Stopping.",
                    flush=True,
                )
                break
            time.sleep(backoff)
    else:
        stop_reason = f"max_systoles_{max_systoles}"

    record_event("run_end", systoles=systole_num, reason=stop_reason)
    autophagy(systole_num, stop_reason)

    if stop_reason.startswith("circuit_breaker"):
        emit_distress_signal("Pulse: circuit breaker fired. Check ~/logs/vivesca-events.jsonl")

    post_usage = measure_vasomotor_tone()
    if post_usage:
        weekly = post_usage.get("seven_day", {}).get("utilization", 0)
        sonnet = post_usage.get("seven_day_sonnet", {}).get("utilization", 0)
        log(f"Final budget: weekly={weekly}%, sonnet={sonnet}%")

    # LLM adaptation: review outcomes and adjust parameters for next cycle
    adapt(
        systoles_run=systole_num,
        saturated=total_saturated,
        failed=total_failed,
        stop_reason=stop_reason,
    )

    # Set adaptive recovery: short interval under debt, long when relaxed
    set_recovery_interval()

    log(f"=== Pulse finished. {systole_num} systoles. Reason: {stop_reason} ===")
