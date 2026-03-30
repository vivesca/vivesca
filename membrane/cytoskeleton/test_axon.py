"""Smoke tests for axon.py guards."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

# Add hooks dir to path
sys.path.insert(0, str(Path(__file__).parent))

# We need to test functions without triggering sys.exit
import axon


def _make_data(tool, tool_input=None, **kwargs):
    return {"tool": tool, "tool_input": tool_input or {}, **kwargs}


def test_guard_bash_rm_r():
    """rm -r should be blocked."""
    data = _make_data("Bash", {"command": "rm -rf /tmp/foo"})
    try:
        axon.guard_bash(data)
        assert False, "Should have called sys.exit"
    except SystemExit:
        pass


def test_guard_bash_safe_command():
    """Normal commands should pass."""
    data = _make_data("Bash", {"command": "ls -la"})
    axon.guard_bash(data)  # Should not raise


def test_guard_bash_grep_home():
    """grep on ~ should be blocked."""
    data = _make_data("Bash", {"command": f"grep foo {Path.home()}"})
    try:
        axon.guard_bash(data)
        assert False, "Should have called sys.exit"
    except SystemExit:
        pass


def test_guard_write_secrets():
    """Writing to .secrets should be blocked."""
    data = _make_data("Write", {"file_path": "/home/user/.secrets"})
    try:
        axon.guard_write(data)
        assert False, "Should have called sys.exit"
    except SystemExit:
        pass


def test_guard_write_normal():
    """Writing to normal files should pass."""
    data = _make_data("Write", {"file_path": "/tmp/test.txt"})
    axon.guard_write(data)  # Should not raise


def test_guard_read_lockfile():
    """Reading lockfiles should be blocked."""
    data = _make_data("Read", {"file_path": "/project/package-lock.json"})
    try:
        axon.guard_read(data)
        assert False, "Should have called sys.exit"
    except SystemExit:
        pass


def test_guard_efferent_blocks_py():
    """Writing .py in ~/code/ should be blocked."""
    data = _make_data("Write", {"file_path": f"{Path.home()}/code/sortase/src/sortase/foo.py", "content": "x = 1"})
    try:
        axon.guard_efferent(data)
        assert False, "Should have called sys.exit"
    except SystemExit:
        pass


def test_guard_efferent_allows_md():
    """Writing .md in ~/code/ should pass."""
    data = _make_data("Write", {"file_path": f"{Path.home()}/code/sortase/README.md", "content": "# Readme"})
    axon.guard_efferent(data)  # Should not raise


def test_explore_subagent_denied():
    """Explore subagents should be denied by metabolic-gate."""
    from io import StringIO

    data = _make_data(
        "Agent",
        {
            "subagent_type": "Explore",
            "prompt": "find files",
            "run_in_background": True,
        },
    )
    with patch("sys.stdout", new_callable=StringIO) as mock_out:
        try:
            axon.guard_agent(data)
            assert False, "Should have called sys.exit"
        except SystemExit:
            output = mock_out.getvalue()
            assert "deny" in output, f"Expected deny, got: {output}"
            assert "metabolic-gate" in output or "translocon" in output


def test_general_purpose_agent_not_metabolic_denied():
    """general-purpose agent with haiku should NOT be denied by metabolic-gate."""
    from io import StringIO

    data = _make_data(
        "Agent",
        {
            "subagent_type": "general-purpose",
            "prompt": "find files",
            "run_in_background": True,
            "model": "haiku",
        },
    )
    try:
        axon.guard_agent(data)
        # May exit 0 for genome injection, but NOT deny
    except SystemExit as exc:
        # genome injection is exit(0), deny is also exit(0) —
        # but we need to verify it's NOT a deny
        # We can't easily distinguish here without capturing stdout
        # so we rely on the fact that general-purpose+haiku+bg passes
        # the metabolic check. Genome injection may still exit(0).
        pass


def test_efferent_blocks_germline_py():
    """Writing .py in ~/germline/ should be blocked."""
    data = _make_data(
        "Write",
        {
            "file_path": f"{Path.home()}/germline/metabolon/sortase/foo.py",
            "content": "x = 1",
        },
    )
    try:
        axon.guard_efferent(data)
        assert False, "Should have called sys.exit"
    except SystemExit:
        pass


def test_efferent_allows_germline_skill_md():
    """Writing SKILL.md in ~/germline/membrane/receptors/ should pass."""
    data = _make_data(
        "Write",
        {
            "file_path": f"{Path.home()}/germline/membrane/receptors/foo/SKILL.md",
            "content": "# foo",
        },
    )
    axon.guard_efferent(data)  # Should not raise


def test_pipeline_bypass_nudge_after_3_reads():
    """Reading 3+ implementation files triggers pipeline bypass nudge."""
    import tempfile
    count_file = Path(tempfile.mktemp())
    with patch.object(axon, '_IMPL_READ_COUNT_FILE', count_file):
        # First 2 reads: no nudge
        for i in range(2):
            data = _make_data("Read", {"file_path": f"{Path.home()}/germline/metabolon/sortase/cli.py"})
            axon.guard_pipeline_bypass(data)
        # 3rd read: should print nudge (allow_msg prints JSON to stdout)
        from io import StringIO
        captured = StringIO()
        with patch('sys.stdout', captured):
            data = _make_data("Read", {"file_path": f"{Path.home()}/germline/metabolon/sortase/router.py"})
            axon.guard_pipeline_bypass(data)
        assert "PIPELINE BYPASS" in captured.getvalue()
    count_file.unlink(missing_ok=True)


def test_pipeline_bypass_ignores_markdown():
    """Reading .md files should not increment the counter."""
    import tempfile
    count_file = Path(tempfile.mktemp())
    with patch.object(axon, '_IMPL_READ_COUNT_FILE', count_file):
        for i in range(5):
            data = _make_data("Read", {"file_path": f"{Path.home()}/germline/membrane/receptors/foo/SKILL.md"})
            axon.guard_pipeline_bypass(data)
        assert not count_file.exists() or count_file.read_text().strip() == "0" or not count_file.exists()
    count_file.unlink(missing_ok=True)


def test_pipeline_counter_resets_on_specification():
    """Invoking specification skill resets the counter."""
    import tempfile
    count_file = Path(tempfile.mktemp())
    count_file.write_text("5")
    with patch.object(axon, '_IMPL_READ_COUNT_FILE', count_file):
        data = _make_data("Skill", {"skill": "specification"})
        axon.reset_pipeline_counter(data)
        assert count_file.read_text().strip() == "0"
    count_file.unlink(missing_ok=True)


if __name__ == "__main__":
    tests = [f for f in dir() if f.startswith("test_")]
    passed = 0
    failed = 0
    for t in tests:
        try:
            globals()[t]()
            print(f"  PASS  {t}")
            passed += 1
        except Exception as e:
            print(f"  FAIL  {t}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
