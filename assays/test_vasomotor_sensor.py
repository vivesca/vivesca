"""Tests for vasomotor_sensor — CC budget usage tracker."""
from __future__ import annotations

import json
from unittest.mock import patch

import pytest


class TestBudgetStatus:
    def test_safe(self):
        from metabolon.organelles.vasomotor_sensor import budget_status
        usage = {"seven_day": {"utilization": 30}, "seven_day_sonnet": {"utilization": 20}}
        assert budget_status(usage) == "SAFE"

    def test_caution(self):
        from metabolon.organelles.vasomotor_sensor import budget_status
        usage = {"seven_day": {"utilization": 60}, "seven_day_sonnet": {"utilization": 40}}
        assert budget_status(usage) == "CAUTION"

    def test_warning(self):
        from metabolon.organelles.vasomotor_sensor import budget_status
        usage = {"seven_day": {"utilization": 80}, "seven_day_sonnet": {"utilization": 50}}
        assert budget_status(usage) == "WARNING"

    def test_danger(self):
        from metabolon.organelles.vasomotor_sensor import budget_status
        usage = {"seven_day": {"utilization": 95}, "seven_day_sonnet": {"utilization": 90}}
        assert budget_status(usage) == "DANGER"

    def test_accepts_tuple(self):
        from metabolon.organelles.vasomotor_sensor import budget_status
        usage = ({"seven_day": {"utilization": 30}, "seven_day_sonnet": {"utilization": 20}}, None)
        assert budget_status(usage) == "SAFE"

    def test_sonnet_drives_status(self):
        from metabolon.organelles.vasomotor_sensor import budget_status
        usage = {"seven_day": {"utilization": 10}, "seven_day_sonnet": {"utilization": 90}}
        assert budget_status(usage) == "DANGER"

    def test_empty_usage(self):
        from metabolon.organelles.vasomotor_sensor import budget_status
        assert budget_status({}) == "SAFE"


class TestReadFallback:
    def test_no_files(self, tmp_path):
        from metabolon.organelles.vasomotor_sensor import _read_fallback
        import metabolon.organelles.vasomotor_sensor as vs
        with patch.object(vs, "HISTORY_FILE", tmp_path / "nope1.jsonl"), \
             patch.object(vs, "WATCH_LOG", tmp_path / "nope2.jsonl"):
            entry, age = _read_fallback()
        assert entry is None
        assert age is None

    def test_reads_last_entry(self, tmp_path):
        from metabolon.organelles.vasomotor_sensor import _read_fallback
        import metabolon.organelles.vasomotor_sensor as vs
        from datetime import datetime, UTC
        log = tmp_path / "history.jsonl"
        now = datetime.now(UTC).isoformat()
        log.write_text(json.dumps({"ts": now, "weekly_pct": 42}) + "\n")
        with patch.object(vs, "HISTORY_FILE", log), \
             patch.object(vs, "WATCH_LOG", tmp_path / "nope.jsonl"):
            entry, age = _read_fallback()
        assert entry is not None
        assert entry["weekly_pct"] == 42
        assert age is not None and age >= 0
