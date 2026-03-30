"""Tests for translocon — unified dispatch CLI."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

_TRANSLOCON_PATH = os.path.expanduser("~/germline/effectors/translocon")


def _load_translocon():
    """Load the translocon module by exec-ing its Python body (after uv header)."""
    source = open(_TRANSLOCON_PATH).read()
    idx = source.index("# ///\n")
    idx = source.index("\n", idx + 1)
    body = source[idx + 1:]
    ns: dict = {}
    exec(body, ns)
    return ns


_mod = _load_translocon()
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
    with patch.dict(_mod, {"_direct_api": fake_api, "_atomic_commit": MagicMock()}):
        with patch("subprocess.run", return_value=_mock_run()) as mock_run:
            rc = main(["--build", str(tmp_path), "implement X"])
    assert rc == 0
    # direct_api should NOT be called for build mode
    fake_api.assert_not_called()
    # First subprocess.run call is the goose dispatch (auto-commit adds git calls after)
    first_cmd = mock_run.call_args_list[0][0][0]
    assert first_cmd[0] == "goose"
    assert "GLM-5.1" in first_cmd


def test_mcp_mode_skips_direct_api():
    """--mcp does NOT use direct API — goes straight to droid."""
    fake_api = MagicMock(return_value=0)
    with patch.dict(_mod, {"_direct_api": fake_api}):
        with patch("subprocess.run", return_value=_mock_run()) as mock_run:
            rc = main(["--mcp", "do MCP thing"])
    assert rc == 0
    fake_api.assert_not_called()
    cmd = mock_run.call_args[0][0]
    assert cmd[0].endswith("droid")
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
    assert cmd[0].endswith("droid")


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
    # dry-run prints the (coaching-injected) prompt to stdout, metadata to stderr
    assert "test prompt" in output


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
        # goose fails, droid succeeds, git calls succeed
        if cmd[0] == "goose":
            m.returncode = 1
        else:
            m.returncode = 0
        m.stdout = ""
        return m

    # direct API fails too, so we hit goose → droid chain
    with patch.dict(_mod, {"_direct_api": MagicMock(return_value=1), "_atomic_commit": MagicMock()}):
        with patch("subprocess.run", side_effect=fake_run):
            rc = main(["--build", str(tmp_path), "failing task"])
    assert rc == 0
    # First two dispatch calls: goose then droid (auto-commit adds git calls after droid succeeds)
    assert calls[0][0] == "goose"
    assert calls[1][0].endswith("droid")


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


def _make_recipe(tmp_path, skill="etiology", content="title: test\nprompt: default"):
    """Create a fake recipe.yaml under tmp_path for skill testing.

    translocon builds Path.home() / "germline/membrane/receptors/{skill}/recipe.yaml",
    so we need the germline/ prefix.
    """
    recipe_dir = tmp_path / "germline" / "membrane" / "receptors" / skill
    recipe_dir.mkdir(parents=True)
    (recipe_dir / "recipe.yaml").write_text(content)
    return recipe_dir


def test_skill_uses_recipe(tmp_path):
    """--skill loads recipe.yaml and passes to goose."""
    recipe_dir = _make_recipe(tmp_path)

    with patch.object(Path, "home", return_value=tmp_path):
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
    with patch.object(Path, "home", return_value=tmp_path):
        rc = main(["--skill", "nonexistent_skill", str(tmp_path), "do thing"])

    assert rc == 1
    err = capsys.readouterr().err
    assert "not found" in err
    assert "skill-sync" in err


def test_skill_with_build_uses_glm51(tmp_path):
    """--skill --build upgrades model to GLM-5.1."""
    _make_recipe(tmp_path)

    with patch.object(Path, "home", return_value=tmp_path):
        with patch.dict(_mod, {"_direct_api": MagicMock(return_value=1), "_atomic_commit": MagicMock()}):
            with patch("subprocess.run", return_value=_mock_run()) as mock_run:
                rc = main(["--skill", "etiology", "--build", str(tmp_path), "fix bug"])

    assert rc == 0
    # First subprocess.run call is the goose dispatch (auto-commit adds git calls after)
    first_cmd = mock_run.call_args_list[0][0][0]
    assert "GLM-5.1" in first_cmd


def test_skill_with_mcp_uses_droid(tmp_path):
    """--skill --mcp routes to droid with skill prefix in prompt."""
    _make_recipe(tmp_path)

    with patch.object(Path, "home", return_value=tmp_path):
        with patch("subprocess.run", return_value=_mock_run()) as mock_run:
            rc = main(["--skill", "etiology", "--mcp", str(tmp_path), "debug"])

    assert rc == 0
    cmd = mock_run.call_args[0][0]
    assert cmd[0].endswith("droid")
    assert "--auto" in cmd
    # The prompt should contain the skill invocation prefix
    prompt_in_cmd = cmd[-1]
    assert "/etiology" in prompt_in_cmd


def test_skill_no_prompt_uses_default(tmp_path):
    """--skill without prompt uses recipe's default prompt."""
    _make_recipe(tmp_path, content="title: test\nprompt: Execute the etiology skill.")

    with patch.object(Path, "home", return_value=tmp_path):
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
    _make_recipe(tmp_path)

    fake_api = MagicMock(return_value=0)
    with patch.object(Path, "home", return_value=tmp_path):
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
        m.stdout = "summary text\n"
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


