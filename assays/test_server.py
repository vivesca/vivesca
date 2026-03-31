from __future__ import annotations

"""Tests for metabolon.server — module-level checks and edge cases.

Complements test_request_logger.py and test_server_request_log.py.
"""

import json
import logging
from pathlib import Path

import pytest

import metabolon.server as server_mod
from metabolon.server import DEFAULT_REQUEST_LOG, RequestLogger


# --- Module-level constants and objects ---


class TestModuleLevel:
    def test_default_request_log_is_path(self):
        assert isinstance(DEFAULT_REQUEST_LOG, Path)

    def test_default_request_log_under_vivesca(self):
        parts = DEFAULT_REQUEST_LOG.parts
        assert "vivesca" in parts

    def test_default_request_log_filename(self):
        assert DEFAULT_REQUEST_LOG.name == "requests.jsonl"

    def test_module_logger_is_standard_logger(self):
        assert isinstance(server_mod.logger, logging.Logger)
        assert server_mod.logger.name == "metabolon.server"


# --- Constructor ---


class TestConstructor:
    def test_stores_path_as_path_object(self, tmp_path):
        p = tmp_path / "test.jsonl"
        rl = RequestLogger(p)
        assert rl._path == p
        assert isinstance(rl._path, Path)

    def test_string_path_wrapped_to_path(self, tmp_path):
        p = str(tmp_path / "test.jsonl")
        rl = RequestLogger(p)
        assert isinstance(rl._path, Path)
        assert rl._path == Path(p)


# --- Log method contract ---


class TestLogContract:
    def test_keyword_only_arguments(self, tmp_path):
        rl = RequestLogger(tmp_path / "x.jsonl")
        with pytest.raises(TypeError):
            rl.log("tool", 10, True)

    def test_missing_required_arguments(self, tmp_path):
        rl = RequestLogger(tmp_path / "x.jsonl")
        with pytest.raises(TypeError, match="tool"):
            rl.log(duration_ms=10, success=True)

    def test_unicode_tool_name(self, tmp_path):
        log_path = tmp_path / "u.jsonl"
        rl = RequestLogger(log_path)
        rl.log(tool="пошук_🔍", duration_ms=7, success=True)
        entry = json.loads(log_path.read_text().strip())
        assert entry["tool"] == "пошук_🔍"

    def test_very_long_tool_name(self, tmp_path):
        log_path = tmp_path / "long.jsonl"
        rl = RequestLogger(log_path)
        name = "a" * 10_000
        rl.log(tool=name, duration_ms=1, success=True)
        entry = json.loads(log_path.read_text().strip())
        assert len(entry["tool"]) == 10_000

    def test_negative_duration_round_trips(self, tmp_path):
        log_path = tmp_path / "neg.jsonl"
        rl = RequestLogger(log_path)
        rl.log(tool="oops", duration_ms=-5, success=False)
        entry = json.loads(log_path.read_text().strip())
        assert entry["duration_ms"] == -5


# --- Append-mode verification ---


class TestAppendMode:
    def test_does_not_truncate_existing_content(self, tmp_path):
        log_path = tmp_path / "append.jsonl"
        log_path.write_text('{"legacy": true}\n')
        rl = RequestLogger(log_path)
        rl.log(tool="new", duration_ms=1, success=True)

        lines = [l for l in log_path.read_text().splitlines() if l.strip()]
        assert len(lines) == 2
        assert json.loads(lines[0])["legacy"] is True
        assert json.loads(lines[1])["tool"] == "new"

    def test_three_appends_in_order(self, tmp_path):
        log_path = tmp_path / "seq.jsonl"
        rl = RequestLogger(log_path)
        for i in range(3):
            rl.log(tool=f"step{i}", duration_ms=i * 100, success=True)

        entries = [json.loads(l) for l in log_path.read_text().splitlines() if l.strip()]
        tools = [e["tool"] for e in entries]
        assert tools == ["step0", "step1", "step2"]


# --- Error suppression ---


class TestErrorSuppression:
    def test_write_to_nonexistent_deep_path_does_not_raise(self, tmp_path):
        rl = RequestLogger(tmp_path / "no" / "such" / "dir" / "f.jsonl")
        # This actually succeeds because mkdir(parents=True) creates the tree
        rl.log(tool="deep", duration_ms=1, success=True)
        assert (tmp_path / "no" / "such" / "dir" / "f.jsonl").exists()

    def test_permission_error_suppressed(self, tmp_path, caplog):
        ro_dir = tmp_path / "readonly"
        ro_dir.mkdir()
        ro_dir.chmod(0o444)
        try:
            rl = RequestLogger(ro_dir / "x.jsonl")
            with caplog.at_level(logging.DEBUG, logger="metabolon.server"):
                rl.log(tool="blocked", duration_ms=1, success=True)
            # Must not raise — exception is caught and logged at debug
        finally:
            ro_dir.chmod(0o755)
