"""Tests for conftest-gen — hardcoded path scanner and rewriter."""
from __future__ import annotations

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
find_hardcoded_paths = _mod["find_hardcoded_paths"]
rewrite_file = _mod["rewrite_file"]
scan_directory = _mod["scan_directory"]
main = _mod["main"]


# ── find_hardcoded_paths ────────────────────────────────────────────


class TestFindHardcodedPaths:
    def test_no_paths_returns_empty(self, tmp_path: Path):
        p = tmp_path / "clean.py"
        p.write_text('x = 1\n')
        assert find_hardcoded_paths(p) == []

    def test_detects_macos_path(self, tmp_path: Path):
        p = tmp_path / "mac.py"
        p.write_text('PATH = "/home/terry/project"\n')
        results = find_hardcoded_paths(p)
        assert len(results) == 1
        lineno, original, fixed = results[0]
        assert lineno == 1
        assert "/home/terry/project" in original
        assert "Path.home()" in fixed

    def test_detects_linux_path(self, tmp_path: Path):
        p = tmp_path / "linux.py"
        p.write_text('PATH = "/home/terry/project"\n')
        results = find_hardcoded_paths(p)
        assert len(results) == 1
        lineno, original, fixed = results[0]
        assert "/home/terry/project" in original
        assert "Path.home()" in fixed

    def test_detects_home_only(self, tmp_path: Path):
        p = tmp_path / "home.py"
        p.write_text('HOME = "/Users/terry"\n')
        results = find_hardcoded_paths(p)
        assert len(results) == 1
        assert "Path.home()" in results[0][2]

    def test_multiple_paths_on_same_line(self, tmp_path: Path):
        p = tmp_path / "multi.py"
        p.write_text('a = "/home/terry/a"; b = "/home/terry/b"\n')
        results = find_hardcoded_paths(p)
        assert len(results) == 2

    def test_paths_across_multiple_lines(self, tmp_path: Path):
        p = tmp_path / "lines.py"
        p.write_text('a = "/home/terry/a"\nb = "/home/terry/b"\n')
        results = find_hardcoded_paths(p)
        assert len(results) == 2
        assert results[0][0] == 1
        assert results[1][0] == 2


# ── rewrite_file ─────────────────────────────────────────────────────


class TestRewriteFile:
    def test_no_changes_returns_false(self, tmp_path: Path):
        p = tmp_path / "clean.py"
        p.write_text('x = 1\n')
        assert rewrite_file(p, []) is False
        assert p.read_text() == 'x = 1\n'

    def test_applies_single_fix(self, tmp_path: Path):
        p = tmp_path / "fix.py"
        p.write_text('PATH = "/home/terry/project"\n')
        issues = find_hardcoded_paths(p)
        result = rewrite_file(p, issues)
        assert result is True
        assert "Path.home()" in p.read_text()
        assert "/Users/terry" not in p.read_text()

    def test_applies_multiple_fixes(self, tmp_path: Path):
        p = tmp_path / "multi.py"
        p.write_text('a = "/home/terry/a"\nb = "/home/terry/b"\n')
        issues = find_hardcoded_paths(p)
        result = rewrite_file(p, issues)
        assert result is True
        text = p.read_text()
        assert "Path.home()" in text
        assert "/Users/terry" not in text
        assert "/home/terry" not in text

    def test_preserves_other_content(self, tmp_path: Path):
        p = tmp_path / "preserve.py"
        original = 'x = 1\nPATH = "/home/terry/project"\ny = 2\n'
        p.write_text(original)
        issues = find_hardcoded_paths(p)
        rewrite_file(p, issues)
        text = p.read_text()
        assert "x = 1" in text
        assert "y = 2" in text


# ── scan_directory ───────────────────────────────────────────────────


class TestScanDirectory:
    def test_empty_directory(self, tmp_path: Path):
        results = scan_directory(tmp_path)
        assert results == []

    def test_finds_files_with_paths(self, tmp_path: Path):
        p1 = tmp_path / "a.py"
        p1.write_text('x = "/home/terry/x"\n')
        p2 = tmp_path / "b.py"
        p2.write_text('x = 1\n')  # clean
        p3 = tmp_path / "subdir"
        p3.mkdir()
        p4 = p3 / "c.py"
        p4.write_text('y = "/home/terry/y"\n')

        results = scan_directory(tmp_path)
        file_paths = [fp for fp, _ in results]
        assert p1 in file_paths
        assert p2 not in file_paths
        assert p4 in file_paths


# ── main (CLI) ───────────────────────────────────────────────────────


class TestMain:
    def test_missing_directory_exits_1(self, capsys):
        result = main(["/nonexistent/path"])
        assert result == 1
        err = capsys.readouterr().err
        assert "not a directory" in err

    def test_empty_directory_reports_none(self, tmp_path: Path, capsys):
        result = main([str(tmp_path)])
        assert result == 0
        out = capsys.readouterr().out
        assert "No hardcoded paths" in out

    def test_dry_run_shows_would_fix(self, tmp_path: Path, capsys):
        p = tmp_path / "test.py"
        p.write_text('X = "/home/terry/x"\n')
        result = main([str(tmp_path)])
        assert result == 0
        out = capsys.readouterr().out
        assert "DRY-RUN" in out or "Would fix" in out.lower() or "line 1" in out
        # File should NOT be modified
        assert "/Users/terry" in p.read_text()

    def test_fix_applies_changes(self, tmp_path: Path, capsys):
        p = tmp_path / "fix.py"
        p.write_text('X = "/home/terry/x"\n')
        result = main(["--fix", str(tmp_path)])
        assert result == 0
        out = capsys.readouterr().out
        assert "Fixed" in out
        # File should be modified
        assert "Path.home()" in p.read_text()
        assert "/Users/terry" not in p.read_text()

    def test_subprocess_dry_run(self, tmp_path: Path):
        """Verify subprocess works in dry-run mode."""
        p = tmp_path / "sub.py"
        p.write_text('X = "/home/terry/x"\n')
        script = "/home/terry/germline/effectors/conftest-gen"
        result = subprocess.run(
            [script, str(tmp_path)],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0
        assert "line 1" in result.stdout
        # Should NOT modify file
        assert "/home/terry" in p.read_text()

    def test_subprocess_fix_mode(self, tmp_path: Path):
        """Verify subprocess works with --fix."""
        p = tmp_path / "sub.py"
        p.write_text('X = "/home/terry/x"\n')
        script = "/home/terry/germline/effectors/conftest-gen"
        result = subprocess.run(
            [script, "--fix", str(tmp_path)],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0
        assert "Fixed" in result.stdout
        assert "Path.home()" in p.read_text()
