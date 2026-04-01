from __future__ import annotations

"""Tests for metabolon.organelles.translocon — helpers, caching, command
building, mode resolution, dispatch edge-cases, and dispatch_stats.

All external calls (subprocess, network, filesystem) are mocked.
"""

import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# _cache_key
# ---------------------------------------------------------------------------

class TestCacheKey:
    def test_deterministic(self):
        from metabolon.organelles.translocon import _cache_key
        assert _cache_key("prompt", "model") == _cache_key("prompt", "model")

    def test_different_inputs_different_keys(self):
        from metabolon.organelles.translocon import _cache_key
        assert _cache_key("aaa", "m1") != _cache_key("bbb", "m1")
        assert _cache_key("aaa", "m1") != _cache_key("aaa", "m2")

    def test_length_32(self):
        from metabolon.organelles.translocon import _cache_key
        key = _cache_key("x", "y")
        assert len(key) == 32


# ---------------------------------------------------------------------------
# _cache_get / _cache_put
# ---------------------------------------------------------------------------

class TestCacheGetPut:
    def test_get_returns_none_when_missing(self, tmp_path):
        import metabolon.organelles.translocon as mod
        with patch.object(mod, "CACHE_DIR", tmp_path / "cache"):
            result = mod._cache_get("nonexistent_key")
        assert result is None

    def test_put_then_get(self, tmp_path):
        import metabolon.organelles.translocon as mod
        cache_dir = tmp_path / "cache"
        with patch.object(mod, "CACHE_DIR", cache_dir):
            mod._cache_put("abc", {"output": "hello"})
            result = mod._cache_get("abc")
        assert result == {"output": "hello"}

    def test_stale_entry_removed(self, tmp_path):
        import metabolon.organelles.translocon as mod
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        # Write a stale entry manually (timestamp = 0)
        stale = {"timestamp": 0, "response": {"output": "old"}}
        (cache_dir / "stale_key.json").write_text(json.dumps(stale))
        with patch.object(mod, "CACHE_DIR", cache_dir):
            with patch.object(mod, "CACHE_TTL", 3600):
                result = mod._cache_get("stale_key")
        assert result is None
        assert not (cache_dir / "stale_key.json").exists()

    def test_corrupt_json_returns_none(self, tmp_path):
        import metabolon.organelles.translocon as mod
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        (cache_dir / "bad.json").write_text("NOT JSON!!!")
        with patch.object(mod, "CACHE_DIR", cache_dir):
            result = mod._cache_get("bad")
        assert result is None


# ---------------------------------------------------------------------------
# _build_goose_cmd
# ---------------------------------------------------------------------------

class TestBuildGooseCmd:
    def test_basic_command(self):
        from metabolon.organelles.translocon import _build_goose_cmd
        cmd = _build_goose_cmd("GLM-5.1", "do stuff")
        assert cmd[:3] == ["goose", "run", "-q"]
        assert "--no-session" in cmd
        assert "--provider" in cmd
        assert "glm-coding" in cmd
        assert "--model" in cmd
        assert "GLM-5.1" in cmd
        assert "-t" in cmd
        assert cmd[-1] == "do stuff"

    def test_with_recipe(self):
        from metabolon.organelles.translocon import _build_goose_cmd
        cmd = _build_goose_cmd("GLM-5.1", "task", recipe="/path/recipe.yaml")
        assert "--recipe" in cmd
        assert "/path/recipe.yaml" in cmd

    def test_no_recipe(self):
        from metabolon.organelles.translocon import _build_goose_cmd
        cmd = _build_goose_cmd("GLM-4.7", "task")
        assert "--recipe" not in cmd


# ---------------------------------------------------------------------------
# _build_droid_cmd
# ---------------------------------------------------------------------------

