from __future__ import annotations

"""Tests for pinocytosis enzyme helpers."""


import os
import time
from pathlib import Path
from unittest.mock import patch


def test_read_if_fresh_missing_file():
    """_read_if_fresh returns None for nonexistent file."""
    from metabolon.enzymes.pinocytosis import _read_if_fresh

    result = _read_if_fresh(Path("/nonexistent/file.md"))
    assert result is None


def test_pinocytosis_actions_read_if_fresh_stale_file(tmp_path):
    """_read_if_fresh returns None for file older than max_age_hours."""
    from metabolon.enzymes.pinocytosis import _read_if_fresh

    f = tmp_path / "old.md"
    f.write_text("stale content")
    old_time = time.time() - 48 * 3600
    os.utime(f, (old_time, old_time))
    result = _read_if_fresh(f, max_age_hours=24)
    assert result is None


def test_read_if_fresh_valid_file(tmp_path):
    """_read_if_fresh returns content for fresh file."""
    from metabolon.enzymes.pinocytosis import _read_if_fresh

    f = tmp_path / "fresh.md"
    f.write_text("fresh content")
    result = _read_if_fresh(f, max_age_hours=24)
    assert result == "fresh content"


def test_read_now_md_missing():
    """_read_now_md returns 'not found' when NOW.md doesn't exist."""
    from metabolon.enzymes.pinocytosis import _read_now_md

    with patch("metabolon.enzymes.pinocytosis.NOW_MD") as mock_path:
        mock_path.exists.return_value = False
        result = _read_now_md()
        assert "not found" in result.lower()


def test_pinocytosis_actions_hkt_now_returns_datetime():
    """_hkt_now returns timezone-aware datetime in HKT."""
    from datetime import datetime, timedelta

    from metabolon.enzymes.pinocytosis import _hkt_now

    result = _hkt_now()
    assert isinstance(result, datetime)
    assert result.tzinfo is not None
    # Verify HKT offset = UTC+8
    assert result.utcoffset() == timedelta(hours=8)
