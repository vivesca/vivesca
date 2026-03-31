from __future__ import annotations
"""Comprehensive tests for metabolon.enzymes.expression."""

import datetime
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from metabolon.enzymes.expression import (
    ForgeLibraryResult,
    ForgePreflightResult,
    _count_sparks,
    _file_age_days,
    expression,
)


# ---------------------------------------------------------------------------
# _count_sparks
# ---------------------------------------------------------------------------

class TestCountSparks:
    def test_missing_file_returns_zero(self, tmp_path):
        assert _count_sparks(tmp_path / "nope.md") == 0

    def test_empty_file_returns_zero(self, tmp_path):
        p = tmp_path / "sparks.md"
        p.write_text("")
        assert _count_sparks(p) == 0

    def test_only_comments_returns_zero(self, tmp_path):
        p = tmp_path / "sparks.md"
        p.write_text("# header\n# another\n")
        assert _count_sparks(p) == 0

    def test_counts_real_lines(self, tmp_path):
        p = tmp_path / "sparks.md"
        p.write_text("# Title\nspark one\nspark two\n\nspark three\n")
        assert _count_sparks(p) == 3

    def test_blank_lines_ignored(self, tmp_path):
        p = tmp_path / "sparks.md"
        p.write_text("\n\n\n")
        assert _count_sparks(p) == 0


# ---------------------------------------------------------------------------
# _file_age_days
# ---------------------------------------------------------------------------

class TestFileAgeDays:
    def test_missing_file_returns_none(self, tmp_path):
        assert _file_age_days(tmp_path / "nope") is None

    def test_recent_file_age_near_zero(self, tmp_path):
        p = tmp_path / "fresh.md"
        p.write_text("data")
        age = _file_age_days(p)
        assert age is not None
        assert age < 0.01  # just created


# ---------------------------------------------------------------------------
# preflight action
# ---------------------------------------------------------------------------

def _preflight_patches(**overrides):
    """Return a dict of standard mock patches for preflight tests."""
    defaults = {
        "exists": True,
        "spark_count": 5,
        "thal_age": 1.0,
    }
    defaults.update(overrides)
    return defaults


class TestPreflight:
    """Tests for expression(action='preflight')."""

    @patch("metabolon.enzymes.expression._file_age_days")
    @patch("metabolon.enzymes.expression._count_sparks")
    @patch("metabolon.enzymes.expression.Path.exists")
    def test_ready_when_all_present_and_sparks(self, mock_exists, mock_count, mock_age):
        mock_exists.return_value = True
        mock_count.return_value = 10
        mock_age.return_value = 2.0
        result = expression(action="preflight")
        assert isinstance(result, ForgePreflightResult)
        assert result.ready is True
        assert result.spark_count == 10
        assert result.missing_files == []
        assert "READY" in result.summary

    @patch("metabolon.enzymes.expression._file_age_days")
    @patch("metabolon.enzymes.expression._count_sparks")
    @patch("metabolon.enzymes.expression.Path.exists")
    def test_not_ready_missing_files(self, mock_exists, mock_count, mock_age):
        mock_exists.return_value = False
        mock_count.return_value = 5
        mock_age.return_value = 1.0
        result = expression(action="preflight")
        assert result.ready is False
        assert len(result.missing_files) > 0
        assert "NOT READY" in result.summary

    @patch("metabolon.enzymes.expression._file_age_days")
    @patch("metabolon.enzymes.expression._count_sparks")
    @patch("metabolon.enzymes.expression.Path.exists")
    def test_not_ready_zero_sparks(self, mock_exists, mock_count, mock_age):
        mock_exists.return_value = True
        mock_count.return_value = 0
        mock_age.return_value = 1.0
        result = expression(action="preflight")
        assert result.ready is False
        assert result.spark_count == 0
        assert any("empty" in w for w in result.warnings)

    @patch("metabolon.enzymes.expression._file_age_days")
    @patch("metabolon.enzymes.expression._count_sparks")
    @patch("metabolon.enzymes.expression.Path.exists")
    def test_low_sparks_warning(self, mock_exists, mock_count, mock_age):
        mock_exists.return_value = True
        mock_count.return_value = 2
        mock_age.return_value = 1.0
        result = expression(action="preflight")
        assert result.ready is True
        assert any("Low spark count" in w for w in result.warnings)

    @patch("metabolon.enzymes.expression._file_age_days")
    @patch("metabolon.enzymes.expression._count_sparks")
    @patch("metabolon.enzymes.expression.Path.exists")
    def test_stale_thalamus_warning(self, mock_exists, mock_count, mock_age):
        mock_exists.return_value = True
        mock_count.return_value = 5
        mock_age.return_value = 10.0
        result = expression(action="preflight")
        assert result.ready is True
        assert any("stale" in w.lower() for w in result.warnings)

    @patch("metabolon.enzymes.expression._file_age_days")
    @patch("metabolon.enzymes.expression._count_sparks")
    @patch("metabolon.enzymes.expression.Path.exists")
    def test_no_warnings_when_fresh(self, mock_exists, mock_count, mock_age):
        mock_exists.return_value = True
        mock_count.return_value = 5
        mock_age.return_value = 1.0
        result = expression(action="preflight")
        assert result.warnings == []

    @patch("metabolon.enzymes.expression._file_age_days")
    @patch("metabolon.enzymes.expression._count_sparks")
    @patch("metabolon.enzymes.expression.Path.exists")
    def test_summary_contains_spark_count(self, mock_exists, mock_count, mock_age):
        mock_exists.return_value = True
        mock_count.return_value = 7
        mock_age.return_value = 1.0
        result = expression(action="preflight")
        assert "7 items" in result.summary


