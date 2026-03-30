"""Tests for scout — unified dispatch CLI."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

_SCOUT_PATH = os.path.expanduser("~/germline/effectors/scout")


def _load_scout():
    """Load the scout module by exec-ing its Python body (after uv header)."""
    source = open(_SCOUT_PATH).read()
    idx = source.index("# ///\n")
    idx = source.index("\n", idx + 1)
    body = source[idx + 1:]
    ns: dict = {}
    exec(body, ns)
    return ns


_mod = _load_scout()
main = _mod["main"]
_direct_api = _mod["_direct_api"]
_read_dir_context = _mod["_read_dir_context"]


def _mock_run(returncode: int = 0) -> MagicMock:
    m = MagicMock()
    m.returncode = returncode
    return m


# ── Direct API tier ────────────────────────────────────────────────


def test_default_mode_uses_direct_api():
    """Default mode (no flags) tries direct API first."""
    fake_api = MagicMock(return_value=0)
    with patch.dict(_mod, {"_direct_api": fake_api, "_read_dir_context": MagicMock(return_value="")}):
        with patch("subprocess.run", return_value=_mock_run()) as mock_run:
            rc = main([".", "hello"])
    assert rc == 0
    fake_api.assert_called_once()
    # subprocess.run should NOT be called — direct API succeeded
    mock_run.assert_not_called()


def test_default_direct_api_fallback_to_goose(tmp_path):
    """If direct API fails, falls back to goose."""
    with patch.dict(_mod, {"_direct_api": MagicMock(return_value=1)}):
        with patch("subprocess.run", return_value=_mock_run()) as mock_run:
            rc = main([str(tmp_path), "hello"])
    assert rc == 0
    # Should have called goose (subprocess.run)
    mock_run.assert_called()


def test_safe_mode_uses_direct_api():
    """--safe routes to direct API first."""
    fake_api = MagicMock(return_value=0)
    with patch.dict(_mod, {"_direct_api": fake_api, "_read_dir_context": MagicMock(return_value="")}):
        with patch("subprocess.run", return_value=_mock_run()) as mock_run:
            rc = main(["--safe", ".", "audit this"])
    assert rc == 0
    # Verify prompt contains READ ONLY guard
    call_args = fake_api.call_args[0]
    assert "READ ONLY" in call_args[0]
    mock_run.assert_not_called()


def test_build_mode_skips_direct_api(tmp_path):
    """--build does NOT use direct API — goes straight to goose."""
    fake_api = MagicMock(return_value=0)
    with patch.dict(_mod, {"_direct_api": fake_api}):
        with patch("subprocess.run", return_value=_mock_run()) as mock_run:
            rc = main(["--build", str(tmp_path), "implement X"])
    assert rc == 0
    # direct_api should NOT be called for build mode
    fake_api.assert_not_called()
    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "goose"
    assert "GLM-5.1" in cmd


def test_mcp_mode_skips_direct_api():
    """--mcp does NOT use direct API — goes straight to droid."""
    fake_api = MagicMock(return_value=0)
    with patch.dict(_mod, {"_direct_api": fake_api}):
        with patch("subprocess.run", return_value=_mock_run()) as mock_run:
            rc = main(["--mcp", "do MCP thing"])
    assert rc == 0
    fake_api.assert_not_called()
    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "droid"
    assert "--auto" in cmd
    assert "high" in cmd


def test_backend_override_skips_direct():
    """--backend droid overrides direct API even for explore."""
    fake_api = MagicMock(return_value=0)
    with patch.dict(_mod, {"_direct_api": fake_api}):
        with patch("subprocess.run", return_value=_mock_run()) as mock_run:
            rc = main(["--backend", "droid", ".", "explore X"])
    assert rc == 0
    fake_api.assert_not_called()
    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "droid"


def test_model_override():
    """--model changes the model for direct API tier."""
    fake_api = MagicMock(return_value=0)
    with patch.dict(_mod, {"_direct_api": fake_api}):
        with patch("subprocess.run", return_value=_mock_run()):
            rc = main(["--model", "GLM-5.1", ".", "quick check"])
    assert rc == 0
    # api_model is model.lower()
    assert fake_api.call_args[0][1] == "glm-5.1"


# ── Existing behaviour preserved ──────────────────────────────────


def test_dry_run_prints_command(tmp_path, capsys):
    with patch("subprocess.run") as mock_run:
        rc = main(["--dry-run", str(tmp_path), "test prompt"])
    assert rc == 0
    mock_run.assert_not_called()
    output = capsys.readouterr().out
    assert "goose" in output


def test_file_prompt(tmp_path):
    prompt_file = tmp_path / "spec.md"
    prompt_file.write_text("do the thing from file")
    with patch.dict(_mod, {"_direct_api": MagicMock(return_value=0)}):
        with patch("subprocess.run", return_value=_mock_run()):
            rc = main(["-f", str(prompt_file), str(tmp_path)])
    assert rc == 0


def test_goose_fallback_to_droid(tmp_path):
    """If goose fails and no backend override, falls back to droid."""
    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        m = MagicMock()
        m.returncode = 1 if cmd[0] == "goose" else 0
        return m

    # direct API fails too, so we hit goose → droid chain
    with patch.dict(_mod, {"_direct_api": MagicMock(return_value=1)}):
        with patch("subprocess.run", side_effect=fake_run):
            rc = main(["--build", str(tmp_path), "failing task"])
    assert rc == 0
    assert len(calls) == 2
    assert calls[0][0] == "goose"
    assert calls[1][0] == "droid"


# ── _direct_api unit tests ────────────────────────────────────────


def test_direct_api_no_key(capsys):
    """Returns 1 when ZHIPU_API_KEY is not set."""
    with patch.dict(os.environ, {}, clear=True):
        # Remove key if present
        os.environ.pop("ZHIPU_API_KEY", None)
        rc = _direct_api("test prompt")
    assert rc == 1
    assert "ZHIPU_API_KEY not set" in capsys.readouterr().err


def test_direct_api_success(capsys):
    """Returns 0 and prints response text on success."""
    fake_resp_data = {"content": [{"text": "hello from API"}]}
    fake_resp = MagicMock()
    fake_resp.read.return_value = json.dumps(fake_resp_data).encode()

    with patch.dict(os.environ, {"ZHIPU_API_KEY": "test-key"}):
        with patch("urllib.request.urlopen", return_value=fake_resp):
            rc = _direct_api("test prompt", model="glm-4.7")
    assert rc == 0
    assert "hello from API" in capsys.readouterr().out


def test_direct_api_failure(capsys):
    """Returns 1 on API error."""
    with patch.dict(os.environ, {"ZHIPU_API_KEY": "test-key"}):
        with patch("urllib.request.urlopen", side_effect=Exception("timeout")):
            rc = _direct_api("test prompt")
    assert rc == 1
    assert "direct API failed" in capsys.readouterr().err


# ── _read_dir_context unit tests ──────────────────────────────────


def test_read_dir_context(tmp_path):
    """Reads .py files and formats them with filenames."""
    (tmp_path / "alpha.py").write_text("print('a')")
    (tmp_path / "beta.py").write_text("print('b')")
    (tmp_path / "notes.txt").write_text("not python")

    result = _read_dir_context(str(tmp_path))
    assert "### alpha.py" in result
    assert "### beta.py" in result
    assert "print('a')" in result
    assert "print('b')" in result
    assert "notes.txt" not in result


def test_read_dir_context_empty(tmp_path):
    """Returns empty string for directory with no .py files."""
    (tmp_path / "readme.md").write_text("hello")
    assert _read_dir_context(str(tmp_path)) == ""


def test_read_dir_context_skips_large(tmp_path):
    """Skips files >= 50000 bytes."""
    big = tmp_path / "huge.py"
    big.write_text("x" * 50001)
    small = tmp_path / "tiny.py"
    small.write_text("ok")

    result = _read_dir_context(str(tmp_path))
    assert "### huge.py" not in result
    assert "### tiny.py" in result


# ── --skill flag tests ────────────────────────────────────────────


def test_skill_uses_recipe(tmp_path):
    """--skill loads recipe.yaml and passes to goose."""
    recipe_dir = tmp_path / "membrane" / "receptors" / "etiology"
    recipe_dir.mkdir(parents=True)
    (recipe_dir / "recipe.yaml").write_text("title: test\nprompt: default prompt")

    with patch.dict(os.environ, {"HOME": str(tmp_path)}):
        with patch.dict(_mod, {"_direct_api": MagicMock(return_value=1)}):
            with patch("subprocess.run", return_value=_mock_run()) as mock_run:
                rc = main(["--skill", "etiology", str(tmp_path), "debug this crash"])

    assert rc == 0
    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "goose"
    assert "--recipe" in cmd
    assert str(recipe_dir / "recipe.yaml") in cmd


def test_skill_not_found(tmp_path, capsys):
    """--skill with nonexistent skill errors with hint."""
    with patch.dict(os.environ, {"HOME": str(tmp_path)}):
        rc = main(["--skill", "nonexistent_skill", str(tmp_path), "do thing"])

    assert rc == 1
    err = capsys.readouterr().err
    assert "not found" in err
    assert "skill-sync" in err


def test_skill_with_build_uses_glm51(tmp_path):
    """--skill --build upgrades model to GLM-5.1."""
    recipe_dir = tmp_path / "membrane" / "receptors" / "etiology"
    recipe_dir.mkdir(parents=True)
    (recipe_dir / "recipe.yaml").write_text("title: test\nprompt: default")

    with patch.dict(os.environ, {"HOME": str(tmp_path)}):
        with patch.dict(_mod, {"_direct_api": MagicMock(return_value=1)}):
            with patch("subprocess.run", return_value=_mock_run()) as mock_run:
                rc = main(["--skill", "etiology", "--build", str(tmp_path), "fix bug"])

    assert rc == 0
    cmd = mock_run.call_args[0][0]
    assert "GLM-5.1" in cmd


def test_skill_with_mcp_uses_droid(tmp_path):
    """--skill --mcp routes to droid with skill prefix in prompt."""
    recipe_dir = tmp_path / "membrane" / "receptors" / "etiology"
    recipe_dir.mkdir(parents=True)
    (recipe_dir / "recipe.yaml").write_text("title: test\nprompt: default")

    with patch.dict(os.environ, {"HOME": str(tmp_path)}):
        with patch("subprocess.run", return_value=_mock_run()) as mock_run:
            rc = main(["--skill", "etiology", "--mcp", str(tmp_path), "debug"])

    assert rc == 0
    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "droid"
    assert "--auto" in cmd
    # The prompt should contain the skill invocation prefix
    prompt_in_cmd = cmd[-1]
    assert "/etiology" in prompt_in_cmd


def test_skill_no_prompt_uses_default(tmp_path):
    """--skill without prompt uses recipe's default prompt."""
    recipe_dir = tmp_path / "membrane" / "receptors" / "etiology"
    recipe_dir.mkdir(parents=True)
    (recipe_dir / "recipe.yaml").write_text(
        "title: test\nprompt: Execute the etiology skill."
    )

    with patch.dict(os.environ, {"HOME": str(tmp_path)}):
        with patch.dict(_mod, {"_direct_api": MagicMock(return_value=1)}):
            with patch("subprocess.run", return_value=_mock_run()) as mock_run:
                # No prompt provided — should use recipe default
                rc = main(["--skill", "etiology", str(tmp_path)])

    assert rc == 0
    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "goose"
    assert "--recipe" in cmd


