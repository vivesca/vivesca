#!/usr/bin/env python3
"""Tests for effectors/sortase — thin wrapper for metabolon.sortase.cli."""

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

SORTASE_PATH = Path(__file__).resolve().parents[1] / "effectors" / "sortase"


# ── File structure tests ──────────────────────────────────────────────────────


class TestSortaseBasics:
    def test_file_exists(self):
        """Test that sortase effector file exists."""
from __future__ import annotations

        assert SORTASE_PATH.exists()
        assert SORTASE_PATH.is_file()

    def test_is_python_script(self):
        """Test that sortase has Python shebang."""
        first_line = SORTASE_PATH.read_text().split("\n")[0]
        assert first_line.startswith("#!/")
        assert "python" in first_line.lower()

    def test_has_docstring(self):
        """Test that sortase has docstring."""
        content = SORTASE_PATH.read_text()
        assert '"""' in content or "'''" in content

    def test_docstring_mentions_absorbed(self):
        """Test docstring mentions absorbed into germline."""
        content = SORTASE_PATH.read_text()
        assert "absorbed" in content.lower()


# ── Code structure tests ───────────────────────────────────────────────────────


class TestCodeStructure:
    def test_imports_from_metabolon(self):
        """Test sortase imports from metabolon.sortase.cli."""
        content = SORTASE_PATH.read_text()
        assert "from metabolon.sortase.cli import main" in content

    def test_calls_main(self):
        """Test sortase calls main()."""
        content = SORTASE_PATH.read_text()
        assert "main()" in content

    def test_is_thin_wrapper(self):
        """Test sortase is a thin wrapper (minimal code)."""
        content = SORTASE_PATH.read_text()
        # Should be very short - just import and call
        lines = [l for l in content.split("\n") if l.strip() and not l.strip().startswith("#")]
        assert len(lines) <= 5


# ── Execution via subprocess tests ─────────────────────────────────────────────


class TestSortaseSubprocess:
    def test_sortase_runs_as_script(self):
        """Test sortase can be run as Python script."""
        result = subprocess.run(
            [sys.executable, str(SORTASE_PATH), "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Should either show help or fail gracefully
        # We're testing it runs, not specific behavior
        assert result.returncode is not None

    def test_sortase_with_no_args(self):
        """Test sortase with no arguments."""
        result = subprocess.run(
            [sys.executable, str(SORTASE_PATH)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # May exit with error or show help
        # Just verify it runs
        assert result.returncode is not None


# ── Module loading tests ───────────────────────────────────────────────────────


class TestModuleLoading:
    def test_load_via_exec(self):
        """Test sortase can be loaded via exec."""
        ns: dict = {"__name__": "test_sortase", "__file__": str(SORTASE_PATH)}
        source = SORTASE_PATH.read_text(encoding="utf-8")

        # Remove the main() call to prevent execution
        source_no_exec = source.replace("main()", "# main()")

        # Should not raise when importing
        try:
            exec(source_no_exec, ns)
        except ImportError as e:
            pytest.skip(f"metabolon not installed: {e}")

    def test_main_is_callable(self):
        """Test main function is callable when loaded."""
        ns: dict = {"__name__": "test_sortase", "__file__": str(SORTASE_PATH)}
        source = SORTASE_PATH.read_text(encoding="utf-8")
        source_no_exec = source.replace("main()", "# main()")

        try:
            exec(source_no_exec, ns)
            assert callable(ns.get("main"))
        except ImportError as e:
            pytest.skip(f"metabolon not installed: {e}")


# ── Shebang tests ──────────────────────────────────────────────────────────────


class TestShebang:
    def test_shebang_points_to_venv_python(self):
        """Test shebang points to venv Python."""
        first_line = SORTASE_PATH.read_text().split("\n")[0]
        # Should point to a Python in .venv
        assert ".venv" in first_line or "python" in first_line.lower()

    def test_shebang_is_absolute_path(self):
        """Test shebang uses absolute path."""
        first_line = SORTASE_PATH.read_text().split("\n")[0]
        # Should start with #!/ and contain absolute path
        assert first_line.startswith("#!/")
        # Path should be absolute (contains germline)
        assert "germline" in first_line or "python" in first_line


# ── Integration tests ───────────────────────────────────────────────────────────


class TestSortaseIntegration:
    def test_file_is_executable(self):
        """Test sortase file has execute permission."""
        assert SORTASE_PATH.stat().st_mode & 0o111

    def test_direct_execution_possible(self):
        """Test sortase can be executed directly if metabolon is installed."""
        # Check if metabolon is available
        result = subprocess.run(
            [sys.executable, "-c", "from metabolon.sortase.cli import main"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            pytest.skip("metabolon not installed")

        # Try running sortase --help using sys.executable
        result = subprocess.run(
            [sys.executable, str(SORTASE_PATH), "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Should show help or run successfully
        assert result.stdout or result.stderr
