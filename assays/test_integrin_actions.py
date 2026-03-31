from __future__ import annotations
"""Tests for integrin enzyme: constants, tool functions, helpers with mocked I/O."""


import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestConstants:
    """Validate module-level constants."""

    def test_builtins_frozenset(self) -> None:
        """BUILTINS should be a frozenset containing expected shell commands."""
        from metabolon.enzymes.integrin import BUILTINS

        assert isinstance(BUILTINS, frozenset)
        for expected in ("echo", "cd", "grep", "git", "python3"):
            assert expected in BUILTINS, f"Expected '{expected}' in BUILTINS"

    def test_skill_usage_log_path(self) -> None:
        """SKILL_USAGE_LOG should point to ~/.claude/skill-usage.tsv."""
        from metabolon.enzymes.integrin import SKILL_USAGE_LOG

        expected = Path.home() / ".claude" / "skill-usage.tsv"
        assert SKILL_USAGE_LOG == expected


# ---------------------------------------------------------------------------
# Tool function existence
# ---------------------------------------------------------------------------


class TestToolFunctions:
    """Verify all three tool functions are importable and callable."""

    def test_tool_functions_exist(self) -> None:
        """integrin_probe, integrin_apoptosis_check, and integrin should be callable."""
        from metabolon.enzymes.integrin import integrin, integrin_apoptosis_check, integrin_probe

        assert callable(integrin_probe)
        assert callable(integrin_apoptosis_check)
        assert callable(integrin)

    def test_tool_annotations_read_only_hint(self) -> None:
        """The integrin tool should have readOnlyHint=True annotation."""
        from metabolon.enzymes.integrin import integrin

        # FastMCP stores metadata on __fastmcp__ attribute
        meta = integrin.__fastmcp__
        assert meta.annotations is not None
        assert meta.annotations.readOnlyHint is True


# ---------------------------------------------------------------------------
# Helper functions with mocked I/O
# ---------------------------------------------------------------------------


class TestBinaryResolution:
    """Test binary resolution via shutil.which mock."""

    def test_probe_responsiveness_returns_false_when_not_on_path(self) -> None:
        """If shutil.which returns None, _probe_responsiveness should return False."""
        from metabolon.enzymes.integrin import _probe_responsiveness

        with patch("metabolon.enzymes.integrin.shutil.which", return_value=None):
            assert _probe_responsiveness("nonexistent_binary_xyz") is False

    def test_probe_responsiveness_returns_true_when_responsive(self) -> None:
        """A binary that produces stdout on --help should be marked responsive."""
        from metabolon.enzymes.integrin import _probe_responsiveness

        mock_result = MagicMock()
        mock_result.stdout = "Usage: mybin [options]"
        mock_result.stderr = ""

        with (
            patch("metabolon.enzymes.integrin.shutil.which", return_value="/usr/local/bin/mybin"),
            patch("metabolon.enzymes.integrin.subprocess.run", return_value=mock_result),
        ):
            assert _probe_responsiveness("mybin") is True

    def test_probe_responsiveness_returns_false_on_timeout(self) -> None:
        """A binary that times out should be marked non-responsive."""
        from metabolon.enzymes.integrin import _probe_responsiveness

        with (
            patch("metabolon.enzymes.integrin.shutil.which", return_value="/usr/local/bin/slowbin"),
            patch(
                "metabolon.enzymes.integrin.subprocess.run",
                side_effect=subprocess.TimeoutExpired(cmd="slowbin", timeout=5),
            ),
        ):
            assert _probe_responsiveness("slowbin") is False
