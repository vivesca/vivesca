
"""hemostasis — Emergency stabilization: stop the bleeding.

Deterministic triage tools for the hemostasis skill:
- List processes matching a pattern (tourniquet candidates)
- Kill a process by name (pkill)
- Unload / load a LaunchAgent by plist path
- Write a handoff note (what was stopped, gaps, next steps)

Root cause analysis, cleanup, and fixing are out of scope.
Clot first, understand second.
"""


import datetime
import platform
import subprocess
from pathlib import Path

from fastmcp.tools.function_tool import tool
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


_ACTIONS = "ps|kill|launchagent|handoff — emergency process stabilization"


@tool(
    name="hemostasis",
    description="Emergency stabilization. Actions: ps|kill|launchagent|handoff",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
)
def hemostasis(
    action: str,
    pattern: str = "",
    signal: str = "TERM",
    plist_path: str = "",
    launchagent_action: str = "unload",
    what_stopped: str = "",
    known_gaps: str = "",
    next_steps: str = "",
) -> ProcessListResult | EffectorResult:
    """Emergency process stabilization.

    Actions:
      ps          List running processes matching a pattern (tourniquet candidates).
      kill        Kill processes matching a name (pkill -f).
      launchagent Load or unload a LaunchAgent plist.
      handoff     Write a hemostasis handoff note.
    """
    action = action.lower().strip()

    # --- ps ---------------------------------------------------------------
    if action == "ps":
        try:
            result = subprocess.run(
                ["pgrep", "-l", "-a", "-f", pattern],
                capture_output=True,
                text=True,
                timeout=5,
            )
            lines = [ln.strip() for ln in result.stdout.splitlines() if ln.strip()]
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

    # --- kill -------------------------------------------------------------
    if action == "kill":
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

    # --- launchagent ------------------------------------------------------
    if action == "launchagent":
        if platform.system() != "Darwin":
            return EffectorResult(
                success=False,
                message=(
                    f"launchctl is not available on {platform.system()}. "
                    "Use `systemctl --user start/stop <service>` instead."
                ),
            )

        la = launchagent_action.lower()
        if la not in ("load", "unload"):
            return EffectorResult(
                success=False,
                message=f"Invalid action '{launchagent_action}'. Use 'load' or 'unload'.",
            )

        path = Path(plist_path).expanduser()
        if not path.exists():
            return EffectorResult(
                success=False,
                message=f"Plist not found: {path}",
            )

        try:
            result = subprocess.run(
                ["launchctl", la, str(path)],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if result.returncode == 0:
                verb = "Unloaded" if la == "unload" else "Loaded"
                return EffectorResult(
                    success=True,
                    message=f"{verb} {path.name}.",
                    data={"path": str(path), "action": la},
                )
            else:
                stderr = result.stderr.strip()
                return EffectorResult(
                    success=False,
                    message=f"launchctl {la} failed (exit {result.returncode}): {stderr}",
                    data={"path": str(path), "action": la, "stderr": stderr},
                )
        except subprocess.TimeoutExpired:
            return EffectorResult(
                success=False,
                message=f"launchctl {la} timed out for {path.name}.",
            )

    # --- handoff ----------------------------------------------------------
    if action == "handoff":
        _HANDOFF_DIR.mkdir(parents=True, exist_ok=True)

        now = datetime.datetime.now()
        filename = now.strftime("hemostasis-%Y-%m-%d-%H%M.md")
        path = _HANDOFF_DIR / filename

        content = f"""---
created: {now.strftime("%Y-%m-%d %H:%M")}
type: hemostasis-handoff
---

# Hemostasis Handoff — {now.strftime("%Y-%m-%d %H:%M")}

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

    # --- unknown action ---------------------------------------------------
    return EffectorResult(
        success=False,
        message=f"Unknown action '{action}'. Use one of: ps, kill, launchagent, handoff.",
    )
