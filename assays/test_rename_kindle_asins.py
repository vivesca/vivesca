#!/usr/bin/env python3
"""Tests for effectors/rename-kindle-asins.py — rename ASIN Kindle files to titles.

rename-kindle-asins.py is a script (effectors/rename-kindle-asins.py), not an importable module.
It is loaded via exec() into isolated namespaces.
Note: The script runs its rename loop at module level (no main() function),
so exec-based tests focus on loading the mapping and verifying structure.
Functional rename tests use subprocess with temp directories.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

RENAME_PATH = Path(__file__).resolve().parents[1] / "effectors" / "rename-kindle-asins.py"


# ── File structure tests ───────────────────────────────────────────────────


class TestRenameKindleAsinsBasics:
    def test_file_exists(self):
        """Test that rename-kindle-asins.py effector file exists."""
        assert RENAME_PATH.exists()
        assert RENAME_PATH.is_file()

    def test_is_python_script(self):
        """Test that rename-kindle-asins.py has Python shebang."""
        first_line = RENAME_PATH.read_text().split("\n")[0]
        assert first_line.startswith("#!/")
        assert "python" in first_line.lower()

    def test_has_docstring(self):
        """Test that rename-kindle-asins.py has docstring."""
        content = RENAME_PATH.read_text()
        assert '"""' in content

    def test_docstring_mentions_rename(self):
        """Test docstring mentions renaming or ASIN."""
        content = RENAME_PATH.read_text()
        lower = content.lower()
        assert "rename" in lower or "asin" in lower


# ── Code structure tests ───────────────────────────────────────────────────


class TestCodeStructure:
    def test_has_asin_mapping(self):
        """Test that script contains ASIN_TO_TITLE dictionary."""
        content = RENAME_PATH.read_text()
        assert "ASIN_TO_TITLE" in content

    def test_has_dry_run_support(self):
        """Test that script supports --dry-run flag."""
        content = RENAME_PATH.read_text()
        assert "dry_run" in content or "--dry-run" in content

    def test_has_books_dir(self):
        """Test that script references Books directory."""
        content = RENAME_PATH.read_text()
        assert "BOOKS_DIR" in content
        assert "Books" in content

    def test_mapping_has_known_asins(self):
        """Test mapping contains specific known ASINs."""
        content = RENAME_PATH.read_text()
        assert "B00CNQ2NTK" in content  # Awakenings
        assert "B08FGV64B1" in content  # Four Thousand Weeks
        assert "B0CM8TRWK3" in content  # Co-Intelligence

    def test_mapping_has_known_titles(self):
        """Test mapping contains specific known titles."""
        content = RENAME_PATH.read_text()
        assert "Awakenings" in content
        assert "Four Thousand Weeks" in content
        assert "Co-Intelligence" in content

    def test_uses_pathlib(self):
        """Test that script uses pathlib.Path."""
        content = RENAME_PATH.read_text()
        assert "from pathlib import Path" in content

    def test_no_main_function(self):
        """Test that script runs logic at module level."""
        content = RENAME_PATH.read_text()
        assert "def main" not in content

    def test_has_rename_call(self):
        """Test that script calls src.rename(dst)."""
        content = RENAME_PATH.read_text()
        assert ".rename(" in content

    def test_checks_src_exists(self):
        """Test that script checks if source file exists before renaming."""
        content = RENAME_PATH.read_text()
        assert ".exists()" in content


# ── exec loading tests ─────────────────────────────────────────────────────