# ---------------------------------------------------------------------------
# library action
# ---------------------------------------------------------------------------

class TestLibrary:
    """Tests for expression(action='library')."""

    @patch("metabolon.enzymes.expression.Path.exists")
    @patch("metabolon.enzymes.expression.Path.glob")
    def test_empty_dirs(self, mock_glob, mock_exists):
        mock_exists.return_value = True
        mock_glob.return_value = []
        result = expression(action="library")
        assert isinstance(result, ForgeLibraryResult)
        assert sum(result.totals.values()) == 0
        assert sum(result.recent_7d.values()) == 0

    @patch("metabolon.enzymes.expression.Path.exists")
    @patch("metabolon.enzymes.expression.Path.glob")
    def test_missing_dirs(self, mock_glob, mock_exists):
        mock_exists.return_value = False
        result = expression(action="library")
        assert all(v == 0 for v in result.totals.values())
        assert all(v == 0 for v in result.recent_7d.values())

    def test_real_files_counted(self, tmp_path):
        """Use real tmp dirs to exercise the actual glob/stat logic."""
        from metabolon.enzymes import expression as mod

        now = datetime.datetime.now()
        old_ts = (now - datetime.timedelta(days=30)).timestamp()
        recent_ts = (now - datetime.timedelta(days=1)).timestamp()

        lib_dirs = {}
        for label, _ in mod._LIBRARY_DIRS.items():
            d = tmp_path / label
            d.mkdir()
            # Create one old and one recent file
            old_f = d / "old.md"
            old_f.write_text("old")
            import os
            os.utime(old_f, (old_ts, old_ts))

            recent_f = d / "recent.md"
            recent_f.write_text("new")
            os.utime(recent_f, (recent_ts, recent_ts))

            lib_dirs[label] = d

        original_dirs = mod._LIBRARY_DIRS.copy()
        mod._LIBRARY_DIRS.clear()
        mod._LIBRARY_DIRS.update(lib_dirs)
        try:
            result = expression(action="library")
            assert isinstance(result, ForgeLibraryResult)
            for label in lib_dirs:
                assert result.totals[label] == 2
                assert result.recent_7d[label] == 1
            assert "10 assets" in result.summary
            assert "5 in last 7d" in result.summary
        finally:
            mod._LIBRARY_DIRS.clear()
            mod._LIBRARY_DIRS.update(original_dirs)


# ---------------------------------------------------------------------------
# unknown action
# ---------------------------------------------------------------------------

class TestUnknownAction:
    def test_returns_error_string(self):
        result = expression(action="bogus")
        assert isinstance(result, str)
        assert "Unknown action" in result

    def test_suggests_valid_actions(self):
        result = expression(action="bogus")
        assert "preflight" in result
        assert "library" in result
