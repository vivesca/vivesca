#!/usr/bin/env python3
"""Tests for golem-reviewer effector script."""
import subprocess
import sys
from pathlib import Path


def test_golem_reviewer_help():
    """Test that golem-reviewer runs and shows help message."""
    germline = Path.home() / "germline"
    effector_path = germline / "effectors" / "golem-reviewer"
    
    result = subprocess.run(
        [sys.executable, str(effector_path), "--help"],
        cwd=str(germline),
        capture_output=True,
        text=True,
        timeout=30
    )
    
    assert result.returncode == 0
    assert "Usage: golem-reviewer" in result.stdout
    assert "--once" in result.stdout
    assert "Monitor golem output" in result.stdout


def test_golem_reviewer_syntax_valid():
    """Test that golem-reviewer has valid Python syntax."""
    germline = Path.home() / "germline"
    effector_path = germline / "effectors" / "golem-reviewer"
    
    # Check syntax by ast parsing
    content = effector_path.read_text()
    import ast
    tree = ast.parse(content)
    assert tree is not None
    assert len(tree.body) > 0


def test_golem_reviewer_runs_once_mode():
    """Test that golem-reviewer can run in --once mode without crashing."""
    germline = Path.home() / "germline"
    effector_path = germline / "effectors" / "golem-reviewer"
    
    # We can't actually run the full cycle because it expects git state and might commit
    # Let's check that it at least starts up and gets to some cycle steps
    result = subprocess.run(
        [sys.executable, str(effector_path), "--once"],
        cwd=str(germline),
        capture_output=True,
        text=True,
        timeout=60
    )
    
    # It might fail depending on environment, but it shouldn't crash immediately
    # Check that it at least logs starting and gets to some cycle steps
    output = result.stdout + result.stderr
    assert "=== Review cycle 1 ===" in output or "Golem reviewer started" in output


def test_golem_functions_loadable_via_exec():
    """Test that all function definitions are loadable via exec."""
    germline = Path.home() / "germline"
    effector_path = germline / "effectors" / "golem-reviewer"
    
    ns = {}
    content = effector_path.read_text()
    
    # Remove the __main__ block so it doesn't run main
    content = content.replace("if __name__ == \"__main__\":\n    sys.exit(main())", "")
    
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
    germline = Path.home() / "germline"
    effector_path = germline / "effectors" / "golem-reviewer"
    
    ns = {}
    content = effector_path.read_text()
    content = content.replace("if __name__ == \"__main__\":\n    sys.exit(main())", "")
    exec(content, ns)
    
    # Create a test file with hardcoded path
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("# Test file\npath = '/Users/terry/germline/some/file.py'\n")
        temp_path = f.name
    
    try:
        # Mock the run function to return our test file as an error
        original_run = ns['run']
        
        def mock_run(cmd, cwd=None):
            if "pytest --co" in cmd:
                return 0, f"ERROR {temp_path}"
            return 0, ""
        
        ns['run'] = mock_run
        
        # Call the function
        fixed = ns['fix_collection_errors']()
        
        # Should have fixed one error
        assert fixed == 1
        
        # Check the file was modified
        new_content = open(temp_path).read()
        assert str(Path.home()) in new_content
        assert "/Users/terry/" not in new_content
        
    finally:
        import os
        os.unlink(temp_path)
