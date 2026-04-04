
import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

DEFAULT_LOG_PATH = Path.home() / ".local" / "share" / "sortase" / "log.jsonl"
DEFAULT_COACHING_PATH = Path.home() / "epigenome" / "marks" / "feedback_golem_coaching.md"
AUTO_DETECTED_COMMENT = re.compile(r"<!--\s*auto-detected\s+(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\s*-->")
COACHING_REASON_TERMS: dict[str, set[str]] = {
    "tests": {"test", "tests", "pytest", "verification"},
    "placeholder-scan": {"placeholder", "todo", "fixme", "stub"},
    "quota": {"429", "quota", "rate", "limit"},
    "auth": {"auth", "authentication", "identity", "credential", "credentials"},
    "sandbox": {"sandbox", "permission", "permitted"},
    "process-error": {"process", "execution", "exit", "error"},
}
GENERIC_REASON_TERMS = {"error", "failure", "process", "execution", "scan", "unknown"}


def resolve_log_path(path: str | os.PathLike[str] | None = None) -> Path:
    if path:
        return Path(path)
    override = os.environ.get("OPIFEX_LOG_PATH")
    return Path(override) if override else DEFAULT_LOG_PATH


def append_log(entry: dict[str, Any], path: str | os.PathLike[str] | None = None) -> Path:
    log_path = resolve_log_path(path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")
    return log_path


def read_logs(path: str | os.PathLike[str] | None = None) -> list[dict[str, Any]]:
    log_path = resolve_log_path(path)
    if not log_path.exists():
        return []
    entries: list[dict[str, Any]] = []
    with log_path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def _parse_iso_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _strip_frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return text
    parts = text.split("---", 2)
    if len(parts) == 3:
        return parts[2]
    return text


def _failure_reason_terms(reason: str) -> set[str]:
    normalized_reason = reason.strip().lower()
    if not normalized_reason:
        return {"unknown"}

    terms = set(re.findall(r"[a-z0-9]+", normalized_reason))
    terms.update(COACHING_REASON_TERMS.get(normalized_reason, set()))
    meaningful_terms = {term for term in terms if term not in GENERIC_REASON_TERMS}
    return meaningful_terms or terms or {"unknown"}


def _extract_coaching_notes(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    text = _strip_frontmatter(path.read_text(encoding="utf-8"))
    fallback_added_at = datetime.fromtimestamp(path.stat().st_mtime)
    note_entries: list[dict[str, Any]] = []
    current_heading: str | None = None
    current_lines: list[str] = []
    current_added_at = fallback_added_at
    pending_added_at = fallback_added_at

    def flush_current() -> None:
        nonlocal current_heading, current_lines, current_added_at
        if current_heading is None:
            return
        note_text = "\n".join([current_heading, *current_lines]).strip()
        if note_text:
            note_entries.append(
                {
                    "text": note_text.lower(),
                    "added_at": current_added_at,
                }
            )
        current_heading = None
        current_lines = []
        current_added_at = fallback_added_at

    for line in text.splitlines():
        timestamp_match = AUTO_DETECTED_COMMENT.search(line)
        if timestamp_match:
            pending_added_at = datetime.strptime(timestamp_match.group(1), "%Y-%m-%d %H:%M")
            continue

        if line.startswith("### "):
            flush_current()
            current_heading = line[4:].strip()
            current_added_at = pending_added_at
            pending_added_at = fallback_added_at
            continue

        if current_heading is not None:
            current_lines.append(line)

    flush_current()
    return note_entries


def _failure_has_relevant_coaching(
    failure_reason: str,
    failure_time: datetime,
    coaching_notes: list[dict[str, Any]],
) -> bool:
    reason_terms = _failure_reason_terms(failure_reason)
    for note in coaching_notes:
        note_text = note["text"]
        if not any(term in note_text for term in reason_terms):
            continue
        note_added_at = note["added_at"]
        if failure_time >= note_added_at:
            return True
    return False


def _file_count(entry: dict[str, Any]) -> int:
    files_changed = entry.get("files_changed", 0)
    if isinstance(files_changed, list):
        return len([value for value in files_changed if str(value).strip()])
    if isinstance(files_changed, (int, float)):
        return max(0, int(files_changed))
    return 0


def aggregate_stats(entries: list[dict[str, Any]]) -> dict[str, Any]:
    now = datetime.now()
    cutoff_24h = (now - timedelta(hours=24)).isoformat()

    tool_totals: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"runs": 0, "successes": 0, "durations": [], "last_24h": 0, "coaching_triggers": 0}
    )
    failure_reasons: Counter[str] = Counter()
    fallback_frequency: Counter[str] = Counter()

    for entry in entries:
        tool = entry.get("tool", "unknown")
        bucket = tool_totals[tool]
        bucket["runs"] += 1
        bucket["successes"] += 1 if entry.get("success") else 0
        d = entry.get("duration_s", 0)
        if d:
            bucket["durations"].append(float(d))

        if entry.get("timestamp", "") >= cutoff_24h:
            bucket["last_24h"] += 1
        if entry.get("failure_reason"):
            bucket["coaching_triggers"] += 1

        for fallback in entry.get("fallbacks", []) or []:
            fallback_frequency[fallback] += 1

        if not entry.get("success"):
            failure_reasons[entry.get("failure_reason", "unknown")] += 1

    per_tool = {}
    for tool, details in tool_totals.items():
        durations = sorted(details["durations"])
        n = len(durations)
        runs = details["runs"]
        per_tool[tool] = {
            "runs": runs,
            "success_rate": round(details["successes"] / runs, 3) if runs else 0.0,
            "avg_duration_s": round(sum(durations) / n, 1) if n else 0.0,
            "p50_duration_s": round(durations[n // 2], 1) if n else 0.0,
            "p90_duration_s": round(durations[int(n * 0.9)], 1) if n else 0.0,
            "last_24h": details["last_24h"],
            "coaching_triggers": details["coaching_triggers"],
        }

    return {
        "per_tool": per_tool,
        "failure_reasons": dict(failure_reasons.most_common()),
        "fallback_frequency": dict(fallback_frequency.most_common()),
        "total_runs": len(entries),
    }


def analyze_logs(
    log_path: str | os.PathLike[str] | None = None,
    coaching_path: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """Analyze log.jsonl for patterns: success rates, durations, failures, coaching coverage.

    Returns a dict with keys:
      - success_rate_by_backend: {tool: float}
      - entries_by_backend: {tool: int}
      - success_rate_by_hour: {HH: float}
      - entries_by_hour: {HH: int}
      - avg_duration_by_plan_complexity: {file_count: float}
      - failure_reasons: {reason: count}
      - coaching_coverage: float | None (None when no failures exist)
      - coaching_gap: float | None (None when no failures exist)
      - total_entries: int
    """
    entries = read_logs(log_path)
    if not entries:
        return {
            "success_rate_by_backend": {},
            "entries_by_backend": {},
            "success_rate_by_hour": {},
            "entries_by_hour": {},
            "avg_duration_by_plan_complexity": {},
            "failure_reasons": {},
            "coaching_coverage": None,
            "coaching_gap": None,
            "coaching_failures_with_prior_note": 0,
            "coaching_failures_without_prior_note": 0,
            "total_entries": 0,
        }

    backend_runs: dict[str, dict[str, int]] = defaultdict(lambda: {"runs": 0, "successes": 0})
    hour_runs: dict[str, dict[str, int]] = defaultdict(lambda: {"runs": 0, "successes": 0})
    complexity_durations: dict[int, list[float]] = defaultdict(list)
    failure_reasons: Counter[str] = Counter()
    failure_events: list[dict[str, Any]] = []

    for entry in entries:
        tool = entry.get("tool", "unknown")
        backend_runs[tool]["runs"] += 1
        if entry.get("success"):
            backend_runs[tool]["successes"] += 1

        timestamp = _parse_iso_timestamp(entry.get("timestamp"))
        if timestamp is not None:
            hour_key = timestamp.strftime("%H")
            hour_runs[hour_key]["runs"] += 1
            if entry.get("success"):
                hour_runs[hour_key]["successes"] += 1

        duration = entry.get("duration_s", 0)
        if duration:
            complexity_durations[_file_count(entry)].append(float(duration))

        if not entry.get("success"):
            reason = entry.get("failure_reason") or "unknown"
            failure_reasons[reason] += 1
            if timestamp is not None:
                failure_events.append({"reason": reason, "timestamp": timestamp})

    success_rate_by_backend: dict[str, float] = {}
    entries_by_backend: dict[str, int] = {}
    for tool, counts in backend_runs.items():
        runs = counts["runs"]
        entries_by_backend[tool] = runs
        success_rate_by_backend[tool] = round(counts["successes"] / runs, 3) if runs else 0.0

    success_rate_by_hour: dict[str, float] = {}
    entries_by_hour: dict[str, int] = {}
    for hour, counts in sorted(hour_runs.items()):
        runs = counts["runs"]
        entries_by_hour[hour] = runs
        success_rate_by_hour[hour] = round(counts["successes"] / runs, 3) if runs else 0.0

    avg_duration_by_plan_complexity: dict[int, float] = {}
    for file_count, durations in sorted(complexity_durations.items()):
        n = len(durations)
        avg_duration_by_plan_complexity[file_count] = round(sum(durations) / n, 1) if n else 0.0

    coaching_coverage: float | None = None
    coaching_gap: float | None = None
    failures_with_prior_note = 0
    failures_without_prior_note = 0
    if failure_events:
        resolved_coaching = Path(coaching_path) if coaching_path else DEFAULT_COACHING_PATH
        coaching_notes = _extract_coaching_notes(resolved_coaching)
        for failure_event in failure_events:
            if _failure_has_relevant_coaching(
                failure_reason=failure_event["reason"],
                failure_time=failure_event["timestamp"],
                coaching_notes=coaching_notes,
            ):
                failures_with_prior_note += 1
            else:
                failures_without_prior_note += 1

        total_failures = len(failure_events)
        coaching_coverage = round(failures_with_prior_note / total_failures, 3)
        coaching_gap = round(failures_without_prior_note / total_failures, 3)

    return {
        "success_rate_by_backend": success_rate_by_backend,
        "entries_by_backend": entries_by_backend,
        "success_rate_by_hour": success_rate_by_hour,
        "entries_by_hour": entries_by_hour,
        "avg_duration_by_plan_complexity": avg_duration_by_plan_complexity,
        "failure_reasons": dict(failure_reasons.most_common()),
        "coaching_coverage": coaching_coverage,
        "coaching_gap": coaching_gap,
        "coaching_failures_with_prior_note": failures_with_prior_note,
        "coaching_failures_without_prior_note": failures_without_prior_note,
        "total_entries": len(entries),
    }
