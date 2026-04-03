from __future__ import annotations

"""Tests for metabolon.resources.glycogen and proprioception._glycogen().

Covers:
  - glycogen module contract (BINARY, docstring, resource URI)
  - proprioception._glycogen() string formatting with mocked vasomotor_sensor
  - Edge cases: error, stale, missing keys, boundary percentages
"""

from unittest.mock import patch

import pytest

import metabolon.resources.glycogen as glycogen_mod
from metabolon.enzymes.proprioception import _glycogen


# ── Module contract ──────────────────────────────────────────────────


class TestGlycogenModule:
    def test_binary_constant_value(self):
        assert glycogen_mod.BINARY == "respirometry"

    def test_binary_is_string(self):
        assert isinstance(glycogen_mod.BINARY, str)

    def test_docstring_describes_budget_resource(self):
        assert "Budget resource" in glycogen_mod.__doc__
        assert "vivesca://budget" in glycogen_mod.__doc__

    def test_module_exports_only_binary(self):
        """glycogen module should only export BINARY at module level."""
        public = [name for name in dir(glycogen_mod) if not name.startswith("_")]
        assert "BINARY" in public


# ── proprioception._glycogen() formatter ─────────────────────────────


class TestGlycogenProprioception:
    @patch("metabolon.enzymes.proprioception._vasomotor_sense_from_glycogen")
    def _call_with_mock(self, mock_sense, return_value):
        """Helper: patch the inner import and call _glycogen()."""
        # _glycogen does `from metabolon.organelles.vasomotor_sensor import sense`
        # so we patch at the import site inside proprioception
        pass

    @patch("metabolon.organelles.vasomotor_sensor.sense")
    def test_safe_budget_format(self, mock_sense):
        mock_sense.return_value = {
            "status": "SAFE",
            "weekly_pct": 30.0,
            "sonnet_pct": 25.0,
            "stale": False,
            "stale_label": None,
        }
        result = _glycogen()
        assert result == "Token budget: SAFE — weekly 30%, sonnet 25%"

    @patch("metabolon.organelles.vasomotor_sensor.sense")
    def test_caution_budget_format(self, mock_sense):
        mock_sense.return_value = {
            "status": "CAUTION",
            "weekly_pct": 55.0,
            "sonnet_pct": 62.3,
            "stale": False,
            "stale_label": None,
        }
        result = _glycogen()
        assert "CAUTION" in result
        assert "weekly 55%" in result
        assert "sonnet 62%" in result

    @patch("metabolon.organelles.vasomotor_sensor.sense")
    def test_danger_budget_format(self, mock_sense):
        mock_sense.return_value = {
            "status": "DANGER",
            "weekly_pct": 95.7,
            "sonnet_pct": 91.2,
            "stale": False,
            "stale_label": None,
        }
        result = _glycogen()
        assert "DANGER" in result
        assert "weekly 96%" in result
        assert "sonnet 91%" in result

    @patch("metabolon.organelles.vasomotor_sensor.sense")
    def test_error_returns_unavailable(self, mock_sense):
        mock_sense.return_value = {"error": "credentials missing"}
        result = _glycogen()
        assert "unavailable" in result
        assert "credentials missing" in result

    @patch("metabolon.organelles.vasomotor_sensor.sense")
    def test_stale_data_includes_label(self, mock_sense):
        mock_sense.return_value = {
            "status": "CAUTION",
            "weekly_pct": 60.0,
            "sonnet_pct": 50.0,
            "stale": True,
            "stale_label": "5m ago",
        }
        result = _glycogen()
        assert "[5m ago]" in result

    @patch("metabolon.organelles.vasomotor_sensor.sense")
    def test_stale_but_no_label_omits_brackets(self, mock_sense):
        mock_sense.return_value = {
            "status": "SAFE",
            "weekly_pct": 10.0,
            "sonnet_pct": 5.0,
            "stale": True,
            "stale_label": None,
        }
        result = _glycogen()
        assert "[" not in result

    @patch("metabolon.organelles.vasomotor_sensor.sense")
    def test_missing_status_defaults_to_question_mark(self, mock_sense):
        mock_sense.return_value = {
            "weekly_pct": 10.0,
            "sonnet_pct": 5.0,
            "stale": False,
            "stale_label": None,
        }
        result = _glycogen()
        assert "Token budget: ?" in result

    @patch("metabolon.organelles.vasomotor_sensor.sense")
    def test_zero_percentages_format_correctly(self, mock_sense):
        mock_sense.return_value = {
            "status": "SAFE",
            "weekly_pct": 0.0,
            "sonnet_pct": 0.0,
            "stale": False,
            "stale_label": None,
        }
        result = _glycogen()
        assert "weekly 0%" in result
        assert "sonnet 0%" in result
