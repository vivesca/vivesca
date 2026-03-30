"""Tests for scout — unified dispatch CLI."""
from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from unittest.mock import MagicMock, patch

import pytest

# scout uses a uv script shebang, so spec_from_file_location fails.
# Extract the pure-Python body after the last '///' marker instead.
_SVCOUT_PATH = os.path.expanduser("~/germline/effectors/scout")


def _load_scout_main():
    """Load the scout module by exec-ing its Python body (after uv header)."""
    source = open(_SVCOUT_PATH).read()
    # Find the end of the uv script header block
    idx = source.index("# ///\n")
    idx = source.index("\n", idx + 1)  # skip the closing # /// line
    body = source[idx + 1:]
    ns: dict = {}
    exec(body, ns)
    return ns["main"]


main = _load_scout_main()


def _mock_run(returncode: int = 0) -> MagicMock:
    m = MagicMock()
    m.returncode = returncode
    return m


# 1. Default mode uses goose backend with GLM-4.7
def test_default_mode_uses_goose(tmp_path):
    with patch("subprocess.run", return_value=_mock_run()) as mock_run:
        main([str(tmp_path), "hello"])
    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "goose"
    assert "GLM-4.7" in cmd


# 2. Build mode uses GLM-5.1
def test_build_mode_uses_glm51(tmp_path):
    with patch("subprocess.run", return_value=_mock_run()) as mock_run:
        main(["--build", str(tmp_path), "implement X"])
    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "goose"
    assert "GLM-5.1" in cmd


# 3. MCP mode uses droid with --auto high
def test_mcp_mode_uses_droid():
    with patch("subprocess.run", return_value=_mock_run()) as mock_run:
        main(["--mcp", "do MCP thing"])
    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "droid"
    assert "--auto" in cmd
    assert "high" in cmd


# 4. Safe mode is read-only, uses droid, no --auto, prompt is prefixed
def test_safe_mode_read_only(tmp_path):
    with patch("subprocess.run", return_value=_mock_run()) as mock_run:
        main(["--safe", str(tmp_path), "audit this"])
    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "droid"
    assert "--auto" not in cmd
    # Prompt should be prefixed with READ ONLY
    prompt_in_cmd = cmd[-1]
    assert prompt_in_cmd.startswith("READ ONLY.")


# 5. Backend override forces droid regardless of mode
def test_backend_override(tmp_path):
    with patch("subprocess.run", return_value=_mock_run()) as mock_run:
        main(["--backend", "droid", str(tmp_path), "explore X"])
    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "droid"


# 6. Model override takes precedence
def test_model_override(tmp_path):
    with patch("subprocess.run", return_value=_mock_run()) as mock_run:
        main(["--model", "GLM-5.1", str(tmp_path), "quick check"])
    cmd = mock_run.call_args[0][0]
    assert "GLM-5.1" in cmd


# 7. Dry run prints command without executing
def test_dry_run_prints_command(tmp_path, capsys):
    with patch("subprocess.run") as mock_run:
        rc = main(["--dry-run", str(tmp_path), "test prompt"])
    assert rc == 0
    mock_run.assert_not_called()
    output = capsys.readouterr().out
    assert "goose" in output


# 8. File prompt reads from file
def test_file_prompt(tmp_path):
    prompt_file = tmp_path / "spec.md"
    prompt_file.write_text("do the thing from file")
    with patch("subprocess.run", return_value=_mock_run()) as mock_run:
        main(["-f", str(prompt_file), str(tmp_path)])
    cmd = mock_run.call_args[0][0]
    assert cmd[-1] == "do the thing from file"


# 9. Goose failure falls back to droid
def test_goose_fallback_to_droid(tmp_path):
    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        m = MagicMock()
        m.returncode = 1 if cmd[0] == "goose" else 0
        return m

    with patch("subprocess.run", side_effect=fake_run):
        rc = main([str(tmp_path), "failing task"])
    assert rc == 0
    assert len(calls) == 2
    assert calls[0][0] == "goose"
    assert calls[1][0] == "droid"
