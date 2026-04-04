"""Smoke tests for axon.py guards."""

from __future__ import annotations

import contextlib
import sys
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))

import axon


def _make_data(tool, tool_input=None, **kwargs):
    return {"tool": tool, "tool_input": tool_input or {}, **kwargs}


def test_guard_bash_rm_r():
    """rm -r should be blocked."""
    data = _make_data("Bash", {"command": "rm -rf /tmp/foo"})
    with contextlib.suppress(SystemExit):
        axon.guard_bash(data)
        raise AssertionError("Should have called sys.exit")


def test_guard_bash_safe_command():
    """Normal commands should pass."""
    data = _make_data("Bash", {"command": "ls -la"})
    axon.guard_bash(data)


def test_guard_bash_grep_home():
    """grep on ~ should be blocked."""
    data = _make_data("Bash", {"command": f"grep foo {Path.home()}"})
    with contextlib.suppress(SystemExit):
        axon.guard_bash(data)
        raise AssertionError("Should have called sys.exit")


def test_guard_write_secrets():
    """Writing to .secrets should be blocked."""
    data = _make_data("Write", {"file_path": "/home/user/.secrets"})
    with contextlib.suppress(SystemExit):
        axon.guard_write(data)
        raise AssertionError("Should have called sys.exit")


def test_guard_write_normal():
    """Writing to normal files should pass."""
    data = _make_data("Write", {"file_path": "/tmp/test.txt"})
    axon.guard_write(data)


def test_guard_read_lockfile():
    """Reading lockfiles should be blocked."""
    data = _make_data("Read", {"file_path": "/project/package-lock.json"})
    with contextlib.suppress(SystemExit):
        axon.guard_read(data)
        raise AssertionError("Should have called sys.exit")


def test_guard_efferent_blocks_py():
    """Writing .py in ~/code/ should be blocked."""
    data = _make_data(
        "Write",
        {"file_path": f"{Path.home()}/code/sortase/src/sortase/foo.py", "content": "x = 1"},
    )
    with contextlib.suppress(SystemExit):
        axon.guard_efferent(data)
        raise AssertionError("Should have called sys.exit")


def test_guard_efferent_allows_md():
    """Writing .md in ~/code/ should pass."""
    data = _make_data(
        "Write", {"file_path": f"{Path.home()}/code/sortase/README.md", "content": "# Readme"}
    )
    axon.guard_efferent(data)


def test_explore_subagent_denied():
    """Explore subagents should be denied by metabolic-gate."""
    data = _make_data(
        "Agent",
        {"subagent_type": "Explore", "prompt": "find files", "run_in_background": True},
    )
    with patch("sys.stdout", new_callable=StringIO) as mock_out:
        try:
            axon.guard_agent(data)
            raise AssertionError("Should have called sys.exit")
        except SystemExit:
            output = mock_out.getvalue()
            assert "deny" in output, f"Expected deny, got: {output}"
            assert "metabolic-gate" in output or "translocon" in output


def test_general_purpose_agent_not_metabolic_denied():
    """general-purpose agent with haiku should NOT be denied by metabolic-gate."""
    data = _make_data(
        "Agent",
        {
            "subagent_type": "general-purpose",
            "prompt": "find files",
            "run_in_background": True,
            "model": "haiku",
        },
    )
    with contextlib.suppress(SystemExit):
        axon.guard_agent(data)


def test_efferent_blocks_germline_py():
    """Writing .py in ~/germline/ should be blocked."""
    data = _make_data(
        "Write",
        {
            "file_path": f"{Path.home()}/germline/metabolon/sortase/foo.py",
            "content": "x = 1",
        },
    )
    with contextlib.suppress(SystemExit):
        axon.guard_efferent(data)
        raise AssertionError("Should have called sys.exit")


def test_efferent_allows_germline_skill_md():
    """Writing SKILL.md in ~/germline/membrane/receptors/ should pass."""
    data = _make_data(
        "Write",
        {
            "file_path": f"{Path.home()}/germline/membrane/receptors/foo/SKILL.md",
            "content": "# foo",
        },
    )
    axon.guard_efferent(data)


def test_pipeline_bypass_nudge_after_3_reads():
    """Reading 3+ implementation files triggers pipeline bypass nudge."""
    count_file = Path(tempfile.mkdtemp()) / "count"
    with patch.object(axon, "_IMPL_READ_COUNT_FILE", count_file):
        for _ in range(2):
            data = _make_data(
                "Read", {"file_path": f"{Path.home()}/germline/metabolon/sortase/cli.py"}
            )
            axon.guard_pipeline_bypass(data)
        captured = StringIO()
        with patch("sys.stdout", captured):
            data = _make_data(
                "Read", {"file_path": f"{Path.home()}/germline/metabolon/sortase/router.py"}
            )
            axon.guard_pipeline_bypass(data)
        assert "PIPELINE BYPASS" in captured.getvalue()
    count_file.unlink(missing_ok=True)


def test_pipeline_bypass_ignores_markdown():
    """Reading .md files should not increment the counter."""
    count_file = Path(tempfile.mkdtemp()) / "count"
    with patch.object(axon, "_IMPL_READ_COUNT_FILE", count_file):
        for _ in range(5):
            data = _make_data(
                "Read", {"file_path": f"{Path.home()}/germline/membrane/receptors/foo/SKILL.md"}
            )
            axon.guard_pipeline_bypass(data)
        assert not count_file.exists() or count_file.read_text().strip() == "0"
    count_file.unlink(missing_ok=True)


def test_pipeline_counter_resets_on_mitogen():
    """Invoking mitogen skill resets the counter."""
    count_file = Path(tempfile.mkdtemp()) / "count"
    count_file.write_text("5")
    with patch.object(axon, "_IMPL_READ_COUNT_FILE", count_file):
        data = _make_data("Skill", {"skill": "mitogen"})
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
            print(f"  PASS: {t}")
            passed += 1
        except Exception as e:
            print(f"  FAIL: {t}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
