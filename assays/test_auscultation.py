"""Tests for metabolon.enzymes.auscultation."""
from __future__ import annotations

import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from metabolon.enzymes.auscultation import _glob_logs, _read_log_lines, auscultation


# ---------------------------------------------------------------------------
# _read_log_lines
# ---------------------------------------------------------------------------

class TestReadLogLines:
    def test_reads_existing_file(self, tmp_path):
        log = tmp_path / "test.log"
        log.write_text("line1\nline2\nline3\n")
        assert _read_log_lines(log) == ["line1", "line2", "line3"]

    def test_tails_to_n_lines(self, tmp_path):
        log = tmp_path / "big.log"
        lines = [f"line{i}" for i in range(20)]
        log.write_text("\n".join(lines) + "\n")
        result = _read_log_lines(log, n=5)
        assert len(result) == 5
        assert result[0] == "line15"

    def test_returns_empty_for_missing_file(self):
        assert _read_log_lines(Path("/nonexistent/file.log")) == []

    def test_handles_unreadable_file_gracefully(self, tmp_path):
        log = tmp_path / "unreadable.log"
        log.write_text("data\n")
        log.chmod(0)
        try:
            assert _read_log_lines(log) == []
        finally:
            log.chmod(0o644)


# ---------------------------------------------------------------------------
# _glob_logs
# ---------------------------------------------------------------------------

class TestGlobLogs:
    def test_returns_log_files_from_dirs(self, tmp_path):
        log_dir = tmp_path / "vivesca"
        log_dir.mkdir()
        (log_dir / "app.log").write_text("x")
        (log_dir / "other.txt").write_text("x")

        tmp_dir = tmp_path / "tmphome"
        tmp_dir.mkdir()
        (tmp_dir / "extra.log").write_text("x")

        with patch("metabolon.enzymes.auscultation._LOG_DIR", log_dir), \
             patch("metabolon.enzymes.auscultation._TMP_DIR", tmp_dir):
            result = _glob_logs()

        names = [p.name for p in result]
        assert "app.log" in names
        assert "extra.log" in names
        assert "other.txt" not in names

    def test_returns_empty_when_dirs_missing(self, tmp_path):
        missing = tmp_path / "nope"
        with patch("metabolon.enzymes.auscultation._LOG_DIR", missing), \
             patch("metabolon.enzymes.auscultation._TMP_DIR", missing):
            assert _glob_logs() == []


# ---------------------------------------------------------------------------
# auscultation — action: logs
# ---------------------------------------------------------------------------

class TestAuscultationLogs:
    def _make_logs(self, tmp_path, files: dict[str, str]):
        log_dir = tmp_path / "vivesca"
        log_dir.mkdir()
        for name, content in files.items():
            (log_dir / name).write_text(content)
        return log_dir

    def test_logs_action_returns_lines(self, tmp_path):
        log_dir = self._make_logs(tmp_path, {"app.log": "alpha\nbeta\n"})
        with patch("metabolon.enzymes.auscultation._LOG_DIR", log_dir), \
             patch("metabolon.enzymes.auscultation._TMP_DIR", tmp_path / "nope"):
            result = auscultation(action="logs")
        assert "alpha" in result
        assert "beta" in result
        assert "app.log" in result

    def test_logs_no_files_found(self, tmp_path):
        missing = tmp_path / "nope"
        with patch("metabolon.enzymes.auscultation._LOG_DIR", missing), \
             patch("metabolon.enzymes.auscultation._TMP_DIR", missing):
            result = auscultation(action="logs")
        assert "No log files found" in result

    def test_logs_with_filter_pattern(self, tmp_path):
        log_dir = self._make_logs(tmp_path, {
            "app.log": "ERROR something broke\nINFO all good\nWARN hmm\n"
        })
        with patch("metabolon.enzymes.auscultation._LOG_DIR", log_dir), \
             patch("metabolon.enzymes.auscultation._TMP_DIR", tmp_path / "nope"):
            result = auscultation(action="logs", filter_pattern="ERROR|WARN")
        assert "ERROR something broke" in result
        assert "WARN hmm" in result
        assert "INFO all good" not in result

    def test_logs_with_log_name_filter(self, tmp_path):
        log_dir = self._make_logs(tmp_path, {
            "app.log": "app-line\n",
            "sys.log": "sys-line\n",
        })
        with patch("metabolon.enzymes.auscultation._LOG_DIR", log_dir), \
             patch("metabolon.enzymes.auscultation._TMP_DIR", tmp_path / "nope"):
            result = auscultation(action="logs", log_name="sys.log")
        assert "sys-line" in result
        assert "app-line" not in result

    def test_logs_log_name_not_found(self, tmp_path):
        log_dir = self._make_logs(tmp_path, {"app.log": "data\n"})
        with patch("metabolon.enzymes.auscultation._LOG_DIR", log_dir), \
             patch("metabolon.enzymes.auscultation._TMP_DIR", tmp_path / "nope"):
            result = auscultation(action="logs", log_name="missing.log")
        assert "Log not found" in result

    def test_logs_no_matching_lines_after_filter(self, tmp_path):
        log_dir = self._make_logs(tmp_path, {"app.log": "INFO ok\n"})
        with patch("metabolon.enzymes.auscultation._LOG_DIR", log_dir), \
             patch("metabolon.enzymes.auscultation._TMP_DIR", tmp_path / "nope"):
            result = auscultation(action="logs", filter_pattern="CRITICAL")
        assert "No log lines matching" in result


