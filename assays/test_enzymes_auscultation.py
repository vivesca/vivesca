"""Tests for metabolon/enzymes/auscultation.py.

Covers _read_log_lines, _glob_logs, and the auscultation tool with actions
'logs', 'errors', and unknown actions. All filesystem access is mocked.
"""

from __future__ import annotations

import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from metabolon.enzymes.auscultation import (
    _glob_logs,
    _read_log_lines,
    auscultation,
)


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

_FAKE_LOG_DIR = Path("/fake/Library/Logs/vivesca")
_FAKE_TMP_DIR = Path("/fake/tmp")


def _make_log(name: str, content: str) -> Path:
    """Return a fake Path whose read_text returns *content*."""
    p = Path(_FAKE_LOG_DIR / name)
    p._fake_content = content  # stash for mock side_effect
    return p


def _mock_paths(log_dir_files: list[str] | None = None,
                tmp_dir_files: list[str] | None = None):
    """Build patches so _LOG_DIR / _TMP_DIR return controlled file lists."""
    log_paths = [Path(_FAKE_LOG_DIR / f) for f in (log_dir_files or [])]
    tmp_paths = [Path(_FAKE_TMP_DIR / f) for f in (tmp_dir_files or [])]

    def _read_text(self, errors="strict"):
        return getattr(self, "_fake_content", "")

    def _glob(self, pattern):
        return [p for p in (log_paths if self == _FAKE_LOG_DIR else tmp_paths)
                if p.suffix == ".log"]

    return (
        patch("metabolon.enzymes.auscultation._LOG_DIR", _FAKE_LOG_DIR),
        patch("metabolon.enzymes.auscultation._TMP_DIR", _FAKE_TMP_DIR),
        patch.object(Path, "exists", return_value=True),
        patch.object(Path, "glob", _glob),
        patch.object(Path, "read_text", _read_text),
    )


def _apply(ctx_list):
    """Enter a list of context managers and return the tuple of mocks."""
    entered = [c.__enter__() for c in ctx_list]
    return entered


# ---------------------------------------------------------------------------
# _read_log_lines
# ---------------------------------------------------------------------------

class TestReadLogLines:
    def test_reads_file_content(self, tmp_path):
        f = tmp_path / "test.log"
        f.write_text("line1\nline2\nline3")
        assert _read_log_lines(f) == ["line1", "line2", "line3"]

    def test_truncates_to_last_n(self, tmp_path):
        f = tmp_path / "test.log"
        lines = [f"line{i}" for i in range(300)]
        f.write_text("\n".join(lines))
        result = _read_log_lines(f, n=5)
        assert len(result) == 5
        assert result[0] == "line295"

    def test_returns_empty_on_missing_file(self):
        result = _read_log_lines(Path("/nonexistent/file.log"))
        assert result == []

    def test_default_n_is_200(self, tmp_path):
        f = tmp_path / "test.log"
        lines = [f"line{i}" for i in range(250)]
        f.write_text("\n".join(lines))
        result = _read_log_lines(f)
        assert len(result) == 200

    def test_replaces_decode_errors(self, tmp_path):
        f = tmp_path / "bad.log"
        f.write_bytes(b"valid\xff\xfealso valid")
        result = _read_log_lines(f)
        assert len(result) == 1


# ---------------------------------------------------------------------------
# _glob_logs
# ---------------------------------------------------------------------------

class TestGlobLogs:
    def test_returns_sorted_log_files(self):
        files = ["b.log", "a.log"]
        with _mock_paths(log_dir_files=files):
            ctx = [c for c in _mock_paths(log_dir_files=files)]
            # Re-enter for this test
            pass
        # Use a simpler approach: patch the module-level constants directly
        with patch("metabolon.enzymes.auscultation._LOG_DIR", _FAKE_LOG_DIR), \
             patch("metabolon.enzymes.auscultation._TMP_DIR", _FAKE_TMP_DIR), \
             patch.object(Path, "exists", return_value=True), \
             patch.object(Path, "glob", lambda self, pat: (
                 sorted([_FAKE_LOG_DIR / "a.log", _FAKE_LOG_DIR / "b.log"])
                 if self == _FAKE_LOG_DIR else []
             )):
            result = _glob_logs()
        assert len(result) == 2
        assert result[0].name == "a.log"
        assert result[1].name == "b.log"

    def test_includes_tmp_logs(self):
        with patch("metabolon.enzymes.auscultation._LOG_DIR", _FAKE_LOG_DIR), \
             patch("metabolon.enzymes.auscultation._TMP_DIR", _FAKE_TMP_DIR), \
             patch.object(Path, "exists", return_value=True), \
             patch.object(Path, "glob", lambda self, pat: (
                 [_FAKE_LOG_DIR / "sys.log"]
                 if self == _FAKE_LOG_DIR else
                 [_FAKE_TMP_DIR / "debug.log"]
             )):
            result = _glob_logs()
        names = [p.name for p in result]
        assert "sys.log" in names
        assert "debug.log" in names

    def test_empty_when_dirs_missing(self):
        with patch("metabolon.enzymes.auscultation._LOG_DIR", _FAKE_LOG_DIR), \
             patch("metabolon.enzymes.auscultation._TMP_DIR", _FAKE_TMP_DIR), \
             patch.object(Path, "exists", return_value=False):
            result = _glob_logs()
        assert result == []


