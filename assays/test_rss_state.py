"""Tests for metabolon/organelles/endocytosis_rss/state.py"""
from __future__ import annotations

import json
import os
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Generator

import pytest

from metabolon.organelles.endocytosis_rss import state as rss_state


class TestLockfile:
    """Tests for lockfile context manager."""

    def test_creates_lock_file(self, tmp_path: Path) -> None:
        lock_target = tmp_path / "test.lock.target"
        with rss_state.lockfile(lock_target):
            lock_path = lock_target.with_suffix(".lock")
            assert lock_path.exists()

    def test_removes_lock_on_exit(self, tmp_path: Path) -> None:
        lock_target = tmp_path / "test.lock.target"
        lock_path = lock_target.with_suffix(".lock")
        with rss_state.lockfile(lock_target):
            pass
        # Lock file should be removed after exit
        assert not lock_path.exists()

    def test_prevents_concurrent_access(self, tmp_path: Path) -> None:
        lock_target = tmp_path / "concurrent.lock.target"
        lock_path = lock_target.with_suffix(".lock")

        with rss_state.lockfile(lock_target):
            # Try to acquire the same lock
            with pytest.raises(SystemExit):
                rss_state.lockfile(lock_target).__enter__()

    def test_creates_parent_directory(self, tmp_path: Path) -> None:
        lock_target = tmp_path / "subdir" / "test.lock.target"
        with rss_state.lockfile(lock_target):
            pass
        # Should not raise


class TestRestoreState:
    """Tests for restore_state function."""

    def test_nonexistent_file_returns_empty_dict(self, tmp_path: Path) -> None:
        result = rss_state.restore_state(tmp_path / "nonexistent.json")
        assert result == {}

    def test_reads_valid_json(self, tmp_path: Path) -> None:
        state_path = tmp_path / "state.json"
        state_path.write_text('{"key1": "value1", "key2": "value2"}', encoding="utf-8")
        result = rss_state.restore_state(state_path)
        assert result == {"key1": "value1", "key2": "value2"}

    def test_handles_invalid_json(self, tmp_path: Path) -> None:
        state_path = tmp_path / "state.json"
        state_path.write_text("not valid json", encoding="utf-8")
        result = rss_state.restore_state(state_path)
        assert result == {}

    def test_handles_non_dict_json(self, tmp_path: Path) -> None:
        state_path = tmp_path / "state.json"
        state_path.write_text('["list", "not", "dict"]', encoding="utf-8")
        result = rss_state.restore_state(state_path)
        assert result == {}

    def test_filters_non_string_keys(self, tmp_path: Path) -> None:
        state_path = tmp_path / "state.json"
        state_path.write_text('{"str_key": "value", 123: "int_key"}', encoding="utf-8")
        result = rss_state.restore_state(state_path)
        assert "str_key" in result
        # Integer keys should be filtered out (or converted)

    def test_filters_non_string_values(self, tmp_path: Path) -> None:
        state_path = tmp_path / "state.json"
        state_path.write_text(
            '{"str_value": "text", "dict_value": {"nested": "dict"}}',
            encoding="utf-8",
        )
        result = rss_state.restore_state(state_path)
        assert result == {"str_value": "text"}

    def test_handles_os_error(self, tmp_path: Path) -> None:
        # Create a directory instead of a file to trigger OSError
        state_path = tmp_path / "state_dir"
        state_path.mkdir()
        result = rss_state.restore_state(state_path)
        assert result == {}


class TestPersistState:
    """Tests for persist_state function."""

    def test_creates_new_file(self, tmp_path: Path) -> None:
        state_path = tmp_path / "state.json"
        rss_state.persist_state(state_path, {"key": "value"})
        assert state_path.exists()

    def test_writes_valid_json(self, tmp_path: Path) -> None:
        state_path = tmp_path / "state.json"
        rss_state.persist_state(state_path, {"key": "value"})
        content = state_path.read_text(encoding="utf-8")
        parsed = json.loads(content)
        assert parsed == {"key": "value"}

    def test_creates_parent_directory(self, tmp_path: Path) -> None:
        state_path = tmp_path / "subdir" / "state.json"
        rss_state.persist_state(state_path, {"key": "value"})
        assert state_path.exists()

    def test_pretty_prints_json(self, tmp_path: Path) -> None:
        state_path = tmp_path / "state.json"
        rss_state.persist_state(state_path, {"key1": "value1", "key2": "value2"})
        content = state_path.read_text(encoding="utf-8")
        assert "\n" in content  # Indented

    def test_sorts_keys(self, tmp_path: Path) -> None:
        state_path = tmp_path / "state.json"
        rss_state.persist_state(state_path, {"z_key": "z", "a_key": "a"})
        content = state_path.read_text(encoding="utf-8")
        # a_key should come before z_key
        assert content.index("a_key") < content.index("z_key")


