"""Tests for metabolon/enzymes/auscultation — deterministic log reading."""
from __future__ import annotations

import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from metabolon.enzymes.auscultation import (
    auscultation,
    _read_log_lines,
    _glob_logs,
    _LOG_DIR,
    _TMP_DIR,
)


# ── _read_log_lines ───────────────────────────────────────────────────

class TestReadLogLines:
    def test_reads_last_n_lines(self, tmp_path):
        p = tmp_path / "test.log"
        p.write_text("line1\nline2\nline3\nline4\nline5\n")
        assert _read_log_lines(p, n=3) == ["line3", "line4", "line5"]

    def test_reads_all_when_fewer_than_n(self, tmp_path):
        p = tmp_path / "short.log"
        p.write_text("only\n")
        assert _read_log_lines(p, n=200) == ["only"]

    def test_returns_empty_for_missing_file(self, tmp_path):
        p = tmp_path / "nonexistent.log"
        assert _read_log_lines(p) == []

    def test_handles_read_error_gracefully(self):
        bad_path = MagicMock(spec=Path)
        bad_path.read_text.side_effect = OSError("permission denied")
        assert _read_log_lines(bad_path) == []

    def test_default_n_is_200(self, tmp_path):
        p = tmp_path / "big.log"
        lines = [f"line{i}" for i in range(300)]
        p.write_text("\n".join(lines) + "\n")
        result = _read_log_lines(p)
        assert len(result) == 200
        assert result[0] == "line100"


# ── _glob_logs ────────────────────────────────────────────────────────

class TestGlobLogs:
    @patch.object(Path, "home")
    def test_returns_sorted_logs_from_both_dirs(self, mock_home):
        base = MagicMock(return_value=None)  # stub
        # Build a fake home with log dirs
        fake_home = MagicMock(spec=Path)
        mock_home.return_value = fake_home

        log_dir = MagicMock(spec=Path)
        tmp_dir = MagicMock(spec=Path)
        # Patch module-level _LOG_DIR and _TMP_DIR via the module
        with patch("metabolon.enzymes.auscultation._LOG_DIR", log_dir), \
             patch("metabolon.enzymes.auscultation._TMP_DIR", tmp_dir):
            log_dir.exists.return_value = True
            f1 = MagicMock(spec=Path)
            f1.name = "b.log"
            f2 = MagicMock(spec=Path)
            f2.name = "a.log"
            log_dir.glob.return_value = [f1, f2]

            tmp_dir.exists.return_value = True
            f3 = MagicMock(spec=Path)
            f3.name = "c.log"
            tmp_dir.glob.return_value = [f3]

            result = _glob_logs()
            # sorted([f1, f2]) + [f3]
            assert len(result) == 3

    @patch("metabolon.enzymes.auscultation._LOG_DIR")
    @patch("metabolon.enzymes.auscultation._TMP_DIR")
    def test_skips_nonexistent_dirs(self, mock_tmp, mock_log):
        mock_log.exists.return_value = False
        mock_tmp.exists.return_value = False
        assert _glob_logs() == []

    @patch("metabolon.enzymes.auscultation._LOG_DIR")
    @patch("metabolon.enzymes.auscultation._TMP_DIR")
    def test_one_dir_exists(self, mock_tmp, mock_log):
        mock_log.exists.return_value = True
        f = MagicMock(spec=Path)
        f.name = "x.log"
        mock_log.glob.return_value = [f]
        mock_tmp.exists.return_value = False
        result = _glob_logs()
        assert result == [f]


# ── auscultation tool ────────────────────────────────────────────────

class TestAuscultationLogs:
    """Tests for action='logs'."""

    @patch("metabolon.enzymes.auscultation._glob_logs")
    def test_no_logs_found(self, mock_glob):
        mock_glob.return_value = []
        result = auscultation(action="logs")
        assert "No log files found" in result

    @patch("metabolon.enzymes.auscultation._glob_logs")
    @patch("metabolon.enzymes.auscultation._read_log_lines")
    def test_returns_log_content(self, mock_read, mock_glob):
        fake_log = MagicMock(spec=Path)
        fake_log.name = "app.log"
        mock_glob.return_value = [fake_log]
        mock_read.return_value = ["INFO starting up", "INFO running"]
        result = auscultation(action="logs")
        assert "=== app.log (2 lines) ===" in result
        assert "INFO starting up" in result

    @patch("metabolon.enzymes.auscultation._glob_logs")
    @patch("metabolon.enzymes.auscultation._read_log_lines")
    def test_filter_pattern(self, mock_read, mock_glob):
        fake_log = MagicMock(spec=Path)
        fake_log.name = "app.log"
        mock_glob.return_value = [fake_log]
        mock_read.return_value = ["INFO ok", "ERROR bad", "INFO fine"]
        result = auscultation(action="logs", filter_pattern="ERROR")
        assert "ERROR bad" in result
        assert "INFO ok" not in result

    @patch("metabolon.enzymes.auscultation._glob_logs")
    def test_log_name_filters_to_specific_file(self, mock_glob):
        fake_log = MagicMock(spec=Path)
        fake_log.name = "target.log"
        other_log = MagicMock(spec=Path)
        other_log.name = "other.log"
        mock_glob.return_value = [fake_log, other_log]

        with patch("metabolon.enzymes.auscultation._read_log_lines") as mock_read:
            mock_read.return_value = ["line1"]
            result = auscultation(action="logs", log_name="target.log")
        assert "target.log" in result
        # other.log should not appear as a section header
        assert "=== other.log" not in result

    @patch("metabolon.enzymes.auscultation._glob_logs")
    def test_log_name_not_found(self, mock_glob):
        fake_log = MagicMock(spec=Path)
        fake_log.name = "other.log"
        mock_glob.return_value = [fake_log]
        result = auscultation(action="logs", log_name="missing.log")
        assert "Log not found: missing.log" in result

    @patch("metabolon.enzymes.auscultation._glob_logs")
    @patch("metabolon.enzymes.auscultation._read_log_lines")
    def test_no_matching_lines_with_filter(self, mock_read, mock_glob):
        fake_log = MagicMock(spec=Path)
        fake_log.name = "app.log"
        mock_glob.return_value = [fake_log]
        mock_read.return_value = ["INFO ok", "INFO fine"]
        result = auscultation(action="logs", filter_pattern="ERROR")
        assert "No log lines matching 'ERROR' found" in result

    @patch("metabolon.enzymes.auscultation._glob_logs")
    @patch("metabolon.enzymes.auscultation._read_log_lines")
    def test_no_matching_lines_without_filter(self, mock_read, mock_glob):
        fake_log = MagicMock(spec=Path)
        fake_log.name = "app.log"
        mock_glob.return_value = [fake_log]
        mock_read.return_value = []
        result = auscultation(action="logs")
        assert "No log lines found" in result


