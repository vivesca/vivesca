"""hemostasis — Emergency stabilization: stop the bleeding.

Deterministic triage tools for the hemostasis skill:
- List processes matching a pattern (tourniquet candidates)
- Kill a process by name (pkill)
- Unload / load a LaunchAgent by plist path
- Write a handoff note (what was stopped, gaps, next steps)

Root cause analysis, cleanup, and fixing are out of scope.
Clot first, understand second.
"""

from __future__ import annotations

import datetime
import subprocess
from pathlib import Path

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.locus import chromatin
from metabolon.morphology import EffectorResult, Secretion

_HANDOFF_DIR = chromatin / "System" / "Hemostasis"


class ProcessListResult(Secretion):
    """Running processes matching a pattern."""

    pattern: str
    matches: list[str]
    count: int
    summary: str


@tool(
    name="hemostasis_ps",
    description="List running processes matching a pattern. Tourniquet candidates.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def hemostasis_ps(pattern: str) -> ProcessListResult:
    """List processes whose command line matches pattern.

    Uses pgrep -l -a to show PID + full command. Use this to confirm
    the target before pkill — overtightening the tourniquet is an anti-pattern.

    Args:
        pattern: Process name or partial command to match (passed to pgrep -f).
    """
    try:
        result = subprocess.run(
            ["pgrep", "-l", "-a", "-f", pattern],
            capture_output=True,
            text=True,
            timeout=5,
        )
        lines = [l.strip() for l in result.stdout.splitlines() if l.strip()]
    except subprocess.TimeoutExpired:
        lines = []

    summary = f"Processes matching '{pattern}': {len(lines)} found"
    if lines:
        summary += "\n" + "\n".join(lines)
    else:
        summary += "\n  (none)"

    return ProcessListResult(
        pattern=pattern,
        matches=lines,
        count=len(lines),
        summary=summary,
    )


@tool(
    name="hemostasis_kill",
    description="Kill processes matching name. Tourniquet — stop the bleeding.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
)
def hemostasis_kill(pattern: str, signal: str = "TERM") -> EffectorResult:
    """Kill processes whose command line matches pattern (pkill -f).

    Prefer TERM (graceful) over KILL (force). Use KILL only if TERM doesn't stop it.

    Args:
        pattern: Process name or partial command to match (passed to pkill -f).
        signal: Signal name without SIG prefix: TERM (default), KILL, HUP, INT.
    """
    valid_signals = {"TERM", "KILL", "HUP", "INT", "QUIT", "USR1", "USR2"}
    sig = signal.upper()
    if sig not in valid_signals:
        return EffectorResult(
            success=False,
            message=f"Invalid signal '{signal}'. Use one of: {', '.join(sorted(valid_signals))}",
        )

    try:
        result = subprocess.run(
            ["pkill", f"-{sig}", "-f", pattern],
            capture_output=True,
            text=True,
            timeout=10,
        )
        # pkill exit codes: 0 = matched and killed, 1 = no match, other = error
        if result.returncode == 0:
            return EffectorResult(
                success=True,
                message=f"Sent {sig} to processes matching '{pattern}'.",
                data={"pattern": pattern, "signal": sig},
            )
        elif result.returncode == 1:
            return EffectorResult(
                success=False,
                message=f"No processes found matching '{pattern}'.",
                data={"pattern": pattern, "signal": sig},
            )
        else:
            stderr = result.stderr.strip()
            return EffectorResult(
                success=False,
                message=f"pkill error (exit {result.returncode}): {stderr}",
                data={"pattern": pattern, "signal": sig, "stderr": stderr},
            )
    except subprocess.TimeoutExpired:
        return EffectorResult(
            success=False,
            message=f"pkill timed out for pattern '{pattern}'.",
        )


@tool(
    name="hemostasis_launchagent",
    description="Load or unload a LaunchAgent plist. Pauses a scheduled job.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
)
def hemostasis_launchagent(plist_path: str, action: str = "unload") -> EffectorResult:
    """Load or unload a LaunchAgent via launchctl.

    Unload disables the agent (stops the bleeding). Load re-enables it.
    Pass the full path to the .plist file.

    Args:
        plist_path: Absolute path to the .plist file (e.g. ~/Library/LaunchAgents/com.foo.plist).
        action: 'unload' (default — disable) or 'load' (re-enable).
    """
    action = action.lower()
    if action not in ("load", "unload"):
        return EffectorResult(
            success=False,
            message=f"Invalid action '{action}'. Use 'load' or 'unload'.",
        )

    path = Path(plist_path).expanduser()
    if not path.exists():
        return EffectorResult(
            success=False,
            message=f"Plist not found: {path}",
        )

    try:
        result = subprocess.run(
            ["launchctl", action, str(path)],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            verb = "Unloaded" if action == "unload" else "Loaded"
            return EffectorResult(
                success=True,
                message=f"{verb} {path.name}.",
                data={"path": str(path), "action": action},
            )
        else:
            stderr = result.stderr.strip()
            return EffectorResult(
                success=False,
                message=f"launchctl {action} failed (exit {result.returncode}): {stderr}",
                data={"path": str(path), "action": action, "stderr": stderr},
            )
    except subprocess.TimeoutExpired:
        return EffectorResult(
            success=False,
            message=f"launchctl {action} timed out for {path.name}.",
        )


@tool(
    name="hemostasis_handoff",
    description="Write hemostasis handoff note: what stopped, gaps, next steps.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def hemostasis_handoff(
    what_stopped: str,
    known_gaps: str,
    next_steps: str,
) -> EffectorResult:
    """Write a hemostasis handoff note to the vault.

    Required before leaving hemostasis mode. The note prevents secondary
    hemorrhage when someone unknowingly restarts the stopped process.

    Args:
        what_stopped: What was stopped and why (1-3 sentences).
        known_gaps: What is currently broken as a result of stopping.
        next_steps: What the next person / session needs to do to resume.
    """
    _HANDOFF_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.datetime.now()
    filename = now.strftime("hemostasis-%Y-%m-%d-%H%M.md")
    path = _HANDOFF_DIR / filename

    content = f"""---
created: {now.strftime('%Y-%m-%d %H:%M')}
type: hemostasis-handoff
---

# Hemostasis Handoff — {now.strftime('%Y-%m-%d %H:%M')}

## What Was Stopped
{what_stopped}

## Known Gaps (currently broken)
{known_gaps}

## Next Steps (to resume)
{next_steps}
"""

    path.write_text(content, encoding="utf-8")

    return EffectorResult(
        success=True,
        message=f"Handoff note written to {path}.",
        data={"path": str(path)},
    )