class TestBuildDroidCmd:
    def test_basic_command(self):
        from metabolon.organelles.translocon import _build_droid_cmd
        cmd = _build_droid_cmd("GLM-4.7", "/proj", "build tool")
        assert cmd[0] == "droid"
        assert "exec" in cmd
        assert "--cwd" in cmd
        assert "/proj" in cmd
        assert cmd[-1] == "build tool"
        # model should be prefixed with custom:
        assert "custom:GLM-4.7" in cmd

    def test_model_already_custom_prefixed(self):
        from metabolon.organelles.translocon import _build_droid_cmd
        cmd = _build_droid_cmd("custom:mymodel", "/tmp", "task")
        assert "custom:mymodel" in cmd
        # Should not double-prefix
        assert "custom:custom:" not in " ".join(cmd)

    def test_auto_flag_inserted(self):
        from metabolon.organelles.translocon import _build_droid_cmd
        cmd = _build_droid_cmd("GLM-4.7", "/dir", "task", auto="high")
        assert "--auto" in cmd
        assert "high" in cmd


# ---------------------------------------------------------------------------
# _resolve_mode
# ---------------------------------------------------------------------------

class TestResolveMode:
    def test_explore_defaults(self):
        from metabolon.organelles.translocon import _resolve_mode
        backend, model, auto = _resolve_mode(mode="explore")
        assert backend == "goose"
        assert model == "GLM-4.7"
        assert auto is None

    def test_build_defaults(self):
        from metabolon.organelles.translocon import _resolve_mode
        backend, model, auto = _resolve_mode(mode="build")
        assert backend == "goose"
        assert model == "GLM-5.1"
        assert auto is None

    def test_mcp_defaults(self):
        from metabolon.organelles.translocon import _resolve_mode
        backend, model, auto = _resolve_mode(mode="mcp")
        assert backend == "droid"
        assert model == "GLM-4.7"
        assert auto == "high"

    def test_safe_defaults(self):
        from metabolon.organelles.translocon import _resolve_mode
        backend, model, auto = _resolve_mode(mode="safe")
        assert backend == "droid"
        assert model == "GLM-4.7"
        assert auto is None

    def test_skill_defaults(self):
        from metabolon.organelles.translocon import _resolve_mode
        backend, model, auto = _resolve_mode(mode="skill")
        assert backend == "goose"
        assert model == "GLM-5.1"
        assert auto is None

    def test_user_overrides(self):
        from metabolon.organelles.translocon import _resolve_mode
        backend, model, auto = _resolve_mode(mode="explore", backend="droid", model="custom:X")
        assert backend == "droid"
        assert model == "custom:X"

    def test_unknown_mode_uses_explore_defaults(self):
        from metabolon.organelles.translocon import _resolve_mode
        backend, model, auto = _resolve_mode(mode="unknown")
        assert backend == "goose"
        assert model == "GLM-4.7"


# ---------------------------------------------------------------------------
# _approx_tokens
# ---------------------------------------------------------------------------

class TestApproxTokens:
    def test_short_string(self):
        from metabolon.organelles.translocon import _approx_tokens
        assert _approx_tokens("abcd") == 1

    def test_longer_string(self):
        from metabolon.organelles.translocon import _approx_tokens
        assert _approx_tokens("a" * 400) == 100

    def test_empty_string_minimum_one(self):
        from metabolon.organelles.translocon import _approx_tokens
        assert _approx_tokens("") == 1


# ---------------------------------------------------------------------------
# _explore_structured
# ---------------------------------------------------------------------------

class TestExploreStructured:
    def test_returns_expected_keys(self):
        from metabolon.organelles.translocon import _explore_structured
        result = _explore_structured("output text", "prompt", "GLM-4.7", 1.5)
        assert result["query"] == "prompt"
        assert result["response"] == "output text"
        assert result["model"] == "GLM-4.7"
        assert result["cached"] is False
        assert result["duration_ms"] == 1500
        assert "tokens_approx" in result

    def test_cached_flag(self):
        from metabolon.organelles.translocon import _explore_structured
        result = _explore_structured("out", "q", "m", 0.1, cached=True)
        assert result["cached"] is True


# ---------------------------------------------------------------------------
# _direct_api
# ---------------------------------------------------------------------------

