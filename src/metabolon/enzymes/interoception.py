"""interoception - sensing internal state."""

import contextlib
import datetime
import json
import os
import platform
import re
import shutil
import subprocess
from collections import defaultdict

from fastmcp.tools.function_tool import tool
from mcp.types import ToolAnnotations

from metabolon.morphology import EffectorResult, Secretion

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
CODE_DIR = os.path.expanduser("~/code")
HEALTH_LOG_RELATIVE = ("Health", "Symptom Log.md")
NODE_MODULES_STALE_DAYS = 7
CARGO_SWEEP_DAYS = 14


class CircadianResult(Secretion):
    summary: str


class HeartRateResult(Secretion):
    summary: str


class MembranePotentialResult(Secretion):
    summary: str
    guidance: str


class HomeostasisResult(Secretion):
    sections: list[str]


class InflammasomeResult(Secretion):
    report: str
    passed: int
    total: int


class HomeostasisFinancialResult(Secretion):
    summary: str
    flagged_count: int


class LysosomeResult(Secretion):
    before_gb: float
    after_gb: float
    freed_gb: float
    output: str


class AnabolismResult(Secretion):
    links: list[dict]
    blind_spots: list[str]


class AngiogenesisResult(Secretion):
    hypoxic_pairs: list[dict]
    proposals: list[dict]
    existing_vessels: list[dict]


class MitophagyResult(Secretion):
    fitness: list[dict]
    blacklist: dict


class GlycolysisResult(Secretion):
    deterministic_count: int
    symbiont_count: int
    hybrid_count: int
    total: int
    glycolysis_pct: float
    trend: list[dict]
    summary: str


class TissueRoutingResult(Secretion):
    routes: dict[str, str]
    report: str


class CrisprResult(Secretion):
    spacer_count: int
    recent: list[dict]
    guide_count: int
    summary: str


class RetrogradeResult(Secretion):
    anterograde_count: int
    retrograde_count: int
    ratio: float
    assessment: str
    window_days: int
    summary: str


def _sleep_result(period: str = "today") -> CircadianResult:
    """Wrapper for circadian.py — delegates to interoception(action='sleep')."""
    return interoception(action="sleep", period=period)


def _heartrate_result(start_datetime: str = "", end_datetime: str = "") -> HeartRateResult:
    """Wrapper for circadian.py — delegates to interoception(action='heartrate')."""
    return interoception(
        action="heartrate", start_datetime=start_datetime, end_datetime=end_datetime
    )


def _health_log_path() -> str:
    from metabolon import locus

    return str(locus.chromatin.joinpath(*HEALTH_LOG_RELATIVE))


