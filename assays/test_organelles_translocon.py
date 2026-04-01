from __future__ import annotations

"""Tests for metabolon.organelles.translocon — pure helpers + mocked dispatch."""

import json
import subprocess
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from metabolon.organelles.translocon import (
    CACHE_DIR,
    CACHE_TTL,
    COACHING_NOTES,
    GOLEM_LOG,
    PROVIDER_LIMITS,
    SORTASE_LOG,
    _approx_tokens,
    _build_droid_cmd,
    _build_goose_cmd,
    _cache_get,
    _cache_key,
    _cache_put,
    _direct_api,
    _explore_structured,
    _inject_coaching,
    _read_dir_context,
    _resolve_mode,
    _run_captured,
    dispatch,
    dispatch_stats,
    run_eval,
)


# ---------------------------------------------------------------------------
# _cache_key
# ---------------------------------------------------------------------------

class TestCacheKey:
    def test_deterministic(self):
        assert _cache_key("hello", "glm-4") == _cache_key("hello", "glm-4")

    def test_different_inputs_differ(self):
        assert _cache_key("hello", "glm-4") != _cache_key("world", "glm-4")

    def test_length(self):
        key = _cache_key("x", "y")
        assert len(key) == 32


# ---------------------------------------------------------------------------
# _cache_get / _cache_put
# ---------------------------------------------------------------------------

class TestCache:
    def test_put_and_get(self, tmp_path):
        with patch.object(Path, "__truediv__", return_value=tmp_path / "test.json"):
            # Directly use tmp_path for cache file
            pass
        cache_file = tmp_path / "abc.json"
        entry = {"output": "hello world"}
        with patch("metabolon.organelles.translocon.CACHE_DIR", tmp_path):
            _cache_put("abc", entry)
            result = _cache_get("abc")
        assert result == entry

    def test_get_missing_returns_none(self, tmp_path):
        with patch("metabolon.organelles.translocon.CACHE_DIR", tmp_path):
            assert _cache_get("nonexistent") is None

    def test_stale_entry_removed(self, tmp_path):
        with patch("metabolon.organelles.translocon.CACHE_DIR", tmp_path):
            # Write a stale entry (timestamp = 0)
            stale_file = tmp_path / "stale.json"
            stale_file.write_text(json.dumps({"timestamp": 0, "response": {"output": "old"}}))
            with patch("metabolon.organelles.translocon.CACHE_TTL", 1):
                result = _cache_get("stale")
            assert result is None
            assert not stale_file.exists()

    def test_corrupt_json_returns_none(self, tmp_path):
        with patch("metabolon.organelles.translocon.CACHE_DIR", tmp_path):
            bad_file = tmp_path / "bad.json"
            bad_file.write_text("not json at all")
            assert _cache_get("bad") is None

    def test_missing_key_field_returns_none(self, tmp_path):
        with patch("metabolon.organelles.translocon.CACHE_DIR", tmp_path):
            bad_file = tmp_path / "nokey.json"
            bad_file.write_text(json.dumps({"timestamp": time.time()}))
            assert _cache_get("nokey") is None


# ---------------------------------------------------------------------------
# _inject_coaching
# ---------------------------------------------------------------------------

class TestInjectCoaching:
    def test_no_coaching_file(self):
        with patch.object(Path, "exists", return_value=False):
            assert _inject_coaching("do stuff") == "do stuff"

    def test_with_coaching_strips_yaml_frontmatter(self, tmp_path):
        notes = tmp_path / "coaching.md"
        notes.write_text("---\ntitle: foo\n---\nCoaching content here")
        with patch("metabolon.organelles.translocon.COACHING_NOTES", notes):
            result = _inject_coaching("my task")
        assert result.startswith("Coaching content here")
        assert "my task" in result
        assert "---" in result  # separator between coaching and task

    def test_with_coaching_no_frontmatter(self, tmp_path):
        notes = tmp_path / "coaching.md"
        notes.write_text("Just plain coaching text")
        with patch("metabolon.organelles.translocon.COACHING_NOTES", notes):
            result = _inject_coaching("my task")
        assert result.startswith("Just plain coaching text")
        assert "my task" in result