class TestDirectApi:
    def test_missing_api_key(self):
        from metabolon.organelles.translocon import _direct_api
        with patch.dict("os.environ", {}, clear=True):
            result = _direct_api("prompt")
        assert result["success"] is False
        assert "ZHIPU_API_KEY" in result["output"]
        assert result["returncode"] == 1

    @patch("metabolon.organelles.translocon.time.sleep")
    def test_success_response(self, mock_sleep):
        from metabolon.organelles.translocon import _direct_api
        fake_response = json.dumps({
            "content": [{"text": "hello from api"}]
        }).encode()

        mock_urlopen = MagicMock()
        mock_urlopen.return_value.read.return_value = fake_response

        with patch.dict("os.environ", {"ZHIPU_API_KEY": "test-key"}):
            with patch("metabolon.organelles.translocon.urllib.request.urlopen", mock_urlopen):
                result = _direct_api("say hi")

        assert result["success"] is True
        assert result["output"] == "hello from api"
        assert result["returncode"] == 0

    @patch("metabolon.organelles.translocon.time.sleep")
    def test_retry_on_429(self, mock_sleep):
        import urllib.error
        from metabolon.organelles.translocon import _direct_api

        exc = urllib.error.HTTPError("url", 429, "rate limited", {}, None)
        mock_urlopen = MagicMock()
        mock_urlopen.side_effect = [exc, exc, exc]  # 3 attempts = 2 retries + 1

        with patch.dict("os.environ", {"ZHIPU_API_KEY": "key"}):
            with patch("metabolon.organelles.translocon.urllib.request.urlopen", mock_urlopen):
                result = _direct_api("prompt")

        assert result["success"] is False
        assert mock_sleep.call_count == 2  # slept between retries

    def test_generic_exception(self):
        from metabolon.organelles.translocon import _direct_api

        with patch.dict("os.environ", {"ZHIPU_API_KEY": "key"}):
            with patch("metabolon.organelles.translocon.urllib.request.urlopen", side_effect=OSError("network")):
                result = _direct_api("prompt")

        assert result["success"] is False
        assert "network" in result["output"]


# ---------------------------------------------------------------------------
# _run_captured
# ---------------------------------------------------------------------------

class TestRunCaptured:
    def test_success(self):
        from metabolon.organelles.translocon import _run_captured
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "output text"
        mock_result.stderr = ""
        with patch("metabolon.organelles.translocon.subprocess.run", return_value=mock_result):
            rc, stdout = _run_captured(["echo", "hi"])
        assert rc == 0
        assert stdout == "output text"

    def test_failure(self):
        from metabolon.organelles.translocon import _run_captured
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = None
        mock_result.stderr = "err"
        with patch("metabolon.organelles.translocon.subprocess.run", return_value=mock_result):
            rc, stdout = _run_captured(["false"])
        assert rc == 1
        assert stdout == ""


# ---------------------------------------------------------------------------
# dispatch — edge cases
# ---------------------------------------------------------------------------

