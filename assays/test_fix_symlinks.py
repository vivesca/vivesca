from __future__ import annotations

"""Tests for effectors/fix-symlinks.

Effectors are scripts — loaded via exec(open(path).read(), ns), never imported.
"""

import os
import subprocess
import sys
import types
from pathlib import Path

import pytest

EFFECTORS_DIR = Path(__file__).resolve().parent.parent / "effectors"
SCRIPT = EFFECTORS_DIR / "fix-symlinks"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_ns() -> dict:
    """Load fix-symlinks into a namespace dict."""
    assert SCRIPT.exists(), f"Effector not found: {SCRIPT}"
    mod = types.ModuleType("_test_fix_symlinks_mod")
    mod.__file__ = str(SCRIPT)
    mod.__name__ = "_test_fix_symlinks_mod"
    old = sys.modules.get(mod.__name__)
    sys.modules[mod.__name__] = mod
    try:
        exec(SCRIPT.read_text(), mod.__dict__)
    except Exception:
        sys.modules.pop(mod.__name__, None)
        if old is not None:
            sys.modules[mod.__name__] = old
        raise
    return mod.__dict__


# ---------------------------------------------------------------------------
# scan_and_fix tests
# ---------------------------------------------------------------------------

class TestScanAndFix:
    """Test scan_and_fix via exec-loaded namespace."""

    def load_with_tmpdir(self, tmp_path: Path):
        """Load the script, patch SCAN_DIRS to tmp_path subdirs, return (ns, dirs)."""
        ns = _load_ns()
        # Create three scan dirs under tmp_path
        dirs = []
        for name in ("cla", "epi", "ger"):
            d = tmp_path / name
            d.mkdir()
            dirs.append(str(d))
        ns["SCAN_DIRS"] = dirs
        return ns, dirs

    def test_fixes_broken_mac_symlink(self, tmp_path):
        """A symlink targeting /Users/terry/... should be rewritten to /home/terry/..."""
        ns, dirs = self.load_with_tmpdir(tmp_path)
        scan_dir = Path(dirs[0])

        # Create a real file at the linux target
        linux_target = Path.home() / "fix_symlinks_test_target.txt"
        linux_target.write_text("hello")

        # Create a symlink pointing to the mac-style path
        mac_target = f"/Users/terry/fix_symlinks_test_target.txt"
        link = scan_dir / "mylink"
        link.symlink_to(mac_target)

        try:
            fixed, skipped = ns["scan_and_fix"]()
            assert fixed == 1
            assert skipped == 0
            assert os.readlink(link) == str(linux_target)
        finally:
            linux_target.unlink(missing_ok=True)

    def test_skips_missing_target(self, tmp_path, capsys):
        """A symlink whose target does not exist on linux should be skipped."""
        ns, dirs = self.load_with_tmpdir(tmp_path)
        scan_dir = Path(dirs[0])

        # Symlink pointing to a mac path that doesn't exist on linux
        link = scan_dir / "dangling"
        link.symlink_to("/Users/terry/__nonexistent_file_xyz__")

        fixed, skipped = ns["scan_and_fix"]()
        assert fixed == 0
        assert skipped == 1
        # Original symlink unchanged
        assert os.readlink(link) == "/Users/terry/__nonexistent_file_xyz__"
        out = capsys.readouterr().out
        assert "WARNING" in out

    def test_ignores_non_mac_symlinks(self, tmp_path):
        """Symlinks without /Users/terry/ in the target should be left alone."""
        ns, dirs = self.load_with_tmpdir(tmp_path)
        scan_dir = Path(dirs[0])

        # Create a real file and a valid linux symlink
        real = scan_dir / "real.txt"
        real.write_text("data")
        link = scan_dir / "goodlink"
        link.symlink_to(str(real))

        fixed, skipped = ns["scan_and_fix"]()
        assert fixed == 0
        assert skipped == 0
        assert os.readlink(link) == str(real)

    def test_ignores_regular_files(self, tmp_path):
        """Regular (non-symlink) files should be completely ignored."""
        ns, dirs = self.load_with_tmpdir(tmp_path)
        scan_dir = Path(dirs[0])
        (scan_dir / "plain.txt").write_text("just a file")

        fixed, skipped = ns["scan_and_fix"]()
        assert fixed == 0
        assert skipped == 0

    def test_idempotent(self, tmp_path):
        """Running scan_and_fix twice should fix once and leave alone on second pass."""
        ns, dirs = self.load_with_tmpdir(tmp_path)
        scan_dir = Path(dirs[0])

        linux_target = Path.home() / "fix_symlinks_idem_target.txt"
        linux_target.write_text("hello")

        link = scan_dir / "link"
        link.symlink_to("/Users/terry/fix_symlinks_idem_target.txt")

        try:
            fixed1, skipped1 = ns["scan_and_fix"]()
            assert fixed1 == 1
            fixed2, skipped2 = ns["scan_and_fix"]()
            assert fixed2 == 0
            assert skipped2 == 0
        finally:
            linux_target.unlink(missing_ok=True)

    def test_skips_nonexistent_scan_dirs(self, tmp_path):
        """SCAN_DIRS entries that don't exist on disk are silently skipped."""
        ns = _load_ns()
        ns["SCAN_DIRS"] = ["/tmp/__fix_symlinks_no_such_dir__"]
        fixed, skipped = ns["scan_and_fix"]()
        assert fixed == 0
        assert skipped == 0

    def test_multiple_fixes_across_dirs(self, tmp_path):
        """Broken symlinks in multiple scan dirs are all fixed."""
        ns, dirs = self.load_with_tmpdir(tmp_path)

        linux_file_a = Path.home() / "fix_symlinks_multi_a.txt"
        linux_file_b = Path.home() / "fix_symlinks_multi_b.txt"
        linux_file_a.write_text("a")
        linux_file_b.write_text("b")

        link_a = Path(dirs[0]) / "link_a"
        link_a.symlink_to("/Users/terry/fix_symlinks_multi_a.txt")
        link_b = Path(dirs[1]) / "link_b"
        link_b.symlink_to("/Users/terry/fix_symlinks_multi_b.txt")

        try:
            fixed, skipped = ns["scan_and_fix"]()
            assert fixed == 2
            assert skipped == 0
            assert os.readlink(link_a) == str(linux_file_a)
            assert os.readlink(link_b) == str(linux_file_b)
        finally:
            linux_file_a.unlink(missing_ok=True)
            linux_file_b.unlink(missing_ok=True)

    def test_nested_symlinks_found(self, tmp_path):
        """Broken symlinks in subdirectories are also found and fixed."""
        ns, dirs = self.load_with_tmpdir(tmp_path)
        scan_dir = Path(dirs[0])
        nested = scan_dir / "sub" / "deep"
        nested.mkdir(parents=True)

        linux_target = Path.home() / "fix_symlinks_nested.txt"
        linux_target.write_text("deep")

        link = nested / "deeplink"
        link.symlink_to("/Users/terry/fix_symlinks_nested.txt")

        try:
            fixed, skipped = ns["scan_and_fix"]()
            assert fixed == 1
            assert os.readlink(link) == str(linux_target)
        finally:
            linux_target.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# CLI / __main__ tests via subprocess
# ---------------------------------------------------------------------------

class TestCLI:
    """Test the script's CLI interface via subprocess.run."""

    def test_help_flag(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "symlinks" in result.stdout.lower()

    def test_no_args_runs(self):
        """Running with no args should complete (exit 0 when no broken links)."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            capture_output=True, text=True,
            timeout=30,
        )
        # May be 0 or 1 depending on whether there are broken links in the
        # real scan dirs, but should not crash.
        assert result.returncode in (0, 1)
        assert "Scanning" in result.stdout