class TestRefractoryElapsed:
    """Tests for refractory_elapsed function."""

    def test_no_last_seen_returns_true(self) -> None:
        result = rss_state.refractory_elapsed({}, "source1", "daily")
        assert result is True

    def test_invalid_last_seen_returns_true(self) -> None:
        result = rss_state.refractory_elapsed(
            {"source1": "invalid-date"}, "source1", "daily"
        )
        assert result is True

    def test_elapsed_time_returns_true(self) -> None:
        now = datetime(2024, 3, 15, tzinfo=UTC)
        last_seen = (now - timedelta(days=2)).isoformat()
        result = rss_state.refractory_elapsed(
            {"source1": last_seen}, "source1", "daily", now=now
        )
        assert result is True

    def test_not_elapsed_returns_false(self) -> None:
        now = datetime(2024, 3, 15, tzinfo=UTC)
        last_seen = (now - timedelta(hours=12)).isoformat()
        result = rss_state.refractory_elapsed(
            {"source1": last_seen}, "source1", "daily", now=now
        )
        assert result is False

    def test_handles_naive_datetime(self) -> None:
        now = datetime(2024, 3, 15, tzinfo=UTC)
        last_seen = (now - timedelta(days=2)).replace(tzinfo=None).isoformat()
        result = rss_state.refractory_elapsed(
            {"source1": last_seen}, "source1", "daily", now=now
        )
        assert result is True

    def test_different_cadences(self) -> None:
        now = datetime(2024, 3, 15, tzinfo=UTC)
        last_seen = (now - timedelta(days=3)).isoformat()

        # Daily: 0 days, should be elapsed
        assert rss_state.refractory_elapsed(
            {"s": last_seen}, "s", "daily", now=now
        ) is True

        # Twice weekly: 2 days, should be elapsed (3 > 2)
        assert rss_state.refractory_elapsed(
            {"s": last_seen}, "s", "twice_weekly", now=now
        ) is True

        # Weekly: 5 days, not elapsed yet (3 < 5)
        assert rss_state.refractory_elapsed(
            {"s": last_seen}, "s", "weekly", now=now
        ) is False


class TestRefractoryDownregulation:
    """Tests for refractory period downregulation (signal_ratio)."""

    def test_high_signal_no_extension(self) -> None:
        now = datetime(2024, 3, 15, tzinfo=UTC)
        last_seen = (now - timedelta(days=1)).isoformat()
        # Daily cadence (0 days) + high signal (>= 0.5) = no extension
        result = rss_state.refractory_elapsed(
            {"s": last_seen}, "s", "daily", now=now, signal_ratio=0.8
        )
        assert result is True  # Elapsed because daily = 0 days

    def test_moderate_noise_extends_refractory(self) -> None:
        now = datetime(2024, 3, 15, tzinfo=UTC)
        last_seen = (now - timedelta(days=1)).isoformat()
        # Daily cadence (0) + moderate noise (+2 days) = 2 day refractory
        result = rss_state.refractory_elapsed(
            {"s": last_seen}, "s", "daily", now=now, signal_ratio=0.3
        )
        assert result is False  # 1 day < 2 days refractory

    def test_high_noise_extends_refractory_more(self) -> None:
        now = datetime(2024, 3, 15, tzinfo=UTC)
        last_seen = (now - timedelta(days=5)).isoformat()
        # Daily cadence (0) + high noise (+7 days) = 7 day refractory
        result = rss_state.refractory_elapsed(
            {"s": last_seen}, "s", "daily", now=now, signal_ratio=0.1
        )
        assert result is False  # 5 days < 7 days refractory

    def test_high_noise_elapsed_after_extended_period(self) -> None:
        now = datetime(2024, 3, 15, tzinfo=UTC)
        last_seen = (now - timedelta(days=10)).isoformat()
        # Daily cadence (0) + high noise (+7 days) = 7 day refractory
        result = rss_state.refractory_elapsed(
            {"s": last_seen}, "s", "daily", now=now, signal_ratio=0.1
        )
        assert result is True  # 10 days > 7 days refractory


class TestCadenceDays:
    """Tests for cadence day mappings."""

    def test_daily_is_zero(self) -> None:
        assert rss_state._CADENCE_DAYS["daily"] == 0

    def test_twice_weekly_is_two(self) -> None:
        assert rss_state._CADENCE_DAYS["twice_weekly"] == 2

    def test_weekly_is_five(self) -> None:
        assert rss_state._CADENCE_DAYS["weekly"] == 5

    def test_biweekly_is_ten(self) -> None:
        assert rss_state._CADENCE_DAYS["biweekly"] == 10

    def test_monthly_is_twenty_five(self) -> None:
        assert rss_state._CADENCE_DAYS["monthly"] == 25

    def test_unknown_cadence_defaults_to_one(self) -> None:
        now = datetime(2024, 3, 15, tzinfo=UTC)
        last_seen = (now - timedelta(days=2)).isoformat()
        # Unknown cadence should default to 1 day
        result = rss_state.refractory_elapsed(
            {"s": last_seen}, "s", "unknown_cadence", now=now
        )
        assert result is True  # 2 days > 1 day default
