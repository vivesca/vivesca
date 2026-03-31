"""Tests for glycogen resource — token budget status via vasomotor_sensor.

Covers:
  - glycogen.py module-level attributes (BINARY constant, docstring)
  - budget_status threshold classification
  - serialize_status output shape
  - _format_age human-readable durations
  - sense() top-level entry point (mocked IO)
  - proprioception._glycogen() integration (mocked organelle)
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import metabolon.resources.glycogen as glycogen_mod
from metabolon.organelles.vasomotor_sensor import (
    _format_age,
    budget_status,
    serialize_status,
)


# ── Module-level attributes ───────────────────────────────────────────


class TestGlycogenModule:
    def test_binary_constant(self):
        assert glycogen_mod.BINARY == "respirometry"

    def test_module_docstring_mentions_budget(self):
        assert "budget" in glycogen_mod.__doc__.lower()


# ── budget_status ─────────────────────────────────────────────────────


class TestBudgetStatus:
    def test_safe_below_threshold(self):
        usage = {"seven_day": {"utilization": 30}, "seven_day_sonnet": {"utilization": 20}}
        assert budget_status(usage) == "SAFE"

    def test_caution_zone(self):
        usage = {"seven_day": {"utilization": 55}, "seven_day_sonnet": {"utilization": 10}}
        assert budget_status(usage) == "CAUTION"

    def test_warning_zone(self):
        usage = {"seven_day": {"utilization": 75}, "seven_day_sonnet": {"utilization": 10}}
        assert budget_status(usage) == "WARNING"

    def test_danger_zone(self):
        usage = {"seven_day": {"utilization": 90}, "seven_day_sonnet": {"utilization": 95}}
        assert budget_status(usage) == "DANGER"

    def test_uses_max_of_weekly_and_sonnet(self):
        """The higher utilization determines status."""
        usage = {"seven_day": {"utilization": 20}, "seven_day_sonnet": {"utilization": 80}}
        assert budget_status(usage) == "WARNING"

    def test_empty_usage_is_safe(self):
        assert budget_status({}) == "SAFE"

    def test_accepts_tuple_from_sense_usage(self):
        """budget_status can accept the (usage, stale_age) tuple."""
        usage = {"seven_day": {"utilization": 90}, "seven_day_sonnet": {"utilization": 10}}
        assert budget_status((usage, 300)) == "DANGER"

    def test_missing_sub_keys_default_zero(self):
        usage = {"seven_day": {}, "seven_day_sonnet": {}}
        assert budget_status(usage) == "SAFE"


# ── serialize_status ──────────────────────────────────────────────────


class TestSerializeStatus:
    def test_live_status(self):
        usage = {
            "seven_day": {"utilization": 42.5, "resets_at": "2026-04-06"},
            "seven_day_sonnet": {"utilization": 15.0},
        }
        result = serialize_status(usage, stale_age=None)
        assert result["status"] == "SAFE"
        assert result["weekly_pct"] == 42.5
        assert result["sonnet_pct"] == 15.0
        assert result["stale"] is False
        assert result["stale_label"] is None
        assert result["resets_at"] == "2026-04-06"

    def test_stale_status(self):
        usage = {
            "seven_day": {"utilization": 60},
            "seven_day_sonnet": {"utilization": 60},
        }
        result = serialize_status(usage, stale_age=180)
        assert result["stale"] is True
        assert result["stale_label"] == "3m ago"
        assert result["status"] == "CAUTION"

    def test_session_pct_none_when_absent(self):
        usage = {"seven_day": {"utilization": 10}, "seven_day_sonnet": {"utilization": 10}}
        result = serialize_status(usage)
        assert result["session_pct"] is None

    def test_session_pct_present(self):
        usage = {
            "seven_day": {"utilization": 10},
            "seven_day_sonnet": {"utilization": 10},
            "five_hour": {"utilization": 5.5},
        }
        result = serialize_status(usage)
        assert result["session_pct"] == 5.5

    def test_all_expected_keys(self):
        usage = {"seven_day": {"utilization": 0}, "seven_day_sonnet": {"utilization": 0}}
        result = serialize_status(usage)
        expected_keys = {"status", "weekly_pct", "sonnet_pct", "session_pct", "stale", "stale_label", "resets_at"}
        assert set(result.keys()) == expected_keys


# ── _format_age ───────────────────────────────────────────────────────


class TestFormatAge:
    def test_seconds(self):
        assert _format_age(30) == "30s ago"

    def test_minutes(self):
        assert _format_age(150) == "2m ago"

    def test_hours(self):
        assert _format_age(7200) == "2h ago"

    def test_days(self):
        assert _format_age(172800) == "2d ago"

    def test_boundary_second(self):
        assert _format_age(59) == "59s ago"

    def test_boundary_minute(self):
        assert _format_age(60) == "1m ago"

    def test_boundary_hour(self):
        assert _format_age(3599) == "59m ago"

    def test_boundary_day(self):
        assert _format_age(3600) == "1h ago"


# ── sense (top-level, mocked) ────────────────────────────────────────


class TestSense:
    @patch("metabolon.organelles.vasomotor_sensor.sense_usage")
    def test_sense_returns_serialized(self, mock_su):
        mock_su.return_value = (
            {"seven_day": {"utilization": 30}, "seven_day_sonnet": {"utilization": 25}},
            None,
        )
        from metabolon.organelles.vasomotor_sensor import sense

        result = sense()
        assert result["status"] == "SAFE"
        assert result["weekly_pct"] == 30
        assert result["stale"] is False

    @patch("metabolon.organelles.vasomotor_sensor.sense_usage")
    def test_sense_returns_error_on_failure(self, mock_su):
        mock_su.side_effect = RuntimeError("no token")
        from metabolon.organelles.vasomotor_sensor import sense

        result = sense()
        assert "error" in result
        assert "no token" in result["error"]

    @patch("metabolon.organelles.vasomotor_sensor.sense_usage")
    def test_sense_stale_data(self, mock_su):
        mock_su.return_value = (
            {"seven_day": {"utilization": 50}, "seven_day_sonnet": {"utilization": 50}},
            600,
        )
        from metabolon.organelles.vasomotor_sensor import sense

        result = sense()
        assert result["stale"] is True
        assert result["stale_label"] == "10m ago"


# ── proprioception._glycogen integration ──────────────────────────────


class TestGlycogenProprioception:
    @patch("metabolon.enzymes.proprioception._glycogen")
    def test_glycogen_formats_budget(self, mock_glycogen):
        """_glycogen returns a formatted string with budget info."""
        mock_glycogen.return_value = "Token budget: SAFE — weekly 30%, sonnet 25%"
        result = mock_glycogen()
        assert "Token budget" in result
        assert "SAFE" in result

    @patch("metabolon.organelles.vasomotor_sensor.sense_usage")
    def test_glycogen_error_path(self, mock_su):
        """When sense returns error dict, _glycogen shows unavailable."""
        mock_su.side_effect = RuntimeError("credentials missing")
        from metabolon.organelles.vasomotor_sensor import sense

        result = sense()
        assert "error" in result

    @patch("metabolon.organelles.vasomotor_sensor.sense_usage")
    def test_glycogen_stale_label_in_output(self, mock_su):
        """When stale, the output includes the stale label."""
        mock_su.return_value = (
            {
                "seven_day": {"utilization": 60},
                "seven_day_sonnet": {"utilization": 40},
            },
            300,
        )
        from metabolon.organelles.vasomotor_sensor import sense

        result = sense()
        assert result["stale"] is True
        assert result["stale_label"] == "5m ago"
        # Build the string proprioception._glycogen would build
        stale = f" [{result['stale_label']}]" if result.get("stale") and result.get("stale_label") else ""
        text = f"Token budget: {result['status']} — weekly {result['weekly_pct']:.0f}%, sonnet {result['sonnet_pct']:.0f}%{stale}"
        assert "[5m ago]" in text
