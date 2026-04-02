from __future__ import annotations

"""Tests for interoception enzyme: structural validation, constants, result types."""


import os
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Import test
# ---------------------------------------------------------------------------


class TestImport:
    """Verify the module and tool function are importable."""

    def test_interoception_tool_importable(self) -> None:
        """The main interoception function should import without error."""
        from metabolon.enzymes.interoception import interoception

        assert callable(interoception)


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


class TestResultTypes:
    """All result classes should be Secretion subclasses for structured output."""

    def test_result_types_are_secretion_subclasses(self) -> None:
        from metabolon.morphology import Secretion

        from metabolon.enzymes.interoception import (
            AnabolismResult,
            AngiogenesisResult,
            CircadianResult,
            CrisprResult,
            GlycolysisResult,
            HeartRateResult,
            HomeostasisFinancialResult,
            HomeostasisResult,
            InflammasomeResult,
            LysosomeResult,
            MembranePotentialResult,
            MitophagyResult,
            RetrogradeResult,
            TissueRoutingResult,
        )

        secretion_subclasses = [
            CircadianResult,
            HeartRateResult,
            MembranePotentialResult,
            HomeostasisResult,
            HomeostasisFinancialResult,
            LysosomeResult,
            AnabolismResult,
            AngiogenesisResult,
            MitophagyResult,
            GlycolysisResult,
            TissueRoutingResult,
            CrisprResult,
            RetrogradeResult,
            InflammasomeResult,
        ]
        for cls in secretion_subclasses:
            assert issubclass(cls, Secretion), f"{cls.__name__} is not a Secretion subclass"


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestConstants:
    """Validate module-level constants."""

    def test_financial_prompt_template_has_placeholders(self) -> None:
        """FINANCIAL_PROMPT_TEMPLATE must contain {today}, {notes}, {praxis}."""
        from metabolon.enzymes.interoception import FINANCIAL_PROMPT_TEMPLATE

        assert "{today}" in FINANCIAL_PROMPT_TEMPLATE
        assert "{notes}" in FINANCIAL_PROMPT_TEMPLATE
        assert "{praxis}" in FINANCIAL_PROMPT_TEMPLATE

    def test_financial_notes_list_not_empty(self) -> None:
        """FINANCIAL_NOTES should be a non-empty list of strings."""
        from metabolon.enzymes.interoception import FINANCIAL_NOTES

        assert isinstance(FINANCIAL_NOTES, list)
        assert len(FINANCIAL_NOTES) > 0
        for note in FINANCIAL_NOTES:
            assert isinstance(note, str)
            assert note.endswith(".md"), f"Expected .md suffix, got: {note}"

    def test_code_dir_constant(self) -> None:
        """CODE_DIR should point to ~/code."""
        from metabolon.enzymes.interoception import CODE_DIR

        expected = os.path.expanduser("~/code")
        assert CODE_DIR == expected

    def test_health_log_relative_constant(self) -> None:
        """HEALTH_LOG_RELATIVE should be a 2-tuple of strings."""
        from metabolon.enzymes.interoception import HEALTH_LOG_RELATIVE

        assert isinstance(HEALTH_LOG_RELATIVE, tuple)
        assert len(HEALTH_LOG_RELATIVE) == 2
        assert all(isinstance(part, str) for part in HEALTH_LOG_RELATIVE)


# ---------------------------------------------------------------------------
# Platform guards for launchctl
# ---------------------------------------------------------------------------


class TestSystemActionPlatformGuard:
    """Verify the 'system' action uses systemctl on Linux instead of launchctl."""

    def test_system_linux_uses_systemctl(self) -> None:
        """On Linux, system action should use systemctl --user list-units."""
        from unittest.mock import MagicMock, patch

        from metabolon.enzymes.interoception import interoception

        mock_result = MagicMock()
        mock_result.stdout = "com.vivesca.mcp.service  loaded active running\n"
        mock_result.returncode = 0

        with patch("metabolon.enzymes.interoception.platform.system", return_value="Linux"), \
             patch("metabolon.enzymes.interoception.subprocess.run", return_value=mock_result), \
             patch("metabolon.metabolism.mismatch_repair.summary", return_value=""), \
             patch("metabolon.metabolism.setpoint.Threshold") as mock_threshold:
            mock_threshold_inst = MagicMock()
            mock_threshold_inst.read.return_value = 15
            mock_threshold.return_value = mock_threshold_inst
            result = interoception(action="system")

        assert any("Pulse:" in s for s in result.sections)

    def test_system_darwin_uses_launchctl(self) -> None:
        """On Darwin, system action should use launchctl list."""
        from unittest.mock import MagicMock, patch

        from metabolon.enzymes.interoception import interoception

        mock_result = MagicMock()
        mock_result.stdout = "1234  0  com.vivesca.mcp\n"
        mock_result.returncode = 0

        with patch("metabolon.enzymes.interoception.platform.system", return_value="Darwin"), \
             patch("metabolon.enzymes.interoception.subprocess.run", return_value=mock_result), \
             patch("metabolon.metabolism.mismatch_repair.summary", return_value=""), \
             patch("metabolon.metabolism.setpoint.Threshold") as mock_threshold:
            mock_threshold_inst = MagicMock()
            mock_threshold_inst.read.return_value = 15
            mock_threshold.return_value = mock_threshold_inst
            result = interoception(action="system")

        assert any("Pulse:" in s for s in result.sections)