class TestExecLoading:
    def test_load_via_exec(self, capsys):
        """Test script can be loaded via exec (runs loop harmlessly)."""
        ns: dict = {"__name__": "test_rename_kindle", "__file__": str(RENAME_PATH)}
        source = RENAME_PATH.read_text(encoding="utf-8")
        with patch("sys.argv", ["rename-kindle-asins.py"]):
            exec(source, ns)
        assert "ASIN_TO_TITLE" in ns
        # Captures the "Renamed 0 files." print
        captured = capsys.readouterr()
        assert "Renamed 0 files" in captured.out or "Would rename 0 files" in captured.out

    def test_asin_mapping_loaded(self, capsys):
        """Test ASIN_TO_TITLE mapping is accessible after exec."""
        ns: dict = {"__name__": "test_rename_kindle", "__file__": str(RENAME_PATH)}
        source = RENAME_PATH.read_text(encoding="utf-8")
        with patch("sys.argv", ["rename-kindle-asins.py"]):
            exec(source, ns)
        capsys.readouterr()  # consume output
        mapping = ns["ASIN_TO_TITLE"]
        assert isinstance(mapping, dict)
        assert len(mapping) > 0

    def test_asin_mapping_keys_are_asin_format(self, capsys):
        """Test all keys look like ASINs (10+ alphanumeric)."""
        ns: dict = {"__name__": "test_rename_kindle", "__file__": str(RENAME_PATH)}
        source = RENAME_PATH.read_text(encoding="utf-8")
        with patch("sys.argv", ["rename-kindle-asins.py"]):
            exec(source, ns)
        capsys.readouterr()  # consume output
        for key in ns["ASIN_TO_TITLE"]:
            assert len(key) >= 10, f"ASIN key too short: {key}"
            assert key.isalnum(), f"ASIN key not alphanumeric: {key}"

    def test_asin_mapping_values_are_nonempty(self, capsys):
        """Test all title values are non-empty strings."""
        ns: dict = {"__name__": "test_rename_kindle", "__file__": str(RENAME_PATH)}
        source = RENAME_PATH.read_text(encoding="utf-8")
        with patch("sys.argv", ["rename-kindle-asins.py"]):
            exec(source, ns)
        capsys.readouterr()  # consume output
        for asin, title in ns["ASIN_TO_TITLE"].items():
            assert isinstance(title, str) and len(title) > 0, f"Empty title for {asin}"

    def test_dry_run_flag_recognized(self, capsys):
        """Test --dry-run flag is recognized during exec."""
        ns: dict = {"__name__": "test_rename_kindle", "__file__": str(RENAME_PATH)}
        source = RENAME_PATH.read_text(encoding="utf-8")
        with patch("sys.argv", ["rename-kindle-asins.py", "--dry-run"]):
            exec(source, ns)
        capsys.readouterr()  # consume output
        assert ns["dry_run"] is True

    def test_no_dry_run_flag_default(self, capsys):
        """Test dry_run is False when flag not present."""
        ns: dict = {"__name__": "test_rename_kindle", "__file__": str(RENAME_PATH)}
        source = RENAME_PATH.read_text(encoding="utf-8")
        with patch("sys.argv", ["rename-kindle-asins.py"]):
            exec(source, ns)
        capsys.readouterr()  # consume output
        assert ns["dry_run"] is False


# ── Functional rename tests via subprocess ─────────────────────────────────


class TestFunctionalRename:
    def test_rename_in_temp_dir(self):
        """Should rename ASIN files to title files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            src = Path(tmpdir) / "B00CNQ2NTK.md"
            src.write_text("# Awakenings notes")

            wrapper = f"""
import sys
from pathlib import Path
source = open({str(RENAME_PATH)!r}).read()
source = source.replace(
    str(Path.home() / "notes" / "Books"),
    {tmpdir!r}
)
sys.argv = ["rename-kindle-asins.py"]
exec(source, {{"__name__": "__main__", "__file__": {str(RENAME_PATH)!r}, "sys": sys}})
"""
            r = subprocess.run(
                [sys.executable, "-c", wrapper],
                capture_output=True, text=True, timeout=30,
            )
            assert r.returncode == 0
            assert (Path(tmpdir) / "Awakenings.md").exists()
            assert not (Path(tmpdir) / "B00CNQ2NTK.md").exists()

    def test_dry_run_does_not_rename(self):
        """Should not actually rename files in dry-run mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            src = Path(tmpdir) / "B00CNQ2NTK.md"
            src.write_text("# Awakenings notes")

            wrapper = f"""
import sys
from pathlib import Path
source = open({str(RENAME_PATH)!r}).read()
source = source.replace(
    str(Path.home() / "notes" / "Books"),
    {tmpdir!r}
)
sys.argv = ["rename-kindle-asins.py", "--dry-run"]
ns = {{"__name__": "__main__", "__file__": {str(RENAME_PATH)!r}, "sys": sys}}
exec(source, ns)
"""
            r = subprocess.run(
                [sys.executable, "-c", wrapper],
                capture_output=True, text=True, timeout=30,
            )
            assert r.returncode == 0
            assert src.exists()
            assert not (Path(tmpdir) / "Awakenings.md").exists()
            assert "dry-run" in r.stdout.lower() or "Would rename" in r.stdout

    def test_skip_when_dest_exists(self):
        """Should skip rename when destination file already exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            src = Path(tmpdir) / "B00CNQ2NTK.md"
            src.write_text("# Original")
            dst = Path(tmpdir) / "Awakenings.md"
            dst.write_text("# Existing")

            wrapper = f"""
