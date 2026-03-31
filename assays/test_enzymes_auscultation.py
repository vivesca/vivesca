"""Tests for metabolon/enzymes/auscultation.py — log diagnostics."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fn():
    """Return the raw function behind the @tool decorator."""
    from metabolon.enzymes.auscultation import auscultation as fn

    # fastmcp wraps the function; the raw callable is .fn
    return getattr(fn, "fn", fn)


# ---------------------------------------------------------------------------
# _read_log_lines unit tests
# ---------------------------------------------------------------------------

class TestReadLogLines:
    """Tests for _read_log_lines helper."""

    def test_reads_tail_lines(self, tmp_path):
        from metabolon.enzymes.auscultation import _read_log_lines

        log = tmp_path / "test.log"
        lines = [f"line {i}" for i in range(10)]
        log.write_text("\n".join(lines))
        result = _read_log_lines(log, n=3)
        assert result == ["line 7", "line 8", "line 9"]

    def test_returns_all_if_fewer_than_n(self, tmp_path):
        from metabolon.enzymes.auscultation import _read_log_lines

        log = tmp_path / "test.log"
        log.write_text("a\nb")
        result = _read_log_lines(log, n=200)
        assert result == ["a", "b"]

    def test_returns_empty_on_missing_file(self):
        from metabolon.enzymes.auscultation import _read_log_lines

        result = _read_log_lines(Path("/nonexistent/file.log"))
        assert result == []

    def test_replaces_errors(self, tmp_path):
        from metabolon.enzymes.auscultation import _read_log_lines

        log = tmp_path / "bad.log"
        log.write_bytes(b"ok\xff\xfebad")
        result = _read_log_lines(log)
        assert len(result) == 1  # one line, garbled chars replaced
        assert isinstance(result[0], str)


# ---------------------------------------------------------------------------
# _glob_logs unit tests
# ---------------------------------------------------------------------------

class TestGlobLogs:
    """Tests for _glob_logs helper."""

    def test_returns_matching_logs(self, tmp_path):
        from metabolon.enzymes.auscultation import _glob_logs, _LOG_DIR, _TMP_DIR

        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        (log_dir / "app.log").write_text("data")
        (log_dir / "other.txt").write_text("data")

        tmp_dir = tmp_path / "tmp"
        tmp_dir.mkdir()
        (tmp_dir / "debug.log").write_text("data")

        with (
            patch("metabolon.enzymes.auscultation._LOG_DIR", log_dir),
            patch("metabolon.enzymes.auscultation._TMP_DIR", tmp_dir),
        ):
            result = _glob_logs()
        names = [p.name for p in result]
        assert "app.log" in names
        assert "debug.log" in names
        assert "other.txt" not in names

    def test_returns_empty_when_no_dirs(self, tmp_path):
        from metabolon.enzymes.auscultation import _glob_logs

        nonexistent = tmp_path / "nope"
        with (
            patch("metabolon.enzymes.auscultation._LOG_DIR", nonexistent),
            patch("metabolon.enzymes.auscultation._TMP_DIR", nonexistent),
        ):
            result = _glob_logs()
        assert result == []


# ---------------------------------------------------------------------------
# auscultation — action: logs
# ---------------------------------------------------------------------------

class TestAuscultationLogs:
    """Tests for auscultation with action='logs'."""

    def _setup_logs(self, tmp_path):
        """Create temp log dirs and return (log_dir, tmp_dir)."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        (log_dir / "app.log").write_text(
            "INFO starting\nERROR crash\nWARN disk low\nERROR crash again"
        )
        (log_dir / "other.log").write_text("INFO ok\nDEBUG trace")

        tmp_dir = tmp_path / "tmp"
        tmp_dir.mkdir()
        (tmp_dir / "extra.log").write_text("INFO extra line\nERROR extra fail")
        return log_dir, tmp_dir

    def _call(self, log_dir, tmp_dir, **kwargs):
        fn = _fn()
        with (
            patch("metabolon.enzymes.auscultation._LOG_DIR", log_dir),
            patch("metabolon.enzymes.auscultation._TMP_DIR", tmp_dir),
        ):
            return fn(action="logs", **kwargs)

    def test_returns_all_logs_by_default(self, tmp_path):
        log_dir, tmp_dir = self._setup_logs(tmp_path)
        result = self._call(log_dir, tmp_dir)
        assert "app.log" in result
        assert "other.log" in result
        assert "extra.log" in result

    def test_filter_pattern(self, tmp_path):
        log_dir, tmp_dir = self._setup_logs(tmp_path)
        result = self._call(log_dir, tmp_dir, filter_pattern="ERROR")
        assert "ERROR" in result
        assert "INFO starting" not in result
        assert "=== app.log" in result

    def test_log_name_filter(self, tmp_path):
        log_dir, tmp_dir = self._setup_logs(tmp_path)
        result = self._call(log_dir, tmp_dir, log_name="app.log")
        assert "app.log" in result
        assert "other.log" not in result

    def test_log_name_not_found(self, tmp_path):
        log_dir, tmp_dir = self._setup_logs(tmp_path)
        result = self._call(log_dir, tmp_dir, log_name="missing.log")
        assert "Log not found: missing.log" == result

    def test_no_log_files(self, tmp_path):
        empty = tmp_path / "empty"
        empty.mkdir()
        result = self._call(empty, empty)
        assert "No log files found" in result

    def test_no_matching_lines(self, tmp_path):
        log_dir, tmp_dir = self._setup_logs(tmp_path)
        result = self._call(log_dir, tmp_dir, filter_pattern="FATAL")
        assert "No log lines" in result
        assert "FATAL" in result

    def test_tail_lines_limits_output(self, tmp_path):
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        (log_dir / "big.log").write_text("\n".join(f"line {i}" for i in range(50)))
        tmp_dir = tmp_path / "tmp"
        tmp_dir.mkdir()

        result = self._call(log_dir, tmp_dir, tail_lines=5)
        # Should contain only last 5 lines from big.log
        assert "line 49" in result
        assert "line 44" in result
        assert "line 0" not in result

    def test_line_count_in_header(self, tmp_path):
        log_dir, tmp_dir = self._setup_logs(tmp_path)
        result = self._call(log_dir, tmp_dir, filter_pattern="ERROR")
        assert "(2 lines)" in result  # 2 ERROR lines in app.log