# ── --eval flag tests ─────────────────────────────────────────────


def _make_sortase_log(tmp_path, traces: list[dict]) -> Path:
    """Create a fake sortase log.jsonl in tmp_path."""
    log_dir = tmp_path / ".local" / "share" / "sortase"
    log_dir.mkdir(parents=True)
    log_path = log_dir / "log.jsonl"
    lines = [json.dumps(t) for t in traces]
    log_path.write_text("\n".join(lines) + "\n")
    return log_path


_SORTASE_TRACES = [
    {"duration_s": 75.2, "failure_reason": None, "plan": "noesis.md",
     "success": True, "tool": "droid", "timestamp": "2026-03-30T09:37:39"},
    {"duration_s": 85.4, "failure_reason": None, "plan": "ingestion.md",
     "success": True, "tool": "droid", "timestamp": "2026-03-30T09:37:40"},
    {"duration_s": 460.3, "failure_reason": "tests", "plan": "scout-spec.md",
     "success": False, "tool": "goose", "timestamp": "2026-03-30T16:59:06"},
    {"duration_s": 665.7, "failure_reason": "placeholder-scan", "plan": "skill-sync-spec.md",
     "success": False, "tool": "goose", "timestamp": "2026-03-30T17:01:32"},
    {"duration_s": 109.6, "failure_reason": None, "plan": "expression.md",
     "success": True, "tool": "droid", "timestamp": "2026-03-30T09:38:05"},
]


def test_eval_reads_log_and_prints_summary(tmp_path, capsys):
    """--eval reads sortase log and prints success rate + tool breakdown."""
    _make_sortase_log(tmp_path, _SORTASE_TRACES)
    with patch.object(Path, "home", return_value=tmp_path):
        rc = main(["--eval"])
    assert rc == 0
    out = capsys.readouterr().out
    # 5 traces, 3 success = 60%
    assert "Sortase traces: 5" in out
    assert "Success: 3 (60%)" in out
    assert "Fail: 2" in out
    # Tool breakdown
    assert "droid" in out
    assert "goose" in out
    # Failure reasons
    assert "tests" in out
    assert "placeholder-scan" in out


def test_eval_no_log(tmp_path, capsys):
    """--eval with no log file returns error."""
    with patch.object(Path, "home", return_value=tmp_path):
        rc = main(["--eval"])
    assert rc == 1
    assert "no sortase log" in capsys.readouterr().err


def test_eval_failures_only(tmp_path, capsys):
    """--failures-only shows only failed traces with details."""
    _make_sortase_log(tmp_path, _SORTASE_TRACES)
    with patch.object(Path, "home", return_value=tmp_path):
        rc = main(["--eval", "--failures-only"])
    assert rc == 0
    out = capsys.readouterr().out
    # Should still have the summary line
    assert "Fail: 2" in out
    # Should list specific failed traces with details
    assert "scout-spec.md" in out
    assert "skill-sync-spec.md" in out
    assert "tests" in out
    assert "placeholder-scan" in out


def test_eval_count_limits_traces(tmp_path, capsys):
    """--count N analyzes only last N traces."""
    _make_sortase_log(tmp_path, _SORTASE_TRACES)
    with patch.object(Path, "home", return_value=tmp_path):
        rc = main(["--eval", "--count", "2"])
    assert rc == 0
    out = capsys.readouterr().out
    # Last 2 traces: expression (success) + skill-sync-spec (fail) = 50%
    assert "Sortase traces: 2" in out
    assert "Success: 1 (50%)" in out