def test_skill_skips_direct_api(tmp_path):
    """--skill always goes to goose, never direct API."""
    recipe_dir = tmp_path / "membrane" / "receptors" / "etiology"
    recipe_dir.mkdir(parents=True)
    (recipe_dir / "recipe.yaml").write_text("title: test\nprompt: default")

    fake_api = MagicMock(return_value=0)
    with patch.dict(os.environ, {"HOME": str(tmp_path)}):
        with patch.dict(_mod, {"_direct_api": fake_api}):
            with patch("subprocess.run", return_value=_mock_run()):
                rc = main(["--skill", "etiology", str(tmp_path), "test"])

    assert rc == 0
    fake_api.assert_not_called()


# ── --output flag tests ───────────────────────────────────────────


def test_output_to_file(tmp_path):
    """--output <file> captures stdout and writes to file."""
    out_file = tmp_path / "result.md"

    # Use goose path: mock subprocess to produce output
    def fake_run(cmd, **kwargs):
        m = MagicMock()
        m.returncode = 0
        m.stdout = "output from goose\n"
        return m

    with patch.dict(_mod, {"_direct_api": MagicMock(return_value=1)}):
        with patch("subprocess.run", side_effect=fake_run):
            rc = main(["--build", "--output", str(out_file), str(tmp_path), "test"])

    assert rc == 0
    assert out_file.exists()
    assert "output from goose" in out_file.read_text()


def test_output_telegram(tmp_path):
    """--output telegram pipes result to efferens telegram."""
    # This test verifies the routing logic — actual telegram call is mocked
    def fake_run(cmd, **kwargs):
        m = MagicMock()
        m.returncode = 0
        m.stdout = b"summary text\n"
        return m

    with patch.dict(_mod, {"_direct_api": MagicMock(return_value=1)}):
        with patch("subprocess.run", side_effect=fake_run) as mock_run:
            rc = main(["--build", "--output", "telegram", str(tmp_path), "test"])

    assert rc == 0
    # Second call should be the efferens dispatch
    calls = mock_run.call_args_list
    assert len(calls) >= 2


def test_output_default_is_stdout(tmp_path, capsys):
    """Without --output, result goes to stdout (no file written)."""
    with patch.dict(_mod, {"_direct_api": MagicMock(return_value=0)}):
        with patch.dict(_mod, {"_read_dir_context": MagicMock(return_value="")}):
            with patch.dict(_mod, {"_direct_api": MagicMock(return_value=0)}):
                rc = main([str(tmp_path), "test"])
    assert rc == 0