# ---------------------------------------------------------------------------
# auscultation — action: errors
# ---------------------------------------------------------------------------

class TestAuscultationErrors:
    def _make_logs(self, tmp_path, files: dict[str, str]):
        log_dir = tmp_path / "vivesca"
        log_dir.mkdir()
        for name, content in files.items():
            (log_dir / name).write_text(content)
        return log_dir

    def test_errors_frequency_analysis(self, tmp_path):
        log_dir = self._make_logs(tmp_path, {
            "app.log": textwrap.dedent("""\
                2025-01-01T10:00:00 ERROR connection refused to 10.0.0.1
                2025-01-01T10:01:00 ERROR connection refused to 10.0.0.2
                INFO ok
                WARN disk low
            """),
        })
        with patch("metabolon.enzymes.auscultation._LOG_DIR", log_dir), \
             patch("metabolon.enzymes.auscultation._TMP_DIR", tmp_path / "nope"):
            result = auscultation(action="errors")

        assert "Error frequency analysis" in result
        assert "3 total error lines" in result  # 2 ERROR + 1 WARN
        # numbers normalized: "connection refused to N" appears twice
        assert "connection refused to N" in result

    def test_errors_no_log_files(self, tmp_path):
        missing = tmp_path / "nope"
        with patch("metabolon.enzymes.auscultation._LOG_DIR", missing), \
             patch("metabolon.enzymes.auscultation._TMP_DIR", missing):
            result = auscultation(action="errors")
        assert "No log files found" in result

    def test_errors_no_matching_severity(self, tmp_path):
        log_dir = self._make_logs(tmp_path, {"app.log": "INFO everything is fine\n"})
        with patch("metabolon.enzymes.auscultation._LOG_DIR", log_dir), \
             patch("metabolon.enzymes.auscultation._TMP_DIR", tmp_path / "nope"):
            result = auscultation(action="errors")
        assert "sounds healthy" in result

    def test_errors_without_number_normalization(self, tmp_path):
        log_dir = self._make_logs(tmp_path, {
            "app.log": "ERROR code 42\nERROR code 42\nERROR code 99\n"
        })
        with patch("metabolon.enzymes.auscultation._LOG_DIR", log_dir), \
             patch("metabolon.enzymes.auscultation._TMP_DIR", tmp_path / "nope"):
            result = auscultation(action="errors", normalize_numbers=False)
        assert "ERROR code 42" in result
        # Without normalization, code 42 and code 99 are separate patterns
        assert "code 99" in result

    def test_errors_custom_severity(self, tmp_path):
        log_dir = self._make_logs(tmp_path, {
            "app.log": "FATAL crash\nERROR bug\nINFO ok\n"
        })
        with patch("metabolon.enzymes.auscultation._LOG_DIR", log_dir), \
             patch("metabolon.enzymes.auscultation._TMP_DIR", tmp_path / "nope"):
            result = auscultation(action="errors", severity="FATAL")
        assert "FATAL crash" in result
        assert "1 total error lines" in result


# ---------------------------------------------------------------------------
# auscultation — unknown action
# ---------------------------------------------------------------------------

class TestAuscultationUnknownAction:
    def test_unknown_action_returns_message(self):
        result = auscultation(action="explode")
        assert "Unknown action" in result
        assert "explode" in result
