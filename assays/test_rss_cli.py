"""Tests for metabolon.organelles.endocytosis_rss.cli."""

from __future__ import annotations

import importlib.metadata
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING
from unittest.mock import patch

from metabolon.organelles.endocytosis_rss.cli import (
    _file_age,
    _get_last_scan_date,
    _get_version,
    _parse_aware,
    _source_since_date,
)

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# _get_version
# ---------------------------------------------------------------------------


def test_get_version_returns_installed_version():
    """When the package is installed, return its version string."""
    with patch.object(importlib.metadata, "version", return_value="1.2.3"):
        assert _get_version() == "1.2.3"


def test_get_version_falls_back_to_dev():
    """When the package is not installed, return 'dev'."""
    with patch.object(
        importlib.metadata,
        "version",
        side_effect=importlib.metadata.PackageNotFoundError("metabolon"),
    ):
        assert _get_version() == "dev"


# ---------------------------------------------------------------------------
# _file_age
# ---------------------------------------------------------------------------


def test_file_age_missing(tmp_path: Path):
    """Non-existent file reports 'missing'."""
    result = _file_age(tmp_path / "nope", datetime.now(UTC))
    assert result == "missing"


def test_file_age_just_now(tmp_path: Path):
    """File modified within the last minute reports 'just now'."""
    f = tmp_path / "fresh"
    f.write_text("x")
    result = _file_age(f, datetime.now(UTC))
    assert result == "just now"


def test_file_age_minutes_ago(tmp_path: Path):
    """File modified 5 minutes ago reports '5m ago'."""
    f = tmp_path / "stale"
    f.write_text("x")
    now = datetime.now(UTC)
    # Back-date the file by 5 minutes
    import os

    five_min_ago = (now - timedelta(minutes=5)).timestamp()
    os.utime(f, (five_min_ago, five_min_ago))
    result = _file_age(f, now)
    assert result == "5m ago"


def test_file_age_hours_ago(tmp_path: Path):
    """File modified 3 hours ago reports '3h ago'."""
    f = tmp_path / "older"
    f.write_text("x")
    now = datetime.now(UTC)
    import os

    three_hours_ago = (now - timedelta(hours=3)).timestamp()
    os.utime(f, (three_hours_ago, three_hours_ago))
    result = _file_age(f, now)
    assert result == "3h ago"


def test_file_age_days_ago(tmp_path: Path):
    """File modified 5 days ago reports '5d ago'."""
    f = tmp_path / "ancient"
    f.write_text("x")
    now = datetime.now(UTC)
    import os

    five_days_ago = (now - timedelta(days=5)).timestamp()
    os.utime(f, (five_days_ago, five_days_ago))
    result = _file_age(f, now)
    assert result == "5d ago"


# ---------------------------------------------------------------------------
# _parse_aware
# ---------------------------------------------------------------------------


def test_parse_aware_with_utc():
    """ISO string with +00:00 preserves timezone."""
    dt = _parse_aware("2025-06-15T12:00:00+00:00")
    assert dt is not None
    assert dt.tzinfo is not None
    assert dt.year == 2025


def test_parse_aware_naive_gets_utc():
    """Naive ISO string gets UTC attached."""
    dt = _parse_aware("2025-06-15T12:00:00")
    assert dt is not None
    assert dt.tzinfo is not None
    assert dt.tzinfo == UTC


def test_parse_aware_invalid_returns_none():
    """Garbage input returns None."""
    assert _parse_aware("not-a-date") is None


def test_parse_aware_none_returns_none():
    """None input returns None."""
    assert _parse_aware(None) is None  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# _get_last_scan_date
# ---------------------------------------------------------------------------


def test_last_scan_date_from_state():
    """Returns the day before the most recent scan timestamp."""
    state = {"src_a": "2025-06-15T10:00:00+00:00", "src_b": "2025-06-14T08:00:00+00:00"}
    result = _get_last_scan_date(state)
    # max date is 2025-06-15, minus 1 day = 2025-06-14
    assert result == "2025-06-14"


def test_last_scan_date_empty_state():
    """Empty state falls back to yesterday."""
    result = _get_last_scan_date({})
    yesterday = (datetime.now(UTC) - timedelta(days=1)).strftime("%Y-%m-%d")
    assert result == yesterday


def test_last_scan_date_all_invalid():
    """State with only unparsable values falls back to yesterday."""
    result = _get_last_scan_date({"x": "garbage"})
    yesterday = (datetime.now(UTC) - timedelta(days=1)).strftime("%Y-%m-%d")
    assert result == yesterday


# ---------------------------------------------------------------------------
# _source_since_date
# ---------------------------------------------------------------------------


def test_source_since_date_known_source():
    """Known source uses its own timestamp minus one day."""
    state = {"mysrc": "2025-06-10T00:00:00+00:00"}
    result = _source_since_date(state, "mysrc", "2025-06-01")
    assert result == "2025-06-09"


def test_source_since_date_new_source_daily():
    """New source with daily cadence uses 2-day lookback."""
    now = datetime(2025, 6, 15, tzinfo=UTC)
    result = _source_since_date({}, "newsrc", "2025-06-15", cadence="daily", now=now)
    # lookback 2 days = 2025-06-13, fallback = 2025-06-15; min = 2025-06-13
    assert result == "2025-06-13"


def test_source_since_date_new_source_weekly():
    """New source with weekly cadence uses 10-day lookback."""
    now = datetime(2025, 6, 20, tzinfo=UTC)
    result = _source_since_date({}, "newsrc", "2025-06-20", cadence="weekly", now=now)
    # lookback 10 days = 2025-06-10, fallback = 2025-06-20; min = 2025-06-10
    assert result == "2025-06-10"


def test_source_since_date_new_source_fallback_wins():
    """When fallback is older than cadence lookback, fallback is used."""
    now = datetime(2025, 6, 20, tzinfo=UTC)
    # fallback 2025-06-05 is older than 2-day lookback (2025-06-18)
    result = _source_since_date({}, "newsrc", "2025-06-05", cadence="daily", now=now)
    assert result == "2025-06-05"
