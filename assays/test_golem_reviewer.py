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
        original_run = ns['run']
        
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