# ---------------------------------------------------------------------------
# auscultation — unknown action
# ---------------------------------------------------------------------------

class TestUnknownAction:
    def test_unknown_action_returns_error(self):
        with patch("metabolon.enzymes.auscultation._LOG_DIR", _FAKE_LOG_DIR), \
             patch("metabolon.enzymes.auscultation._TMP_DIR", _FAKE_TMP_DIR):
            result = auscultation(action="bogus")
        assert "Unknown action" in result
        assert "bogus" in result


# ---------------------------------------------------------------------------
# auscultation — action=logs
# ---------------------------------------------------------------------------

class TestLogsAction:
    def _setup(self, log_contents: dict[str, str]):
        """Return patches that serve the given log_name->content mapping."""
        def read_text(self, errors="strict"):
            return log_contents.get(self.name, "")

        def glob(self, pat):
            return [Path(_FAKE_LOG_DIR / n) for n in log_contents if n.endswith(".log")]

        return (
            patch("metabolon.enzymes.auscultation._LOG_DIR", _FAKE_LOG_DIR),
            patch("metabolon.enzymes.auscultation._TMP_DIR", _FAKE_TMP_DIR),
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "glob", glob),
            patch.object(Path, "read_text", read_text),
        )

    def test_no_log_files_returns_message(self):
        with patch("metabolon.enzymes.auscultation._LOG_DIR", _FAKE_LOG_DIR), \
             patch("metabolon.enzymes.auscultation._TMP_DIR", _FAKE_TMP_DIR), \
             patch.object(Path, "exists", return_value=False):
            result = auscultation(action="logs")
        assert "No log files found" in result

    def test_reads_all_logs(self):
        ctx = self._setup({"app.log": "alpha\nbeta", "sys.log": "gamma"})
        with ctx[0], ctx[1], ctx[2], ctx[3], ctx[4]:
            result = auscultation(action="logs")
        assert "app.log" in result
        assert "sys.log" in result
        assert "alpha" in result

    def test_log_name_filter(self):
        ctx = self._setup({"app.log": "alpha", "other.log": "bravo"})
        with ctx[0], ctx[1], ctx[2], ctx[3], ctx[4]:
            result = auscultation(action="logs", log_name="app.log")
        assert "alpha" in result
        assert "other.log" not in result

    def test_log_name_not_found(self):
        ctx = self._setup({"app.log": "alpha"})
        with ctx[0], ctx[1], ctx[2], ctx[3], ctx[4]:
            result = auscultation(action="logs", log_name="missing.log")
        assert "Log not found" in result

    def test_filter_pattern(self):
        ctx = self._setup({"app.log": "ERROR bad\nINFO ok\nERROR worse"})
        with ctx[0], ctx[1], ctx[2], ctx[3], ctx[4]:
            result = auscultation(action="logs", filter_pattern="ERROR")
        assert "ERROR bad" in result
        assert "INFO ok" not in result
        assert "ERROR worse" in result

    def test_filter_pattern_no_matches(self):
        ctx = self._setup({"app.log": "INFO fine\nDEBUG ok"})
        with ctx[0], ctx[1], ctx[2], ctx[3], ctx[4]:
            result = auscultation(action="logs", filter_pattern="FATAL")
        assert "No log lines matching" in result
        assert "FATAL" in result

    def test_tail_lines_limits_output(self):
        lines = "\n".join(f"line{i}" for i in range(50))
        ctx = self._setup({"app.log": lines})
        with ctx[0], ctx[1], ctx[2], ctx[3], ctx[4]:
            result = auscultation(action="logs", tail_lines=3)
        # Should contain last 3 lines only
        assert "line49" in result
        assert "line0" not in result

    def test_empty_log_skipped(self):
        ctx = self._setup({"empty.log": "", "full.log": "content"})
        with ctx[0], ctx[1], ctx[2], ctx[3], ctx[4]:
            result = auscultation(action="logs")
        assert "full.log" in result
        assert "empty.log" not in result

    def test_header_shows_line_count(self):
        ctx = self._setup({"app.log": "a\nb\nc"})
        with ctx[0], ctx[1], ctx[2], ctx[3], ctx[4]:
            result = auscultation(action="logs")
        assert "(3 lines)" in result


# ---------------------------------------------------------------------------
# auscultation — action=errors
# ---------------------------------------------------------------------------

