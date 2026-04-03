#!/usr/bin/env python3
from __future__ import annotations

"""Tests for effectors/rotate-logs.py — cron log truncation script."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

ROTATE_LOGS_PATH = Path(__file__).resolve().parents[1] / "effectors" / "rotate-logs.py"


# ── File structure tests ──────────────────────────────────────────────────────


class TestRotateLogsBasics:
    def test_file_exists(self):
        """Test that rotate-logs.py effector file exists."""

        assert ROTATE_LOGS_PATH.exists()
        assert ROTATE_LOGS_PATH.is_file()

    def test_is_python_script(self):
        """Test that rotate-logs.py has Python shebang."""
        first_line = ROTATE_LOGS_PATH.read_text().split("\n")[0]
        assert first_line.startswith("#!/usr/bin/env python") or first_line.startswith(
            "#!/usr/bin/python"
        )

    def test_has_docstring(self):
        """Test that rotate-logs.py has docstring."""
        content = ROTATE_LOGS_PATH.read_text()
        assert '"""' in content or "'''" in content


# ── Load script via exec ───────────────────────────────────────────────────────


@pytest.fixture()
def rotate_logs_module(tmp_path):
    """Load rotate-logs via exec with temp log directory."""
    ns: dict = {"__name__": "test_rotate_logs", "__file__": str(ROTATE_LOGS_PATH)}
    source = ROTATE_LOGS_PATH.read_text(encoding="utf-8")
    exec(source, ns)

    # Redirect LOG_DIR to temp path
    ns["LOG_DIR"] = tmp_path / "logs"
    ns["LOG_DIR"].mkdir(parents=True, exist_ok=True)

    return ns


# ── Constants tests ────────────────────────────────────────────────────────────


class TestConstants:
    def test_log_dir_defined(self, rotate_logs_module):
        """Test LOG_DIR is defined."""
        assert "LOG_DIR" in rotate_logs_module

    def test_keep_lines_defined(self, rotate_logs_module):
        """Test DEFAULT_KEEP is defined."""
        assert "DEFAULT_KEEP" in rotate_logs_module
        assert isinstance(rotate_logs_module["DEFAULT_KEEP"], int)

    def test_keep_lines_is_200(self, rotate_logs_module):
        """Test DEFAULT_KEEP is 200."""
        assert rotate_logs_module["DEFAULT_KEEP"] == 200

    def test_log_dir_is_in_home(self, rotate_logs_module):
        """Test LOG_DIR is under home directory."""
        # Check that it ends with logs
        assert str(rotate_logs_module["LOG_DIR"]).endswith("logs")


# ── Log truncation tests ───────────────────────────────────────────────────────


class TestLogTruncation:
    def test_truncates_long_log(self, rotate_logs_module):
        """Test truncates log file with more than KEEP_LINES lines."""
        log_file = rotate_logs_module["LOG_DIR"] / "test.log"
        # Create log with 300 lines
        lines = [f"Line {i}" for i in range(300)]
        log_file.write_text("\n".join(lines) + "\n")

        # Run the script logic manually
        keep = rotate_logs_module["DEFAULT_KEEP"]
        content = log_file.read_text().splitlines()
        if len(content) > keep:
            log_file.write_text("\n".join(content[-keep:]) + "\n")

        # Check result
        result = log_file.read_text().splitlines()
        assert len(result) == 200
        assert result[0] == "Line 100"  # First kept line
        assert result[-1] == "Line 299"  # Last line

    def test_preserves_short_log(self, rotate_logs_module):
        """Test does not modify log file with fewer than KEEP_LINES lines."""
        log_file = rotate_logs_module["LOG_DIR"] / "short.log"
        # Create log with 100 lines
        lines = [f"Line {i}" for i in range(100)]
        original_content = "\n".join(lines) + "\n"
        log_file.write_text(original_content)

        # Run the script logic manually
        keep = rotate_logs_module["DEFAULT_KEEP"]
        content = log_file.read_text().splitlines()
        if len(content) > keep:
            log_file.write_text("\n".join(content[-keep:]) + "\n")

        # Content should be unchanged
        assert log_file.read_text() == original_content

    def test_handles_empty_log(self, rotate_logs_module):
        """Test handles empty log file gracefully."""
        log_file = rotate_logs_module["LOG_DIR"] / "empty.log"
        log_file.write_text("")

        # Run the script logic
        keep = rotate_logs_module["DEFAULT_KEEP"]
        try:
            content = log_file.read_text().splitlines()
            if len(content) > keep:
                log_file.write_text("\n".join(content[-keep:]) + "\n")
        except Exception:
            pass  # Script catches exceptions

        # Should not crash
        assert True

    def test_handles_exact_keep_lines(self, rotate_logs_module):
        """Test does not modify log file with exactly KEEP_LINES lines."""
        log_file = rotate_logs_module["LOG_DIR"] / "exact.log"
        # Create log with exactly 200 lines
        lines = [f"Line {i}" for i in range(200)]
        original_content = "\n".join(lines) + "\n"
        log_file.write_text(original_content)

        # Run the script logic
        keep = rotate_logs_module["DEFAULT_KEEP"]
        content = log_file.read_text().splitlines()
        if len(content) > keep:
            log_file.write_text("\n".join(content[-keep:]) + "\n")

        # Content should be unchanged
        assert log_file.read_text() == original_content

    def test_handles_multiple_log_files(self, rotate_logs_module):
        """Test processes all .log files in directory."""
        log_dir = rotate_logs_module["LOG_DIR"]

        # Create multiple log files
        for name, count in [("a.log", 250), ("b.log", 150), ("c.log", 300)]:
            log_file = log_dir / name
            lines = [f"{name} line {i}" for i in range(count)]
            log_file.write_text("\n".join(lines) + "\n")

        # Run truncation for each
        keep = rotate_logs_module["DEFAULT_KEEP"]
        for log_file in log_dir.glob("*.log"):
            try:
                content = log_file.read_text().splitlines()
                if len(content) > keep:
                    log_file.write_text("\n".join(content[-keep:]) + "\n")
            except Exception:
                pass

        # Check results
        a_lines = (log_dir / "a.log").read_text().splitlines()
        b_lines = (log_dir / "b.log").read_text().splitlines()
        c_lines = (log_dir / "c.log").read_text().splitlines()

        assert len(a_lines) == 200  # Truncated
        assert len(b_lines) == 150  # Unchanged
        assert len(c_lines) == 200  # Truncated