import sys
from pathlib import Path
source = open({str(RENAME_PATH)!r}).read()
source = source.replace(
    str(Path.home() / "notes" / "Books"),
    {tmpdir!r}
)
sys.argv = ["rename-kindle-asins.py"]
ns = {{"__name__": "__main__", "__file__": {str(RENAME_PATH)!r}, "sys": sys}}
exec(source, ns)
"""
            r = subprocess.run(
                [sys.executable, "-c", wrapper],
                capture_output=True, text=True, timeout=30,
            )
            assert r.returncode == 0
            assert src.exists()
            assert dst.exists()
            assert "SKIP" in r.stdout

    def test_no_files_to_rename(self):
        """Should report 0 renamed when no ASIN files exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            wrapper = f"""
import sys
from pathlib import Path
source = open({str(RENAME_PATH)!r}).read()
source = source.replace(
    str(Path.home() / "notes" / "Books"),
    {tmpdir!r}
)
sys.argv = ["rename-kindle-asins.py"]
ns = {{"__name__": "__main__", "__file__": {str(RENAME_PATH)!r}, "sys": sys}}
exec(source, ns)
"""
            r = subprocess.run(
                [sys.executable, "-c", wrapper],
                capture_output=True, text=True, timeout=30,
            )
            assert r.returncode == 0
            assert "Renamed 0 files" in r.stdout

    def test_multiple_renames(self):
        """Should rename multiple ASIN files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "B00CNQ2NTK.md").write_text("# Awakenings")
            (Path(tmpdir) / "B08FGV64B1.md").write_text("# Four Thousand Weeks")

            wrapper = f"""
import sys
from pathlib import Path
source = open({str(RENAME_PATH)!r}).read()
source = source.replace(
    str(Path.home() / "notes" / "Books"),
    {tmpdir!r}
)
sys.argv = ["rename-kindle-asins.py"]
ns = {{"__name__": "__main__", "__file__": {str(RENAME_PATH)!r}, "sys": sys}}
exec(source, ns)
"""
            r = subprocess.run(
                [sys.executable, "-c", wrapper],
                capture_output=True, text=True, timeout=30,
            )
            assert r.returncode == 0
            assert (Path(tmpdir) / "Awakenings.md").exists()
            assert (Path(tmpdir) / "Four Thousand Weeks.md").exists()
            assert "Renamed 2 files" in r.stdout


# ── CLI subprocess ──────────────────────────────────────────────────────────


class TestCLISubprocess:
    def test_runs_without_error(self):
        """Running rename-kindle-asins.py directly should succeed."""
        r = subprocess.run(
            [sys.executable, str(RENAME_PATH)],
            capture_output=True, text=True, timeout=30,
        )
        assert r.returncode == 0
        assert "Renamed" in r.stdout

    def test_dry_run_flag(self):
        """Running with --dry-run should show would-rename message."""
        r = subprocess.run(
            [sys.executable, str(RENAME_PATH), "--dry-run"],
            capture_output=True, text=True, timeout=30,
        )
        assert r.returncode == 0
        assert "Would rename" in r.stdout or "Renamed" in r.stdout
