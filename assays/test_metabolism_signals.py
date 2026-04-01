from __future__ import annotations

"""Tests for metabolon.metabolism.signals."""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from metabolon.metabolism.signals import (
    DEFAULT_LOG,
    Outcome,
    SensorySystem,
    Stimulus,
)


# ── Outcome enum ─────────────────────────────────────────────────────────


class TestOutcome:
    def test_values(self):
        assert Outcome.success == "success"
        assert Outcome.error == "error"
        assert Outcome.correction == "correction"
        assert Outcome.reinvocation == "reinvocation"

    def test_is_str(self):
        for member in Outcome:
            assert isinstance(member, str)

    def test_member_count(self):
        assert len(Outcome) == 4


# ── Stimulus model ───────────────────────────────────────────────────────


class TestStimulus:
    def test_defaults(self):
        s = Stimulus(tool="read", outcome=Outcome.success)
        assert s.tool == "read"
        assert s.outcome is Outcome.success
        assert s.substrate_consumed == 0
        assert s.product_released == 0
        assert s.response_latency == 0
        assert s.error is None
        assert s.correction is None
        assert s.context is None
        assert isinstance(s.ts, datetime)

    def test_full_fields(self):
        now = datetime(2026, 1, 1, tzinfo=UTC)
        s = Stimulus(
            ts=now,
            tool="write",
            outcome=Outcome.error,
            substrate_consumed=100,
            product_released=50,
            response_latency=200,
            error="boom",
            correction="retry",
            context="file edit",
        )
        assert s.ts == now
        assert s.tool == "write"
        assert s.outcome is Outcome.error
        assert s.substrate_consumed == 100
        assert s.product_released == 50
        assert s.response_latency == 200
        assert s.error == "boom"
        assert s.correction == "retry"
        assert s.context == "file edit"

    def test_json_roundtrip(self):
        s = Stimulus(tool="bash", outcome=Outcome.correction, context="test")
        json_str = s.model_dump_json()
        s2 = Stimulus.model_validate_json(json_str)
        assert s2.tool == s.tool
        assert s2.outcome == s.outcome
        assert s2.context == s.context
        assert s2.ts == s.ts

    def test_invalid_outcome_raises(self):
        with pytest.raises(Exception):
            Stimulus(tool="x", outcome="not_a_value")


# ── DEFAULT_LOG ──────────────────────────────────────────────────────────


class TestDefaultLog:
    def test_default_path(self):
        expected = Path.home() / ".local" / "share" / "vivesca" / "signals.jsonl"
        assert DEFAULT_LOG == expected


# ── SensorySystem ────────────────────────────────────────────────────────


class TestSensorySystem:
    def test_default_path(self):
        ss = SensorySystem()
        assert ss.sensory_surface_path == DEFAULT_LOG

    def test_custom_path(self, tmp_path):
        custom = tmp_path / "signals.jsonl"
        ss = SensorySystem(sensory_surface_path=custom)
        assert ss.sensory_surface_path == custom

    def test_append_creates_dirs_and_writes(self, tmp_path):
        log = tmp_path / "nested" / "dir" / "signals.jsonl"
        ss = SensorySystem(sensory_surface_path=log)
        s = Stimulus(tool="grep", outcome=Outcome.success)
        ss.append(s)
        assert log.exists()
        content = log.read_text().strip()
        assert content == s.model_dump_json()

    def test_append_multiple(self, tmp_path):
        log = tmp_path / "signals.jsonl"
        ss = SensorySystem(sensory_surface_path=log)
        s1 = Stimulus(tool="a", outcome=Outcome.success)
        s2 = Stimulus(tool="b", outcome=Outcome.error, error="fail")
        ss.append(s1)
        ss.append(s2)
        lines = log.read_text().strip().splitlines()
        assert len(lines) == 2
        assert Stimulus.model_validate_json(lines[0]).tool == "a"
        assert Stimulus.model_validate_json(lines[1]).tool == "b"

    def test_recall_all_missing_file(self, tmp_path):
        log = tmp_path / "nonexistent.jsonl"
        ss = SensorySystem(sensory_surface_path=log)
        assert ss.recall_all() == []

    def test_recall_all_reads_entries(self, tmp_path):
        log = tmp_path / "signals.jsonl"
        ss = SensorySystem(sensory_surface_path=log)
        s = Stimulus(tool="cat", outcome=Outcome.success)
        ss.append(s)
        results = ss.recall_all()
        assert len(results) == 1
        assert results[0].tool == "cat"
        assert results[0].outcome == Outcome.success

    def test_recall_all_skips_blank_and_malformed_lines(self, tmp_path):
        log = tmp_path / "signals.jsonl"
        log.write_text("\n  \nnot-json\n{\"tool\":\"ok\",\"outcome\":\"success\",\"ts\":\"2026-01-01T00:00:00Z\"}\n\n")
        ss = SensorySystem(sensory_surface_path=log)
        results = ss.recall_all()
        assert len(results) == 1
        assert results[0].tool == "ok"

    def test_recall_since_filters_by_timestamp(self, tmp_path):
        log = tmp_path / "signals.jsonl"
        ss = SensorySystem(sensory_surface_path=log)
        t0 = datetime(2026, 1, 1, tzinfo=UTC)
        t1 = datetime(2026, 6, 1, tzinfo=UTC)
        t2 = datetime(2026, 12, 1, tzinfo=UTC)
        ss.append(Stimulus(tool="old", outcome=Outcome.success, ts=t0))
        ss.append(Stimulus(tool="mid", outcome=Outcome.success, ts=t1))
        ss.append(Stimulus(tool="new", outcome=Outcome.success, ts=t2))
        cutoff = datetime(2026, 5, 1, tzinfo=UTC)
        results = ss.recall_since(cutoff)
        assert len(results) == 2
        assert results[0].tool == "mid"
        assert results[1].tool == "new"

    def test_recall_since_exact_boundary(self, tmp_path):
        log = tmp_path / "signals.jsonl"
        ss = SensorySystem(sensory_surface_path=log)
        ts = datetime(2026, 3, 15, 12, 0, tzinfo=UTC)
        ss.append(Stimulus(tool="exact", outcome=Outcome.success, ts=ts))
        results = ss.recall_since(ts)
        assert len(results) == 1  # >= so exact match included

    def test_roundtrip_preserves_all_fields(self, tmp_path):
        log = tmp_path / "signals.jsonl"
        ss = SensorySystem(sensory_surface_path=log)
        original = Stimulus(
            tool="write",
            outcome=Outcome.correction,
            substrate_consumed=42,
            product_released=10,
            response_latency=350,
            error="typo",
            correction="fixed",
            context="edit",
        )
        ss.append(original)
        recalled = ss.recall_all()[0]
        assert recalled.tool == original.tool
        assert recalled.outcome == original.outcome
        assert recalled.substrate_consumed == 42
        assert recalled.product_released == 10
        assert recalled.response_latency == 350
        assert recalled.error == "typo"
        assert recalled.correction == "fixed"
        assert recalled.context == "edit"
