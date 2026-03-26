"""AnamScanSubstrate -- cross-session transcript pattern recognition.

The forgetting/synthesis layer. Senses anam transcripts for repeated
corrections, recurring topics, and unused memories. Complements
within-session capture (nociception, hebbian nudge, telophase) with
cross-session pattern detection.

Design: ~/germline/loci/copia/cross-session-scanner-design-2026-03-23.md
Architecture: ~/germline/loci/pulse/transcript-scan-architecture-2026-03-24.md
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ANAM_SCAN = Path.home() / "germline" / "effectors" / "anam-scan"


def _run(
    cmd: list[str],
    timeout: int = 300,
) -> subprocess.CompletedProcess[str]:
    """Run a command, return CompletedProcess. Never raises."""
    try:
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(
            args=cmd, returncode=1, stdout="", stderr=f"timeout after {timeout}s"
        )
    except FileNotFoundError:
        return subprocess.CompletedProcess(
            args=cmd, returncode=1, stdout="", stderr=f"not found: {cmd[0]}"
        )


class AnamScanSubstrate:
    """Transcript-level substrate: cross-session pattern recognition.

    Senses Claude Code transcripts for repeated corrections, recurring
    topics, and emergent clusters. The forgetting/synthesis layer --
    detects what the organism should remember, forget, or build.
    """

    name: str = "anam_scan"

    def sense(self, days: int = 7) -> list[dict]:
        """Pull transcript signals by running anam-scan --dry-run.

        Uses dry-run mode to get session/correction counts without
        invoking LLM calls (those happen in act()).
        """
        result = _run(
            [sys.executable, str(ANAM_SCAN), "--days", str(days), "--dry-run"],
        )
        if result.returncode != 0:
            return [{"kind": "error", "message": result.stderr[:200]}]

        # Parse dry-run output for counts
        output = result.stdout
        signals: list[dict] = []
        for line in output.splitlines():
            line = line.strip()
            if line.startswith("Sessions:"):
                try:
                    count = int(line.split(":")[1].strip())
                    signals.append({"kind": "sessions", "count": count})
                except (ValueError, IndexError):
                    pass
            elif line.startswith("Corrections:"):
                parts = line.split("across")
                try:
                    total = int(parts[0].split(":")[1].strip())
                    sessions = int(parts[1].strip().split()[0]) if len(parts) > 1 else 0
                    signals.append({
                        "kind": "corrections",
                        "total": total,
                        "sessions": sessions,
                    })
                except (ValueError, IndexError):
                    pass
            elif line.startswith("Session prompts:"):
                try:
                    count = int(line.split(":")[1].strip())
                    signals.append({"kind": "session_prompts", "count": count})
                except (ValueError, IndexError):
                    pass

        return signals if signals else [{"kind": "no_data", "message": "No sessions found"}]

    def candidates(self, sensed: list[dict]) -> list[dict]:
        """Identify when a scan run is warranted.

        Threshold: at least 5 sessions with corrections, or at least
        10 sessions total (to make topic extraction worthwhile).
        """
        actionable: list[dict] = []

        corrections = next((s for s in sensed if s.get("kind") == "corrections"), None)
        sessions = next((s for s in sensed if s.get("kind") == "sessions"), None)

        if corrections and corrections.get("sessions", 0) >= 5:
            actionable.append({
                "action": "daily_scan",
                "reason": f"{corrections['sessions']} sessions with corrections",
                "priority": "high" if corrections["sessions"] >= 10 else "normal",
            })
        elif sessions and sessions.get("count", 0) >= 10:
            actionable.append({
                "action": "daily_scan",
                "reason": f"{sessions['count']} sessions to scan for topics",
                "priority": "normal",
            })

        # Check if it's Sunday for weekly synthesis
        from datetime import date as date_cls
        if date_cls.today().weekday() == 6:  # Sunday
            actionable.append({
                "action": "weekly_synthesis",
                "reason": "Sunday weekly synthesis window",
                "priority": "normal",
            })

        return actionable

    def act(self, candidate: dict) -> str:
        """Execute the scan (daily or weekly)."""
        action = candidate.get("action", "daily_scan")

        if action == "weekly_synthesis":
            result = _run(
                [sys.executable, str(ANAM_SCAN), "--weekly"],
                timeout=300,
            )
        else:
            result = _run(
                [sys.executable, str(ANAM_SCAN), "--days", "1"],
                timeout=300,
            )

        if result.returncode == 0:
            return f"completed: {action} -- {result.stdout.splitlines()[-1] if result.stdout else 'done'}"
        return f"failed: {action} -- {result.stderr[:200]}"

    def report(self, sensed: list[dict], acted: list[str]) -> str:
        """Format a human-readable scan report."""
        lines: list[str] = []
        lines.append("Anam scan substrate report")
        lines.append("")

        sessions = next((s for s in sensed if s.get("kind") == "sessions"), None)
        corrections = next((s for s in sensed if s.get("kind") == "corrections"), None)
        prompts = next((s for s in sensed if s.get("kind") == "session_prompts"), None)

        if sessions:
            lines.append(f"-- Sessions: {sessions['count']} --")
        if corrections:
            lines.append(
                f"-- Corrections: {corrections['total']} across "
                f"{corrections['sessions']} sessions --"
            )
        if prompts:
            lines.append(f"-- Prompt sets: {prompts['count']} --")

        if acted:
            lines.append("\n-- Actions --")
            for action in acted:
                lines.append(f"  {action}")

        return "\n".join(lines)
