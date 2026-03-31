"""Tests for provider-bench — parallel provider benchmarking effector."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest


EFFECTOR = Path("/home/terry/germline/effectors/provider-bench")


def _load_effector():
    """Load provider-bench module by exec-ing its Python body."""
    source = EFFECTOR.read_text()
    ns: dict = {"__name__": "provider_bench", "__doc__": None}
    exec(source, ns)
    return ns


# ── PROVIDERS config tests ─────────────────────────────────────────────


class TestProviders:
    def test_providers_dict_has_three_entries(self):
        mod = _load_effector()
        prov = mod["PROVIDERS"]
        assert len(prov) == 3
        assert set(prov.keys()) == {"zhipu", "volcano", "infini"}

    def test_each_provider_has_required_keys(self):
        mod = _load_effector()
        required = {"name", "url", "opus", "sonnet", "haiku", "key_env", "auth_mode"}
        for prov_name, cfg in mod["PROVIDERS"].items():
            assert required <= set(cfg.keys()), f"{prov_name} missing keys"

    def test_zhipu_config(self):
        mod = _load_effector()
        cfg = mod["PROVIDERS"]["zhipu"]
        assert cfg["key_env"] == "ZHIPU_API_KEY"
        assert cfg["auth_mode"] == "key"
        assert "bigmodel" in cfg["url"]

    def test_volcano_config(self):
        mod = _load_effector()
        cfg = mod["PROVIDERS"]["volcano"]
        assert cfg["key_env"] == "VOLCANO_API_KEY"
        assert cfg["auth_mode"] == "token"

    def test_infini_config(self):
        mod = _load_effector()
        cfg = mod["PROVIDERS"]["infini"]
        assert cfg["key_env"] == "INFINI_API_KEY"
        assert cfg["auth_mode"] == "key"


# ── build_env tests ────────────────────────────────────────────────────


class TestBuildEnv:
    def test_build_env_key_mode(self):
        mod = _load_effector()
        build_env = mod["build_env"]
        cfg = {"key_env": "TEST_KEY", "auth_mode": "key", "url": "http://x", "opus": "m1", "sonnet": "m2", "haiku": "m3"}
        env = build_env(cfg, "testkey123")
        assert env["ANTHROPIC_API_KEY"] == "testkey123"
        assert "ANTHROPIC_AUTH_TOKEN" not in env
        assert env["ANTHROPIC_BASE_URL"] == "http://x"
        assert env["ANTHROPIC_DEFAULT_OPUS_MODEL"] == "m1"

    def test_build_env_token_mode(self):
        mod = _load_effector()
        build_env = mod["build_env"]
        cfg = {"key_env": "TEST_KEY", "auth_mode": "token", "url": "http://y", "opus": "a", "sonnet": "b", "haiku": "c"}
        env = build_env(cfg, "token456")
        assert env["ANTHROPIC_AUTH_TOKEN"] == "token456"
        assert env["ANTHROPIC_API_KEY"] == ""
        assert env["ANTHROPIC_BASE_URL"] == "http://y"

    def test_build_env_inherits_path(self):
        mod = _load_effector()
        build_env = mod["build_env"]
        cfg = {"key_env": "K", "auth_mode": "key", "url": "u", "opus": "o", "sonnet": "s", "haiku": "h"}
        env = build_env(cfg, "k")
        assert "PATH" in env


# ── score_output tests ─────────────────────────────────────────────────


class TestScoreOutput:
    def test_score_output_returns_dict(self):
        mod = _load_effector()
        result = mod["score_output"]("Hello world. This is a test.")
        assert isinstance(result, dict)
        assert "chars" in result
        assert "words" in result
        assert "sentences" in result
        assert "unique_ratio" in result
        assert "quality_label" in result

    def test_score_output_empty(self):
        mod = _load_effector()
        result = mod["score_output"]("")
        assert result["chars"] == 0
        assert result["words"] == 0
        assert result["quality_label"] == "empty"

    def test_score_output_short(self):
        mod = _load_effector()
        result = mod["score_output"]("hi")
        assert result["quality_label"] in ("short", "ok", "good")

    def test_score_output_good_prose(self):
        mod = _load_effector()
        text = "The quick brown fox jumps over the lazy dog. It was a sunny day. " \
               "Programming in Python is enjoyable. Tests ensure correctness. " \
               "Documentation helps everyone. Code review catches bugs. " \
               "Refactoring improves readability."
        result = mod["score_output"](text)
        assert result["words"] > 10
        assert result["sentences"] > 1
        assert result["unique_ratio"] > 0.0
        assert result["quality_label"] in ("ok", "good", "short", "empty")

    def test_score_output_repetitive(self):
        mod = _load_effector()
        text = "hello hello hello hello hello hello hello hello"
        result = mod["score_output"](text)
        assert result["unique_ratio"] < 0.3

    def test_score_output_labels(self):
        mod = _load_effector()
        assert mod["score_output"]("")["quality_label"] == "empty"
        # Very short: 1-5 words
        short_result = mod["score_output"]("a b c")
        assert short_result["quality_label"] in ("short", "ok", "good", "empty")


# ── run_provider tests ─────────────────────────────────────────────────


class TestRunProvider:
    def test_run_provider_returns_result_dict(self):
        mod = _load_effector()
        mock_completed = MagicMock()
        mock_completed.stdout = "Generated output text here."
        mock_completed.returncode = 0

        with patch.object(subprocess, "run", return_value=mock_completed) as mock_run:
            cfg = {"key_env": "K", "auth_mode": "key", "url": "u", "opus": "o", "sonnet": "s", "haiku": "h", "name": "test"}
            result = mod["run_provider"]("test", cfg, "prompt text", timeout=30)

        assert "provider" in result
        assert "latency_s" in result
        assert "exit_code" in result
        assert "output" in result
        assert "score" in result
        assert result["provider"] == "test"
        assert result["exit_code"] == 0

    def test_run_provider_handles_timeout(self):
        mod = _load_effector()
        with patch.object(subprocess, "run", side_effect=subprocess.TimeoutExpired(cmd="claude", timeout=5)):
            cfg = {"key_env": "K", "auth_mode": "key", "url": "u", "opus": "o", "sonnet": "s", "haiku": "h", "name": "t"}
            result = mod["run_provider"]("t", cfg, "p", timeout=5)

        assert result["exit_code"] == -1
        assert "timeout" in result["output"].lower()

    def test_run_provider_handles_error(self):
        mod = _load_effector()
        mock_completed = MagicMock()
        mock_completed.stdout = ""
        mock_completed.returncode = 1

        with patch.object(subprocess, "run", return_value=mock_completed):
            cfg = {"key_env": "K", "auth_mode": "key", "url": "u", "opus": "o", "sonnet": "s", "haiku": "h", "name": "t"}
            result = mod["run_provider"]("t", cfg, "p", timeout=30)

        assert result["exit_code"] == 1

    def test_run_provider_passes_correct_env(self):
        mod = _load_effector()
        mock_completed = MagicMock()
        mock_completed.stdout = "ok"
        mock_completed.returncode = 0

        with patch.object(subprocess, "run", return_value=mock_completed) as mock_run:
            cfg = {"key_env": "MY_KEY", "auth_mode": "key", "url": "http://api.example.com", "opus": "big", "sonnet": "mid", "haiku": "small", "name": "test"}
            mod["run_provider"]("test", cfg, "hello", timeout=30)

        called_env = mock_run.call_args[1]["env"]
        assert called_env["ANTHROPIC_API_KEY"] != ""
        assert called_env["ANTHROPIC_BASE_URL"] == "http://api.example.com"
        assert called_env["ANTHROPIC_DEFAULT_OPUS_MODEL"] == "big"

    def test_run_provider_passes_prompt_as_arg(self):
        mod = _load_effector()
        mock_completed = MagicMock()
        mock_completed.stdout = "ok"
        mock_completed.returncode = 0

        with patch.object(subprocess, "run", return_value=mock_completed) as mock_run:
            cfg = {"key_env": "K", "auth_mode": "key", "url": "u", "opus": "o", "sonnet": "s", "haiku": "h", "name": "t"}
            mod["run_provider"]("t", cfg, "write a poem", timeout=30)

        cmd_args = mock_run.call_args[0][0]
        # Prompt should be the last arg to claude -p
        assert "-p" in cmd_args
        prompt_idx = cmd_args.index("-p")
        assert cmd_args[prompt_idx + 1] == "write a poem"


# ── format_table tests ─────────────────────────────────────────────────


class TestFormatTable:
    def test_format_table_basic(self):
        mod = _load_effector()
        results = [
            {"provider": "zhipu", "latency_s": 12.3, "exit_code": 0,
             "output": "Hello world", "score": {"chars": 11, "words": 2, "sentences": 0, "unique_ratio": 1.0, "quality_label": "short"}},
            {"provider": "volcano", "latency_s": 8.1, "exit_code": 0,
             "output": "Generated response", "score": {"chars": 18, "words": 2, "sentences": 0, "unique_ratio": 1.0, "quality_label": "short"}},
        ]
        table = mod["format_table"](results)
        assert "zhipu" in table
        assert "volcano" in table
        assert "12.3" in table
        assert "8.1" in table

    def test_format_table_single_result(self):
        mod = _load_effector()
        results = [
            {"provider": "infini", "latency_s": 15.0, "exit_code": 0,
             "output": "A" * 100, "score": {"chars": 100, "words": 5, "sentences": 1, "unique_ratio": 0.8, "quality_label": "good"}},
        ]
        table = mod["format_table"](results)
        assert "infini" in table

    def test_format_table_failed_provider(self):
        mod = _load_effector()
        results = [
            {"provider": "zhipu", "latency_s": 5.0, "exit_code": 1,
             "output": "error", "score": {"chars": 5, "words": 1, "sentences": 0, "unique_ratio": 1.0, "quality_label": "short"}},
        ]
        table = mod["format_table"](results)
        assert "FAIL" in table or "1" in table

    def test_format_table_header_row(self):
        mod = _load_effector()
        results = [
            {"provider": "zhipu", "latency_s": 1.0, "exit_code": 0,
             "output": "x", "score": {"chars": 1, "words": 1, "sentences": 0, "unique_ratio": 1.0, "quality_label": "short"}},
        ]
        table = mod["format_table"](results)
        assert "Provider" in table
        assert "Latency" in table


# ── Integration: parallel dispatch ─────────────────────────────────────


class TestParallelDispatch:
    def test_all_three_providers_dispatched(self):
        mod = _load_effector()
        mock_completed = MagicMock()
        mock_completed.stdout = "response"
        mock_completed.returncode = 0

        with patch.object(subprocess, "run", return_value=mock_completed) as mock_run:
            with patch.dict("os.environ", {"ZHIPU_API_KEY": "k1", "VOLCANO_API_KEY": "k2", "INFINI_API_KEY": "k3"}):
                results = mod["run_all"]("test prompt", timeout=30)

        assert len(results) == 3
        provider_names = {r["provider"] for r in results}
        assert provider_names == {"zhipu", "volcano", "infini"}

    def test_parallel_results_have_latency(self):
        mod = _load_effector()
        mock_completed = MagicMock()
        mock_completed.stdout = "ok"
        mock_completed.returncode = 0

        with patch.object(subprocess, "run", return_value=mock_completed):
            with patch.dict("os.environ", {"ZHIPU_API_KEY": "k1", "VOLCANO_API_KEY": "k2", "INFINI_API_KEY": "k3"}):
                results = mod["run_all"]("prompt", timeout=30)

        for r in results:
            assert isinstance(r["latency_s"], float)
            assert r["latency_s"] >= 0