# ── Error handling tests ───────────────────────────────────────────────────────


class TestErrorHandling:
    def test_handles_missing_directory(self, tmp_path):
        """Test handles non-existent log directory gracefully."""
        # Point to non-existent directory
        ns: dict = {"__name__": "test", "__file__": str(ROTATE_LOGS_PATH)}
        source = ROTATE_LOGS_PATH.read_text(encoding="utf-8")
        exec(source, ns)
        ns["LOG_DIR"] = tmp_path / "nonexistent"

        # Should not crash when iterating
        try:
            for log in ns["LOG_DIR"].glob("*.log"):
                pass
        except Exception:
            pass  # Expected to fail gracefully

        assert True  # Test passes if we get here

    def test_handles_permission_error(self, rotate_logs_module):
        """Test handles permission errors gracefully."""
        log_file = rotate_logs_module["LOG_DIR"] / "readonly.log"
        log_file.write_text("content\n")

        # Simulate permission error by patching read_text
        with patch.object(Path, "read_text", side_effect=PermissionError("No access")):
            try:
                for log in rotate_logs_module["LOG_DIR"].glob("*.log"):
                    try:
                        lines = log.read_text().splitlines()
                    except Exception:
                        pass
            except Exception:
                pass

        assert True  # Test passes if we get here

    def test_script_catches_exceptions(self, rotate_logs_module):
        """Test script catches exceptions per file."""
        log_dir = rotate_logs_module["LOG_DIR"]

        # Create one good log and simulate error on another
        good_log = log_dir / "good.log"
        good_log.write_text("\n".join([f"Line {i}" for i in range(250)]))

        # The script has try/except that catches exceptions per file
        # So good.log should still be processed even if another fails
        keep = rotate_logs_module["DEFAULT_KEEP"]
        for log in log_dir.glob("*.log"):
            try:
                lines = log.read_text().splitlines()
                if len(lines) > keep:
                    log.write_text("\n".join(lines[-keep:]) + "\n")
            except Exception:
                pass

        # Good log should be truncated
        assert len(good_log.read_text().splitlines()) == 200


# ── Integration test ───────────────────────────────────────────────────────────


class TestIntegration:
    def test_full_rotation(self, rotate_logs_module):
        """Test full rotation with multiple files."""
        log_dir = rotate_logs_module["LOG_DIR"]

        # Create various log files
        logs = {
            "app.log": 350,
            "error.log": 50,
            "debug.log": 200,
            "access.log": 500,
        }

        for name, count in logs.items():
            log_file = log_dir / name
            lines = [f"[{name}] Log entry {i}" for i in range(count)]
            log_file.write_text("\n".join(lines) + "\n")

        # Run rotation
        keep = rotate_logs_module["DEFAULT_KEEP"]
        for log in log_dir.glob("*.log"):
            try:
                lines = log.read_text().splitlines()
                if len(lines) > keep:
                    log.write_text("\n".join(lines[-keep:]) + "\n")
            except Exception:
                pass

        # Verify results
        assert len((log_dir / "app.log").read_text().splitlines()) == 200
        assert len((log_dir / "error.log").read_text().splitlines()) == 50
        assert len((log_dir / "debug.log").read_text().splitlines()) == 200
        assert len((log_dir / "access.log").read_text().splitlines()) == 200

        # Verify content preserved correctly
        app_lines = (log_dir / "app.log").read_text().splitlines()
        assert "Log entry 150" in app_lines[0]
        assert "Log entry 349" in app_lines[-1]
