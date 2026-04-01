from __future__ import annotations

"""Tests for test-fixer — automated test file fixer for common issues."""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch


def _load_test_fixer():
    """Load the test-fixer module by exec-ing its Python body."""
    source = open(str(Path.home() / "germline/effectors/test-fixer")).read()
    ns: dict = {"__name__": "test_fixer"}
    exec(source, ns)
    return ns


# ── CLI argument tests ─────────────────────────────────────────────────────


def test_cli_requires_test_file_arg():
    """test-fixer exits with error if no test file provided."""
    result = subprocess.run(
        [str(Path.home() / "germline/effectors/test-fixer")],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    output = result.stdout + result.stderr
    assert "test_file" in output.lower() or "usage" in output.lower()


def test_cli_reports_missing_file():
    """test-fixer reports error for non-existent test file."""
    result = subprocess.run(
        [str(Path.home() / "germline/effectors/test-fixer"), "/nonexistent/test_file.py"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "not found" in result.stdout.lower() or "does not exist" in result.stdout.lower()


# ── Fix detection tests ────────────────────────────────────────────────────


def test_detect_hardcoded_macos_path():
    """detect_issues flags /Users/terry/ hardcoded paths."""
    _mod = _load_test_fixer()
    detect_issues = _mod["detect_issues"]
    
    test_code = '''
def test_foo():
    path = str(Path.home() / "germline/effectors/foo")
    assert True
'''
    issues = detect_issues(test_code)
    assert any("Users/terry" in i for i in issues)


def test_detect_hardcoded_linux_path():
    """detect_issues flags /home/terry/ hardcoded paths."""
    _mod = _load_test_fixer()
    detect_issues = _mod["detect_issues"]
    
    test_code = '''
def test_bar():
    config = open(str(Path.home() / ".config/app.conf"))
'''
    issues = detect_issues(test_code)
    assert any("home/terry" in i for i in issues)


def test_detect_import_effector():
    """detect_issues flags 'import <effector>' pattern (effectors are scripts)."""
    _mod = _load_test_fixer()
    detect_issues = _mod["detect_issues"]
    
    test_code = '''
import lacuna
from telophase import main
'''
    issues = detect_issues(test_code)
    assert any("import" in i.lower() and "effector" in i.lower() for i in issues)


def test_detect_no_issues_in_clean_code():
    """detect_issues returns empty list for clean test code."""
    _mod = _load_test_fixer()
    detect_issues = _mod["detect_issues"]
    
    test_code = '''
from pathlib import Path
from unittest.mock import patch

def test_foo():
    path = Path.home() / "germline"
    assert path.exists()
'''
    issues = detect_issues(test_code)
    assert issues == []


# ── Fix application tests ──────────────────────────────────────────────────


def test_fix_hardcoded_path():
    """apply_fixes replaces /Users/terry/ with Path.home()."""
    _mod = _load_test_fixer()
    apply_fixes = _mod["apply_fixes"]
    
    test_code = '''path = str(Path.home() / "germline/effectors/foo")'''
    fixed = apply_fixes(test_code)
    assert "Path.home()" in fixed
    assert str(Path.home() / "") not in fixed


def test_fix_hardcoded_linux_path():
    """apply_fixes replaces /home/terry/ with Path.home()."""
    _mod = _load_test_fixer()
    apply_fixes = _mod["apply_fixes"]
    
    test_code = '''config = open(str(Path.home() / ".config/app.conf"))'''
    fixed = apply_fixes(test_code)
    assert "Path.home()" in fixed
    assert str(Path.home() / "") not in fixed


def test_fix_adds_path_import():
    """apply_fixes adds Path import if not present and Path.home() used."""
    _mod = _load_test_fixer()
    apply_fixes = _mod["apply_fixes"]
    
    test_code = '''
def test_foo():
    path = str(Path.home() / "germline")
'''
    fixed = apply_fixes(test_code)
    assert "from pathlib import Path" in fixed


def test_fix_preserves_existing_path_import():
    """apply_fixes does not duplicate Path import."""
    _mod = _load_test_fixer()
    apply_fixes = _mod["apply_fixes"]
    
    test_code = '''
from pathlib import Path
def test_foo():
    path = str(Path.home() / "germline")
'''
    fixed = apply_fixes(test_code)
    assert fixed.count("from pathlib import Path") == 1


def test_fix_import_effector_to_exec_pattern():
    """apply_fixes replaces 'import lacuna' with exec loading pattern."""
    _mod = _load_test_fixer()
    apply_fixes = _mod["apply_fixes"]
    
    test_code = '''
import lacuna

def test_foo():
    result = lacuna.process("input")
'''
    fixed = apply_fixes(test_code)
    # Should have exec-based loading pattern
    assert "exec(" in fixed or "subprocess.run" in fixed
    assert "import lacuna" not in fixed


# ── Integration tests ──────────────────────────────────────────────────────


def test_run_pytest_and_parse_results():
    """run_pytest returns parsed pass/fail counts."""
    _mod = _load_test_fixer()
    run_pytest = _mod["run_pytest"]
    
    # Create a simple passing test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write('def test_pass():\n    assert True\n')
        f.flush()
        temp_path = Path(f.name)
    
    try:
        result = run_pytest(temp_path)
        assert "passed" in result
        assert result["passed"] >= 1
    finally:
        temp_path.unlink()


def test_run_pytest_detects_failures():
    """run_pytest returns failure count for failing tests."""
    _mod = _load_test_fixer()
    run_pytest = _mod["run_pytest"]
    
    # Create a failing test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write('def test_fail():\n    assert False, "intentional failure"\n')
        f.flush()
        temp_path = Path(f.name)
    
    try:
        result = run_pytest(temp_path)
        assert result["failed"] >= 1
    finally:
        temp_path.unlink()


# ── Report generation tests ────────────────────────────────────────────────


def test_format_report_shows_summary():
    """format_report includes pass/fail summary."""
    _mod = _load_test_fixer()
    format_report = _mod["format_report"]
    
    report = format_report(
        test_file="test_foo.py",
        initial={"passed": 0, "failed": 2, "errors": []},
        final={"passed": 2, "failed": 0, "errors": []},
        fixes_applied=["Replaced /Users/terry/ with Path.home()"]
    )
    
    assert "test_foo.py" in report
    assert "2 passed" in report
    assert "fixes applied" in report.lower() or "fixes:" in report.lower()


def test_format_report_shows_no_fixes_needed():
    """format_report indicates when no fixes were needed."""
    _mod = _load_test_fixer()
    format_report = _mod["format_report"]
    
    report = format_report(
        test_file="test_clean.py",
        initial={"passed": 3, "failed": 0, "errors": []},
        final={"passed": 3, "failed": 0, "errors": []},
        fixes_applied=[]
    )
    
    assert "no fixes" in report.lower() or "passed" in report.lower()


def test_main_returns_zero_on_pass():
    """main returns 0 when all tests pass after fixes."""
    _mod = _load_test_fixer()
    main = _mod["main"]
    
    # Create a test that passes
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write('def test_pass():\n    assert True\n')
        f.flush()
        temp_path = Path(f.name)
    
    try:
        rc = main([str(temp_path)])
        assert rc == 0
    finally:
        temp_path.unlink()


def test_main_returns_nonzero_on_persistent_failure():
    """main returns non-zero when tests still fail after fixes."""
    _mod = _load_test_fixer()
    main = _mod["main"]
    
    # Create a test with a logic error (can't be fixed automatically)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write('def test_broken():\n    assert 1 == 2, "logic error"\n')
        f.flush()
        temp_path = Path(f.name)
    
    try:
        rc = main([str(temp_path)])
        assert rc != 0
    finally:
        temp_path.unlink()
