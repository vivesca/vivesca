"""checkpoint — homeostatic monitoring + system health.

Tools:
  circadian_sleep      — circadian rhythm data from Oura
  membrane_potential   — readiness score + exercise recommendation
  homeostasis_system   — pulse status, budget, disk pressure, hook health
  homeostasis_financial — vault financial health: deadlines, overdue items
  lysosome_digest      — digest disk caches when pressure is high
  nociception_log      — log a pain/symptom signal to vault
  anabolism_flywheel   — anabolic flywheel: are the links reinforcing?
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

from metabolon.cytosol import invoke_organelle, synthesize
from metabolon.metabolism.mismatch_repair import summary as precision_summary
from metabolon.metabolism.setpoint import Threshold
from metabolon.morphology import EffectorResult, Secretion

SOPOR = "sopor"
HEALTH_LOG = os.path.expanduser("~/code/epigenome/chromatin/Health/Symptom Log.md")

disk_threshold = Threshold(name="disk", default=15, clamp=(5, 50))


class CircadianResult(Secretion):
    """Circadian rhythm data from Oura."""

    summary: str


class MembranePotentialResult(Secretion):
    """Membrane potential — readiness with exercise guidance."""

    summary: str
    guidance: str


class HomeostasisResult(Secretion):
    """Homeostatic system check results."""

    sections: list[str]


@tool(
    name="circadian_sleep",
    description="Oura sleep data. 'today' for last night, 'week' for trend.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def circadian_sleep(period: str = "today") -> CircadianResult:
    """Read circadian rhythm data with chemoreceptor-style threshold alerts."""
    from metabolon.organelles.chemoreceptor import sense

    result = sense().get("formatted", str(sense()))

    # Chemoreceptor: detect specific signals against thresholds
    alerts = []
    sleep_m = re.search(r"Sleep Score:\s*(\d+)", result)
    ready_m = re.search(r"Readiness:\s*(\d+)", result)
    hrv_m = re.search(r"HRV.*?(\d+)", result)

    if sleep_m and int(sleep_m.group(1)) < 70:
        alerts.append(f"SLEEP LOW ({sleep_m.group(1)}): below 70 threshold")
    if ready_m and int(ready_m.group(1)) < 70:
        alerts.append(f"READINESS LOW ({ready_m.group(1)}): light activity only")
    if hrv_m and int(hrv_m.group(1)) < 20:
        alerts.append(f"HRV LOW ({hrv_m.group(1)}): recovery priority")

    if alerts:
        result = "--- Chemoreceptor alerts ---\n" + "\n".join(alerts) + "\n\n" + result

    return CircadianResult(summary=result)


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
        from metabolon.organelles.respiration_sensor import sense

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

FINANCIAL_PROMPT_TEMPLATE = """Review the financial vault notes below and Praxis.md excerpt.

For each item: status (done/in-progress/overdue/upcoming), deadline, next step.
Flag anything overdue or due within 14 days. Sort by urgency. Be concise.

Today: {today}

--- VAULT NOTES ---
{notes}

--- PRAXIS (financial items) ---
{praxis}
"""


class HomeostasisFinancialResult(Secretion):
    """Financial health status from vault notes."""

    summary: str
    flagged_count: int


@tool(
    name="homeostasis_financial",
    description="Vault financial health: deadlines, overdue items, next steps.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def homeostasis_financial() -> HomeostasisFinancialResult:
    """Read vault financial notes and flag overdue or upcoming items (within 14 days)."""
    import datetime

    notes_dir = os.path.expanduser("~/code/epigenome/chromatin/")
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
    praxis_path = os.path.expanduser("~/code/epigenome/chromatin/Praxis.md")
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


@tool(
    name="nociception_log",
    description="Log a symptom to vault health log.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def nociception_log(symptom: str, severity: str = "mild", notes: str = "") -> EffectorResult:
    """Log a nociceptive signal to the vault."""
    today = datetime.date.today().isoformat()
    entry = f"\n## {today} — {symptom}\n- Severity: {severity}\n"
    if notes:
        entry += f"- Notes: {notes}\n"

    os.makedirs(os.path.dirname(HEALTH_LOG), exist_ok=True)
    with open(HEALTH_LOG, "a") as f:
        f.write(entry)

    return EffectorResult(success=True, message=f"Logged: {symptom} ({severity}) on {today}")


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
        sopor_out = invoke_organelle(SOPOR, ["today"], timeout=15)

        # Sleep
        sleep_match = re.search(r"Sleep Score:\s*(\d+)", sopor_out)
        if sleep_match:
            score = int(sleep_match.group(1))
            links.append({"name": "sleep", "score": score})
        else:
            links.append({"name": "sleep", "score": None})

        # Energy
        energy_match = re.search(r"Readiness:\s*(\d+)", sopor_out)
        if energy_match:
            readiness = int(energy_match.group(1))
            links.append({"name": "energy", "score": readiness})
        else:
            links.append({"name": "energy", "score": None})

    except Exception:
        links.append({"name": "sleep", "score": None})
        links.append({"name": "energy", "score": None})

    # 3. Calendar load
    try:
        from metabolon.organelles.circadian_clock import list_events

        fasti_out = list_events()
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
        notes_dir = os.path.expanduser("~/code/epigenome/chromatin/")

        vault_cmd = ["git", "log", "--since=7.days", "--oneline"]
        vault_out = subprocess.run(
            vault_cmd, cwd=notes_dir, capture_output=True, text=True, timeout=10
        )
        vault_commits = (
            len(vault_out.stdout.strip().splitlines()) if vault_out.stdout.strip() else 0
        )

        blog_cmd = ["git", "log", "--since=14.days", "--oneline", "--", "Writing/Blog/Published/"]
        blog_out = subprocess.run(
            blog_cmd, cwd=notes_dir, capture_output=True, text=True, timeout=10
        )
        blog_posts = len(blog_out.stdout.strip().splitlines()) if blog_out.stdout.strip() else 0

        links.append(
            {
                "name": "creative",
                "vault_commits_7d": vault_commits,
                "blog_commits_14d": blog_posts,
            }
        )
    except Exception:
        links.append({"name": "creative", "vault_commits_7d": None, "blog_commits_14d": None})

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
