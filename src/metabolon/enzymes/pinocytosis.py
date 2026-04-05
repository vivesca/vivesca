"""pinocytosis — deterministic context gathering and overnight summaries."""

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastmcp.tools.function_tool import tool
from mcp.types import ToolAnnotations

from metabolon.locus import chromatin as CHROMATIN
from metabolon.morphology import EffectorResult, Secretion

HKT = timezone(timedelta(hours=8))
NOW_MD = CHROMATIN / "NOW.md"
JOB_HUNT_DIR = CHROMATIN / "Job Hunting"
NIGHTLY_HEALTH = Path.home() / ".claude" / "nightly-health.md"
SKILL_FLYWHEEL = Path.home() / ".claude" / "skill-flywheel-daily.md"


class PinocytosisResult(Secretion):
    output: str


def _hkt_now() -> datetime:
    return datetime.now(HKT)


def _read_if_fresh(path: Path, max_age_hours: int = 24) -> str | None:
    try:
        if not path.exists():
            return None
        import time

        age_hours = (time.time() - path.stat().st_mtime) / 3600
        if age_hours > max_age_hours:
            return None
        return path.read_text().strip()
    except Exception:
        return None


def _read_now_md() -> str:
    if not NOW_MD.exists():
        return "NOW.md not found."
    try:
        text = NOW_MD.read_text()
    except Exception as exc:
        return f"NOW.md read error: {exc}"
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        lower = stripped.lower()
        if any(marker in lower for marker in ["[decided]", "[done]", "[x]", "- [x]"]):
            continue
        lines.append(stripped)
    if not lines:
        return "NOW.md: no open items."
    return "NOW.md open items:\n" + "\n".join(f"  {line}" for line in lines[:20])


def _count_job_alerts() -> str:
    today_string = _hkt_now().strftime("%Y-%m-%d")
    alert_file = JOB_HUNT_DIR / f"Job Alerts {today_string}.md"
    if not alert_file.exists():
        candidates = sorted(JOB_HUNT_DIR.glob("Job Alerts *.md"))
        if not candidates:
            return "No job alert files found."
        alert_file = candidates[-1]
    try:
        text = alert_file.read_text()
        unchecked = len(re.findall(r"^- \[ \]", text, re.MULTILINE))
        total = len(re.findall(r"^- \[[ x]\]", text, re.MULTILINE))
        return f"Job alerts ({alert_file.name}): {unchecked}/{total} unchecked."
    except Exception as exc:
        return f"Job alerts read error: {exc}"


def _read_efferens() -> str:
    try:
        import acta

        messages = getattr(acta, "read", lambda: [])()
    except Exception as exc:
        return f"Efferens unavailable: {exc}"
    if not messages:
        return "Efferens: board empty."
    lines = [f"Efferens ({len(messages)} message(s)):"]
    for message in messages[:5]:
        severity = message.get("severity", "info")
        sender = message.get("from", "?")
        body = message.get("body", "")[:80].replace("\n", " ")
        lines.append(f"  [{severity}] {sender}: {body}")
    return "\n".join(lines)


def _count_goose_tasks() -> str:
    try:
        done_dir = CHROMATIN / "task-queue" / "done"
        if not done_dir.exists():
            return "Goose tasks: 0 ready for review."
        count = sum(1 for _ in done_dir.glob("*.md"))
        if count == 0:
            return "Goose tasks: 0 ready for review."
        return f"Goose tasks: {count} ready for review."
    except Exception as exc:
        return f"Goose tasks read error: {exc}"


def _read_praxis_today() -> str:
    try:
        from metabolon.organelles import praxis

        data = praxis.today()
    except Exception as exc:
        return f"Praxis unavailable: {exc}"
    items = []
    for group in ("overdue", "today"):
        for item in data.get(group, []):
            label = item.get("text") or item.get("title", "")
            due = item.get("due", "")
            items.append(f"  [{group}] {label}" + (f" (due {due})" if due else ""))
    if not items:
        return "Praxis: nothing due today."
    return "Praxis (today/overdue):\n" + "\n".join(items[:5])


def _day_snapshot(json_output: bool) -> PinocytosisResult:
    now = _hkt_now()
    time_string = now.strftime("%I:%M%p %A %Y-%m-%d HKT").lstrip("0")
    sections = {
        "time": time_string,
        "now_md": _read_now_md(),
        "praxis": _read_praxis_today(),
        "efferens": _read_efferens(),
        "goose_tasks": _count_goose_tasks(),
    }
    if now.hour >= 12:
        sections["job_alerts"] = _count_job_alerts()
    else:
        sections["job_alerts"] = f"Job alerts: skipped (pre-noon, {time_string})."
    if json_output:
        return PinocytosisResult(output=json.dumps(sections, ensure_ascii=False, indent=2))
    parts = [f"Situational snapshot @ {time_string}", ""]
    for key in ("now_md", "praxis", "efferens", "job_alerts", "goose_tasks"):
        parts.append(sections[key])
        parts.append("")
    return PinocytosisResult(output="\n".join(parts).strip())