# ---------------------------------------------------------------------------
# _read_dir_context
# ---------------------------------------------------------------------------

class TestReadDirContext:
    def test_reads_py_files(self, tmp_path):
        (tmp_path / "a.py").write_text("print('a')")
        (tmp_path / "b.py").write_text("print('b')")
        (tmp_path / "c.txt").write_text("ignored")
        result = _read_dir_context(str(tmp_path))
        assert "a.py" in result
        assert "b.py" in result
        assert "c.txt" not in result

    def test_custom_glob(self, tmp_path):
        (tmp_path / "a.py").write_text("py file")
        (tmp_path / "b.md").write_text("md file")
        result = _read_dir_context(str(tmp_path), "*.md")
        assert "b.md" in result
        assert "a.py" not in result

    def test_skips_large_files(self, tmp_path):
        (tmp_path / "big.py").write_text("x" * 50001)
        (tmp_path / "small.py").write_text("y")
        result = _read_dir_context(str(tmp_path))
        assert "small.py" in result
        assert "big.py" not in result

    def test_empty_dir(self, tmp_path):
        result = _read_dir_context(str(tmp_path))
        assert result == ""

    def test_cumulative_cap(self, tmp_path):
        # Create many small files that together exceed 100KB
        for i in range(50):
            (tmp_path / f"file{i:03d}.py").write_text("x" * 3000)
        result = _read_dir_context(str(tmp_path))
        # Should have some files but not all — result length capped
        assert len(result) < 150_000


# ---------------------------------------------------------------------------
# _build_goose_cmd
# ---------------------------------------------------------------------------

class TestBuildGooseCmd:
    def test_basic(self):
        cmd = _build_goose_cmd("GLM-5.1", "hello world")
        assert cmd[:3] == ["goose", "run", "-q"]
        assert "--provider" in cmd
        assert "glm-coding" in cmd
        assert "--model" in cmd
        assert "GLM-5.1" in cmd
        assert "-t" in cmd
        assert "hello world" in cmd

    def test_with_recipe(self):
        cmd = _build_goose_cmd("GLM-5.1", "task", recipe="/path/recipe.yaml")
        assert "--recipe" in cmd
        assert "/path/recipe.yaml" in cmd

    def test_no_recipe(self):
        cmd = _build_goose_cmd("GLM-5.1", "task")
        assert "--recipe" not in cmd


# ---------------------------------------------------------------------------
# _build_droid_cmd
# ---------------------------------------------------------------------------

class TestBuildDroidCmd:
    def test_basic(self):
        cmd = _build_droid_cmd("GLM-4.7", "/home/project", "fix the bug")
        assert cmd[0] == "droid"
        assert "exec" in cmd
        assert "--cwd" in cmd
        assert "/home/project" in cmd
        assert "fix the bug" in cmd
        # model gets custom: prefix
        assert "custom:GLM-4.7" in cmd

    def test_model_already_prefixed(self):
        cmd = _build_droid_cmd("custom:my-model", "/tmp", "prompt")
        assert "custom:my-model" in cmd

    def test_with_auto(self):
        cmd = _build_droid_cmd("GLM-4.7", "/tmp", "prompt", auto="high")
        assert "--auto" in cmd
        assert "high" in cmd

    def test_no_auto(self):
        cmd = _build_droid_cmd("GLM-4.7", "/tmp", "prompt")
        assert "--auto" not in cmd


# ---------------------------------------------------------------------------
# _resolve_mode
# ---------------------------------------------------------------------------