class TestErrorsAction:
    def _setup(self, log_contents: dict[str, str]):
        def read_text(self, errors="strict"):
            return log_contents.get(self.name, "")

        def glob(self, pat):
            return [Path(_FAKE_LOG_DIR / n) for n in log_contents if n.endswith(".log")]

        return (
            patch("metabolon.enzymes.auscultation._LOG_DIR", _FAKE_LOG_DIR),
            patch("metabolon.enzymes.auscultation._TMP_DIR", _FAKE_TMP_DIR),
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "glob", glob),
            patch.object(Path, "read_text", read_text),
        )

    def test_no_log_files(self):
        with patch("metabolon.enzymes.auscultation._LOG_DIR", _FAKE_LOG_DIR), \
             patch("metabolon.enzymes.auscultation._TMP_DIR", _FAKE_TMP_DIR), \
             patch.object(Path, "exists", return_value=False):
            result = auscultation(action="errors")
        assert "No log files found" in result

    def test_no_matching_errors(self):
        ctx = self._setup({"app.log": "INFO all good\nDEBUG fine"})
        with ctx[0], ctx[1], ctx[2], ctx[3], ctx[4]:
            result = auscultation(action="errors")
        assert "healthy" in result.lower()

    def test_counts_errors(self):
        log = textwrap.dedent("""\
            2025-01-01T12:00:00 ERROR connection failed to host 10.0.0.1
            2025-01-01T12:01:00 ERROR connection failed to host 10.0.0.2
            INFO ok
            2025-01-01T12:02:00 WARN disk space low
        """)
        ctx = self._setup({"app.log": log})
        with ctx[0], ctx[1], ctx[2], ctx[3], ctx[4]:
            result = auscultation(action="errors")
        assert "3 total error lines" in result
        assert "Count" in result
        assert "Pattern" in result

    def test_normalize_numbers_collapses_similar(self):
        log = "ERROR timeout after 5s\nERROR timeout after 10s\nERROR timeout after 99s\n"
        ctx = self._setup({"app.log": log})
        with ctx[0], ctx[1], ctx[2], ctx[3], ctx[4]:
            result = auscultation(action="errors", normalize_numbers=True)
        # All three should collapse to same pattern with N replacing digits
        assert "timeout after Ns" in result

    def test_no_normalize_numbers_keeps_original(self):
        log = "ERROR timeout after 5s\nERROR timeout after 10s\n"
        ctx = self._setup({"app.log": log})
        with ctx[0], ctx[1], ctx[2], ctx[3], ctx[4]:
            result = auscultation(action="errors", normalize_numbers=False)
        assert "timeout after 5s" in result
        assert "timeout after 10s" in result

    def test_custom_severity(self):
        log = "CRITICAL system down\nERROR minor issue\nINFO fine\n"
        ctx = self._setup({"app.log": log})
        with ctx[0], ctx[1], ctx[2], ctx[3], ctx[4]:
            result = auscultation(action="errors", severity="CRITICAL")
        assert "system down" in result
        assert "minor issue" not in result

    def test_top_n_limits_output(self):
        lines = [f"ERROR unique pattern {i}" for i in range(50)]
        log = "\n".join(lines) + "\n"
        ctx = self._setup({"app.log": log})
        with ctx[0], ctx[1], ctx[2], ctx[3], ctx[4]:
            result = auscultation(action="errors", top_n=5)
        # Count data rows (lines after header that start with spaces+digits)
        data_rows = [l for l in result.splitlines()
                     if l.strip() and l.strip()[0].isdigit()]
        assert len(data_rows) == 5

    def test_timestamps_stripped_in_normalization(self):
        log = "2025-03-15T08:00:00 ERROR crash\n2025-03-15T09:00:00 ERROR crash\n"
        ctx = self._setup({"app.log": log})
        with ctx[0], ctx[1], ctx[2], ctx[3], ctx[4]:
            result = auscultation(action="errors")
        # Both lines collapse to same pattern (timestamp stripped)
        assert "crash" in result

    def test_read_failure_skipped(self):
        """A log file that raises on read_text should be silently skipped."""
        def read_text(self, errors="strict"):
            if self.name == "bad.log":
                raise OSError("permission denied")
            return "ERROR visible error"

        def glob(self, pat):
            return [Path(_FAKE_LOG_DIR / "bad.log"), Path(_FAKE_LOG_DIR / "good.log")]

        with patch("metabolon.enzymes.auscultation._LOG_DIR", _FAKE_LOG_DIR), \
             patch("metabolon.enzymes.auscultation._TMP_DIR", _FAKE_TMP_DIR), \
             patch.object(Path, "exists", return_value=True), \
             patch.object(Path, "glob", glob), \
             patch.object(Path, "read_text", read_text):
            result = auscultation(action="errors")
        assert "visible error" in result

    def test_multiple_log_files_aggregated(self):
        ctx = self._setup({"a.log": "ERROR from a\n", "b.log": "WARN from b\n"})
        with ctx[0], ctx[1], ctx[2], ctx[3], ctx[4]:
            result = auscultation(action="errors")
        assert "2 total error lines" in result
        assert "2 logs" in result

    def test_action_case_insensitive(self):
        ctx = self._setup({"app.log": "ERROR oops\n"})
        with ctx[0], ctx[1], ctx[2], ctx[3], ctx[4]:
            result = auscultation(action="LOGS")
        assert "ERROR oops" in result

    def test_action_whitespace_stripped(self):
        ctx = self._setup({"app.log": "ERROR oops\n"})
        with ctx[0], ctx[1], ctx[2], ctx[3], ctx[4]:
            result = auscultation(action="  logs  ")
        assert "ERROR oops" in result
