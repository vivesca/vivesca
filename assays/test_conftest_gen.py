from __future__ import annotations

"""Tests for conftest-gen — hardcoded path scanner and rewriter."""

import subprocess
from pathlib import Path

import pytest


def _load_module() -> dict:
    """Load conftest-gen via exec (effector pattern)."""
    source = Path("/home/terry/germline/effectors/conftest-gen").read_text()
    ns: dict = {"__name__": "conftest_gen"}
    exec(source, ns)
    return ns


_mod = _load_module()
scan_file = _mod["scan_file"]
apply_fix = _mod["apply_fix"]
Finding = _mod["Finding"]


# ── scan_file ────────────────────────────────────────────────────────


class TestScanFile:
    def test_no_paths_returns_empty(self, tmp_path: Path):
        p = tmp_path / "clean.py"
        p.write_text('x = 1\n')
        assert scan_file(p) == []

    def test_detects_linux_path(self, tmp_path: Path):
        p = tmp_path / "linux.py"
        p.write_text('PATH = "/home/terry/project"\n')
        results = scan_file(p)
        assert len(results) == 1
        f = results[0]
        assert f.line == 1
        assert "/home/terry/project" in f.original
        assert "Path.home()" in f.replacement

    def test_detects_macos_path(self, tmp_path: Path):
        p = tmp_path / "mac.py"
        p.write_text('PATH = "/Users/terry/project"\n')
        results = scan_file(p)
        assert len(results) == 1
        f = results[0]
        assert "/Users/terry/project" in f.original
        assert "Path.home()" in f.replacement

    def test_detects_home_only(self, tmp_path: Path):
        p = tmp_path / "home.py"
        p.write_text('HOME = "/Users/terry/project"\n')
        results = scan_file(p)
        assert len(results) == 1
        assert "Path.home()" in results[0].replacement

    def test_multiple_paths_on_same_line(self, tmp_path: Path):
        p = tmp_path / "multi.py"
        p.write_text('a = "/home/terry/a"; b = "/home/terry/b"\n')
        results = scan_file(p)
        assert len(results) == 2

    def test_paths_across_multiple_lines(self, tmp_path: Path):
        p = tmp_path / "lines.py"
        p.write_text('a = "/home/terry/a"\nb = "/home/terry/b"\n')
        results = scan_file(p)
        assert len(results) == 2
        assert results[0].line == 1
        assert results[1].line == 2


# ── apply_fix ─────────────────────────────────────────────────────


class TestApplyFix:
    def test_no_changes_returns_0(self, tmp_path: Path):
        p = tmp_path / "clean.py"
        p.write_text('x = 1\n')
        assert apply_fix(p, []) == 0
        assert p.read_text() == 'x = 1\n'

    def test_applies_single_fix(self, tmp_path: Path):
        p = tmp_path / "fix.py"
        p.write_text('PATH = "/home/terry/project"\n')
        findings = scan_file(p)
        result = apply_fix(p, findings)
        assert result == 1
        assert "Path.home()" in p.read_text()
        assert "/Users/terry" not in p.read_text()

    def test_applies_multiple_fixes(self, tmp_path: Path):
        p = tmp_path / "multi.py"
        p.write_text('a = "/home/terry/a"\nb = "/home/terry/b"\n')
        findings = scan_file(p)
        result = apply_fix(p, findings)
        assert result == 2
        text = p.read_text()
        assert "Path.home()" in text
        assert "/Users/terry" not in text
        assert "/home/terry" not in text

    def test_preserves_other_content(self, tmp_path: Path):
        p = tmp_path / "preserve.py"
        original = 'x = 1\nPATH = "/home/terry/project"\ny = 2\n'
        p.write_text(original)
        findings = scan_file(p)
        apply_fix(p, findings)
        text = p.read_text()
        assert "x = 1" in text
        assert "y = 2" in text


# ── subprocess CLI ───────────────────────────────────────────────────


class TestSubprocessCLI:
    def test_dry_run_shows_findings(self, tmp_path: Path):
        """Verify subprocess works in dry-run mode."""
        p = tmp_path / "test_sub.py"
        p.write_text('X = "/home/terry/x"\n')
        script = "/home/terry/germline/effectors/conftest-gen"
        result = subprocess.run(
            [script, "--assays-dir", str(tmp_path)],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0
        assert "line 1" in result.stdout or "hardcoded" in result.stdout.lower() or "/home/terry" in result.stdout
        # Should NOT modify file
        assert "/home/terry" in p.read_text()

    def test_fix_mode_applies_changes(self, tmp_path: Path):
        """Verify subprocess works with --fix."""
        p = tmp_path / "test_sub.py"
        p.write_text('X = "/home/terry/x"\n')
        script = "/home/terry/germline/effectors/conftest-gen"
        result = subprocess.run(
            [script, "--fix", "--assays-dir", str(tmp_path)],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0
        assert "Fixed" in result.stdout
        assert "Path.home()" in p.read_text()
