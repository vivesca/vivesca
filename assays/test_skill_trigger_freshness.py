#!/usr/bin/env python3
"""Integration test: skill-triggers.json must stay fresh and complete.

Regression coverage for the 25-day silent-failure incident (28 Apr 2026,
finding_skill_trigger_system_silent_failure.md). The system silently
matched against a stale JSON because skill-trigger-gen.py crashed on an
out-of-date path and capture_output=True swallowed the error.

These tests assert: (1) JSON exists, (2) modtime within 7 days, (3) every
user_invocable skill registers at least one trigger, (4) generator runs
without crashing.
"""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

import pytest

SKILLS_DIR = Path.home() / "germline" / "membrane" / "receptors"
TRIGGERS_JSON = Path.home() / ".claude" / "skill-triggers.json"
GEN_SCRIPT = Path.home() / "germline" / "membrane" / "cytoskeleton" / "skill-trigger-gen.py"
FRESHNESS_DAYS = 7


def test_triggers_json_exists() -> None:
    assert TRIGGERS_JSON.exists(), (
        f"{TRIGGERS_JSON} missing — mod_priming returns early without it. "
        "Run skill-trigger-gen.py."
    )


def test_triggers_json_fresh() -> None:
    age_seconds = time.time() - TRIGGERS_JSON.stat().st_mtime
    age_days = age_seconds / 86400
    assert age_days <= FRESHNESS_DAYS, (
        f"{TRIGGERS_JSON} is {age_days:.1f} days old (>{FRESHNESS_DAYS}). "
        "Auto-regen via dendrite is failing silently. Check "
        "~/.claude/skill-trigger-gen.log."
    )


BASELINE_MISSING_TRIGGERS = 0


def test_user_invocable_trigger_coverage_does_not_regress() -> None:
    """Skills with `user_invocable: true` AND no `disable-model-invocation: true`
    must register triggers. Baseline 0 as of 28 Apr 2026 after parser fixes."""
    user_invocable = []
    for skill_dir in SKILLS_DIR.iterdir():
        if not skill_dir.is_dir():
            continue
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            continue
        text = skill_file.read_text()
        if "user_invocable: true" not in text:
            continue
        if "disable-model-invocation: true" in text:
            continue
        user_invocable.append(skill_dir.name)

    registered = json.loads(TRIGGERS_JSON.read_text())
    missing = sorted(s for s in user_invocable if s not in registered)

    assert len(missing) <= BASELINE_MISSING_TRIGGERS, (
        f"REGRESSION: {len(missing)} user_invocable skills lack triggers "
        f"(baseline {BASELINE_MISSING_TRIGGERS} as of 28 Apr 2026 post-parser-fix). "
        f"Missing: {', '.join(missing[:15])}"
        f"{'...' if len(missing) > 15 else ''}. "
        "Add `## Triggers` markdown section or `triggers:` YAML list. "
        "If baseline reduces, lower BASELINE_MISSING_TRIGGERS in this test."
    )


def test_generator_runs_clean() -> None:
    result = subprocess.run(
        ["python3", str(GEN_SCRIPT)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        f"skill-trigger-gen.py exit {result.returncode}\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )


def test_schema_is_object_per_skill() -> None:
    data = json.loads(TRIGGERS_JSON.read_text())
    for skill, value in data.items():
        assert isinstance(value, dict), (
            f"Schema violation: {skill} value is {type(value).__name__}, "
            "expected dict with 'triggers' and 'anti_triggers' keys"
        )
        assert "triggers" in value, f"{skill}: missing 'triggers' key"
        assert isinstance(value["triggers"], list), f"{skill}: 'triggers' must be a list"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