class TestResolveMode:
    @pytest.mark.parametrize("mode,expected_backend,expected_model", [
        ("explore", "goose", "GLM-4.7"),
        ("build", "goose", "GLM-5.1"),
        ("mcp", "droid", "GLM-4.7"),
        ("safe", "droid", "GLM-4.7"),
        ("skill", "goose", "GLM-5.1"),
    ])
    def test_defaults(self, mode, expected_backend, expected_model):
        backend, model, auto = _resolve_mode(mode=mode)
        assert backend == expected_backend
        assert model == expected_model

    def test_mcp_sets_auto_high(self):
        _, _, auto = _resolve_mode(mode="mcp")
        assert auto == "high"

    def test_explore_no_auto(self):
        _, _, auto = _resolve_mode(mode="explore")
        assert auto is None

    def test_safe_no_auto(self):
        _, _, auto = _resolve_mode(mode="safe")
        assert auto is None

    def test_user_backend_override(self):
        backend, _, _ = _resolve_mode(mode="explore", backend="droid")
        assert backend == "droid"

    def test_user_model_override(self):
        _, model, _ = _resolve_mode(mode="explore", model="my-model")
        assert model == "my-model"

    def test_skill_backend_override(self):
        backend, _, _ = _resolve_mode(mode="skill", backend="droid")
        assert backend == "droid"


# ---------------------------------------------------------------------------
# _approx_tokens
# ---------------------------------------------------------------------------

class TestApproxTokens:
    def test_basic(self):
        assert _approx_tokens("abcdefgh") == 2  # 8 / 4

    def test_empty_string(self):
        assert _approx_tokens("") == 1  # max(1, 0)

    def test_single_char(self):
        assert _approx_tokens("a") == 1  # max(1, 0)


# ---------------------------------------------------------------------------
# _explore_structured
# ---------------------------------------------------------------------------

class TestExploreStructured:
    def test_fields(self):
        result = _explore_structured("output text", "prompt?", "glm-4", 1.5, cached=True)
        assert result["query"] == "prompt?"
        assert result["response"] == "output text"
        assert result["model"] == "glm-4"
        assert result["cached"] is True
        assert result["duration_ms"] == 1500
        assert "tokens_approx" in result


# ---------------------------------------------------------------------------
# _run_captured
# ---------------------------------------------------------------------------

class TestRunCaptured:
    def test_success(self):
        rc, stdout = _run_captured(["echo", "hello"])
        assert rc == 0
        assert "hello" in stdout

    def test_failure(self):
        rc, stdout = _run_captured(["false"])
        assert rc != 0


# ---------------------------------------------------------------------------
# _direct_api
# ---------------------------------------------------------------------------

class TestDirectApi:
    def test_missing_key(self):
        with patch.dict("os.environ", {}, clear=True):
            result = _direct_api("prompt")
        assert result["success"] is False
        assert "ZHIPU_API_KEY" in result["output"]
        assert result["returncode"] == 1

    def test_success_response(self):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "content": [{"text": "the answer"}]
        }).encode()
        with patch.dict("os.environ", {"ZHIPU_API_KEY": "test-key"}):
            with patch("urllib.request.urlopen", return_value=mock_response):
                result = _direct_api("prompt")
        assert result["success"] is True
        assert result["output"] == "the answer"
        assert result["returncode"] == 0

    def test_http_error_retried(self):
        import urllib.error
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "content": [{"text": "ok"}]
        }).encode()
        exc429 = urllib.error.HTTPError("url", 429, "rate limited", {}, None)
        with patch.dict("os.environ", {"ZHIPU_API_KEY": "test-key"}):
            with patch("urllib.request.urlopen", side_effect=[exc429, mock_resp]):
                with patch("time.sleep"):  # skip retry delay
                    result = _direct_api("prompt")
        assert result["success"] is True

    def test_persistent_http_error_fails(self):
        import urllib.error
        exc500 = urllib.error.HTTPError("url", 500, "server error", {}, None)
        with patch.dict("os.environ", {"ZHIPU_API_KEY": "test-key"}):
            with patch("urllib.request.urlopen", side_effect=[exc500, exc500, exc500]):
                with patch("time.sleep"):
                    result = _direct_api("prompt")
        assert result["success"] is False
        assert "direct API failed" in result["output"]

    def test_generic_exception(self):
        with patch.dict("os.environ", {"ZHIPU_API_KEY": "test-key"}):
            with patch("urllib.request.urlopen", side_effect=ConnectionError("network down")):
                result = _direct_api("prompt")
        assert result["success"] is False
        assert "direct API failed" in result["output"]


