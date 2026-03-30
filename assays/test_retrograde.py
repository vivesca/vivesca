"""Tests for retrograde — symbiont influence tracker."""
from __future__ import annotations

import json
from datetime import datetime, UTC
from unittest.mock import patch

import pytest


class TestLogSignal:
    def test_appends_to_file(self, tmp_path):
        from metabolon.organelles.retrograde import log_signal
        import metabolon.organelles.retrograde as retro
        log_file = tmp_path / "signals.jsonl"
        with patch.object(retro, "SIGNALS_LOG", log_file):
            log_signal("anterograde", "channel_call", "test detail")
        assert log_file.exists()
        entry = json.loads(log_file.read_text().strip())
        assert entry["direction"] == "anterograde"
        assert entry["type"] == "channel_call"

    def test_creates_parent_dirs(self, tmp_path):
        from metabolon.organelles.retrograde import log_signal
        import metabolon.organelles.retrograde as retro
        log_file = tmp_path / "sub" / "dir" / "signals.jsonl"
        with patch.object(retro, "SIGNALS_LOG", log_file):
            log_signal("retrograde", "git_commit")
        assert log_file.exists()


class TestCutoffIso:
    def test_returns_iso_string(self):
        from metabolon.organelles.retrograde import _cutoff_iso
        result = _cutoff_iso(7)
        # Should be a valid ISO format string
        assert "T" in result
        # Parse should not crash
        datetime.fromisoformat(result)

    def test_shorter_period(self):
        from metabolon.organelles.retrograde import _cutoff_iso
        r7 = _cutoff_iso(7)
        r1 = _cutoff_iso(1)
        # 1-day cutoff should be more recent than 7-day
        assert r1 > r7


class TestCountLogged:
    def test_empty_log(self, tmp_path):
        from metabolon.organelles.retrograde import _count_logged
        import metabolon.organelles.retrograde as retro
        with patch.object(retro, "SIGNALS_LOG", tmp_path / "nope.jsonl"):
            assert _count_logged(7, "anterograde") == 0

    def test_counts_matching_direction(self, tmp_path):
        from metabolon.organelles.retrograde import _count_logged
        import metabolon.organelles.retrograde as retro
        log = tmp_path / "signals.jsonl"
        now = datetime.now(UTC).isoformat()
        entries = [
            json.dumps({"ts": now, "direction": "anterograde", "type": "test"}),
            json.dumps({"ts": now, "direction": "retrograde", "type": "test"}),
            json.dumps({"ts": now, "direction": "anterograde", "type": "test"}),
        ]
        log.write_text("\n".join(entries) + "\n")
        with patch.object(retro, "SIGNALS_LOG", log):
            assert _count_logged(7, "anterograde") == 2