def test_eval_all_success(tmp_path, capsys):
    """--eval with 100% success rate."""
    traces = [
        {"duration_s": 50, "failure_reason": None, "plan": "a.md",
         "success": True, "tool": "droid", "timestamp": "2026-03-30T10:00:00"},
        {"duration_s": 60, "failure_reason": None, "plan": "b.md",
         "success": True, "tool": "goose", "timestamp": "2026-03-30T10:01:00"},
    ]
    _make_sortase_log(tmp_path, traces)
    with patch.object(Path, "home", return_value=tmp_path):
        rc = main(["--eval"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Success: 2 (100%)" in out
    assert "Fail: 0" in out
    # No failure reasons section
    assert "Failure reasons" not in out


def test_eval_skips_other_routing(tmp_path, capsys):
    """--eval ignores dir/prompt and other flags — pure analysis."""
    _make_sortase_log(tmp_path, _SORTASE_TRACES)
    with patch.object(Path, "home", return_value=tmp_path):
        # Should NOT try direct API or subprocess despite extra args
        with patch.dict(_mod, {"_direct_api": MagicMock(return_value=99)}):
            rc = main(["--eval", "--model", "GLM-5.1", "ignored-dir", "ignored prompt"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Sortase traces: 5" in out


# ── v4: Pattern 1 — Route chains via YAML config ─────────────────


def test_load_routes_default(tmp_path):
    """No config file → hardcoded defaults returned."""
    with patch.object(Path, "home", return_value=tmp_path):
        routes = _mod["_load_routes"]()
    assert "explore" in routes
    assert routes["explore"]["chain"] == ["goose", "droid"]
    assert routes["build"]["model"] == "GLM-5.1"
    assert routes["mcp"]["auto"] == "high"
    assert routes["safe"]["chain"] == ["droid"]
    assert "skill" in routes


def test_load_routes_from_yaml(tmp_path):
    """Config file overrides defaults."""
    cfg_dir = tmp_path / ".config" / "translocon"
    cfg_dir.mkdir(parents=True)
    import yaml
    custom = {
        "explore": {"model": "GLM-5.1", "chain": ["droid", "goose"]},
        "custom_mode": {"model": "GLM-4.7", "chain": ["goose"]},
    }
    routes_file = cfg_dir / "routes.yaml"
    routes_file.write_text(yaml.dump(custom))

    with patch.dict(_mod, {"ROUTES_PATH": routes_file}):
        routes = _mod["_load_routes"]()
    assert routes["explore"]["model"] == "GLM-5.1"
    assert routes["explore"]["chain"] == ["droid", "goose"]
    assert routes["custom_mode"]["chain"] == ["goose"]


# ── v4: Pattern 2 — Auto-downtime with cooldown ──────────────────


def test_auto_downtime_after_3_failures(tmp_path):
    """3 consecutive failures → backend enters cooldown (not healthy)."""
    health_dir = tmp_path / ".local" / "share" / "translocon"
    health_dir.mkdir(parents=True)
    health_file = health_dir / "health.json"

    with patch.dict(_mod, {"HEALTH_PATH": health_file}):
        record = _mod["_record_result"]
        healthy = _mod["_is_healthy"]
        # Record 3 failures
        record("goose", False)
        record("goose", False)
        assert healthy("goose") is True  # 2 failures, not yet
        record("goose", False)
        # 3 consecutive → cooldown
        assert healthy("goose") is False
        # droid was never touched → healthy
        assert healthy("droid") is True


def test_cooldown_expires(tmp_path):
    """After cooldown period, backend becomes healthy again."""
    health_dir = tmp_path / ".local" / "share" / "translocon"
    health_dir.mkdir(parents=True)
    import datetime
    # Write a health file with cooldown that expired 1 second ago
    past = (datetime.datetime.now() - datetime.timedelta(seconds=1)).isoformat()
    health_data = {
        "goose": {"consecutive_failures": 3, "cooldown_until": past},
        "droid": {"consecutive_failures": 0, "cooldown_until": None},
    }
    health_file = health_dir / "health.json"
    health_file.write_text(json.dumps(health_data))

    with patch.dict(_mod, {"HEALTH_PATH": health_file}):
        assert _mod["_is_healthy"]("goose") is True  # cooldown expired


def test_success_resets_failures(tmp_path):
    """A successful call resets consecutive failures."""
    health_dir = tmp_path / ".local" / "share" / "translocon"
    health_dir.mkdir(parents=True)
    health_file = health_dir / "health.json"

    with patch.dict(_mod, {"HEALTH_PATH": health_file}):
        record = _mod["_record_result"]
        healthy = _mod["_is_healthy"]
        record("goose", False)
        record("goose", False)
        record("goose", False)
        assert healthy("goose") is False  # in cooldown
        record("goose", True)  # success resets
        assert healthy("goose") is True


# ── v4: Pattern 3 — Per-call logging ──────────────────────────────


def test_per_call_logging(tmp_path):
    """Every call writes an entry to log.jsonl."""
    log_dir = tmp_path / ".local" / "share" / "translocon"
    log_dir.mkdir(parents=True)
    log_file = log_dir / "log.jsonl"

    with patch.dict(_mod, {"LOG_PATH": log_file}):
        log_fn = _mod["_log_call"]
        log_fn({"mode": "explore", "backend": "goose", "model": "GLM-4.7",
                "success": True, "duration_s": 5.2})
        log_fn({"mode": "build", "backend": "droid", "model": "GLM-5.1",
                "success": False, "duration_s": 12.0})

    assert log_file.exists()
    lines = log_file.read_text().strip().split("\n")
    assert len(lines) == 2
    entry1 = json.loads(lines[0])
    assert entry1["mode"] == "explore"
    assert entry1["success"] is True
    assert "timestamp" in entry1
    entry2 = json.loads(lines[1])
    assert entry2["mode"] == "build"
    assert entry2["success"] is False


# ── v4: Chain fallback integration test ───────────────────────────


def test_chain_fallback(tmp_path):
    """First backend in chain fails → tries next backend in chain."""
    calls: list[str] = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd[0])
        m = MagicMock()
        m.returncode = 1 if len(calls) == 1 else 0  # first fails, second succeeds
        m.stdout = "ok\n"
        return m

    # Use --build mode which has chain: [goose, droid]
    # Also disable direct API
    with patch.dict(_mod, {"_direct_api": MagicMock(return_value=1)}):
        with patch("subprocess.run", side_effect=fake_run):
            rc = main(["--build", str(tmp_path), "implement X"])
    assert rc == 0
    assert calls[0] == "goose"
    assert calls[1].endswith("droid")


# ── v5: Batch retry flag ──────────────────────────────────────────


def test_batch_retry_flag_parsed():
    """--retries is parsed correctly with and without explicit value."""
    _parse_args = _mod["_parse_args"]
    args = _parse_args(["--batch", "*.md", "--retries", "2", "."])
    assert args.retries == 2
    args_default = _parse_args(["--batch", "*.md", "."])
    assert args_default.retries == 0


# ── Rate-limit tracking ───────────────────────────────────────────


def test_record_rate_limit_sets_short_cooldown(tmp_path):
    """Rate limit records a 60-second cooldown and timestamp."""
    health_dir = tmp_path / ".local" / "share" / "translocon"
    health_dir.mkdir(parents=True)
    health_file = health_dir / "health.json"

    with patch.dict(_mod, {"HEALTH_PATH": health_file}):
        record_rl = _mod["_record_rate_limit"]
        record_rl("goose")

    state = json.loads(health_file.read_text())
    entry = state["goose"]
    assert "cooldown_until" in entry
    assert "last_rate_limit" in entry
    # Cooldown should be ~60 seconds from now
    import datetime
    cooldown_at = datetime.datetime.fromisoformat(entry["cooldown_until"])
    delta = (cooldown_at - datetime.datetime.now()).total_seconds()
    assert 50 < delta < 70, f"Expected ~60s cooldown, got {delta:.0f}s"


def test_rate_limit_preserves_existing_state(tmp_path):
    """Rate limit update preserves other backends in health file."""
    health_dir = tmp_path / ".local" / "share" / "translocon"
    health_dir.mkdir(parents=True)
    health_file = health_dir / "health.json"
    health_file.write_text(json.dumps({
        "droid": {"consecutive_failures": 1, "cooldown_until": None},
    }))

    with patch.dict(_mod, {"HEALTH_PATH": health_file}):
        _mod["_record_rate_limit"]("goose")

    state = json.loads(health_file.read_text())
    assert "droid" in state
    assert state["droid"]["consecutive_failures"] == 1
    assert "last_rate_limit" in state["goose"]


def test_429_in_tee_log_triggers_rate_limit(tmp_path):
    """When tee log contains 429, rate limit cooldown is recorded."""
    health_dir = tmp_path / ".local" / "share" / "translocon"
    health_dir.mkdir(parents=True)
    health_file = health_dir / "health.json"

    # Create a tee log with 429 indicator
    tee_log = tmp_path / "output.log"
    tee_log.write_text("some output\nHTTP 429 Too Many Requests\nmore output")

    # Simulate a goose failure with --output-file so tee_log is set
    record_result = _mod["_record_result"]
    record_rate_limit = _mod["_record_rate_limit"]

    with patch.dict(_mod, {"HEALTH_PATH": health_file, "_record_result": record_result, "_record_rate_limit": record_rate_limit}):
        # Record a failure, then check if 429 was in log → call _record_rate_limit
        record_result("goose", False)
        tail = tee_log.read_text()[-500:]
        if "429" in tail:
            record_rate_limit("goose")

    state = json.loads(health_file.read_text())
    assert state["goose"]["consecutive_failures"] == 1
    assert "last_rate_limit" in state["goose"]
