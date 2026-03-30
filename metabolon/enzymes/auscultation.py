"""auscultation — deterministic log reading for system diagnostics.

Exposes the listening surfaces the auscultation skill taps:
  auscultation    — System log diagnostics. Actions: logs|errors
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

_LOG_DIR = Path.home() / "Library" / "Logs" / "vivesca"
_TMP_DIR = Path.home() / "tmp"


def _read_log_lines(path: Path, n: int = 200) -> list[str]:
    """Read last N lines from a log file."""
    try:
        text = path.read_text(errors="replace")
        return text.splitlines()[-n:]
    except Exception:
        return []


def _glob_logs() -> list[Path]:
    """Return all .log files in ~/Library/Logs/vivesca/ + ~/tmp/*.log."""
    logs = sorted(_LOG_DIR.glob("*.log")) if _LOG_DIR.exists() else []
    logs += sorted(_TMP_DIR.glob("*.log")) if _TMP_DIR.exists() else []
    return logs


@tool(
    name="auscultation",
    description="System log diagnostics. Actions: logs|errors",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def auscultation(
    action: str,
    filter_pattern: str = "",
    tail_lines: int = 100,
    log_name: str = "",
    severity: str = "ERROR|WARN|FAIL",
    top_n: int = 20,
    normalize_numbers: bool = True,
) -> str:
    """Read recent log lines from ~/Library/Logs/vivesca/*.log.

    Args:
        action: 'logs' or 'errors'.
        filter_pattern: Optional regex to filter lines (e.g. 'ERROR|WARN').
        tail_lines: How many lines to read from each log (default 100).
        log_name: Specific log filename (without path) to read. Empty = all logs.
        severity: Pipe-separated severities to match (default 'ERROR|WARN|FAIL').
        top_n: Return top N patterns by frequency (default 20).
        normalize_numbers: Strip numbers before counting to collapse similar errors.
    """
    action = action.lower().strip()
    if action == "logs":
        logs = _glob_logs()
        if not logs:
            return "No log files found in ~/Library/Logs/vivesca/ or ~/tmp/"

        if log_name:
            logs = [lg for lg in logs if lg.name == log_name]
            if not logs:
                return f"Log not found: {log_name}"

        pat = re.compile(filter_pattern, re.IGNORECASE) if filter_pattern else None

        output_parts: list[str] = []
        for log in logs:
            lines = _read_log_lines(log, tail_lines)
            if pat:
                lines = [ln for ln in lines if pat.search(ln)]
            if not lines:
                continue
            output_parts.append(f"=== {log.name} ({len(lines)} lines) ===")
            output_parts.extend(lines)

        if not output_parts:
            qualifier = f" matching '{filter_pattern}'" if filter_pattern else ""
            return f"No log lines{qualifier} found."

        return "\n".join(output_parts)
    elif action == "errors":
        logs = _glob_logs()
        if not logs:
            return "No log files found."

        pat = re.compile(severity, re.IGNORECASE)
        digit_pat = re.compile(r"\d+") if normalize_numbers else None

        error_lines: list[str] = []
        for log in logs:
            try:
                text = log.read_text(errors="replace")
                for line in text.splitlines():
                    if pat.search(line):
                        error_lines.append(line)
            except Exception:
                continue

        if not error_lines:
            return f"No lines matching '{severity}' found. System sounds healthy."

        # Normalise for counting
        def _normalise(line: str) -> str:
            # Strip timestamps (common formats)
            line = re.sub(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}[^\s]*", "", line)
            if digit_pat:
                line = digit_pat.sub("N", line)
            return line.strip()

        counts: Counter = Counter(_normalise(ln) for ln in error_lines)
        total = len(error_lines)

        lines = [f"Error frequency analysis ({total} total error lines across {len(logs)} logs):"]
        lines.append(f"{'Count':>6}  Pattern")
        lines.append("-" * 60)
        for pattern, count in counts.most_common(top_n):
            lines.append(f"{count:>6}  {pattern[:100]}")

        return "\n".join(lines)
    else:
        return f"Unknown action: {action}. Use: logs|errors"
