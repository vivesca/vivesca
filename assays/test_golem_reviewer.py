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
        cwd=str(GERMLINE),
        timeout=10
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


def test_golem_reviewer_syntax_valid():
    """Test that golem-reviewer has valid Python syntax."""
    content = GOLEM_REVIEWER_PATH.read_text()
    import ast
    tree = ast.parse(content)
    assert tree is not None
    assert len(tree.body) > 0


def test_golem_functions_loadable_via_exec():
    """Test that all function definitions are loadable via exec."""
    ns = {}
    content = GOLEM_REVIEWER_PATH.read_text()
    exec(content, ns)
    
    # Check key functions exist
    assert "log" in ns
    assert "run" in ns
    assert "check_daemon_status" in ns
    assert "check_new_output" in ns
    assert "fix_collection_errors" in ns
    assert "run_test_snapshot" in ns
    assert "check_daemon_failures" in ns
    assert "auto_commit" in ns
    assert "write_progress_report" in ns
    assert "review_cycle" in ns
    assert "main" in ns
    
    # Check constants are defined
    assert "GERMLINE" in ns
    assert "QUEUE_FILE" in ns
    assert "POLL_INTERVAL" in ns
    assert ns["POLL_INTERVAL"] == 300


def test_fix_collection_errors_identifies_hardcoded_paths():
    """Test that fix_collection_errors correctly identifies /Users/terry/ paths."""
    ns = {}
    content = GOLEM_REVIEWER_PATH.read_text()
    exec(content, ns)
    
    # Create a test file in assays with hardcoded path
    temp_test_file = GERMLINE / "assays" / "tmp_test_hardcoded.py"
    temp_test_file.write_text("test_path = '/Users/terry/germline/some/file.py'\n")
    
    try:
        # Mock the run function to return our test file as an error
        def mock_run(cmd, cwd=None):
            if "pytest --co" in cmd:
                return 0, f"ERROR assays/{temp_test_file.name}"
            return 0, ""
        
        ns['run'] = mock_run
        ns['GERMLINE'] = GERMLINE
        
        # Call the function
        fixed = ns['fix_collection_errors']()
        
        # Should have fixed one error
        assert fixed == 1
        
        # Check the file was modified
        new_content = temp_test_file.read_text()
        assert str(Path.home()) in new_content
        assert "/Users/terry/" not in new_content
        
        # Verify AST still valid
        import ast
        ast.parse(new_content)
        
    finally:
        if temp_test_file.exists():
            temp_test_file.unlink()


def test_all_expected_functions_present():
    """Check that all expected top-level functions are present."""
    import ast
    content = GOLEM_REVIEWER_PATH.read_text()
    tree = ast.parse(content)

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
        assert func_name in function_names, f"Missing expected function: {func_name}"


def test_run_function_executes_command():
    """Test that run function executes command and returns result."""
    ns = {}
    content = GOLEM_REVIEWER_PATH.read_text()
    exec(content, ns)

    returncode, output = ns['run']("echo 'hello world'")
    assert returncode == 0
    assert output == "hello world"

    # Test non-zero exit code
    returncode, output = ns['run']("false")
    assert returncode != 0


def test_check_daemon_status_parses_output():
    """Test that check_daemon_status correctly parses daemon output."""
    ns = {}
    content = GOLEM_REVIEWER_PATH.read_text()
    exec(content, ns)

    # Mock the run function
    def mock_run(cmd):
        return 0, "Daemon running (PID 1234), 5 pending tasks (current 1/5)"

    ns['run'] = mock_run

    result = ns['check_daemon_status']()
    assert result['running'] is True
    assert result['pending'] == 5
    assert "1234" in result['raw']

    # Test parsing when no match
    def mock_run_no_match(cmd):
        return 0, "Daemon stopped"

    ns['run'] = mock_run_no_match
    result = ns['check_daemon_status']()
    assert result['pending'] == 0


def test_check_daemon_failures_finds_failures():
    """Test that check_daemon_failures extracts failure lines."""
    ns = {}
    content = GOLEM_REVIEWER_PATH.read_text()
    exec(content, ns)

    # Mock the run function
    def mock_run(cmd):
        return 0, "FAILED: task 1\nFAILED: task 2"

    ns['run'] = mock_run

    failures = ns['check_daemon_failures']()
    assert len(failures) == 2
    assert "FAILED: task 1" in failures

    # Test empty case
    def mock_run_empty(cmd):
        return 1, ""

    ns['run'] = mock_run_empty
    failures = ns['check_daemon_failures']()
    assert failures == []


def test_run_test_snapshot_parses_output():
    """Test that run_test_snapshot parses pytest output."""
    ns = {}
    content = GOLEM_REVIEWER_PATH.read_text()
    exec(content, ns)

    # Mock the run function
    def mock_run(cmd):
        return 0, "10 passed, 2 failed, 1 error\n"

    ns['run'] = mock_run

    result = ns['run_test_snapshot']()
    assert result['passed'] == 10
    assert result['failed'] == 2
    assert result['errors'] == 1

    # Test when no numbers found
    def mock_run_no_match(cmd):
        return 0, "no tests ran"

    ns['run'] = mock_run_no_match
    result = ns['run_test_snapshot']()
    assert result['passed'] == 0
    assert result['failed'] == 0


def test_write_progress_report_creates_file():
    """Test that write_progress_report creates a report file."""
    ns = {}
    content = GOLEM_REVIEWER_PATH.read_text()
    exec(content, ns)

    # Set GERMLINE and reset cycle_number
    ns['GERMLINE'] = GERMLINE
    ns['cycle_number'] = 999

    # Call with test data
    status = {"running": True, "pending": 3}
    output = {"new_tests": 2, "new_effectors": 1, "consulting_pieces": 5}
    tests = {"passed": 100, "failed": 2, "errors": 1, "raw": ""}
    failures = ["Failure 1", "Failure 2"]

    ns['write_progress_report'](status, output, tests, failures)

    # Check file was created
    report_path = GERMLINE / "loci" / "copia" / "reviewer-cycle-999.md"
    assert report_path.exists(), "Report file not created"

    # Verify content
    report_content = report_path.read_text()
    assert "Golem Reviewer — Cycle 999" in report_content
    assert "Queue: 3 pending" in report_content
    assert "Passed: 100" in report_content
    assert "Failed: 2" in report_content

    # Cleanup
    if report_path.exists():
        report_path.unlink()


def test_log_creates_log_file():
    """Test that log writes to log file."""
    ns = {}
    content = GOLEM_REVIEWER_PATH.read_text()
    exec(content, ns)

    # Override REVIEW_LOG to a temp file
    temp_log = GERMLINE / "tmp_golem_reviewer_test.log"
    ns['REVIEW_LOG'] = temp_log

    ns['log']("test message")

    assert temp_log.exists()
    assert "test message" in temp_log.read_text()

    # Cleanup
    if temp_log.exists():
        temp_log.unlink()


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])
