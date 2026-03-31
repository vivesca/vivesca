"""Tests for golem-validate — Python file validator for common issues."""
from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path

import pytest


def _load_module() -> dict:
    """Load golem-validate via exec (effector pattern)."""
    source = Path("/home/terry/germline/effectors/golem-validate").read_text()
    ns: dict = {"__name__": "golem_validate"}
    exec(source, ns)
    return ns


_mod = _load_module()
check_syntax = _mod["check_syntax"]
check_patterns = _mod["check_patterns"]
check_pytest_collect = _mod["check_pytest_collect"]
validate_file = _mod["validate_file"]
main = _mod["main"]
FORBIDDEN_PATTERNS = _mod["FORBIDDEN_PATTERNS"]


@pytest.fixture()
def clean_py(tmp_path: Path) -> Path:
    """Write a clean Python file and return its path."""
    p = tmp_path / "clean.py"
    p.write_text('x = 1\n')
    return p


@pytest.fixture()
def bad_syntax_py(tmp_path: Path) -> Path:
    """Write a file with a syntax error."""
    p = tmp_path / "bad_syntax.py"
    p.write_text('def f(\n')
    return p


@pytest.fixture()
def mac_path_py(tmp_path: Path) -> Path:
    """Write a file containing a hardcoded macOS path."""
    p = tmp_path / "mac_path.py"
    p.write_text('PATH = "/Users/terry/project"\n')
    return p


@pytest.fixture()
def todo_py(tmp_path: Path) -> Path:
    """Write a file containing a TODO marker."""
    p = tmp_path / "has_todo.py"
    p.write_text('# TODO: fix this later\n')
    return p


@pytest.fixture()
def fixme_py(tmp_path: Path) -> Path:
    """Write a file containing a FIXME marker."""
    p = tmp_path / "has_fixme.py"
    p.write_text('# FIXME: broken\n')
    return p


@pytest.fixture()
def stub_py(tmp_path: Path) -> Path:
    """Write a file containing a stub marker."""
    p = tmp_path / "has_stub.py"
    p.write_text('def stub(): pass\n')
    return p


# ── check_syntax ──────────────────────────────────────────────────


class TestCheckSyntax:
    def test_valid_file_returns_none(self, clean_py: Path):
        assert check_syntax(clean_py) is None

    def test_syntax_error_returns_message(self, bad_syntax_py: Path):
        result = check_syntax(bad_syntax_py)
        assert result is not None
        assert "SyntaxError" in result


# ── check_patterns ────────────────────────────────────────────────


class TestCheckPatterns:
    def test_clean_file_no_issues(self, clean_py: Path):
        assert check_patterns(clean_py) == []

    def test_detects_macos_path(self, mac_path_py: Path):
        issues = check_patterns(mac_path_py)
        assert any("macOS" in i for i in issues)

    def test_detects_todo(self, todo_py: Path):
        issues = check_patterns(todo_py)
        assert any("work-in-progress" in i for i in issues)

    def test_detects_fixme(self, fixme_py: Path):
        issues = check_patterns(fixme_py)
        assert any("work-in-progress" in i for i in issues)

    def test_detects_stub(self, stub_py: Path):
        issues = check_patterns(stub_py)
        assert any("placeholder" in i for i in issues)


# ── check_pytest_collect ──────────────────────────────────────────


class TestCheckPytestCollect:
    def test_valid_test_file_passes(self, tmp_path: Path):
        p = tmp_path / "test_sample.py"
        p.write_text('def test_ok(): assert True\n')
        assert check_pytest_collect(p) is None

    def test_broken_test_file_fails(self, tmp_path: Path):
        p = tmp_path / "test_broken.py"
        p.write_text('def test_bad(): import nonexistent_module_xyz\n')
        result = check_pytest_collect(p)
        assert result is not None
        assert "pytest collection" in result


# ── validate_file ─────────────────────────────────────────────────


class TestValidateFile:
    def test_clean_file_passes(self, clean_py: Path):
        status, issues = validate_file(clean_py)
        assert status == "PASS"
        assert issues == []

    def test_syntax_error_fails_immediately(self, bad_syntax_py: Path):
        status, issues = validate_file(bad_syntax_py)
        assert status == "FAIL"
        assert len(issues) == 1
        assert "SyntaxError" in issues[0]

    def test_pattern_violations_fail(self, mac_path_py: Path):
        status, issues = validate_file(mac_path_py)
        assert status == "FAIL"
        assert any("macOS" in i for i in issues)

    def test_non_test_file_skips_pytest(self, clean_py: Path):
        """Non-test files should not trigger pytest collection."""
        status, issues = validate_file(clean_py)
        assert status == "PASS"

    def test_test_file_triggers_pytest_check(self, tmp_path: Path):
        """A test_*.py file should run pytest collection."""
        p = tmp_path / "test_good.py"
        p.write_text('def test_ok(): assert 1 + 1 == 2\n')
        status, issues = validate_file(p)
        assert status == "PASS"

    def test_multiple_violations_detected(self, tmp_path: Path):
        """File with multiple issues reports all of them."""
        p = tmp_path / "multi.py"
        p.write_text('"/Users/terry/x"  # TODO: fix\n')
        status, issues = validate_file(p)
        assert status == "FAIL"
        assert len(issues) >= 2


# ── main (CLI) ────────────────────────────────────────────────────


class TestMain:
    def test_no_args_returns_1(self, capsys):
        assert main([]) == 1
        assert "Usage" in capsys.readouterr().err

    def test_missing_file_reports_missing(self, tmp_path: Path, capsys):
        assert main([str(tmp_path / "gone.py")]) == 1
        out = capsys.readouterr().out
        assert "MISSING" in out

    def test_all_pass_exits_0(self, clean_py: Path, capsys):
        assert main([str(clean_py)]) == 0
        out = capsys.readouterr().out
        assert "PASS" in out

    def test_failure_exits_1(self, bad_syntax_py: Path, capsys):
        assert main([str(bad_syntax_py)]) == 1
        out = capsys.readouterr().out
        assert "FAIL" in out

    def test_subprocess_invocation(self, clean_py: Path):
        """Verify the script works when run as a subprocess."""
        script = "/home/terry/germline/effectors/golem-validate"
        result = subprocess.run(
            [script, str(clean_py)],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0
        assert "PASS" in result.stdout

    def test_subprocess_failure(self, bad_syntax_py: Path):
        """Verify subprocess exits 1 on failure."""
        script = "/home/terry/germline/effectors/golem-validate"
        result = subprocess.run(
            [script, str(bad_syntax_py)],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 1
        assert "FAIL" in result.stdout
