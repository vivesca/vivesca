"""Tests for symbiont — shared LLM dispatch."""

import json
import subprocess
from unittest.mock import patch, MagicMock
from metabolon.symbiont import (
    _strip_ansi,
    restore_symbionts,
    available_symbionts,
    _resolve_model_timeout,
    transduce,
    transduce_safe,
    parallel_query,
    parallel_transduce,
    parallel_transduce_multi,
    DEFAULT_TIMEOUT,
)


SAMPLE_CONFIG = {
    "gemini": {
        "backend": "cmd",
        "cmd": ["gemini", "-p"],
        "description": "Gemini model",
        "timeout": 120,
    },
    "codex": {
        "backend": "codex",
        "cmd": ["codex", "exec"],
        "description": "Codex model",
    },
}


# --- _strip_ansi ---

def test_strip_ansi_removes_codes():
    assert _strip_ansi("\x1b[31mred\x1b[0m") == "red"

def test_strip_ansi_no_codes():
    assert _strip_ansi("plain text") == "plain text"

def test_strip_ansi_empty():
    assert _strip_ansi("") == ""

def test_strip_ansi_complex():
    assert _strip_ansi("\x1b[1;32mbold green\x1b[0m") == "bold green"


# --- restore_symbionts ---

def test_restore_symbionts(tmp_path):
    cfg = tmp_path / "models.json"
    cfg.write_text(json.dumps(SAMPLE_CONFIG))
    result = restore_symbionts(str(cfg))
    assert "gemini" in result
    assert result["gemini"]["backend"] == "cmd"


# --- available_symbionts ---

def test_available_symbionts(tmp_path):
    cfg = tmp_path / "models.json"
    cfg.write_text(json.dumps(SAMPLE_CONFIG))
    result = available_symbionts(str(cfg))
    assert result["gemini"] == "Gemini model"
    assert "codex" in result


# --- _resolve_model_timeout ---

def test_timeout_int():
    assert _resolve_model_timeout("x", {}, 42) == 42

def test_timeout_dict_specific():
    assert _resolve_model_timeout("gemini", {}, {"gemini": 99}) == 99

def test_timeout_dict_default():
    assert _resolve_model_timeout("unknown", {}, {"default": 77}) == 77

def test_timeout_dict_star():
    assert _resolve_model_timeout("unknown", {}, {"*": 55}) == 55

def test_timeout_none_from_config():
    assert _resolve_model_timeout("x", {"timeout": "200"}, None) == 200

def test_timeout_none_default():
    assert _resolve_model_timeout("x", {}, None) == DEFAULT_TIMEOUT

def test_timeout_dict_falls_to_config():
    assert _resolve_model_timeout("x", {"timeout": "150"}, {"other": 99}) == 150


# --- transduce ---

def test_transduce_cmd(tmp_path):
    cfg = tmp_path / "models.json"
    cfg.write_text(json.dumps(SAMPLE_CONFIG))
    with patch("metabolon.symbiont.subprocess.Popen") as mock_popen:
        proc = MagicMock()
        proc.communicate.return_value = ("hello world", "")
        proc.returncode = 0
        mock_popen.return_value = proc
        result = transduce("gemini", "test prompt", config_path=str(cfg))
        assert result == "hello world"


def test_transduce_unknown_model(tmp_path):
    import pytest
    cfg = tmp_path / "models.json"
    cfg.write_text(json.dumps(SAMPLE_CONFIG))
    with pytest.raises(ValueError, match="Unknown model"):
        transduce("nonexistent", "test", config_path=str(cfg))


def test_transduce_unknown_backend(tmp_path):
    import pytest
    cfg_data = {"test": {"backend": "unknown_backend", "cmd": ["x"]}}
    cfg = tmp_path / "models.json"
    cfg.write_text(json.dumps(cfg_data))
    with pytest.raises(ValueError, match="Unknown backend"):
        transduce("test", "prompt", config_path=str(cfg))


# --- transduce_safe ---

def test_transduce_safe_success(tmp_path):
    cfg = tmp_path / "models.json"
    cfg.write_text(json.dumps(SAMPLE_CONFIG))
    with patch("metabolon.symbiont.subprocess.Popen") as mock_popen:
        proc = MagicMock()
        proc.communicate.return_value = ("result", "")
        proc.returncode = 0
        mock_popen.return_value = proc
        name, content = transduce_safe("gemini", "test", config_path=str(cfg))
        assert name == "gemini"
        assert content == "result"


def test_transduce_safe_error(tmp_path):
    cfg = tmp_path / "models.json"
    cfg.write_text(json.dumps(SAMPLE_CONFIG))
    name, content = transduce_safe("nonexistent", "test", config_path=str(cfg))
    assert name == "nonexistent"
    assert "error" in content.lower()


# --- parallel_query ---

def test_parallel_query_empty():
    result = parallel_query([], "test")
    assert result == []


def test_parallel_query_single(tmp_path):
    cfg = tmp_path / "models.json"
    cfg.write_text(json.dumps(SAMPLE_CONFIG))
    with patch("metabolon.symbiont.subprocess.Popen") as mock_popen:
        proc = MagicMock()
        proc.communicate.return_value = ("answer", "")
        proc.returncode = 0
        mock_popen.return_value = proc
        results = parallel_query(["gemini"], "test", config_path=str(cfg))
        assert len(results) == 1
        assert results[0]["ok"] is True
        assert results[0]["content"] == "answer"


# --- parallel_transduce ---

def test_parallel_transduce_returns_tuples(tmp_path):
    cfg = tmp_path / "models.json"
    cfg.write_text(json.dumps(SAMPLE_CONFIG))
    with patch("metabolon.symbiont.subprocess.Popen") as mock_popen:
        proc = MagicMock()
        proc.communicate.return_value = ("yes", "")
        proc.returncode = 0
        mock_popen.return_value = proc
        results = parallel_transduce(["gemini"], "test", config_path=str(cfg))
        assert len(results) == 1
        name, content = results[0]
        assert name == "gemini"
        assert content == "yes"


# --- parallel_transduce_multi ---

def test_parallel_transduce_multi_empty():
    assert parallel_transduce_multi([]) == []


def test_parallel_transduce_multi(tmp_path):
    cfg = tmp_path / "models.json"
    cfg.write_text(json.dumps(SAMPLE_CONFIG))
    with patch("metabolon.symbiont.subprocess.Popen") as mock_popen:
        proc = MagicMock()
        proc.communicate.return_value = ("multi", "")
        proc.returncode = 0
        mock_popen.return_value = proc
        results = parallel_transduce_multi(
            [("gemini", "q1")], config_path=str(cfg)
        )
        assert len(results) == 1
        assert results[0][0] == "gemini"