def _format_duration(seconds: int | float | None) -> str:
    if seconds is None:
        return "n/a"
    hours, minutes = divmod(int(seconds) // 60, 60)
    return f"{hours}h{minutes:02d}m" if hours else f"{minutes}m"


def _clean_build_artifacts() -> tuple[float, list[str]]:
    import time

    before_free = shutil.disk_usage("/").free
    log_lines: list[str] = []
    if os.path.isdir(CODE_DIR):
        try:
            result = subprocess.run(
                ["cargo", "sweep", "--recursive", f"--time={CARGO_SWEEP_DAYS}"],
                capture_output=True,
                text=True,
                cwd=CODE_DIR,
                timeout=120,
            )
            swept = result.stderr.strip() or result.stdout.strip()
            if swept:
                log_lines.append(f"  cargo sweep ({CARGO_SWEEP_DAYS}d): {swept[-200:]}")
        except FileNotFoundError:
            log_lines.append("  cargo-sweep not installed (brew install cargo-sweep)")
        except Exception as exc:
            log_lines.append(f"  cargo sweep FAILED: {exc}")

    stale_cutoff = time.time() - (NODE_MODULES_STALE_DAYS * 86400)
    if os.path.isdir(CODE_DIR):
        for entry in os.scandir(CODE_DIR):
            if not entry.is_dir():
                continue
            node_modules_path = os.path.join(entry.path, "node_modules")
            if not os.path.isdir(node_modules_path):
                continue
            try:
                if os.path.getmtime(node_modules_path) > stale_cutoff:
                    continue
                shutil.rmtree(node_modules_path, ignore_errors=True)
                log_lines.append(f"  Node: {entry.name}/node_modules (stale)")
            except Exception as exc:
                log_lines.append(f"  Node: {entry.name}/node_modules FAILED ({exc})")

    after_free = shutil.disk_usage("/").free
    return max(0.0, (after_free - before_free) / (1024**3)), log_lines


def _cross_link_experiment_symptom(symptom: str, severity: str, notes: str) -> str | None:
    from metabolon import locus

    if not locus.experiments.exists():
        return None
    combined = f"{symptom} {notes}".lower()
    for experiment_file in locus.experiments.glob("assay-*.md"):
        text = experiment_file.read_text()
        if "status: active" not in text:
            continue
        match = re.search(r"watch_keywords:\s*\[(.+?)\]", text)
        if not match:
            continue
        keywords = [keyword.strip().lower() for keyword in match.group(1).split(",")]
        if any(keyword in combined for keyword in keywords):
            intake_note = f"\n> **Symptom logged:** {symptom} (severity: {severity}) - {notes}\n"
            tmp = experiment_file.with_suffix(".md.tmp")
            tmp.write_text(text.rstrip() + "\n" + intake_note + "\n")
            tmp.replace(experiment_file)
            return f"Cross-linked to experiment: {experiment_file.name}"
    return None


_ACTIONS = (
    "system|financial|sleep|readiness|heartrate|log_symptom|flywheel|disk_clean|"
    "glycolysis|tissue_routing|crispr|retrograde|mitophagy|angiogenesis|membrane|probe"
)


@tool(
    name="interoception",
    description="Internal sensing by action.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def interoception(
    action: str,
    query: str = "",
    period: str = "today",
    start_datetime: str = "",
    end_datetime: str = "",
    symptom: str = "",
    severity: str = "mild",
    notes: str = "",
    trend_days: int = 30,
    recent_n: int = 5,
    task_type: str = "",
    days: int = 7,
) -> (
    CircadianResult
    | HeartRateResult
    | MembranePotentialResult
    | HomeostasisResult
    | HomeostasisFinancialResult
    | LysosomeResult
    | AnabolismResult
    | AngiogenesisResult
    | MitophagyResult
    | GlycolysisResult
    | TissueRoutingResult
    | CrisprResult
    | RetrogradeResult
    | InflammasomeResult
    | EffectorResult
):
    """Unified internal state sensor."""
    del query
    action = action.lower().strip()

    if action == "system":
        from metabolon.metabolism.mismatch_repair import summary as precision_summary
        from metabolon.metabolism.setpoint import Threshold

        parts: list[str] = []
        if platform.system() == "Darwin":
            try:
                result = subprocess.run(
                    ["launchctl", "list"], capture_output=True, text=True, timeout=5
                )
                pulse_lines = [line for line in result.stdout.splitlines() if "vivesca" in line]
                parts.append("Pulse: " + ("; ".join(pulse_lines) or "NOT FOUND"))
            except Exception as exc:
                parts.append(f"Pulse: check failed ({exc})")
        else:
            try:
                result = subprocess.run(
                    ["systemctl", "--user", "list-units", "--type=service", "--no-legend"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                pulse_lines = [line for line in result.stdout.splitlines() if "vivesca" in line]
                parts.append("Pulse: " + ("; ".join(pulse_lines) or "NOT FOUND"))
            except Exception as exc:
                parts.append(f"Pulse: check failed ({exc})")

        try:
            from metabolon.organelles.vasomotor_sensor import sense

            budget = sense()
            parts.append(f"Budget: {budget.get('formatted', str(budget))}")
        except Exception:
            parts.append("Budget: respirometry unavailable")

        log_path = os.path.expanduser("~/logs/vivesca-events.jsonl")
        try:
            with open(log_path, encoding="utf-8") as handle:
                lines = handle.readlines()
            tail = lines[-5:] if len(lines) >= 5 else lines
            parts.append("Recent events:\n" + "".join(tail))
        except Exception:
            parts.append("Events: log not found")

        health_path = os.path.expanduser("~/.coding-tools-health.json")
        try:
            with open(health_path, encoding="utf-8") as handle:
                health = json.load(handle)
            if health.get("failures"):
                parts.append(
                    f"Updates: DEGRADED - missing: {', '.join(health['failures'])} "
                    f"(checked {health['checked']})"
                )
            else:
                parts.append(f"Updates: ok (checked {health['checked']})")
        except FileNotFoundError:
            parts.append("Updates: no health data yet (awaiting first hourly run)")
        except Exception as exc:
            parts.append(f"Updates: check failed ({exc})")

        try:
            usage = shutil.disk_usage("/")
            free_gb = usage.free / (1024**3)
            total_gb = usage.total / (1024**3)
            pct_free = (usage.free / usage.total) * 100
            disk_threshold = Threshold(name="disk", default=15, clamp=(5, 50))
            threshold = disk_threshold.read()
            disk_message = f"Disk: {free_gb:.1f}GB free / {total_gb:.0f}GB ({pct_free:.0f}% free)"
            if free_gb < threshold:
                disk_message += f" LOW (threshold {threshold}GB) - recommend `mo clean`"
            parts.append(disk_message)
        except Exception as exc:
            parts.append(f"Disk: check failed ({exc})")

        with contextlib.suppress(Exception):
            parts.append(precision_summary())

        with contextlib.suppress(Exception):
            from metabolon.metabolism.infection import infection_summary

            summary = infection_summary()
            if summary:
                parts.append(summary)

        gate = "PASS"
        arrest_signals: list[str] = []
        report_text = "\n".join(parts)
        if "NOT FOUND" in report_text:
            gate = "BLOCK"
            arrest_signals.append("pulse not running")
        if "LOW" in report_text and "Disk" in report_text:
            gate = "BLOCK"
            arrest_signals.append("disk pressure")
        if "DEGRADED" in report_text:
            gate = "WARN"
            arrest_signals.append("tool updates degraded")
        if "CHRONIC" in report_text:
            if gate != "BLOCK":
                gate = "WARN"
            arrest_signals.append("chronic tool infections")
        gate_line = f"Gate: {gate}" + (f" ({', '.join(arrest_signals)})" if arrest_signals else "")
        parts.insert(0, gate_line)
        return HomeostasisResult(sections=parts)

    if action == "financial":
        from metabolon import locus
        from metabolon.cytosol import synthesize

        notes_dir = str(locus.chromatin)
        today = datetime.date.today().isoformat()
        note_parts = []
        for filename in FINANCIAL_NOTES:
            file_path = os.path.join(notes_dir, filename)
            try:
                with open(file_path, encoding="utf-8") as handle:
                    file_content = handle.read(3000)
                note_parts.append(f"## {filename}\n{file_content}")
            except FileNotFoundError:
                note_parts.append(f"## {filename}\n(not found)")
            except Exception as exc:
                note_parts.append(f"## {filename}\n(read error: {exc})")

        praxis_excerpt = ""
        try:
            with open(str(locus.praxis), encoding="utf-8") as handle:
                lines = handle.readlines()
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
            financial_lines = [
                line.rstrip()
                for line in lines
                if any(keyword in line.lower() for keyword in keywords)
            ]
            praxis_excerpt = (
                "\n".join(financial_lines) if financial_lines else "(no financial items)"
            )
        except FileNotFoundError:
            praxis_excerpt = "(Praxis.md not found)"
        except Exception as exc:
            praxis_excerpt = f"(read error: {exc})"

        prompt = FINANCIAL_PROMPT_TEMPLATE.format(
            today=today, notes="\n\n".join(note_parts), praxis=praxis_excerpt
        )
        try:
            summary = synthesize(prompt, timeout=60)
        except Exception as exc:
            summary = f"LLM synthesis failed: {exc}\n\nRaw notes loaded for {len(FINANCIAL_NOTES)} files."

        flagged = sum(
            1
            for line in summary.splitlines()
            if any(
                keyword in line.upper()
                for keyword in ("OVERDUE", "DUE WITHIN", "FLAGGED", "URGENT")
            )
        )
        return HomeostasisFinancialResult(summary=summary, flagged_count=flagged)

    if action == "sleep":
        from metabolon import locus
        from metabolon.organelles.chemoreceptor import sense, week

        if period == "week":
            return CircadianResult(summary=str(week()))

        data = sense()
        if "error" in data:
            return CircadianResult(summary=f"Error: {data['error']}")

        lines: list[str] = []
        alerts = []
        sleep_score = data.get("sleep_score")
        readiness_score = data.get("readiness_score")
        average_hrv = data.get("average_hrv")
        if sleep_score is not None and sleep_score < 70:
            alerts.append(f"SLEEP LOW ({sleep_score}): below 70 threshold")
        if readiness_score is not None and readiness_score < 70:
            alerts.append(f"READINESS LOW ({readiness_score}): light activity only")
        if average_hrv is not None and average_hrv < 20:
            alerts.append(f"HRV LOW ({average_hrv}): recovery priority")
        if alerts:
            lines.append("--- Alerts ---")
            lines.extend(alerts)
            lines.append("")

        lines.append("--- Scores ---")
        lines.append(f"Sleep: {sleep_score}  Readiness: {readiness_score}")
        lines.append(f"Sleep contributors: {data.get('sleep_contributors', {})}")
        lines.append(f"Readiness contributors: {data.get('contributors', {})}")
        lines.append(
            f"Temp deviation: {data.get('temperature_deviation')}°C  Trend: {data.get('temperature_trend_deviation')}°C"
        )
        lines.append("")

        lines.append("--- Sleep detail ---")
        lines.append(
            f"Deep:  {_format_duration(data.get('deep_sleep_duration'))}  "
            f"Light: {_format_duration(data.get('light_sleep_duration'))}  "
            f"REM:   {_format_duration(data.get('rem_sleep_duration'))}"
        )
        lines.append(
            f"Awake: {_format_duration(data.get('awake_time'))}  "
            f"Total: {_format_duration(data.get('total_sleep_duration'))}  "
            f"In bed: {_format_duration(data.get('time_in_bed'))}"
        )
        if data.get("bedtime_start") and data.get("bedtime_end"):
            lines.append(f"Bed:   {data['bedtime_start'][:16]} -> {data['bedtime_end'][:16]}")
        lines.append(
            f"Latency: {_format_duration(data.get('latency'))}  "
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

        hypnogram = data.get("sleep_phase_5_min")
        if hypnogram:
            legend = {"1": "█", "2": "▓", "3": "░", "4": " "}
            lines.append("--- Hypnogram (5-min) ---")
            lines.append("█=deep ▓=light ░=REM (space)=awake")
            lines.append("".join(legend.get(char, "?") for char in hypnogram))
            lines.append("")

        movement = data.get("movement_30_sec")
        if movement:
            legend = {"1": "·", "2": "~", "3": "≈", "4": "▲"}
            lines.append("--- Movement (30-sec) ---")
            lines.append("·=still ~=restless ≈=tossing ▲=active")
            lines.append("".join(legend.get(char, "?") for char in movement))
            lines.append("")

        activity = data.get("activity")
        if activity:
            lines.append("--- Activity (yesterday) ---")
            lines.append(
                f"Score: {activity.get('score')}  Steps: {activity.get('steps')}  "
                f"Calories: {activity.get('active_calories')} active / {activity.get('total_calories')} total"
            )
            lines.append(
                f"High: {_format_duration(activity.get('high_activity_time'))}  "
                f"Med: {_format_duration(activity.get('medium_activity_time'))}  "
                f"Low: {_format_duration(activity.get('low_activity_time'))}  "
                f"Sedentary: {_format_duration(activity.get('sedentary_time'))}"
            )
            lines.append(f"Walking equiv: {activity.get('equivalent_walking_distance')}m")
            lines.append("")

        stress = data.get("stress")
        if stress:
            lines.append("--- Stress ---")
            lines.append(
                f"Summary: {stress.get('day_summary')}  "
                f"Stress high: {_format_duration(stress.get('stress_high'))}  "
                f"Recovery high: {_format_duration(stress.get('recovery_high'))}"
            )
            lines.append("")

        spo2 = data.get("spo2")
        if spo2:
            lines.append("--- SpO2 ---")
            lines.append(
                f"Average: {spo2.get('average')}%  "
                f"Breathing disturbance index: {spo2.get('breathing_disturbance_index')}"
            )
            lines.append("")

        resilience = data.get("resilience")
        if resilience:
            lines.append("--- Resilience ---")
            lines.append(
                f"Level: {resilience.get('level')}  Contributors: {resilience.get('contributors', {})}"
            )
            lines.append("")

        sleep_time = data.get("sleep_time")
        if sleep_time:
            lines.append("--- Bedtime recommendation ---")
            lines.append(
                f"Recommendation: {sleep_time.get('recommendation')}  Status: {sleep_time.get('status')}"
            )
            optimal = sleep_time.get("optimal_bedtime") or {}
            if optimal:
                lines.append(f"Optimal window: {optimal}")
            lines.append("")

        vascular_age = data.get("vascular_age")
        vo2_max = data.get("vo2_max")
        if vascular_age is not None or vo2_max is not None:
            lines.append("--- Cardiovascular ---")
            parts = []
            if vascular_age is not None:
                parts.append(f"Vascular age: {vascular_age}")
            if vo2_max is not None:
                parts.append(f"VO2 max: {vo2_max}")
            lines.append("  ".join(parts))
            lines.append("")

        workouts = data.get("workouts")
        if workouts:
            lines.append("--- Workouts ---")
            for workout in workouts:
                start = (workout.get("start") or "")[:16]
                calories = workout.get("calories")
                lines.append(
                    f"{workout.get('activity')} ({workout.get('intensity')}) "
                    f"{start}  {f'{calories:.0f} kcal' if calories else ''} "
                    f"[{workout.get('source')}]"
                )
            lines.append("")

        try:
            experiment_lines: list[str] = []
            today_date = datetime.date.today()
            for experiment_file in sorted(locus.experiments.glob("assay-*.md")):
                text = experiment_file.read_text()
                frontmatter_match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
                if not frontmatter_match:
                    continue
                frontmatter = frontmatter_match.group(1)
                status_match = re.search(r"^status:\s*(\S+)", frontmatter, re.MULTILINE)
                if not status_match or status_match.group(1).strip('"') != "active":
                    continue
                name_match = re.search(r'^name:\s*"?([^"\n]+)"?', frontmatter, re.MULTILINE)
                start_match = re.search(r"^start_date:\s*(\S+)", frontmatter, re.MULTILINE)
                hypothesis_match = re.search(
                    r'^hypothesis:\s*"?([^"\n]+)"?', frontmatter, re.MULTILINE
                )
                name = name_match.group(1).strip() if name_match else experiment_file.stem
                hypothesis = hypothesis_match.group(1).strip() if hypothesis_match else ""
                start_date = None
                day_number = ""
                if start_match:
                    try:
                        start_date = datetime.date.fromisoformat(start_match.group(1))
                        day_number = (today_date - start_date).days + 1
                    except ValueError:
                        start_date = None
                total_days = ""
                end_match = re.search(r"^end_date:\s*(\S+)", frontmatter, re.MULTILINE)
                if end_match and start_date is not None:
                    try:
                        end_date = datetime.date.fromisoformat(end_match.group(1))
                        total_days = (end_date - start_date).days + 1
                    except ValueError:
                        total_days = ""
                checkin_blocks = re.findall(r"(### Day \d+[^\n]*\n(?:[^\n#][^\n]*\n)*)", text)
                checkin_summary = ""
                if checkin_blocks:
                    last_block = checkin_blocks[-1]
                    readiness_match = re.search(r"Readiness:\s*avg\s*([\d.]+)", last_block)
                    sleep_match = re.search(r"Sleep:\s*avg\s*([\d.]+)", last_block)
                    exp_parts = []
                    if sleep_match:
                        exp_parts.append(f"sleep {sleep_match.group(1)}")
                    if readiness_match:
                        exp_parts.append(f"readiness {readiness_match.group(1)}")
                    if exp_parts:
                        checkin_summary = f" Last check-in: {', '.join(exp_parts)}."
                baseline_match = re.search(r"Readiness:\s*avg\s*([\d.]+)", text)
                baseline_value = baseline_match.group(1) if baseline_match else None
                if day_number and total_days:
                    day_label = f"Day {day_number} of {total_days}"
                elif day_number:
                    day_label = f"Day {day_number}"
                else:
                    day_label = ""
                label = f"{name} ({day_label})" if day_label else name
                hypothesis_short = hypothesis.split(",")[0] if hypothesis else ""
                line = f"{label}: {hypothesis_short}."
                if baseline_value:
                    line += f" Baseline readiness: {baseline_value}."
                line += checkin_summary
                experiment_lines.append(line)
            if experiment_lines:
                lines.append("--- Active Experiments ---")
                lines.extend(experiment_lines)
        except Exception:
            pass

        return CircadianResult(summary="\n".join(lines))

    if action in {"readiness", "membrane"}:
        from metabolon.organelles.chemoreceptor import today as oura_today

        raw = oura_today().get("formatted", "")
        guidance = (
            "Exercise guidance: check readiness score above.\n"
            "- <70: light only (walk, gentle stretch)\n"
            "- 70-75: moderate OK (yoga, light weights)\n"
            "- >75: full intensity cleared"
        )
        return MembranePotentialResult(summary=raw, guidance=guidance)

    if action == "heartrate":
        from metabolon.organelles.chemoreceptor import heartrate

        records = heartrate(start_datetime or None, end_datetime or None)
        if not records:
            return HeartRateResult(summary="No heart rate data available.")

        buckets: dict[str, list[int]] = defaultdict(list)
        for record in records:
            timestamp = record.get("timestamp", "")[:15]
            bpm = record.get("bpm")
            if timestamp and bpm is not None:
                buckets[timestamp + "0"].append(bpm)

        lines = [f"HR time-series ({len(records)} readings, {len(buckets)} buckets)"]
        lines.append("Time           Avg  Min  Max  Source-mix")
        for key in sorted(buckets):
            values = buckets[key]
            average_bpm = sum(values) // len(values)
            lines.append(f"{key}  {average_bpm:>3}  {min(values):>3}  {max(values):>3}")

        all_bpm = [record["bpm"] for record in records if record.get("bpm") is not None]
        if all_bpm:
            lines.append("")
            lines.append(
                f"Overall: avg {sum(all_bpm) // len(all_bpm)} bpm, "
                f"min {min(all_bpm)} bpm, max {max(all_bpm)} bpm, "
                f"{len(all_bpm)} readings"
            )
        return HeartRateResult(summary="\n".join(lines))

    if action == "log_symptom":
        if not symptom:
            return EffectorResult(success=False, message="log_symptom requires: symptom")
        today_iso = datetime.date.today().isoformat()
        entry = f"\n## {today_iso} - {symptom}\n- Severity: {severity}\n"
        if notes:
            entry += f"- Notes: {notes}\n"
        health_log = _health_log_path()
        os.makedirs(os.path.dirname(health_log), exist_ok=True)
        with open(health_log, "a", encoding="utf-8") as handle:
            handle.write(entry)
        message = f"Logged: {symptom} ({severity}) on {today_iso}"
        cross_link = _cross_link_experiment_symptom(symptom, severity, notes)
        if cross_link:
            message += f"\n{cross_link}"
        return EffectorResult(success=True, message=message)

    if action == "flywheel":
        from metabolon import locus

        links: list[dict] = []
        try:
            from metabolon.organelles.chemoreceptor import today as chemoreceptor_today

            health = chemoreceptor_today()
            links.append({"name": "sleep", "score": health.get("sleep_score")})
            links.append({"name": "energy", "score": health.get("readiness_score")})
        except Exception:
            links.append({"name": "sleep", "score": None})
            links.append({"name": "energy", "score": None})

        try:
            from metabolon.organelles.circadian_clock import scheduled_events

            scheduled = scheduled_events()
            events = 0
            for line in scheduled.splitlines():
                stripped = line.strip()
                if stripped and re.search(r"\d{1,2}:\d{2}|\d{1,2}\s*[ap]m", stripped.lower()):
                    events += 1
            links.append({"name": "calendar", "events": events})
        except Exception:
            links.append({"name": "calendar", "events": None})

        try:
            notes_dir = str(locus.chromatin)
            chromatin_log = subprocess.run(
                ["git", "log", "--since=7.days", "--oneline"],
                cwd=notes_dir,
                capture_output=True,
                text=True,
                timeout=10,
            )
            chromatin_commits = (
                len(chromatin_log.stdout.strip().splitlines())
                if chromatin_log.stdout.strip()
                else 0
            )
            blog_log = subprocess.run(
                ["git", "log", "--since=14.days", "--oneline", "--", "Writing/Blog/Published/"],
                cwd=notes_dir,
                capture_output=True,
                text=True,
                timeout=10,
            )
            blog_posts = (
                len(blog_log.stdout.strip().splitlines()) if blog_log.stdout.strip() else 0
            )
            links.append(
                {
                    "name": "creative",
                    "chromatin_commits_7d": chromatin_commits,
                    "blog_commits_14d": blog_posts,
                }
            )
        except Exception:
            links.append(
                {"name": "creative", "chromatin_commits_7d": None, "blog_commits_14d": None}
            )

        try:
            health_log = _health_log_path()
            if os.path.exists(health_log):
                with open(health_log, encoding="utf-8") as handle:
                    lines_log = handle.readlines()
                recent_entries = 0
                seven_days_ago = datetime.date.today() - datetime.timedelta(days=7)
                for line in reversed(lines_log[-50:]):
                    match = re.match(r"^##\s+(\d{4}-\d{2}-\d{2})", line)
                    if match:
                        entry_date = datetime.date.fromisoformat(match.group(1))
                        if entry_date >= seven_days_ago:
                            recent_entries += 1
                links.append({"name": "symptoms", "recent_entries_7d": recent_entries})
            else:
                links.append({"name": "symptoms", "recent_entries_7d": 0})
        except Exception:
            links.append({"name": "symptoms", "recent_entries_7d": None})

        return AnabolismResult(
            links=links,
            blind_spots=["exercise (no sensor)", "mood/joy (ask)", "anxiety (ask)"],
        )

    if action == "disk_clean":
        from metabolon.metabolism.setpoint import Threshold

        before = shutil.disk_usage("/").free / (1024**3)
        output_parts: list[str] = []
        try:
            result = subprocess.run(["mo", "clean"], capture_output=True, text=True, timeout=300)
            output_parts.append(result.stdout + result.stderr)
        except subprocess.TimeoutExpired:
            output_parts.append("mo clean timed out after 5 minutes")
        except Exception as exc:
            output_parts.append(f"mo clean failed: {exc}")

        artifact_gb, artifact_log = _clean_build_artifacts()
        if artifact_log:
            output_parts.append(
                f"Build artifacts ({artifact_gb:.1f}GB):\n" + "\n".join(artifact_log)
            )

        after = shutil.disk_usage("/").free / (1024**3)
        freed = after - before
        disk_threshold = Threshold(name="disk", default=15, clamp=(5, 50))
        disk_threshold.record(prior_load=before, post_response=after, freed_gb=round(freed, 1))
        return LysosomeResult(
            before_gb=round(before, 1),
            after_gb=round(after, 1),
            freed_gb=round(freed, 1),
            output="\n---\n".join(output_parts)[-500:],
        )

    if action == "glycolysis":
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
                f"  Trend ({trend_days}d): {direction}{delta}% ({trend_data[0]['date']} -> {trend_data[-1]['date']})"
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

    if action == "tissue_routing":
        from metabolon.organelles.tissue_routing import observed_routes, route_report

        return TissueRoutingResult(routes=observed_routes(), report=route_report())

    if action == "crispr":
        from pathlib import Path

        from metabolon.organelles.crispr import compile_guides, spacer_count

        spacers_path = Path.home() / ".cache" / "crispr" / "spacers.jsonl"
        count = spacer_count()
        guides = compile_guides()
        recent: list[dict] = []
        if spacers_path.exists():
            try:
                for line in reversed(spacers_path.read_text().splitlines()):
                    stripped = line.strip()
                    if not stripped:
                        continue
                    try:
                        entry = json.loads(stripped)
                    except Exception:
                        continue
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
                pass

        summary_lines = [f"CRISPR spacers: {count} acquired, {len(guides)} guides compiled"]
        if recent:
            summary_lines.append("Recent acquisitions:")
            for item in recent:
                summary_lines.append(f"  [{item['ts']}] {item['tool']}: {item['pattern']}")
        else:
            summary_lines.append("No spacers acquired yet.")
        return CrisprResult(
            spacer_count=count,
            recent=recent,
            guide_count=len(guides),
            summary="\n".join(summary_lines),
        )

    if action == "retrograde":
        from metabolon.organelles.retrograde import signal_balance

        balance = signal_balance(days=days)
        if balance["retrograde_count"] > 0:
            ratio_string = f"{balance['ratio']:.1f}:1"
        else:
            ratio_string = f"{balance['anterograde_count']}:0"
        summary_val = (
            f"Retrograde balance ({days}d): {balance['assessment'].upper()}\n"
            f"  Anterograde (organism→symbiont): {balance['anterograde_count']}\n"
            f"  Retrograde  (symbiont→organism): {balance['retrograde_count']}\n"
            f"  Ratio: {ratio_string}\n"
            f"  Assessment: {balance['assessment']}"
        )
        return RetrogradeResult(
            anterograde_count=balance["anterograde_count"],
            retrograde_count=balance["retrograde_count"],
            ratio=balance["ratio"],
            assessment=balance["assessment"],
            window_days=days,
            summary=summary_val,
        )

    if action == "mitophagy":
        from metabolon.organelles.mitophagy import _load_blacklist, model_fitness

        return MitophagyResult(
            fitness=model_fitness(task_type=task_type, days=days), blacklist=_load_blacklist()
        )

    if action == "angiogenesis":
        from metabolon.organelles.angiogenesis import (
            detect_hypoxia,
            propose_vessel,
            vessel_registry,
        )

        pairs = detect_hypoxia()
        return AngiogenesisResult(
            hypoxic_pairs=pairs,
            proposals=[propose_vessel(pair["source"], pair["target"]) for pair in pairs],
            existing_vessels=vessel_registry(),
        )

    if action == "probe":
        from metabolon.organelles.inflammasome import run_all_probes

        results = run_all_probes()
        lines_probe = []
        for result in results:
            tag = "PASS" if result["passed"] else "FAIL"
            lines_probe.append(
                f"[{tag}] {result['name']} - {result['message']} ({result['duration_ms']}ms)"
            )
        passed_count = sum(1 for result in results if result["passed"])
        lines_probe.append(f"\nSummary: {passed_count}/{len(results)} passed")
        return InflammasomeResult(
            report="\n".join(lines_probe), passed=passed_count, total=len(results)
        )

    return EffectorResult(
        success=False,
        message=f"Unknown action '{action}'. Valid: {_ACTIONS}",
    )
