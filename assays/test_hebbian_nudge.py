from __future__ import annotations

"""Tests for hebbian_nudge shared library."""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "synaptic"))
import hebbian_nudge as hb


# ── log_nudge ────────────────────────────────────────────────


def test_log_nudge_creates_entry(tmp_path: Path) -> None:
    log_file = tmp_path / "nudge-log.jsonl"
    with patch.object(hb, "NUDGE_LOG", log_file):
        hb.log_nudge("mitogen", "delegate", prompt_snippet="build cli")
    lines = log_file.read_text().strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["hook"] == "mitogen"
    assert entry["prediction"] == "delegate"
    assert "ts" in entry


def test_log_nudge_appends(tmp_path: Path) -> None:
    log_file = tmp_path / "nudge-log.jsonl"
    with patch.object(hb, "NUDGE_LOG", log_file):
        hb.log_nudge("a", "x")
        hb.log_nudge("b", "y")
    lines = log_file.read_text().strip().splitlines()
    assert len(lines) == 2


def test_log_nudge_with_metadata(tmp_path: Path) -> None:
    log_file = tmp_path / "nudge-log.jsonl"
    with patch.object(hb, "NUDGE_LOG", log_file):
        hb.log_nudge("test", "pred", metadata={"key": "val"})
    entry = json.loads(log_file.read_text().strip())
    assert entry.get("meta", {}).get("key") == "val"


def test_log_nudge_truncates_prompt(tmp_path: Path) -> None:
    log_file = tmp_path / "nudge-log.jsonl"
    long_snippet = "x" * 500
    with patch.object(hb, "NUDGE_LOG", log_file):
        hb.log_nudge("hook", "pred", prompt_snippet=long_snippet)
    entry = json.loads(log_file.read_text().strip())
    assert len(entry["prompt"]) == 200


def test_log_nudge_no_metadata(tmp_path: Path) -> None:
    log_file = tmp_path / "nudge-log.jsonl"
    with patch.object(hb, "NUDGE_LOG", log_file):
        hb.log_nudge("hook", "pred")
    entry = json.loads(log_file.read_text().strip())
    assert "meta" not in entry


# ── summarize ────────────────────────────────────────────────


def test_summarize_empty(tmp_path: Path) -> None:
    log_file = tmp_path / "nudge-log.jsonl"
    with patch.object(hb, "NUDGE_LOG", log_file):
        result = hb.summarize(days=7)
    assert result == {}


def test_summarize_counts_entries(tmp_path: Path) -> None:
    log_file = tmp_path / "nudge-log.jsonl"
    with patch.object(hb, "NUDGE_LOG", log_file):
        hb.log_nudge("mitogen", "delegate")
        hb.log_nudge("mitogen", "delegate")
        hb.log_nudge("mitogen", "skip")
        hb.log_nudge("priming", "use-skill")
    with patch.object(hb, "NUDGE_LOG", log_file):
        result = hb.summarize(days=7)
    assert result["mitogen"]["total"] == 3
    assert result["mitogen"]["predictions"]["delegate"] == 2
    assert result["mitogen"]["predictions"]["skip"] == 1
    assert result["priming"]["total"] == 1