# ---------------------------------------------------------------------------
# dispatch
# ---------------------------------------------------------------------------

class TestDispatch:
    def test_skill_mode_missing_skill_name(self):
        result = dispatch("prompt", mode="skill")
        assert result["success"] is False
        assert "skill" in result["output"].lower()

    def test_skill_mode_missing_recipe(self):
        result = dispatch("prompt", mode="skill", skill="nonexistent_skill_xyz")
        assert result["success"] is False
        assert "not found" in result["output"]

    def test_explore_direct_api_success(self):
        with patch.dict("os.environ", {"ZHIPU_API_KEY": "test-key"}):
            with patch("metabolon.organelles.translocon._read_dir_context", return_value=""):
                with patch("metabolon.organelles.translocon._cache_get", return_value=None):
                    with patch("metabolon.organelles.translocon._direct_api",
                               return_value={"success": True, "output": "answer", "returncode": 0}):
                        with patch("metabolon.organelles.translocon._cache_put"):
                            result = dispatch("test prompt", mode="explore")
        assert result["success"] is True
        assert result["output"] == "answer"
        assert result["backend"] == "direct"

    def test_explore_cached_result(self):
        cached = {"output": "cached answer"}
        with patch.dict("os.environ", {"ZHIPU_API_KEY": "test-key"}):
            with patch("metabolon.organelles.translocon._read_dir_context", return_value=""):
                with patch("metabolon.organelles.translocon._cache_get", return_value=cached):
                    result = dispatch("test prompt", mode="explore")
        assert result["success"] is True
        assert result["output"] == "cached answer"
        assert "cached" in result["backend"]

    def test_explore_json_output(self):
        with patch.dict("os.environ", {"ZHIPU_API_KEY": "test-key"}):
            with patch("metabolon.organelles.translocon._read_dir_context", return_value=""):
                with patch("metabolon.organelles.translocon._cache_get", return_value=None):
                    with patch("metabolon.organelles.translocon._direct_api",
                               return_value={"success": True, "output": "answer", "returncode": 0}):
                        with patch("metabolon.organelles.translocon._cache_put"):
                            result = dispatch("test prompt", mode="explore", json_output=True)
        assert result["success"] is True
        parsed = json.loads(result["output"])
        assert "response" in parsed
        assert "cached" in parsed

    def test_goose_success(self):
        with patch("metabolon.organelles.translocon._run_captured",
                    return_value=(0, "goose output")):
            with patch("metabolon.organelles.translocon._inject_coaching",
                       side_effect=lambda p: p):
                result = dispatch("task", mode="build", backend="goose")
        assert result["success"] is True
        assert result["output"] == "goose output"
        assert result["backend"] == "goose"

    def test_goose_failure_no_fallback_when_backend_forced(self):
        with patch("metabolon.organelles.translocon._run_captured",
                    return_value=(1, "goose error")):
            with patch("metabolon.organelles.translocon._inject_coaching",
                       side_effect=lambda p: p):
                result = dispatch("task", mode="build", backend="goose")
        assert result["success"] is False
        assert result["backend"] == "goose"

    def test_goose_failure_fallback_to_droid(self):
        call_count = 0

        def mock_run_captured(cmd, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return (1, "goose error")
            return (0, "droid output")

        with patch("metabolon.organelles.translocon._run_captured",
                    side_effect=mock_run_captured):
            with patch("metabolon.organelles.translocon._inject_coaching",
                       side_effect=lambda p: p):
                result = dispatch("task", mode="build")
        assert result["success"] is True
        assert result["output"] == "droid output"
        assert result["backend"] == "droid"

    def test_droid_success(self):
        with patch("metabolon.organelles.translocon._run_captured",
                    return_value=(0, "droid output")):
            with patch("metabolon.organelles.translocon._inject_coaching",
                       side_effect=lambda p: p):
                result = dispatch("task", mode="mcp")
        assert result["success"] is True
        assert result["output"] == "droid output"
        assert result["backend"] == "droid"

    def test_droid_failure(self):
        with patch("metabolon.organelles.translocon._run_captured",
                    return_value=(1, "droid error")):
            with patch("metabolon.organelles.translocon._inject_coaching",
                       side_effect=lambda p: p):
                result = dispatch("task", mode="safe")
        assert result["success"] is False
        assert result["backend"] == "droid"

    def test_safe_mode_prepends_read_only(self):
        captured_prompts = {}

        def fake_run_captured(cmd, **kwargs):
            captured_prompts["last"] = cmd
            return (0, "ok")

        with patch("metabolon.organelles.translocon._run_captured",
                    side_effect=fake_run_captured):
            with patch("metabolon.organelles.translocon._inject_coaching",
                       side_effect=lambda p: p):
                dispatch("do audit", mode="safe")
        # The last arg of the droid command should contain READ ONLY
        last_arg = captured_prompts["last"][-1]
        assert "READ ONLY" in last_arg

    def test_goose_exception_caught(self):
        with patch("metabolon.organelles.translocon._run_captured",
                    side_effect=OSError("boom")):
            with patch("metabolon.organelles.translocon._inject_coaching",
                       side_effect=lambda p: p):
                result = dispatch("task", mode="build", backend="goose")
        assert result["success"] is False
        assert "goose execution failed" in result["output"]

    def test_droid_exception_caught(self):
        with patch("metabolon.organelles.translocon._run_captured",
                    side_effect=OSError("boom")):
            with patch("metabolon.organelles.translocon._inject_coaching",
                       side_effect=lambda p: p):
                result = dispatch("task", mode="mcp")
        assert result["success"] is False
        assert "droid execution failed" in result["output"]

    def test_result_has_duration(self):
        with patch("metabolon.organelles.translocon._run_captured",
                    return_value=(0, "ok")):
            with patch("metabolon.organelles.translocon._inject_coaching",
                       side_effect=lambda p: p):
                result = dispatch("task", mode="build")
        assert "duration_s" in result
        assert isinstance(result["duration_s"], float)


# ---------------------------------------------------------------------------
# run_eval
# ---------------------------------------------------------------------------

class TestRunEval:
    def test_no_sortase_log(self):
        with patch.object(Path, "exists", return_value=False):
            result = run_eval()
        assert result["success"] is False
        assert "no sortase log" in result["output"]

    def test_empty_log(self, tmp_path):
        log = tmp_path / "sortase.jsonl"
        log.write_text("")
        with patch("metabolon.organelles.translocon.SORTASE_LOG", log):
            result = run_eval()
        assert result["success"] is True
        assert "no traces" in result["output"]

    def test_with_traces(self, tmp_path):
        log = tmp_path / "sortase.jsonl"
        traces = [
            {"tool": "golem-reviewer", "success": True, "duration_s": 30},
            {"tool": "golem-reviewer", "success": True, "duration_s": 25},
            {"tool": "golem-builder", "success": False, "failure_reason": "timeout", "plan": "build-x", "duration_s": 120},
        ]
        log.write_text("\n".join(json.dumps(t) for t in traces))
        with patch("metabolon.organelles.translocon.SORTASE_LOG", log):
            result = run_eval()
        assert result["success"] is True
        assert "Success: 2" in result["output"]
        assert "Fail: 1" in result["output"]
        assert "golem-reviewer" in result["output"]
        assert "timeout" in result["output"]

    def test_count_limits_results(self, tmp_path):
        log = tmp_path / "sortase.jsonl"
        traces = [{"tool": "t", "success": True}] * 10
        log.write_text("\n".join(json.dumps(t) for t in traces))
        with patch("metabolon.organelles.translocon.SORTASE_LOG", log):
            result = run_eval(count=3)
        assert "Success: 3" in result["output"]

    def test_failures_only_flag(self, tmp_path):
        log = tmp_path / "sortase.jsonl"
        traces = [
            {"tool": "t1", "success": True},
            {"tool": "t2", "success": False, "failure_reason": "err", "plan": "p", "duration_s": 5},
        ]
        log.write_text("\n".join(json.dumps(t) for t in traces))
        with patch("metabolon.organelles.translocon.SORTASE_LOG", log):
            result = run_eval(failures_only=True)
        assert "Failed traces" in result["output"]

    def test_malformed_lines_skipped(self, tmp_path):
        log = tmp_path / "sortase.jsonl"
        log.write_text("bad line\n{\"tool\": \"t\", \"success\": true}")
        with patch("metabolon.organelles.translocon.SORTASE_LOG", log):
            result = run_eval()
        assert result["success"] is True
        assert "Success: 1" in result["output"]


# ---------------------------------------------------------------------------
# dispatch_stats
# ---------------------------------------------------------------------------

class TestDispatchStats:
    def test_no_golem_log(self):
        with patch.object(Path, "exists", return_value=False):
            result = dispatch_stats()
        assert result["success"] is False
        assert "no golem log" in result["output"]

    def test_empty_log(self, tmp_path):
        log = tmp_path / "golem.jsonl"
        log.write_text("")
        with patch("metabolon.organelles.translocon.GOLEM_LOG", log):
            result = dispatch_stats()
        assert result["success"] is True
        assert "no entries" in result["output"]

    def test_with_entries(self, tmp_path):
        log = tmp_path / "golem.jsonl"
        entries = [
            {"provider": "zhipu", "exit": 0, "duration": 60, "turns": 5},
            {"provider": "zhipu", "exit": 0, "duration": 45, "turns": 3},
            {"provider": "infini", "exit": 1, "duration": 30, "turns": 2, "prompt": "failed task prompt here"},
        ]
        log.write_text("\n".join(json.dumps(e) for e in entries))
        with patch("metabolon.organelles.translocon.GOLEM_LOG", log):
            result = dispatch_stats()
        assert result["success"] is True
        assert "Success: 2" in result["output"]
        assert "Fail: 1" in result["output"]
        assert "zhipu" in result["output"]
        assert "infini" in result["output"]
        assert "stats" in result
        assert result["stats"]["total"] == 3
        assert result["stats"]["success"] == 2
        assert result["stats"]["fail"] == 1

    def test_provider_limits_in_output(self, tmp_path):
        log = tmp_path / "golem.jsonl"
        log.write_text(json.dumps({"provider": "zhipu", "exit": 0, "duration": 10, "turns": 1}))
        with patch("metabolon.organelles.translocon.GOLEM_LOG", log):
            result = dispatch_stats()
        assert f"limit={PROVIDER_LIMITS['zhipu']}" in result["output"]

    def test_recent_failures_shown(self, tmp_path):
        log = tmp_path / "golem.jsonl"
        entries = [
            {"provider": "zhipu", "exit": 1, "duration": 10, "turns": 1, "prompt": "a" * 60},
        ]
        log.write_text("\n".join(json.dumps(e) for e in entries))
        with patch("metabolon.organelles.translocon.GOLEM_LOG", log):
            result = dispatch_stats()
        assert "Recent failures" in result["output"]