class TestDispatchEdgeCases:
    @patch("metabolon.organelles.translocon._inject_coaching", side_effect=lambda p: p)
    def test_skill_mode_without_skill_returns_error(self, mock_coach):
        from metabolon.organelles.translocon import dispatch
        result = dispatch("task", mode="skill")
        assert result["success"] is False
        assert "skill" in result["output"].lower()

    @patch("metabolon.organelles.translocon._inject_coaching", side_effect=lambda p: p)
    def test_safe_mode_prepends_readonly_guard(self, mock_coach):
        from metabolon.organelles.translocon import dispatch
        captured_prompt = {}

        def fake_run(cmd, **kwargs):
            # Extract prompt (last arg after -t or last positional)
            captured_prompt["cmd"] = cmd
            return (0, "safe output")

        with patch("metabolon.organelles.translocon._run_captured", side_effect=fake_run):
            result = dispatch("check things", mode="safe")

        assert result["success"] is True
        cmd = captured_prompt["cmd"]
        # The prompt passed to droid should contain READ ONLY
        assert "READ ONLY" in cmd[-1]

    @patch("metabolon.organelles.translocon._read_dir_context", return_value="")
    @patch("metabolon.organelles.translocon._direct_api")
    @patch("metabolon.organelles.translocon._cache_get", return_value=None)
    @patch("metabolon.organelles.translocon._inject_coaching", side_effect=lambda p: p)
    def test_explore_json_output(self, mock_coach, mock_cache, mock_api, mock_ctx):
        from metabolon.organelles.translocon import dispatch
        mock_api.return_value = {"success": True, "output": "api result", "returncode": 0}
        result = dispatch("query", mode="explore", json_output=True)
        assert result["success"] is True
        # Output should be JSON string
        parsed = json.loads(result["output"])
        assert parsed["query"] == "query"
        assert parsed["response"] == "api result"
        assert parsed["cached"] is False

    @patch("metabolon.organelles.translocon._read_dir_context", return_value="")
    @patch("metabolon.organelles.translocon._cache_get")
    @patch("metabolon.organelles.translocon._inject_coaching", side_effect=lambda p: p)
    def test_explore_cached_json_output(self, mock_coach, mock_cache, mock_ctx):
        from metabolon.organelles.translocon import dispatch
        mock_cache.return_value = {"output": "cached result"}
        result = dispatch("query", mode="explore", json_output=True)
        assert result["success"] is True
        parsed = json.loads(result["output"])
        assert parsed["cached"] is True
        assert result["backend"] == "direct (cached)"

    @patch("metabolon.organelles.translocon._run_captured")
    @patch("metabolon.organelles.translocon._inject_coaching", side_effect=lambda p: p)
    def test_goose_failure_with_forced_backend(self, mock_coach, mock_run):
        """If user forced backend=goose, don't fall back to droid."""
        from metabolon.organelles.translocon import dispatch
        mock_run.return_value = (1, "goose error")
        result = dispatch("task", mode="build", backend="goose")
        assert result["success"] is False
        assert result["backend"] == "goose"
        # _run_captured should only be called once (no droid fallback)
        assert mock_run.call_count == 1

    @patch("metabolon.organelles.translocon._run_captured")
    @patch("metabolon.organelles.translocon._inject_coaching", side_effect=lambda p: p)
    def test_goose_failure_falls_back_to_droid(self, mock_coach, mock_run):
        from metabolon.organelles.translocon import dispatch
        mock_run.side_effect = [
            (1, "goose error"),  # goose fails
            (0, "droid success"),  # droid succeeds
        ]
        result = dispatch("task", mode="build")
        assert result["success"] is True
        assert result["backend"] == "droid"
        assert mock_run.call_count == 2

    @patch("metabolon.organelles.translocon._run_captured")
    @patch("metabolon.organelles.translocon._inject_coaching", side_effect=lambda p: p)
    def test_goose_exception_returns_error(self, mock_coach, mock_run):
        from metabolon.organelles.translocon import dispatch
        mock_run.side_effect = OSError("goose crashed")
        result = dispatch("task", mode="build")
        assert result["success"] is False
        assert "goose execution failed" in result["output"]
        assert result["backend"] == "goose"

    @patch("metabolon.organelles.translocon._run_captured")
    @patch("metabolon.organelles.translocon._inject_coaching", side_effect=lambda p: p)
    def test_droid_exception_returns_error(self, mock_coach, mock_run):
        from metabolon.organelles.translocon import dispatch
        mock_run.side_effect = OSError("droid crashed")
        result = dispatch("task", mode="mcp")  # mcp routes to droid
        assert result["success"] is False
        assert "droid execution failed" in result["output"]

    @patch("metabolon.organelles.translocon._inject_coaching", side_effect=lambda p: p)
    def test_skill_default_prompt(self, mock_coach):
        """If prompt is empty and skill is provided, a default prompt is used."""
        import tempfile
        from metabolon.organelles.translocon import dispatch

        captured = {}
        def fake_run(cmd, **kwargs):
            captured["cmd"] = cmd
            return (0, "ok")

        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "germline" / "membrane" / "receptors" / "myskill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "recipe.yaml").write_text("name: myskill\n")

            with patch.object(Path, "home", return_value=Path(tmpdir)):
                with patch("metabolon.organelles.translocon._run_captured", side_effect=fake_run):
                    result = dispatch("", mode="skill", skill="myskill")

        assert result["success"] is True
        assert "myskill" in captured["cmd"][-1]


