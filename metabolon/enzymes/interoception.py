from metabolon.locus import chromatin, experiments as EXPERIMENTS_DIR, praxis

"""interoception — sensing internal state (health, system, financial).

Tools:
  circadian_sleep      — circadian rhythm data from Oura
  membrane_potential   — readiness score + exercise recommendation
  homeostasis_system   — pulse status, budget, disk pressure, hook health
  homeostasis_financial — financial health: deadlines, overdue items
  lysosome_digest      — digest disk caches when pressure is high
  nociception_log      — log a pain/symptom signal
  anabolism_flywheel   — anabolic flywheel: are the links reinforcing?
  angiogenesis         — detect underserved subsystem connections, propose integrations
  mitophagy_status     — model performance tracking and fitness scores
  glycolysis_rate      — symbiont dependency ratio: % of organism that is deterministic
  tissue_routing       — model routing by task type: which symbiont strain for which subsystem
  retrograde_balance   — symbiont influence ratio: is the organism sovereign or dependent?
  crispr_status        — adaptive memory: spacer count, recent acquisitions, guide coverage
"""

import contextlib
import datetime
import json
import os
import re
import shutil
import subprocess

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.cytosol import synthesize
from metabolon.metabolism.mismatch_repair import summary as precision_summary
from metabolon.metabolism.setpoint import Threshold
from metabolon.morphology import EffectorResult, Secretion

HEALTH_LOG = str(chromatin / "Health" / "Symptom Log.md")

disk_threshold = Threshold(name="disk", default=15, clamp=(5, 50))


class CircadianResult(Secretion):
    """Circadian rhythm data from Oura."""

    summary: str


class HeartRateResult(Secretion):
    """Heart rate time-series from Oura."""

    summary: str


class MembranePotentialResult(Secretion):
    """Membrane potential — readiness with exercise guidance."""

    summary: str
    guidance: str


class HomeostasisResult(Secretion):
    """Homeostatic system check results."""

    sections: list[str]


class InflammasomeResult(Secretion):
    """Self-test probe results."""

    report: str
    passed: int
    total: int