class TestAuscultationErrors:
    """Tests for action='errors'."""

    @patch("metabolon.enzymes.auscultation._glob_logs")
    def test_no_logs_found(self, mock_glob):
        mock_glob.return_value = []
        result = auscultation(action="errors")
        assert "No log files found" in result

    @patch("metabolon.enzymes.auscultation._glob_logs")
    def test_no_error_lines(self, mock_glob, tmp_path):
        fake_log = tmp_path / "clean.log"
        fake_log.write_text("INFO all good\nINFO still good\n")
        mock_glob.return_value = [fake_log]
        result = auscultation(action="errors")
        assert "sounds healthy" in result

    @patch("metabolon.enzymes.auscultation._glob_logs")
    def test_counts_errors_with_normalization(self, mock_glob, tmp_path):
        log_file = tmp_path / "errors.log"
        log_file.write_text(textwrap.dedent("""\
            2025-01-01T12:00:00 ERROR connection to host 10 failed
            2025-01-01T12:01:00 ERROR connection to host 20 failed
            2025-01-01T12:02:00 ERROR connection to host 30 failed
            INFO everything is fine
            WARN disk usage at 80%
        """))
        mock_glob.return_value = [log_file]
        result = auscultation(action="errors", severity="ERROR|WARN")
        assert "4 total error lines" in result
        # Numbers should be normalized to 'N' so all three connection errors collapse
        assert "connection to host N failed" in result
        assert "disk usage at N%" in result

    @patch("metabolon.enzymes.auscultation._glob_logs")
    def test_top_n_limits_output(self, mock_glob, tmp_path):
        log_file = tmp_path / "many.log"
        lines = [f"ERROR unique error type {i}" for i in range(30)]
        log_file.write_text("\n".join(lines) + "\n")
        mock_glob.return_value = [log_file]
        result = auscultation(action="errors", top_n=5)
        # Count the pattern rows (exclude header lines)
        data_lines = [l for l in result.splitlines() if l and l[0].isdigit() or (l and l[:6].strip().isdigit())]
        # The header + separator + count lines — let's just check <=5 patterns shown
        count_lines = [l for l in result.splitlines() if l.strip() and not l.startswith("Error") and not l.startswith("---") and not l.startswith("Count")]
        assert len(count_lines) <= 5

    @patch("metabolon.enzymes.auscultation._glob_logs")
    def test_no_normalize_numbers(self, mock_glob, tmp_path):
        log_file = tmp_path / "nums.log"
        log_file.write_text("ERROR failed port 8080\nERROR failed port 9090\n")
        mock_glob.return_value = [log_file]
        result = auscultation(action="errors", normalize_numbers=False)
        # Each line should be counted separately (not normalized)
        assert "2 total error lines" not in result  # they are distinct
        # Both original patterns should appear
        assert "failed port 8080" in result
        assert "failed port 9090" in result

    @patch("metabolon.enzymes.auscultation._glob_logs")
    def test_custom_severity(self, mock_glob, tmp_path):
        log_file = tmp_path / "custom.log"
        log_file.write_text("CRITICAL system down\nERROR minor issue\nINFO ok\n")
        mock_glob.return_value = [log_file]
        result = auscultation(action="errors", severity="CRITICAL")
        assert "CRITICAL system down" in result
        # ERROR should not be counted since we only asked for CRITICAL
        assert "1 total error lines" in result

    @patch("metabolon.enzymes.auscultation._glob_logs")
    def test_handles_unreadable_log_gracefully(self, mock_glob):
        bad_log = MagicMock(spec=Path)
        bad_log.read_text.side_effect = OSError("permission denied")
        bad_log.name = "bad.log"
        # Need a good log too so we don't just get "no logs"
        mock_glob.return_value = [bad_log]
        result = auscultation(action="errors")
        # Should not crash; the bad log is skipped
        assert "No lines matching" in result or "total error lines" in result


class TestAuscultationUnknownAction:
    def test_unknown_action(self):
        result = auscultation(action="bogus")
        assert "Unknown action: bogus" in result
        assert "logs|errors" in result

    def test_action_is_case_insensitive(self):
        # uppercase should still work
        with patch("metabolon.enzymes.auscultation._glob_logs") as mock_glob:
            mock_glob.return_value = []
            result = auscultation(action="LOGS")
            assert "No log files found" in result
