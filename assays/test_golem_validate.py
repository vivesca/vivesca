"""Tests for effectors/golem-validate — Python file validation checker."""
from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path

import pytest

EFFECTOR = Path("/home/terry/germline/effectors/golem-validate")


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    """Run golem-validate with given args, return CompletedProcess."""
    return subprocess.run(
        ["python3", str(EFFECTOR), *args],
        capture_output=True,
        text=True,
        timeout=60,
    )


@pytest.fixture()
def good_file(tmp_path: Path) -> Path:
    """A clean Python file that should pass all checks."""
    p = tmp_path / "clean.py"
    p.write_text('"""Module docstring."""\nprint("hello")\n')
    return p


@pytest.fixture()
def syntax_error_file(tmp_path: Path) -> Path:
    """A Python file with a syntax error."""
    p = tmp_path / "bad_syntax.py"
    p.write_text("def f(\n")  # incomplete function def
    return p


@pytest.fixture()
def hardcoded_path_file(tmp_path: Path) -> Path:
    """A Python file with /Users/terry/ hardcoded."""
    p = tmp_path / "mac_path.py"
    p.write_text('path = "/Users/terry/project"\n')
    return p


@pytest.fixture()
def todo_file(tmp_path: Path) -> Path:
    """A Python file with TODO marker."""
    p = tmp_path / "todo.py"
    p.write_text("# TODO: implement this later\n")
    return p


@pytest.fixture()
def fixme_file(tmp_path: Path) -> Path:
    """A Python file with FIXME marker."""
    p = tmp_path / "fixme.py"
    p.write_text("# FIXME broken logic\n")
    return p


@pytest.fixture()
def stub_file(tmp_path: Path) -> Path:
    """A Python file with stub marker."""
    p = tmp_path / "stub.py"
    p.write_text("def process():\n    pass  # stub implementation\n")
    return p


# ── CLI behaviour ────────────────────────────────────────────────────


def test_no_args_exits_1():
    """Running with no args prints usage and exits 1."""
    r = _run([])
    assert r.returncode == 1
    assert "Usage" in r.stderr


def test_missing_file_exits_1(tmp_path: Path):
    """Non-existent file is reported MISSING, exit 1."""
    missing = tmp_path / "nonexistent.py"
    r = _run([str(missing)])
    assert r.returncode == 1
    assert "MISSING" in r.stdout


# ── Syntax check ─────────────────────────────────────────────────────


def test_clean_file_passes(good_file: Path):
    """A well-formed file with no issues should PASS."""
    r = _run([str(good_file)])
    assert r.returncode == 0
    assert "PASS" in r.stdout


def test_syntax_error_fails(syntax_error_file: Path):
    """A file with a SyntaxError should FAIL."""
    r = _run([str(syntax_error_file)])
    assert r.returncode == 1
    assert "SyntaxError" in r.stdout


# ── Pattern checks ───────────────────────────────────────────────────


def test_hardcoded_mac_path_fails(hardcoded_path_file: Path):
    """A file with /Users/terry/ should FAIL."""
    r = _run([str(hardcoded_path_file)])
    assert r.returncode == 1
    assert "macOS hardcoded path" in r.stdout


def test_todo_fails(todo_file: Path):
    """A file with TODO should FAIL."""
    r = _run([str(todo_file)])
    assert r.returncode == 1
    assert "work-in-progress marker" in r.stdout


def test_fixme_fails(fixme_file: Path):
    """A file with FIXME should FAIL."""
    r = _run([str(fixme_file)])
    assert r.returncode == 1
    assert "work-in-progress marker" in r.stdout


def test_stub_fails(stub_file: Path):
    """A file with stub should FAIL."""
    r = _run([str(stub_file)])
    assert r.returncode == 1
    assert "stub" in r.stdout.lower()


def test_multiple_issues_reported(tmp_path: Path):
    """All issues in a single file are reported."""
    p = tmp_path / "multi.py"
    p.write_text('path = "/Users/terry/x"\n# TODO: fix\n')
    r = _run([str(p)])
    assert r.returncode == 1
    assert "/Users/terry/" in r.stdout or "macOS hardcoded path" in r.stdout
    assert "work-in-progress marker" in r.stdout


# ── Multiple files ───────────────────────────────────────────────────


def test_mixed_files_exit_1(good_file: Path, todo_file: Path):
    """If any file fails, overall exit code is 1."""
    r = _run([str(good_file), str(todo_file)])
    assert r.returncode == 1
    lines = r.stdout.strip().splitlines()
    assert len(lines) == 2


def test_all_pass_exit_0(good_file: Path, tmp_path: Path):
    """All passing files → exit 0."""
    p2 = tmp_path / "also_clean.py"
    p2.write_text("x = 1\n")
    r = _run([str(good_file), str(p2)])
    assert r.returncode == 0


# ── Pytest collection (test files only) ──────────────────────────────


def test_valid_test_file_passes_collection(tmp_path: Path):
    """A valid test_*.py file that pytest can collect should PASS."""
    p = tmp_path / "test_sample.py"
    p.write_text(textwrap.dedent("""\
        def test_addition():
            assert 1 + 1 == 2
    """))
    r = _run([str(p)])
    assert r.returncode == 0
    assert "PASS" in r.stdout


def test_broken_test_file_fails_collection(tmp_path: Path):
    """A test_*.py with import errors should FAIL collection."""
    p = tmp_path / "test_broken_import.py"
    p.write_text("from nonexistent_module_xyz import foo\n\ndef test_x(): pass\n")
    r = _run([str(p)])
    assert r.returncode == 1
    assert "pytest collection failed" in r.stdout


# ── Self-validation ──────────────────────────────────────────────────


def test_validate_self():
    """golem-validate itself should pass its own checks."""
    r = _run([str(EFFECTOR)])
    assert r.returncode == 0
    assert "PASS" in r.stdout
