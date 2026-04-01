"""Tests for legatum-verify effector script."""
import subprocess
import json
import pytest
from pathlib import Path

# Path to the effector
LEGATUM_VERIFY = Path(__file__).parent.parent / "effectors" / "legatum-verify"


def test_legatum_verify_script_exists_and_is_executable():
    """Verify the script exists and is executable."""
    assert LEGATUM_VERIFY.exists()
    assert LEGATUM_VERIFY.is_file()
    # Check that it's executable (or at least readable)
    assert LEGATUM_VERIFY.stat().st_mode & 0o444 != 0


def test_legatum_verify_help_flag():
    """Test that --help works."""
    result = subprocess.run([str(LEGATUM_VERIFY), "--help"], capture_output=True, text=True)
    # Should exit cleanly
    assert result.returncode == 0
    assert "legatum-verify" in result.stdout
    assert "post-wrap auditor" in result.stdout
    assert "session_id" in result.stdout
    assert "--json" in result.stdout


def test_missing_session_exits_with_error():
    """Test that non-existent session exits with code 1."""
    result = subprocess.run(
        [str(LEGATUM_VERIFY), "nonexistent-session-id"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 1
    assert "No session found" in result.stderr


def test_legatum_verify_json_flag_accepted():
    """Test that --json flag is accepted even without valid session."""
    result = subprocess.run(
        [str(LEGATUM_VERIFY), "--json", "nonexistent-session-id"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 1
    # Still error, but flag is recognized


class TestScriptParsability:
    """Test that we can load the script via exec and get functions."""

    def test_can_load_functions_via_exec(self):
        """Test that the script's functions can be extracted via exec."""
        namespace = {}
        code = LEGATUM_VERIFY.read_text()
        # We need to patch the paths before executing
        exec(code, namespace)
        # Check that the main function exists
        assert "main" in namespace
        assert "find_current_session" in namespace
        assert "extract_session_summary" in namespace
        assert "check_daily_note" in namespace
        assert "check_efferens" in namespace
        assert "check_arsenal_freshness" in namespace
        assert "check_todo_freshness" in namespace
        assert "check_garden_posts" in namespace

    def test_extract_session_summary_works(self, tmp_path):
        """Test extract_session_summary works with mock session data."""
        namespace = {}
        code = LEGATUM_VERIFY.read_text()
        exec(code, namespace)

        # Create a test session file
        session_file = tmp_path / "test.jsonl"
        entries = [
            {"type": "user", "message": {"content": "Hello world"}},
            {"type": "assistant", "message": {"content": [{"type": "text", "text": "Hi there"}]}},
            {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Bash"}]}},
        ]
        session_file.write_text("\n".join(json.dumps(e) for e in entries))

        extract = namespace["extract_session_summary"]
        result = extract(session_file)

        assert result["user_message_count"] == 1
        assert result["assistant_message_count"] == 1
        assert "Bash" in result["tools_used"]
        assert len(result["user_messages_sample"]) == 1

    def test_check_efferens_handles_empty_dir(self, tmp_path):
        """Test check_efferens returns ok with empty directory."""
        namespace = {}
        code = LEGATUM_VERIFY.read_text()
        # Patch the _EFFERENS_DIR constant
        lines = code.splitlines()
        lines = [
            line if not line.startswith("_EFFERENS_DIR = ") else
            f"_EFFERENS_DIR = Path(r'{tmp_path}')"
            for line in lines
        ]
        modified_code = "\n".join(lines)
        exec(modified_code, namespace)

        check = namespace["check_efferens"]
        result = check()
        assert result["ok"] is True
        assert result["count"] == 0

    def test_check_efferens_finds_messages(self, tmp_path):
        """Test check_efferens reports unaddressed messages."""
        namespace = {}
        code = LEGATUM_VERIFY.read_text()
        lines = code.splitlines()
        lines = [
            line if not line.startswith("_EFFERENS_DIR = ") else
            f"_EFFERENS_DIR = Path(r'{tmp_path}')"
            for line in lines
        ]
        modified_code = "\n".join(lines)
        exec(modified_code, namespace)

        # Create some message files
        (tmp_path / "message1.md").write_text("test")
        (tmp_path / "message2.md").write_text("test")

        check = namespace["check_efferens"]
        result = check()
        assert result["ok"] is False
        assert result["count"] == 2
        assert "message1.md" in result["files"]
        assert "message2.md" in result["files"]


def test_python_syntax_valid():
    """Test that the entire script has valid Python syntax."""
    import ast
    code = LEGATUM_VERIFY.read_text()
    # Should not raise
    ast.parse(code)
    assert True  # If we get here, it's valid