# ---------------------------------------------------------------------------
# dispatch_stats
# ---------------------------------------------------------------------------

class TestDispatchStats:
    def test_no_log_returns_error(self):
        import metabolon.organelles.translocon as mod
        from metabolon.organelles.translocon import dispatch_stats
        fake_log = Path("/tmp/nonexistent_golem_log_test.jsonl")
        with patch.object(mod, "GOLEM_LOG", fake_log):
            result = dispatch_stats()
        assert result["success"] is False
        assert "no golem log" in result["output"].lower()

    def test_empty_log_returns_success(self, tmp_path):
        import metabolon.organelles.translocon as mod
        from metabolon.organelles.translocon import dispatch_stats
        log_path = tmp_path / "golem.jsonl"
        log_path.write_text("")
        with patch.object(mod, "GOLEM_LOG", log_path):
            result = dispatch_stats()
        assert result["success"] is True
        assert "no entries" in result["output"].lower()

    def test_returns_summary(self, tmp_path):
        import metabolon.organelles.translocon as mod
        from metabolon.organelles.translocon import dispatch_stats
        entries = [
            json.dumps({"exit": 0, "provider": "zhipu", "duration": 30, "turns": 5, "prompt": "ok task"}),
            json.dumps({"exit": 1, "provider": "infini", "duration": 60, "turns": 3, "prompt": "bad task"}),
            json.dumps({"exit": 0, "provider": "zhipu", "duration": 20, "turns": 4, "prompt": "another ok"}),
        ]
        log_path = tmp_path / "golem.jsonl"
        log_path.write_text("\n".join(entries))
        with patch.object(mod, "GOLEM_LOG", log_path):
            result = dispatch_stats(count=50)
        assert result["success"] is True
        assert "3" in result["output"]  # total
        assert result["stats"]["total"] == 3
        assert result["stats"]["success"] == 2
        assert result["stats"]["fail"] == 1
        assert "zhipu" in result["stats"]["providers"]
        assert result["stats"]["provider_success"]["zhipu"] == 2

    def test_recent_failures_shown(self, tmp_path):
        import metabolon.organelles.translocon as mod
        from metabolon.organelles.translocon import dispatch_stats
        entries = [
            json.dumps({"exit": 1, "provider": "volcano", "duration": 10, "turns": 1,
                        "prompt": "a" * 80}),
        ]
        log_path = tmp_path / "golem.jsonl"
        log_path.write_text("\n".join(entries))
        with patch.object(mod, "GOLEM_LOG", log_path):
            result = dispatch_stats()
        assert "Recent failures" in result["output"]
        assert "volcano" in result["output"]

    def test_corrupt_lines_skipped(self, tmp_path):
        import metabolon.organelles.translocon as mod
        from metabolon.organelles.translocon import dispatch_stats
        content = "not json\n" + json.dumps({"exit": 0, "provider": "zhipu", "duration": 5, "turns": 1, "prompt": "ok"})
        log_path = tmp_path / "golem.jsonl"
        log_path.write_text(content)
        with patch.object(mod, "GOLEM_LOG", log_path):
            result = dispatch_stats()
        assert result["success"] is True
        assert result["stats"]["total"] == 1


# ---------------------------------------------------------------------------
# PROVIDER_LIMITS constant
# ---------------------------------------------------------------------------

class TestProviderLimits:
    def test_known_providers(self):
        from metabolon.organelles.translocon import PROVIDER_LIMITS
        assert PROVIDER_LIMITS["zhipu"] == 4
        assert PROVIDER_LIMITS["infini"] == 6
        assert PROVIDER_LIMITS["volcano"] == 8
