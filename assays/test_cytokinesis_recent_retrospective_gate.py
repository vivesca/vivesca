"""Regression test for cytokinesis Gate 8 (recent_retrospective).

Catches silent rot in the post-wrap continuation detector. The gate scans
chromatin/retrospectives/<today>-*.md files <4h old and fires PENDING when
found, prompting telophase to default to thin checkpoint mode.

Same failure shape as skill-trigger-gen 25-day silent rot (2026-04-28
trigger-system overhaul) — without an assay, gate logic could break and
nothing would notice until Terry caught a missed thin-session prompt.

Smoke test only: invokes the live effector subprocess and asserts the
gate fields exist in the result envelope. Filesystem state is whatever
exists at test time; we don't manipulate retrospectives directory.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

CYTOKINESIS_BIN = Path(__file__).parent.parent / "effectors" / "cytokinesis"


def _run_gather() -> dict:
    """Run `cytokinesis gather` and return parsed result dict."""
    result = subprocess.run(
        [str(CYTOKINESIS_BIN), "gather"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, f"gather failed: {result.stderr[:200]}"
    last_line = result.stdout.strip().split("\n")[-1]
    payload = json.loads(last_line)
    assert payload.get("ok") is True, f"gather returned not-ok: {payload}"
    return payload["result"]


def test_recent_retrospective_gate_present():
    """Gate 8 must always appear in gates dict — DONE or PENDING."""
    result = _run_gather()
    gates = result["gates"]
    assert "recent_retrospective" in gates, (
        "Gate 8 (recent_retrospective) missing from gates. "
        "Silent rot risk: post-wrap continuation detection broken."
    )
    gate_value = gates["recent_retrospective"]
    assert gate_value.startswith(("DONE", "PENDING")), f"Unexpected gate format: {gate_value!r}"


def test_recent_retrospective_fields_in_envelope():
    """Result envelope must expose the deterministic fields."""
    result = _run_gather()
    assert "recent_retrospective_age_hours" in result, (
        "Missing recent_retrospective_age_hours field in result envelope"
    )
    assert "recent_retrospective_path" in result, (
        "Missing recent_retrospective_path field in result envelope"
    )
    age = result["recent_retrospective_age_hours"]
    path = result["recent_retrospective_path"]
    if age is None:
        assert path is None, "age=None implies path=None"
    else:
        assert isinstance(age, (int, float)), f"age must be numeric, got {type(age)}"
        assert age >= 0, f"age must be non-negative, got {age}"
        assert isinstance(path, str), f"path must be string when age set, got {type(path)}"


def test_pending_gate_directs_to_checkpoint():
    """When PENDING, gate text must steer to thin checkpoint mode."""
    result = _run_gather()
    gate_value = result["gates"]["recent_retrospective"]
    if gate_value.startswith("PENDING"):
        assert "checkpoint" in gate_value.lower(), (
            f"PENDING gate must mention checkpoint mode, got: {gate_value!r}"
        )
        assert "telophase" in gate_value.lower(), (
            f"PENDING gate must reference telophase routing, got: {gate_value!r}"
        )