# ---------------------------------------------------------------------------
# auscultation — action: errors
# ---------------------------------------------------------------------------

class TestAuscultationErrors:
    """Tests for auscultation with action='errors'."""

    def _setup_errors(self, tmp_path):
        """Create logs with error patterns. Returns (log_dir, tmp_dir)."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        (log_dir / "server.log").write_text(
            "2025-01-15T10:00:00 ERROR connection failed to 10.0.0.1 port 5432\n"
            "2025-01-15T10:01:00 INFO heartbeat ok\n"
            "2025-01-15T10:02:00 ERROR connection failed to 10.0.0.2 port 5432\n"
            "2025-01-15T10:03:00 WARN disk usage at 85 percent\n"
            "2025-01-15T10:04:00 ERROR connection failed to 10.0.0.3 port 5432\n"
            "2025-01-15T10:05:00 WARN disk usage at 90 percent\n"
        )
        tmp_dir = tmp_path / "tmp"
        tmp_dir.mkdir()
        return log_dir, tmp_dir

    def _call_errors(self, log_dir, tmp_dir, **kwargs):
        fn = _fn()
        with (
            patch("metabolon.enzymes.auscultation._LOG_DIR", log_dir),
            patch("metabolon.enzymes.auscultation._TMP_DIR", tmp_dir),
        ):
            return fn(action="errors", **kwargs)

    def test_counts_error_patterns(self, tmp_path):
        log_dir, tmp_dir = self._setup_errors(tmp_path)
        result = self._call_errors(log_dir, tmp_dir)
        assert "Error frequency analysis" in result
        assert "5 total error lines" in result
        # "connection failed" should appear as a pattern (normalized)
        assert "connection failed" in result

    def test_normalizes_numbers(self, tmp_path):
        log_dir, tmp_dir = self._setup_errors(tmp_path)
        result = self._call_errors(log_dir, tmp_dir)
        # All 3 "connection failed" lines should be normalized to count 3
        # Timestamps stripped, numbers replaced with N
        assert "3" in result  # count of the top pattern

    def test_no_normalization_when_disabled(self, tmp_path):
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        (log_dir / "app.log").write_text(
            "ERROR error 100\nERROR error 200\nERROR error 100\n"
        )
        tmp_dir = tmp_path / "tmp"
        tmp_dir.mkdir()
        result = self._call_errors(log_dir, tmp_dir, normalize_numbers=False)
        # Without normalization, "error 100" and "error 200" are different
        assert "error 100" in result
        assert "error 200" in result

    def test_custom_severity(self, tmp_path):
        log_dir, tmp_dir = self._setup_errors(tmp_path)
        result = self._call_errors(log_dir, tmp_dir, severity="WARN")
        assert "WARN" in result
        assert "Error frequency analysis" in result
        # Only 2 WARN lines
        assert "2 total error lines" in result

    def test_top_n_limits_output(self, tmp_path):
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        lines = [f"ERROR unique error number {i}" for i in range(10)]
        (log_dir / "app.log").write_text("\n".join(lines))
        tmp_dir = tmp_path / "tmp"
        tmp_dir.mkdir()
        result = self._call_errors(log_dir, tmp_dir, top_n=3)
        # Should have header (3 lines) + 3 pattern lines = 6 lines total
        data_lines = [l for l in result.splitlines() if l and not l.startswith("-") and not l.startswith("Error freq") and "Pattern" not in l]
        assert len(data_lines) == 3

    def test_no_errors_found(self, tmp_path):
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        (log_dir / "app.log").write_text("INFO all good\nDEBUG trace info\n")
        tmp_dir = tmp_path / "tmp"
        tmp_dir.mkdir()
        result = self._call_errors(log_dir, tmp_dir)
        assert "sounds healthy" in result

    def test_no_log_files_at_all(self, tmp_path):
        empty = tmp_path / "empty"
        empty.mkdir()
        result = self._call_errors(empty, empty)
        assert "No log files found" in result


# ---------------------------------------------------------------------------
# auscultation — unknown action
# ---------------------------------------------------------------------------

class TestAuscultationUnknownAction:
    """Tests for unknown action handling."""

    def test_unknown_action_returns_error(self):
        fn = _fn()
        result = fn(action="unknown")
        assert "Unknown action: unknown" in result

    def test_case_insensitive_action(self, tmp_path):
        """Action is lowercased, so 'LOGS' should work like 'logs'."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        (log_dir / "test.log").write_text("hello")
        tmp_dir = tmp_path / "tmp"
        tmp_dir.mkdir()
        fn = _fn()
        with (
            patch("metabolon.enzymes.auscultation._LOG_DIR", log_dir),
            patch("metabolon.enzymes.auscultation._TMP_DIR", tmp_dir),
        ):
            result = fn(action="LOGS")
        assert "test.log" in result
