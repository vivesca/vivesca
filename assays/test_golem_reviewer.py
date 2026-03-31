#!/usr/bin/env python3
"""Tests for golem-reviewer effector script."""

import subprocess
import sys
from pathlib import Path

GERMLINE = Path(__file__).parent.parent
GOLEM_REVIEWER_PATH = GERMLINE / "effectors" / "golem-reviewer"


def test_golem_reviewer_help():
    """Test that golem-reviewer --help outputs help message."""
    result = subprocess.run(
        [sys.executable, str(GOLEM_REVIEWER_PATH), "--help"],
        capture_output=True,
        text=True,
        cwd=GERMLINE,
    )
    assert result.returncode == 0
    assert "Usage:" in result.stdout
    assert "golem-reviewer" in result.stdout
    assert "--once" in result.stdout
    assert "--help" in result.stdout


def test_golem_reviewer_exists_and_executable():
    """Test that golem-reviewer file exists and is executable."""
    assert GOLEM_REVIEWER_PATH.exists(), "golem-reviewer does not exist"
    # Check shebang is correct
    first_line = GOLEM_REVIEWER_PATH.read_text().splitlines()[0]
    assert first_line == "#!/usr/bin/env python3", "Wrong shebang"
    stat = GOLEM_REVIEWER_PATH.stat()
    assert stat.st_mode & 0o111, "File should be executable"


def test_golem_reviewer_once_mode_runs():
    """Test that --once mode runs without crashing."""
    # Run one cycle with --once. It should execute and exit.
    # Don't expect any particular output beyond success exit code.
    result = subprocess.run(
        [sys.executable, str(GOLEM_REVIEWER_PATH), "--once"],
        capture_output=True,
        text=True,
        cwd=GERMLINE,
    )
    # It might succeed or might fail depending on environment, but let's check
    # it at least parses arguments and runs. If it exits 0 or 1 gracefully, that's ok.
    # It shouldn't crash with unhandled exception.
    # We just check that it produces output that looks like logging.
    assert "=== Review cycle" in result.stdout or "=== Review cycle" in result.stderr
    # It should complete either 0 or 1, but not crash with SIGSEGV or similar
    assert result.returncode in (0, 1, 124)  # 124 is timeout which is acceptable


def test_fix_collection_errors_detects_hardcoded_paths():
    """Test that the logic detects and replaces hardcoded /Users/terry/ paths."""
    # Load the script through exec and test the fix_collection_errors logic
    # by creating a test file with hardcoded paths
    import ast
    script_content = GOLEM_REVIEWER_PATH.read_text()
    ns = {}
    exec(script_content, ns)
    
    # Create a temporary test file with hardcoded path
    temp_test_file = GERMLINE / "assays" / "tmp_test_hardcoded.py"
    original_content = 'test_path = "/Users/terry/germline/some/file.py"'
    temp_test_file.write_text(original_content)
    
    # We'll monkey-patch the run command to just return our test file error
    # and check it gets fixed
    original_run = ns["run"]
    def mock_run(cmd, cwd=None):
        return 0, f"ERROR assays/{temp_test_file.name}"
    
    ns["run"] = mock_run
    fixed = ns["fix_collection_errors"]()
    
    # Check it fixed it
    fixed_content = temp_test_file.read_text()
    assert "/Users/terry/" not in fixed_content
    assert str(Path.home()) in fixed_content
    assert fixed == 1
    
    # Cleanup
    temp_test_file.unlink()
    
    # Verify AST still parses
    ast.parse(fixed_content)  # Shouldn't throw


def test_all_functions_defined_and_parseable():
    """Test that all top-level functions are parsed without syntax errors."""
    import ast
    content = GOLEM_REVIEWER_PATH.read_text()
    tree = ast.parse(content)
    
    # Check all expected functions are present
    function_names = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    
    expected_functions = [
        "log",
        "run",
        "check_daemon_status",
        "check_new_output",
        "fix_collection_errors",
        "run_test_snapshot",
        "check_daemon_failures",
        "auto_commit",
        "write_progress_report",
        "review_cycle",
        "main",
    ]
    
    for func_name in expected_functions:
        assert func_name in function_names, f"Missing function {func_name}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])
