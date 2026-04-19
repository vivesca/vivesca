"""Tests for axon.py git merge guard — deny remote merge without prior diff check."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

AXON = Path.home() / "germline" / "membrane" / "cytoskeleton" / "axon.py"


def _run_axon(command: str) -> dict:
    """Simulate a PreToolUse Bash event and return axon's JSON output."""
    event = {
        "tool": "Bash",
        "tool_input": {"command": command},
    }
    proc = subprocess.run(
        [sys.executable, str(AXON)],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        timeout=10,
    )
    if proc.stdout.strip():
        return json.loads(proc.stdout.strip())
    return {}


class TestMergeGuard:
    """git merge from remote requires prior log/diff of incoming range."""

    def test_bare_merge_ganglion_denied(self):
        result = _run_axon("git merge ganglion/main --ff-only")
        decision = result.get("hookSpecificOutput", {}).get("permissionDecision")
        assert decision == "deny", f"Expected deny, got {result}"

    def test_bare_merge_origin_denied(self):
        result = _run_axon("git merge origin/main --ff-only")
        decision = result.get("hookSpecificOutput", {}).get("permissionDecision")
        assert decision == "deny", f"Expected deny, got {result}"

    def test_merge_with_log_chain_allowed(self):
        result = _run_axon(
            "git log HEAD..ganglion/main --oneline && git merge ganglion/main --ff-only"
        )
        decision = result.get("hookSpecificOutput", {}).get("permissionDecision")
        assert decision != "deny", f"Chained log+merge should be allowed, got {result}"

    def test_merge_with_diff_chain_allowed(self):
        result = _run_axon(
            "git diff HEAD..ganglion/main --stat && git merge ganglion/main --ff-only"
        )
        decision = result.get("hookSpecificOutput", {}).get("permissionDecision")
        assert decision != "deny", f"Chained diff+merge should be allowed, got {result}"

    def test_local_merge_not_affected(self):
        """git merge of a local branch should not be blocked."""
        result = _run_axon("git merge feature-branch --ff-only")
        decision = result.get("hookSpecificOutput", {}).get("permissionDecision")
        assert decision != "deny", f"Local branch merge should be allowed, got {result}"