@tool(
    name="inflammasome_probe",
    description="Self-test: verify all subsystems work end-to-end.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def inflammasome_probe() -> InflammasomeResult:
    """Run innate immune probes on all organism subsystems."""
    from metabolon.organelles.inflammasome import run_all_probes

    results = run_all_probes()
    lines = []
    for r in results:
        tag = "PASS" if r["passed"] else "FAIL"
        lines.append(f"[{tag}] {r['name']} — {r['message']} ({r['duration_ms']}ms)")
    passed_count = sum(1 for r in results if r["passed"])
    total = len(results)
    lines.append(f"\nSummary: {passed_count}/{total} passed")
    return InflammasomeResult(report="\n".join(lines), passed=passed_count, total=total)


@tool(
    name="circadian_sleep",
    description="Oura sleep data. 'today' for last night, 'week' for trend.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def circadian_sleep(period: str = "today") -> CircadianResult:
    """Read circadian rhythm data with chemoreceptor-style threshold alerts."""
    from metabolon.organelles.chemoreceptor import sense, week

    if period == "week":
        return CircadianResult(summary=str(week()))

    data = sense()
    if "error" in data:
        return CircadianResult(summary=f"Error: {data['error']}")

    def _fmt_dur(secs):
        if secs is None:
            return "n/a"
        h, m = divmod(int(secs) // 60, 60)
        return f"{h}h{m:02d}m" if h else f"{m}m"

    lines: list[str] = []

    # --- Alerts ---
    alerts = []
    ss, rs = data.get("sleep_score"), data.get("readiness_score")
    av_hrv = data.get("average_hrv")
    if ss is not None and ss < 70:
        alerts.append(f"SLEEP LOW ({ss}): below 70 threshold")
    if rs is not None and rs < 70:
        alerts.append(f"READINESS LOW ({rs}): light activity only")
    if av_hrv is not None and av_hrv < 20:
        alerts.append(f"HRV LOW ({av_hrv}): recovery priority")
    if alerts:
        lines.append("--- Alerts ---")
        lines.extend(alerts)
        lines.append("")

    # --- Scores ---
    lines.append("--- Scores ---")
    lines.append(f"Sleep: {ss}  Readiness: {rs}")
    lines.append(f"Sleep contributors: {data.get('sleep_contributors', {})}")
    lines.append(f"Readiness contributors: {data.get('contributors', {})}")
    lines.append(
        f"Temp deviation: {data.get('temperature_deviation')}°C  "
        f"Trend: {data.get('temperature_trend_deviation')}°C"
    )
    lines.append("")

    # --- Sleep detail ---
    lines.append("--- Sleep detail ---")
    lines.append(
        f"Deep:  {_fmt_dur(data.get('deep_sleep_duration'))}  "
        f"Light: {_fmt_dur(data.get('light_sleep_duration'))}  "
        f"REM:   {_fmt_dur(data.get('rem_sleep_duration'))}"
    )
    lines.append(
        f"Awake: {_fmt_dur(data.get('awake_time'))}  "
        f"Total: {_fmt_dur(data.get('total_sleep_duration'))}  "
        f"In bed: {_fmt_dur(data.get('time_in_bed'))}"
    )
    if data.get("bedtime_start") and data.get("bedtime_end"):
        lines.append(f"Bed:   {data['bedtime_start'][:16]} → {data['bedtime_end'][:16]}")
    lines.append(
        f"Latency: {_fmt_dur(data.get('latency'))}  "
        f"Efficiency: {data.get('efficiency')}%  "
        f"Restless periods: {data.get('restless_periods')}"
    )
    lines.append(
        f"Avg HR: {data.get('average_heart_rate')} bpm  "
        f"Lowest HR: {data.get('lowest_heart_rate')} bpm  "
        f"Avg HRV: {data.get('average_hrv')} ms"
    )
    lines.append(f"Avg breath: {data.get('average_breath')} br/s  Type: {data.get('type')}")
    lines.append("")

    # --- Hypnogram ---
    hyp = data.get("sleep_phase_5_min")
    if hyp:
        legend = {"1": "█", "2": "▓", "3": "░", "4": " "}
        bar = "".join(legend.get(c, "?") for c in hyp)
        lines.append("--- Hypnogram (5-min) ---")
        lines.append("█=deep ▓=light ░=REM (space)=awake")
        lines.append(bar)
        lines.append("")

    # --- Movement (30-sec) ---
    mov = data.get("movement_30_sec")
    if mov:
        legend_m = {"1": "·", "2": "~", "3": "≈", "4": "▲"}
        bar_m = "".join(legend_m.get(c, "?") for c in mov)
        lines.append("--- Movement (30-sec) ---")
        lines.append("·=still ~=restless ≈=tossing ▲=active")
        lines.append(bar_m)
        lines.append("")

    # --- Activity ---
    act = data.get("activity")
    if act:
        lines.append("--- Activity (yesterday) ---")
        lines.append(
            f"Score: {act.get('score')}  Steps: {act.get('steps')}  "
            f"Calories: {act.get('active_calories')} active / {act.get('total_calories')} total"
        )
        lines.append(
            f"High: {_fmt_dur(act.get('high_activity_time'))}  "
            f"Med: {_fmt_dur(act.get('medium_activity_time'))}  "
            f"Low: {_fmt_dur(act.get('low_activity_time'))}  "
            f"Sedentary: {_fmt_dur(act.get('sedentary_time'))}"
        )
        lines.append(f"Walking equiv: {act.get('equivalent_walking_distance')}m")
        lines.append("")

    # --- Stress ---
    st = data.get("stress")
    if st:
        lines.append("--- Stress ---")
        lines.append(
            f"Summary: {st.get('day_summary')}  "
            f"Stress high: {_fmt_dur(st.get('stress_high'))}  "
            f"Recovery high: {_fmt_dur(st.get('recovery_high'))}"
        )
        lines.append("")

    # --- SpO2 ---
    sp = data.get("spo2")
    if sp:
        lines.append("--- SpO2 ---")
        lines.append(
            f"Average: {sp.get('average')}%  "
            f"Breathing disturbance index: {sp.get('breathing_disturbance_index')}"
        )
        lines.append("")

    # --- Resilience ---
    res = data.get("resilience")
    if res:
        lines.append("--- Resilience ---")
        lines.append(f"Level: {res.get('level')}  Contributors: {res.get('contributors', {})}")
        lines.append("")

    # --- Sleep time recommendation ---
    stm = data.get("sleep_time")
    if stm:
        lines.append("--- Bedtime recommendation ---")
        lines.append(f"Recommendation: {stm.get('recommendation')}  Status: {stm.get('status')}")
        opt = stm.get("optimal_bedtime") or {}
        if opt:
            lines.append(f"Optimal window: {opt}")
        lines.append("")

    # --- Cardiovascular / VO2 ---
    va, vo = data.get("vascular_age"), data.get("vo2_max")
    if va is not None or vo is not None:
        lines.append("--- Cardiovascular ---")
        parts = []
        if va is not None:
            parts.append(f"Vascular age: {va}")
        if vo is not None:
            parts.append(f"VO2 max: {vo}")
        lines.append("  ".join(parts))
        lines.append("")

    # --- Workouts ---
    wk = data.get("workouts")
    if wk:
        lines.append("--- Workouts ---")
        for w in wk:
            start = (w.get("start") or "")[:16]
            cal = w.get("calories")
            lines.append(
                f"{w.get('activity')} ({w.get('intensity')}) "
                f"{start}  {f'{cal:.0f} kcal' if cal else ''} "
                f"[{w.get('source')}]"
            )
        lines.append("")

    # --- Active Experiments ---
    try:
        exp_lines: list[str] = []
        today = datetime.date.today()
        for exp_file in sorted(EXPERIMENTS_DIR.glob("assay-*.md")):
            text = exp_file.read_text()
            # Extract front matter
            fm_match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
            if not fm_match:
                continue
            fm = fm_match.group(1)
            status_m = re.search(r"^status:\s*(\S+)", fm, re.MULTILINE)
            if not status_m or status_m.group(1).strip('"') != "active":
                continue
            name_m = re.search(r'^name:\s*"?([^"\n]+)"?', fm, re.MULTILINE)
            start_m = re.search(r"^start_date:\s*(\S+)", fm, re.MULTILINE)
            hyp_m = re.search(r"^hypothesis:\s*\"?([^\"\n]+)\"?", fm, re.MULTILINE)
            name = name_m.group(1).strip() if name_m else exp_file.stem
            hypothesis = hyp_m.group(1).strip() if hyp_m else ""
            day_num = ""
            if start_m:
                try:
                    start_date = datetime.date.fromisoformat(start_m.group(1))
                    day_num = (today - start_date).days + 1
                except ValueError:
                    pass
            # Duration from end_date
            end_m = re.search(r"^end_date:\s*(\S+)", fm, re.MULTILINE)
            total_days = ""
            if end_m and start_m:
                try:
                    end_date = datetime.date.fromisoformat(end_m.group(1))
                    total_days = (end_date - start_date).days + 1
                except ValueError:
                    pass
            # Most recent check-in: last ### Day N line + following metrics
            checkin_blocks = re.findall(
                r"(### Day \d+[^\n]*\n(?:[^\n#][^\n]*\n)*)", text
            )
            checkin_summary = ""
            if checkin_blocks:
                last = checkin_blocks[-1]
                readiness_m = re.search(r"Readiness:\s*avg\s*([\d.]+)", last)
                sleep_m = re.search(r"Sleep:\s*avg\s*([\d.]+)", last)
                parts = []
                if sleep_m:
                    parts.append(f"sleep {sleep_m.group(1)}")
                if readiness_m:
                    parts.append(f"readiness {readiness_m.group(1)}")
                if parts:
                    checkin_summary = f" Last check-in: {', '.join(parts)}."
            # Baseline readiness
            baseline_m = re.search(r"Readiness:\s*avg\s*([\d.]+)", text)
            baseline_val = baseline_m.group(1) if baseline_m else None
            day_label = f"Day {day_num} of {total_days}" if day_num and total_days else (f"Day {day_num}" if day_num else "")
            label = f"{name} ({day_label})" if day_label else name
            hyp_short = hypothesis.split(",")[0] if hypothesis else ""
            line = f"{label}: {hyp_short}."
            if baseline_val:
                line += f" Baseline readiness: {baseline_val}."
            line += checkin_summary
            exp_lines.append(line)
        if exp_lines:
            lines.append("--- Active Experiments ---")
            lines.extend(exp_lines)
    except Exception:
        pass  # Never let experiment parsing break the main output

    return CircadianResult(summary="\n".join(lines))


@tool(
    name="circadian_heartrate",
    description="Oura HR time-series. Defaults to last night's sleep window.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def circadian_heartrate(start_datetime: str = "", end_datetime: str = "") -> HeartRateResult:
    """Heart rate time-series from Oura, bucketed into 10-min intervals."""
    from metabolon.organelles.chemoreceptor import heartrate

    records = heartrate(start_datetime or None, end_datetime or None)
    if not records:
        return HeartRateResult(summary="No heart rate data available.")

    # Bucket into 10-min intervals for readability
    from collections import defaultdict

    buckets: dict[str, list[int]] = defaultdict(list)
    for r in records:
        ts = r.get("timestamp", "")[:15]  # "2026-03-27T01:2" → 10-min bucket
        bpm = r.get("bpm")
        if ts and bpm is not None:
            bucket_key = ts + "0"  # round to 10-min
            buckets[bucket_key].append(bpm)

    lines = [f"HR time-series ({len(records)} readings, {len(buckets)} buckets)"]
    lines.append("Time           Avg  Min  Max  Source-mix")
    for key in sorted(buckets):
        vals = buckets[key]
        avg_bpm = sum(vals) // len(vals)
        mn, mx = min(vals), max(vals)
        lines.append(f"{key}  {avg_bpm:>3}  {mn:>3}  {mx:>3}")

    # Summary stats
    all_bpm = [r["bpm"] for r in records if r.get("bpm") is not None]
    if all_bpm:
        lines.append("")
        lines.append(
            f"Overall: avg {sum(all_bpm) // len(all_bpm)} bpm, "
            f"min {min(all_bpm)} bpm, max {max(all_bpm)} bpm, "
            f"{len(all_bpm)} readings"
        )

    return HeartRateResult(summary="\n".join(lines))


@tool(
    name="membrane_potential",
    description="Oura readiness + exercise recommendation.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def membrane_potential() -> MembranePotentialResult:
    """Measure membrane potential — readiness and exercise capacity."""
    from metabolon.organelles.chemoreceptor import today as _oura_today

    raw = _oura_today().get("formatted", "")
    guidance = (
        "Exercise guidance: check readiness score above.\n"
        "- <70: light only (walk, gentle stretch)\n"
        "- 70-75: moderate OK (yoga, light weights)\n"
        "- >75: full intensity cleared"
    )
    return MembranePotentialResult(summary=raw, guidance=guidance)


@tool(
    name="homeostasis_system",
    description="System health: pulse, budget, disk pressure, recent events.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def homeostasis_system() -> HomeostasisResult:
    """Check organism homeostasis — pulse + system health."""
    parts = []

    try:
        result = subprocess.run(
            ["launchctl", "list"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        pulse_lines = [ln for ln in result.stdout.splitlines() if "vivesca" in ln]
        parts.append("Pulse: " + ("; ".join(pulse_lines) or "NOT FOUND"))
    except Exception as e:
        parts.append(f"Pulse: check failed ({e})")

    try:
        from metabolon.organelles.vasomotor_sensor import sense

        budget = sense()
        parts.append(f"Budget: {budget.get('formatted', str(budget))}")
    except Exception:
        parts.append("Budget: respirometry unavailable")

    log = os.path.expanduser("~/logs/vivesca-events.jsonl")
    try:
        with open(log) as f:
            lines = f.readlines()
        tail = lines[-5:] if len(lines) >= 5 else lines
        parts.append("Recent events:\n" + "".join(tail))
    except Exception:
        parts.append("Events: log not found")

    # Tool update health
    health_file = os.path.expanduser("~/.coding-tools-health.json")
    try:
        with open(health_file) as f:
            health = json.load(f)
        if health.get("failures"):
            parts.append(
                f"Updates: DEGRADED — missing: {', '.join(health['failures'])} "
                f"(checked {health['checked']})"
            )
        else:
            parts.append(f"Updates: ok (checked {health['checked']})")
    except FileNotFoundError:
        parts.append("Updates: no health data yet (awaiting first hourly run)")
    except Exception as e:
        parts.append(f"Updates: check failed ({e})")

    # Disk pressure (setpoint acclimatises)
    try:
        usage = shutil.disk_usage("/")
        free_gb = usage.free / (1024**3)
        total_gb = usage.total / (1024**3)
        pct_free = (usage.free / usage.total) * 100
        threshold = disk_threshold.read()
        disk_msg = f"Disk: {free_gb:.1f}GB free / {total_gb:.0f}GB ({pct_free:.0f}% free)"
        if free_gb < threshold:
            disk_msg += f" ⚠ LOW (threshold {threshold}GB) — recommend `mo clean`"
        parts.append(disk_msg)
    except Exception as e:
        parts.append(f"Disk: check failed ({e})")

    # Metaphor precision gaps (backward compat aliases = sensors)
    with contextlib.suppress(Exception):
        parts.append(precision_summary())

    # Immune infection log — chronic tool errors needing human review
    with contextlib.suppress(Exception):
        from metabolon.metabolism.infection import infection_summary

        summary = infection_summary()
        if summary:
            parts.append(summary)

    # Checkpoint gate: BLOCK if critical conditions unmet
    gate = "PASS"
    arrest_signals = []
    full_report = "\n".join(parts)
    if "NOT FOUND" in full_report:
        gate = "BLOCK"
        arrest_signals.append("pulse not running")
    if "LOW" in full_report and "Disk" in full_report:
        gate = "BLOCK"
        arrest_signals.append("disk pressure")
    if "DEGRADED" in full_report:
        gate = "WARN"
        arrest_signals.append("tool updates degraded")
    if "CHRONIC" in full_report:
        if gate != "BLOCK":
            gate = "WARN"
        arrest_signals.append("chronic tool infections")

    gate_line = f"Gate: {gate}" + (f" ({', '.join(arrest_signals)})" if arrest_signals else "")
    parts.insert(0, gate_line)

    return HomeostasisResult(sections=parts)


FINANCIAL_NOTES = [
    "Investing.md",
    "Investing Strategy.md",
    "Insurance Action Checklist.md",
    "Term Life Insurance Research.md",
    "IBKR Account Opening Prep.md",
    "HK Mobile Banking UX - Mox Lessons.md",
    "MPF Review - Capco Transition.md",
    "Salaries Tax Summary 2024-25.md",
    "US Estate Tax for HK Residents.md",
]

FINANCIAL_PROMPT_TEMPLATE = """Review the financial notes below and Praxis.md excerpt.

For each item: status (done/in-progress/overdue/upcoming), deadline, next step.
Flag anything overdue or due within 14 days. Sort by urgency. Be concise.

Today: {today}

--- FINANCIAL NOTES ---
{notes}

--- praxis (financial items) ---
{praxis}
"""


class HomeostasisFinancialResult(Secretion):
    """Financial health status from chromatin notes."""

    summary: str
    flagged_count: int


@tool(
    name="homeostasis_financial",
    description="Financial health: deadlines, overdue items, next steps.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def homeostasis_financial() -> HomeostasisFinancialResult:
    """Read financial notes and flag overdue or upcoming items (within 14 days)."""
    import datetime

    notes_dir = str(chromatin)
    today = datetime.date.today().isoformat()

    # Read each financial note
    note_parts = []
    for fname in FINANCIAL_NOTES:
        fpath = os.path.join(notes_dir, fname)
        try:
            with open(fpath) as f:
                content = f.read(3000)  # cap per-file to avoid overflow
            note_parts.append(f"## {fname}\n{content}")
        except FileNotFoundError:
            note_parts.append(f"## {fname}\n(not found)")
        except Exception as e:
            note_parts.append(f"## {fname}\n(read error: {e})")

    # Read Praxis.md for financial-tagged items
    praxis_path = str(praxis)
    praxis_excerpt = ""
    try:
        with open(praxis_path) as f:
            lines = f.readlines()
        # Include lines with finance-adjacent keywords
        keywords = (
            "invest",
            "insur",
            "ibkr",
            "mox",
            "mpf",
            "bowtie",
            "tax",
            "mortgage",
            "due:",
            "deadline",
        )
        financial_lines = [ln.rstrip() for ln in lines if any(kw in ln.lower() for kw in keywords)]
        praxis_excerpt = "\n".join(financial_lines) if financial_lines else "(no financial items)"
    except FileNotFoundError:
        praxis_excerpt = "(Praxis.md not found)"
    except Exception as e:
        praxis_excerpt = f"(read error: {e})"

    notes_text = "\n\n".join(note_parts)
    prompt = FINANCIAL_PROMPT_TEMPLATE.format(
        today=today,
        notes=notes_text,
        praxis=praxis_excerpt,
    )

    try:
        summary = synthesize(prompt, timeout=60)
    except Exception as e:
        summary = (
            f"LLM synthesis failed: {e}\n\nRaw notes loaded for {len(FINANCIAL_NOTES)} files."
        )

    # Count flagged items (lines containing "OVERDUE" or "due within")
    flagged = sum(
        1
        for ln in summary.splitlines()
        if any(kw in ln.upper() for kw in ("OVERDUE", "DUE WITHIN", "FLAGGED", "URGENT"))
    )

    return HomeostasisFinancialResult(summary=summary, flagged_count=flagged)


class LysosomeResult(Secretion):
    """Product of lysosomal digestion — disk cleanup."""

    before_gb: float
    after_gb: float
    freed_gb: float
    output: str


CODE_DIR = os.path.expanduser("~/code")
# Only rm -rf node_modules older than this many days
NODE_MODULES_STALE_DAYS = 7
# cargo sweep removes artifacts older than this many days (within target/)
CARGO_SWEEP_DAYS = 14


def _clean_build_artifacts() -> tuple[float, list[str]]:
    """Clean build artifacts. Cargo sweep for Rust, rm for stale node_modules."""
    import time

    freed_before = shutil.disk_usage("/").free
    log_lines = []

    # Phase A: cargo sweep (surgical — removes old artifacts, keeps recent builds)
    if os.path.isdir(CODE_DIR):
        try:
            result = subprocess.run(
                ["cargo", "sweep", "--recursive", f"--time={CARGO_SWEEP_DAYS}"],
                capture_output=True,
                text=True,
                cwd=CODE_DIR,
                timeout=120,
            )
            # cargo sweep reports what it cleaned
            swept = result.stderr.strip() or result.stdout.strip()
            if swept:
                log_lines.append(f"  cargo sweep ({CARGO_SWEEP_DAYS}d): {swept[-200:]}")
        except FileNotFoundError:
            log_lines.append("  cargo-sweep not installed (brew install cargo-sweep)")
        except Exception as e:
            log_lines.append(f"  cargo sweep FAILED: {e}")

    # Phase B: stale node_modules (no surgical tool — rm -rf)
    stale_cutoff = time.time() - (NODE_MODULES_STALE_DAYS * 86400)
    if os.path.isdir(CODE_DIR):
        for entry in os.scandir(CODE_DIR):
            if not entry.is_dir():
                continue
            nm_path = os.path.join(entry.path, "node_modules")
            if not os.path.isdir(nm_path):
                continue
            try:
                mtime = os.path.getmtime(nm_path)
                if mtime > stale_cutoff:
                    continue
                shutil.rmtree(nm_path, ignore_errors=True)
                log_lines.append(f"  Node: {entry.name}/node_modules (stale)")
            except Exception as e:
                log_lines.append(f"  Node: {entry.name}/node_modules FAILED ({e})")

    freed_after = shutil.disk_usage("/").free
    freed_gb = (freed_after - freed_before) / (1024**3)
    return max(0, freed_gb), log_lines


@tool(
    name="lysosome_digest",
    description="Clean disk: caches + stale build artifacts. Records before/after.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def lysosome_digest() -> LysosomeResult:
    """Lysosomal digestion — caches + build artifacts. Records free space before/after."""
    before = shutil.disk_usage("/").free / (1024**3)
    output_parts = []

    # Phase 1: mo clean (system caches)
    try:
        result = subprocess.run(
            ["mo", "clean"],
            capture_output=True,
            text=True,
            timeout=300,
        )
        output_parts.append(result.stdout + result.stderr)
    except subprocess.TimeoutExpired:
        output_parts.append("mo clean timed out after 5 minutes")
    except Exception as e:
        output_parts.append(f"mo clean failed: {e}")

    # Phase 2: stale build artifacts (target/, node_modules/)
    artifact_gb, artifact_log = _clean_build_artifacts()
    if artifact_log:
        output_parts.append(f"Build artifacts ({artifact_gb:.1f}GB):\n" + "\n".join(artifact_log))

    after = shutil.disk_usage("/").free / (1024**3)
    freed = after - before

    # Record + acclimatise
    disk_threshold.record(prior_load=before, post_response=after, freed_gb=round(freed, 1))

    output = "\n---\n".join(output_parts)
    return LysosomeResult(
        before_gb=round(before, 1),
        after_gb=round(after, 1),
        freed_gb=round(freed, 1),
        output=output[-500:],  # tail to avoid huge tool output
    )


def _cross_link_experiment_symptom(symptom: str, severity: str, notes: str) -> str | None:
    """If an active experiment watches keywords matching this symptom or notes, append a note."""
    if not EXPERIMENTS_DIR.exists():
        return None

    combined = f"{symptom} {notes}".lower()
    for exp_file in EXPERIMENTS_DIR.glob("assay-*.md"):
        text = exp_file.read_text()
        if "status: active" not in text:
            continue
        # Extract watch_keywords from frontmatter
        match = re.search(r"watch_keywords:\s*\[(.+?)\]", text)
        if not match:
            continue
        keywords = [kw.strip().lower() for kw in match.group(1).split(",")]
        if any(kw in combined for kw in keywords):
            intake_note = f"\n> **Symptom logged:** {symptom} (severity: {severity}) — {notes}\n"
            exp_file.write_text(text.rstrip() + "\n" + intake_note + "\n")
            return f"Cross-linked to experiment: {exp_file.name}"
    return None


@tool(
    name="nociception_log",
    description="Log a symptom to health log.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def nociception_log(symptom: str, severity: str = "mild", notes: str = "") -> EffectorResult:
    """Log a nociceptive signal."""
    today = datetime.date.today().isoformat()
    entry = f"\n## {today} — {symptom}\n- Severity: {severity}\n"
    if notes:
        entry += f"- Notes: {notes}\n"

    os.makedirs(os.path.dirname(HEALTH_LOG), exist_ok=True)
    with open(HEALTH_LOG, "a") as f:
        f.write(entry)

    message = f"Logged: {symptom} ({severity}) on {today}"

    xlink = _cross_link_experiment_symptom(symptom, severity, notes)
    if xlink:
        message += f"\n{xlink}"

    return EffectorResult(success=True, message=message)


class AnabolismLink(Secretion):
    """One link in the anabolic flywheel."""

    name: str
    signal: str


class AnabolismResult(Secretion):
    """Anabolic flywheel raw data — links with numeric signals for LLM interpretation."""

    links: list[dict]
    blind_spots: list[str]


@tool(
    name="anabolism_flywheel",
    description="Life flywheel: sleep, energy, creative output, calendar. Finds the break.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def anabolism_flywheel() -> AnabolismResult:
    """Check the anabolic flywheel."""
    links = []

    # 1. Sleep & Energy
    try:
        from metabolon.organelles.chemoreceptor import today as _chemoreceptor_today

        health = _chemoreceptor_today()
        links.append({"name": "sleep", "score": health.get("sleep_score")})
        links.append({"name": "energy", "score": health.get("readiness_score")})
    except Exception:
        links.append({"name": "sleep", "score": None})
        links.append({"name": "energy", "score": None})

    # 3. Calendar load
    try:
        from metabolon.organelles.circadian_clock import scheduled_events

        fasti_out = scheduled_events()
        events = 0
        for line in fasti_out.splitlines():
            line = line.strip()
            # simple heuristic: non-empty line with a time pattern
            if line and re.search(r"\d{1,2}:\d{2}|\d{1,2}\s*[ap]m", line.lower()):
                events += 1
        links.append({"name": "calendar", "events": events})
    except Exception:
        links.append({"name": "calendar", "events": None})

    # 4. Creative output
    try:
        notes_dir = str(chromatin)

        chromatin_cmd = ["git", "log", "--since=7.days", "--oneline"]
        chromatin_out = subprocess.run(
            chromatin_cmd, cwd=notes_dir, capture_output=True, text=True, timeout=10
        )
        chromatin_commits = (
            len(chromatin_out.stdout.strip().splitlines()) if chromatin_out.stdout.strip() else 0
        )

        blog_cmd = ["git", "log", "--since=14.days", "--oneline", "--", "Writing/Blog/Published/"]
        blog_out = subprocess.run(
            blog_cmd, cwd=notes_dir, capture_output=True, text=True, timeout=10
        )
        blog_posts = len(blog_out.stdout.strip().splitlines()) if blog_out.stdout.strip() else 0

        links.append(
            {
                "name": "creative",
                "chromatin_commits_7d": chromatin_commits,
                "blog_commits_14d": blog_posts,
            }
        )
    except Exception:
        links.append({"name": "creative", "chromatin_commits_7d": None, "blog_commits_14d": None})

    # 5. Symptoms
    try:
        if os.path.exists(HEALTH_LOG):
            with open(HEALTH_LOG) as f:
                lines = f.readlines()

            recent_entries = 0
            seven_days_ago = datetime.date.today() - datetime.timedelta(days=7)

            for line in reversed(lines[-50:]):
                m = re.match(r"^##\s+(\d{4}-\d{2}-\d{2})", line)
                if m:
                    entry_date = datetime.date.fromisoformat(m.group(1))
                    if entry_date >= seven_days_ago:
                        recent_entries += 1

            links.append({"name": "symptoms", "recent_entries_7d": recent_entries})
        else:
            links.append({"name": "symptoms", "recent_entries_7d": 0})
    except Exception:
        links.append({"name": "symptoms", "recent_entries_7d": None})

    # 6. Blind spots
    blind_spots = ["exercise (no sensor)", "mood/joy (ask)", "anxiety (ask)"]

    return AnabolismResult(links=links, blind_spots=blind_spots)


class AngiogenesisResult(Secretion):
    """Angiogenesis scan: hypoxic pairs and proposed vessels."""

    hypoxic_pairs: list[dict]
    proposals: list[dict]
    existing_vessels: list[dict]


class MitophagyResult(Secretion):
    """Model performance fitness scores and blacklist status."""

    fitness: list[dict]
    blacklist: dict


@tool(
    name="mitophagy_status",
    description="Model performance tracking and fitness scores.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def mitophagy_status(task_type: str = "", days: int = 7) -> MitophagyResult:
    """Return model fitness scores and current blacklist for the last N days."""
    from metabolon.organelles.mitophagy import _load_blacklist, model_fitness

    fitness = model_fitness(task_type=task_type, days=days)
    bl = _load_blacklist()
    return MitophagyResult(fitness=fitness, blacklist=bl)


@tool(
    name="angiogenesis",
    description="Detect underserved subsystem connections and propose new integrations.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def angiogenesis() -> AngiogenesisResult:
    """Scan infection log for sequential failures, propose integrations between hypoxic pairs."""
    from metabolon.organelles.angiogenesis import (
        detect_hypoxia,
        propose_vessel,
        vessel_registry,
    )

    pairs = detect_hypoxia()
    proposals = [propose_vessel(p["source"], p["target"]) for p in pairs]
    existing = vessel_registry()
    return AngiogenesisResult(
        hypoxic_pairs=pairs,
        proposals=proposals,
        existing_vessels=existing,
    )


class GlycolysisResult(Secretion):
    """Glycolysis rate — symbiont dependency ratio."""

    deterministic_count: int
    symbiont_count: int
    hybrid_count: int
    total: int
    glycolysis_pct: float
    trend: list[dict]
    summary: str


@tool(
    name="glycolysis_rate",
    description="Symbiont dependency ratio — what % of the organism is deterministic.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def glycolysis_rate(trend_days: int = 30) -> GlycolysisResult:
    """Measure and return the organism's glycolysis rate with optional trend."""
    from metabolon.organelles.glycolysis_rate import snapshot, trend

    rate = snapshot()
    trend_data = trend(days=trend_days)

    summary_parts = [
        f"Glycolysis: {rate['glycolysis_pct']}% deterministic",
        f"  Deterministic: {rate['deterministic_count']}",
        f"  Symbiont: {rate['symbiont_count']}",
        f"  Hybrid: {rate['hybrid_count']}",
        f"  Total capabilities: {rate['total']}",
    ]
    if len(trend_data) >= 2:
        first = trend_data[0]["glycolysis_pct"]
        last = trend_data[-1]["glycolysis_pct"]
        delta = round(last - first, 1)
        direction = "+" if delta >= 0 else ""
        summary_parts.append(
            f"  Trend ({trend_days}d): {direction}{delta}% ({trend_data[0]['date']} → {trend_data[-1]['date']})"
        )

    return GlycolysisResult(
        deterministic_count=rate["deterministic_count"],
        symbiont_count=rate["symbiont_count"],
        hybrid_count=rate["hybrid_count"],
        total=rate["total"],
        glycolysis_pct=rate["glycolysis_pct"],
        trend=trend_data,
        summary="\n".join(summary_parts),
    )


class TissueRoutingResult(Secretion):
    """Tissue routing — current model allocation by task type."""

    routes: dict[str, str]
    report: str


@tool(
    name="tissue_routing",
    description="Model routing by task type — which symbiont strain for which subsystem.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def tissue_routing_tool() -> TissueRoutingResult:
    """Return current tissue routing table with performance data from mitophagy."""
    from metabolon.organelles.tissue_routing import observed_routes, route_report

    routes = observed_routes()
    report = route_report()
    return TissueRoutingResult(routes=routes, report=report)


class CrisprResult(Secretion):
    """CRISPR adaptive immunity status."""

    spacer_count: int
    recent: list[dict]
    guide_count: int
    summary: str


@tool(
    name="crispr_status",
    description="Adaptive memory: spacer count, recent acquisitions, guide coverage.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def crispr_status(recent_n: int = 5) -> CrisprResult:
    """Return adaptive immune memory state: spacers acquired, compiled guides, recent entries."""
    import json
    from pathlib import Path

    from metabolon.organelles.crispr import compile_guides, spacer_count

    spacers_path = Path.home() / ".cache" / "crispr" / "spacers.jsonl"
    count = spacer_count()
    guides = compile_guides()

    recent: list[dict] = []
    if spacers_path.exists():
        try:
            lines = spacers_path.read_text().splitlines()
            for line in reversed(lines):
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    recent.append(
                        {
                            "ts": entry.get("ts", "")[:10],
                            "tool": entry.get("tool", ""),
                            "pattern": entry.get("pattern", "")[:80],
                        }
                    )
                    if len(recent) >= recent_n:
                        break
                except Exception:
                    continue
        except Exception:
            pass

    summary_lines = [
        f"CRISPR spacers: {count} acquired, {len(guides)} guides compiled",
    ]
    if recent:
        summary_lines.append("Recent acquisitions:")
        for r in recent:
            summary_lines.append(f"  [{r['ts']}] {r['tool']}: {r['pattern']}")
    else:
        summary_lines.append("No spacers acquired yet.")

    return CrisprResult(
        spacer_count=count,
        recent=recent,
        guide_count=len(guides),
        summary="\n".join(summary_lines),
    )


class RetrogradeResult(Secretion):
    """Retrograde signal balance — symbiont influence ratio."""

    anterograde_count: int
    retrograde_count: int
    ratio: float
    assessment: str
    window_days: int
    summary: str


@tool(
    name="retrograde_balance",
    description="Symbiont influence ratio — is the organism sovereign or dependent?",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def retrograde_balance(days: int = 7) -> RetrogradeResult:
    """Measure anterograde vs retrograde signal balance over last N days.

    Anterograde (organism→symbiont): pulse systoles, channel calls, agent dispatches.
    Retrograde (symbiont→organism): agent git commits, methylation proposals, repairs.

    Assessment: sovereign (>3:1), balanced (1-3:1), dependent (<1:1).
    """
    from metabolon.organelles.retrograde import signal_balance

    b = signal_balance(days=days)
    ratio_str = (
        f"{b['ratio']:.1f}:1" if b["retrograde_count"] > 0 else f"{b['anterograde_count']}:0"
    )
    summary = (
        f"Retrograde balance ({days}d): {b['assessment'].upper()}\n"
        f"  Anterograde (organism→symbiont): {b['anterograde_count']}\n"
        f"  Retrograde  (symbiont→organism): {b['retrograde_count']}\n"
        f"  Ratio: {ratio_str}\n"
        f"  Assessment: {b['assessment']}"
    )
    return RetrogradeResult(
        anterograde_count=b["anterograde_count"],
        retrograde_count=b["retrograde_count"],
        ratio=b["ratio"],
        assessment=b["assessment"],
        window_days=days,
        summary=summary,
    )