def _entrainment_brief() -> PinocytosisResult:
    alerts: list[str] = []
    try:
        from metabolon.organelles.chemoreceptor import sense

        data = sense()
        if "error" in data:
            sleep = f"sopor error: {data['error']}"
        else:
            parts = []
            if data.get("sleep_score") is not None:
                parts.append(f"Sleep: {data['sleep_score']}")
            if data.get("readiness_score") is not None:
                parts.append(f"Readiness: {data['readiness_score']}")
            if data.get("spo2", {}).get("average") is not None:
                parts.append(f"SpO2: {data['spo2']['average']}%")
            if data.get("resilience", {}).get("level"):
                parts.append(f"Resilience: {data['resilience']['level']}")
            if data.get("stress", {}).get("day_summary"):
                parts.append(f"Stress: {data['stress']['day_summary']}")
            if data.get("total_sleep_duration") is not None:
                parts.append(f"Total sleep: {data['total_sleep_duration'] / 3600:.1f}h")
            if data.get("efficiency") is not None:
                parts.append(f"Efficiency: {data['efficiency']}%")
            if data.get("average_heart_rate") is not None:
                parts.append(f"Avg HR: {data['average_heart_rate']} bpm")
            if data.get("average_hrv") is not None:
                parts.append(f"Avg HRV: {data['average_hrv']} ms")
            if data.get("lowest_heart_rate") is not None:
                parts.append(f"Lowest HR: {data['lowest_heart_rate']} bpm")
            if data.get("activity", {}).get("steps") is not None:
                parts.append(f"Steps: {data['activity']['steps']}")
            sleep = " | ".join(parts) if parts else "No Oura data for today"
            readiness_value = data.get("readiness_score")
            if readiness_value is not None and readiness_value < 65:
                alerts.append(f"Low readiness ({readiness_value}) -- consider an easier day")
    except Exception:
        sleep = "sopor unavailable"

    overnight_parts = []
    health = _read_if_fresh(NIGHTLY_HEALTH)
    if health:
        warning_lines = [
            line
            for line in health.splitlines()
            if "warning" in line.lower() or "red" in line.lower()
        ]
        if warning_lines:
            overnight_parts.append("System health: " + "; ".join(warning_lines[:3]))
        else:
            overnight_parts.append("System health: all green")
    flywheel = _read_if_fresh(SKILL_FLYWHEEL)
    if flywheel:
        miss_lines = [
            line for line in flywheel.splitlines() if "miss" in line.lower() or "0%" in line
        ]
        if miss_lines:
            overnight_parts.append("Skill routing: " + "; ".join(miss_lines[:3]))
    try:
        from metabolon.cytosol import VIVESCA_ROOT, invoke_organelle

        kinesin_output = invoke_organelle(
            str(VIVESCA_ROOT / "effectors" / "overnight-gather"),
            ["brief"],
            timeout=15,
        )
        if "NEEDS_ATTENTION" in kinesin_output or "CRITICAL" in kinesin_output:
            attention = [
                line
                for line in kinesin_output.splitlines()
                if "NEEDS_ATTENTION" in line or "CRITICAL" in line
            ]
            overnight_parts.extend(attention[:3])
            alerts.extend(attention[:3])
        elif kinesin_output.strip():
            overnight_parts.append(kinesin_output[:200])
    except Exception:
        pass
    overnight = "\n".join(overnight_parts) if overnight_parts else "No overnight data"
    output = f"Sleep\n{sleep}\n\nOvernight\n{overnight}"
    if alerts:
        output += "\n\nAlerts\n" + "\n".join(alerts)
    return PinocytosisResult(output=output)


def _overnight_results(task: str) -> PinocytosisResult:
    from metabolon.cytosol import VIVESCA_ROOT, invoke_organelle

    args = ["results"]
    if task:
        args.extend(["--task", task])
    return PinocytosisResult(
        output=invoke_organelle(
            str(VIVESCA_ROOT / "effectors" / "overnight-gather"), args, timeout=15
        )
    )


def _overnight_list() -> PinocytosisResult:
    from metabolon.cytosol import VIVESCA_ROOT, invoke_organelle

    return PinocytosisResult(
        output=invoke_organelle(
            str(VIVESCA_ROOT / "effectors" / "overnight-gather"), ["list"], timeout=15
        )
    )


@tool(
    name="pinocytosis",
    description="Circadian context intake. Actions: morning|day|evening|weekly|overnight|results|list",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def pinocytosis(
    action: str,
    json_output: bool = True,
    send_weather: bool = False,
    task: str = "",
) -> PinocytosisResult | EffectorResult:
    action = action.lower().strip()

    if action == "morning":
        from metabolon.pinocytosis import photoreception

        return PinocytosisResult(
            output=photoreception.intake(as_json=json_output, send_weather=send_weather)
        )
    if action == "day":
        return _day_snapshot(json_output)
    if action == "evening":
        from metabolon.pinocytosis import interphase

        return PinocytosisResult(output=interphase.intake(as_json=json_output))
    if action == "weekly":
        from metabolon.pinocytosis import ecdysis

        return PinocytosisResult(output=ecdysis.intake(as_json=json_output))
    if action == "overnight":
        return _entrainment_brief()
    if action == "overnight_results":
        return _overnight_results(task)
    if action == "overnight_list":
        return _overnight_list()
    return EffectorResult(
        success=False,
        message=(
            "Unknown action. Valid: morning, day, evening, weekly, overnight, "
            "overnight_results, overnight_list"
        ),
    )
