"""Tests for metabolon.enzymes.expression module."""

from __future__ import annotations

import datetime
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


class TestCountSparks:
    """Tests for _count_sparks helper."""

    def test_nonexistent_file_returns_zero(self):
        """Nonexistent path should return 0."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = False
        assert _count_sparks(mock_path) == 0

    def test_empty_file_returns_zero(self):
        """Empty file should return 0."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = ""
        assert _count_sparks(mock_path) == 0

    def test_only_headers_returns_zero(self):
        """File with only # comment lines should return 0."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = "# Header 1\n# Header 2\n"
        assert _count_sparks(mock_path) == 0

    def test_counts_non_empty_non_header_lines(self):
        """Should count lines that are non-empty and not headers."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = (
            "# Header\n"
            "\n"
            "spark one\n"
            "spark two\n"
            "  spark three  \n"  # whitespace should be stripped
            "# another comment\n"
            "spark four\n"
        )
        assert _count_sparks(mock_path) == 4

    def test_whitespace_only_lines_ignored(self):
        """Lines with only whitespace should not be counted."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = "   \n\t\n  \n"
        assert _count_sparks(mock_path) == 0


class TestFileAgeDays:
    """Tests for _file_age_days helper."""

    def test_nonexistent_file_returns_none(self):
        """Nonexistent path should return None."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = False
        assert _file_age_days(mock_path) is None

    def test_returns_age_in_days(self):
        """Should return file age in days."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        # File modified 2 days ago
        now = datetime.datetime.now().timestamp()
        two_days_ago = now - (2 * 86400)
        mock_stat = MagicMock()
        mock_stat.st_mtime = two_days_ago
        mock_path.stat.return_value = mock_stat

        result = _file_age_days(mock_path)
        assert result is not None
        assert 1.9 < result < 2.1  # approximately 2 days


class TestExpressionPreflight:
    """Tests for expression(action='preflight')."""

    @patch("metabolon.enzymes.expression._SPARKS")
    @patch("metabolon.enzymes.expression._THALAMUS")
    @patch("metabolon.enzymes.expression._NEWS_LOG")
    @patch("metabolon.enzymes.expression._NORTH_STAR")
    @patch("metabolon.enzymes.expression._count_sparks")
    @patch("metabolon.enzymes.expression._file_age_days")
    def test_all_files_missing(
        self,
        mock_file_age,
        mock_count_sparks,
        mock_north_star,
        mock_news_log,
        mock_thalamus,
        mock_sparks,
    ):
        """All required files missing should return not ready."""
        mock_sparks.exists.return_value = False
        mock_thalamus.exists.return_value = False
        mock_news_log.exists.return_value = False
        mock_north_star.exists.return_value = False
        mock_count_sparks.return_value = 0
        mock_file_age.return_value = None  # thalamus doesn't exist

        result = expression("preflight")

        assert isinstance(result, ForgePreflightResult)
        assert result.ready is False
        assert len(result.missing_files) == 4
        assert result.spark_count == 0

    @patch("metabolon.enzymes.expression._SPARKS")
    @patch("metabolon.enzymes.expression._THALAMUS")
    @patch("metabolon.enzymes.expression._NEWS_LOG")
    @patch("metabolon.enzymes.expression._NORTH_STAR")
    @patch("metabolon.enzymes.expression._count_sparks")
    @patch("metabolon.enzymes.expression._file_age_days")
    def test_ready_when_all_files_exist_and_sparks_present(
        self,
        mock_file_age,
        mock_count_sparks,
        mock_north_star,
        mock_news_log,
        mock_thalamus,
        mock_sparks,
    ):
        """Should be ready when all files exist and sparks > 0."""
        mock_sparks.exists.return_value = True
        mock_thalamus.exists.return_value = True
        mock_news_log.exists.return_value = True
        mock_north_star.exists.return_value = True
        mock_count_sparks.return_value = 5
        mock_file_age.return_value = 1.0  # fresh thalamus

        result = expression("preflight")

        assert isinstance(result, ForgePreflightResult)
        assert result.ready is True
        assert result.missing_files == []
        assert result.spark_count == 5
        assert "READY" in result.summary

    @patch("metabolon.enzymes.expression._SPARKS")
    @patch("metabolon.enzymes.expression._THALAMUS")
    @patch("metabolon.enzymes.expression._NEWS_LOG")
    @patch("metabolon.enzymes.expression._NORTH_STAR")
    @patch("metabolon.enzymes.expression._count_sparks")
    @patch("metabolon.enzymes.expression._file_age_days")
    def test_warning_for_empty_sparks(
        self,
        mock_file_age,
        mock_count_sparks,
        mock_north_star,
        mock_news_log,
        mock_thalamus,
        mock_sparks,
    ):
        """Should warn if sparks file exists but is empty."""
        mock_sparks.exists.return_value = True
        mock_thalamus.exists.return_value = True
        mock_news_log.exists.return_value = True
        mock_north_star.exists.return_value = True
        mock_count_sparks.return_value = 0
        mock_file_age.return_value = 1.0

        result = expression("preflight")

        assert result.ready is False
        assert any("empty" in w.lower() for w in result.warnings)

    @patch("metabolon.enzymes.expression._SPARKS")
    @patch("metabolon.enzymes.expression._THALAMUS")
    @patch("metabolon.enzymes.expression._NEWS_LOG")
    @patch("metabolon.enzymes.expression._NORTH_STAR")
    @patch("metabolon.enzymes.expression._count_sparks")
    @patch("metabolon.enzymes.expression._file_age_days")
    def test_warning_for_low_spark_count(
        self,
        mock_file_age,
        mock_count_sparks,
        mock_north_star,
        mock_news_log,
        mock_thalamus,
        mock_sparks,
    ):
        """Should warn if spark count is low (< 3)."""
        mock_sparks.exists.return_value = True
        mock_thalamus.exists.return_value = True
        mock_news_log.exists.return_value = True
        mock_north_star.exists.return_value = True
        mock_count_sparks.return_value = 2
        mock_file_age.return_value = 1.0

        result = expression("preflight")

        assert result.ready is True  # still ready with low count
        assert any("low spark count" in w.lower() for w in result.warnings)

    @patch("metabolon.enzymes.expression._SPARKS")
    @patch("metabolon.enzymes.expression._THALAMUS")
    @patch("metabolon.enzymes.expression._NEWS_LOG")
    @patch("metabolon.enzymes.expression._NORTH_STAR")
    @patch("metabolon.enzymes.expression._count_sparks")
    @patch("metabolon.enzymes.expression._file_age_days")
    def test_warning_for_stale_thalamus(
        self,
        mock_file_age,
        mock_count_sparks,
        mock_north_star,
        mock_news_log,
        mock_thalamus,
        mock_sparks,
    ):
        """Should warn if thalamus is older than 7 days."""
        mock_sparks.exists.return_value = True
        mock_thalamus.exists.return_value = True
        mock_news_log.exists.return_value = True
        mock_north_star.exists.return_value = True
        mock_count_sparks.return_value = 5
        mock_file_age.return_value = 10.0  # 10 days old

        result = expression("preflight")

        assert result.ready is True
        assert any("stale" in w.lower() or "old" in w.lower() for w in result.warnings)


class TestExpressionLibrary:
    """Tests for expression(action='library')."""

    @patch("metabolon.enzymes.expression._LIBRARY_DIRS")
    def test_empty_library(self, mock_dirs):
        """Should return zeros for nonexistent directories."""
        mock_dirs.items.return_value = []

        result = expression("library")

        assert isinstance(result, ForgeLibraryResult)
        assert result.totals == {}
        assert result.recent_7d == {}

    @patch("metabolon.enzymes.expression._LIBRARY_DIRS")
    def test_counts_files_in_directory(self, mock_dirs):
        """Should count .md files in each directory."""
        mock_policies = MagicMock(spec=Path)
        mock_policies.exists.return_value = True
        mock_file1 = MagicMock(spec=Path)
        mock_file1.is_file.return_value = True
        mock_file1.suffix = ".md"
        mock_file1.stat.return_value.st_mtime = datetime.datetime.now().timestamp()
        mock_policies.glob.return_value = [mock_file1]

        mock_dirs.items.return_value = [("Policies", mock_policies)]

        result = expression("library")

        assert result.totals.get("Policies", 0) == 1

    @patch("metabolon.enzymes.expression._LIBRARY_DIRS")
    def test_nonexistent_directory_returns_zero(self, mock_dirs):
        """Nonexistent directory should return 0 counts."""
        mock_dir = MagicMock(spec=Path)
        mock_dir.exists.return_value = False

        mock_dirs.__iter__ = lambda self: iter([("Missing", mock_dir)])
        mock_dirs.__getitem__ = lambda self, key: mock_dir

        result = expression("library")

        assert result.totals.get("Missing", 0) == 0
        assert result.recent_7d.get("Missing", 0) == 0

    @patch("metabolon.enzymes.expression._LIBRARY_DIRS")
    def test_recent_count_within_7_days(self, mock_dirs):
        """Should count files modified within last 7 days."""
        mock_dir = MagicMock(spec=Path)
        mock_dir.exists.return_value = True

        # Recent file (1 day old)
        recent_file = MagicMock(spec=Path)
        recent_file.is_file.return_value = True
        recent_file.suffix = ".md"
        recent_file.stat.return_value.st_mtime = (
            datetime.datetime.now() - datetime.timedelta(days=1)
        ).timestamp()

        # Old file (10 days old)
        old_file = MagicMock(spec=Path)
        old_file.is_file.return_value = True
        old_file.suffix = ".md"
        old_file.stat.return_value.st_mtime = (
            datetime.datetime.now() - datetime.timedelta(days=10)
        ).timestamp()

        mock_dir.glob.return_value = [recent_file, old_file]
        mock_dirs.__iter__ = lambda self: iter([("Test", mock_dir)])
        mock_dirs.__getitem__ = lambda self, key: mock_dir

        result = expression("library")

        assert result.totals.get("Test", 0) == 2
        assert result.recent_7d.get("Test", 0) == 1

    @patch("metabolon.enzymes.expression._LIBRARY_DIRS")
    def test_summary_includes_grand_total(self, mock_dirs):
        """Summary should include grand total and recent counts."""
        mock_dir = MagicMock(spec=Path)
        mock_dir.exists.return_value = True
        mock_file = MagicMock(spec=Path)
        mock_file.is_file.return_value = True
        mock_file.suffix = ".md"
        mock_file.stat.return_value.st_mtime = datetime.datetime.now().timestamp()
        mock_dir.glob.return_value = [mock_file]

        mock_dirs.__iter__ = lambda self: iter([("Docs", mock_dir)])
        mock_dirs.__getitem__ = lambda self, key: mock_dir

        result = expression("library")

        assert "1 assets" in result.summary
        assert "1 in last 7d" in result.summary


class TestExpressionUnknownAction:
    """Tests for unknown action handling."""

    def test_unknown_action_returns_error_string(self):
        """Unknown action should return error string."""
        result = expression("invalid")

        assert isinstance(result, str)
        assert "Unknown action" in result
        assert "preflight|library" in result

    def test_empty_action_returns_error(self):
        """Empty action should return error string."""
        result = expression("")

        assert isinstance(result, str)
        assert "Unknown action" in result


class TestResultTypes:
    """Tests for result type structure."""

    def test_preflight_result_is_secretion(self):
        """ForgePreflightResult should inherit from Secretion."""
        from metabolon.morphology import Secretion

        assert issubclass(ForgePreflightResult, Secretion)

    def test_library_result_is_secretion(self):
        """ForgeLibraryResult should inherit from Secretion."""
        from metabolon.morphology import Secretion

        assert issubclass(ForgeLibraryResult, Secretion)

    def test_preflight_result_has_required_fields(self):
        """ForgePreflightResult should have all required fields."""
        result = ForgePreflightResult(
            ready=True,
            spark_count=5,
            missing_files=[],
            warnings=[],
            summary="test",
        )
        assert result.ready is True
        assert result.spark_count == 5
        assert result.missing_files == []
        assert result.warnings == []
        assert result.summary == "test"

    def test_library_result_has_required_fields(self):
        """ForgeLibraryResult should have all required fields."""
        result = ForgeLibraryResult(
            totals={"Policies": 5},
            recent_7d={"Policies": 1},
            summary="test",
        )
        assert result.totals == {"Policies": 5}
        assert result.recent_7d == {"Policies": 1}
        assert result.summary == "test"
