from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from metabolon.metabolism.infection import (
    ChronicPattern,
    InfectionEvent,
    _fingerprint,
    chronic_infections,
    infection_summary,
    record_infection,
    recall_infections,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fp(tool: str, error: str) -> str:
    """Compute expected fingerprint matching module logic."""
    raw = f"{tool}:{error[:200]}"
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def _write_events(path: Path, events: list[dict]) -> None:
    """Write JSONL events to a file."""
    with path.open("w") as f:
        for ev in events:
            f.write(json.dumps(ev) + "\n")


# ---------------------------------------------------------------------------
# _fingerprint
# ---------------------------------------------------------------------------

class TestFingerprint:
    def test_deterministic(self):
        assert _fingerprint("tool_a", "error msg") == _fingerprint("tool_a", "error msg")

    def test_different_tool_differs(self):
        assert _fingerprint("tool_a", "error") != _fingerprint("tool_b", "error")

    def test_different_error_differs(self):
        assert _fingerprint("tool_a", "err1") != _fingerprint("tool_a", "err2")

    def test_truncation_200(self):
        long_error = "x" * 300
        assert _fingerprint("t", long_error) == _fingerprint("t", long_error[:200])
        assert _fingerprint("t", long_error) != _fingerprint("t", long_error[:199])

    def test_length_12(self):
        fp = _fingerprint("t", "e")
        assert len(fp) == 12

    def test_hex_chars(self):
        fp = _fingerprint("t", "e")
        assert all(c in "0123456789abcdef" for c in fp)


# ---------------------------------------------------------------------------
# record_infection
# ---------------------------------------------------------------------------

class TestRecordInfection:
    def test_returns_event(self, tmp_path):
        log = tmp_path / "infections.jsonl"
        ev = record_infection("my_tool", "something broke", log_path=log)
        assert isinstance(ev, dict)
        assert ev["tool"] == "my_tool"
        assert ev["error"] == "something broke"
        assert ev["healed"] is False
        assert "ts" in ev
        assert "fingerprint" in ev

    def test_fingerprint_in_event(self, tmp_path):
        log = tmp_path / "infections.jsonl"
        ev = record_infection("t", "err", log_path=log)
        assert ev["fingerprint"] == _fp("t", "err")

    def test_error_truncated_300(self, tmp_path):
        log = tmp_path / "infections.jsonl"
        long_err = "A" * 500
        ev = record_infection("t", long_err, log_path=log)
        assert len(ev["error"]) == 300
        assert ev["error"] == long_err[:300]

    def test_writes_to_file(self, tmp_path):
        log = tmp_path / "infections.jsonl"
        record_infection("t1", "e1", log_path=log)
        record_infection("t2", "e2", log_path=log)
        lines = log.read_text().strip().splitlines()
        assert len(lines) == 2
        assert json.loads(lines[0])["tool"] == "t1"
        assert json.loads(lines[1])["tool"] == "t2"

    def test_creates_parent_dirs(self, tmp_path):
        log = tmp_path / "deep" / "nested" / "inf.jsonl"
        record_infection("t", "e", log_path=log)
        assert log.exists()

    def test_healed_flag(self, tmp_path):
        log = tmp_path / "infections.jsonl"
        ev = record_infection("t", "e", healed=True, log_path=log)
        assert ev["healed"] is True

    def test_never_raises_on_bad_path(self):
        # Writing to a path whose parent is a file should not raise
        bad_log = Path("/dev/null/impossible/infections.jsonl")
        ev = record_infection("t", "e", log_path=bad_log)
        assert ev["tool"] == "t"

    def test_iso_timestamp(self, tmp_path):
        log = tmp_path / "infections.jsonl"
        ev = record_infection("t", "e", log_path=log)
        # ISO format should parse without error
        from datetime import datetime
        datetime.fromisoformat(ev["ts"])


# ---------------------------------------------------------------------------
# recall_infections
# ---------------------------------------------------------------------------

class TestRecallInfections:
    def test_missing_file_returns_empty(self, tmp_path):
        log = tmp_path / "nonexistent.jsonl"
        assert recall_infections(log) == []

    def test_reads_events(self, tmp_path):
        log = tmp_path / "inf.jsonl"
        events = [
            {"ts": "2025-01-01T00:00:00", "tool": "a", "error": "e1", "fingerprint": "abc123", "healed": False},
            {"ts": "2025-01-01T00:01:00", "tool": "b", "error": "e2", "fingerprint": "def456", "healed": True},
        ]
        _write_events(log, events)
        result = recall_infections(log)
        assert len(result) == 2
        assert result[0]["tool"] == "a"
        assert result[1]["healed"] is True

    def test_skips_blank_lines(self, tmp_path):
        log = tmp_path / "inf.jsonl"
        log.write_text("\n\n\n")
        assert recall_infections(log) == []

    def test_skips_invalid_json(self, tmp_path):
        log = tmp_path / "inf.jsonl"
        log.write_text("not json\n")
        assert recall_infections(log) == []

    def test_mixed_valid_invalid(self, tmp_path):
        log = tmp_path / "inf.jsonl"
        valid = '{"ts":"t","tool":"x","error":"e","fingerprint":"f","healed":false}'
        log.write_text(f"bad line\n{valid}\n\nalso bad\n")
        result = recall_infections(log)
        assert len(result) == 1
        assert result[0]["tool"] == "x"


# ---------------------------------------------------------------------------
# chronic_infections
# ---------------------------------------------------------------------------

class TestChronicInfections:
    def test_empty_log(self, tmp_path):
        log = tmp_path / "inf.jsonl"
        assert chronic_infections(log, threshold=3) == []

    def test_below_threshold(self, tmp_path):
        log = tmp_path / "inf.jsonl"
        fp = _fp("tool_a", "err")
        events = [
            {"ts": "2025-01-01T00:00:00", "tool": "tool_a", "error": "err",
             "fingerprint": fp, "healed": False},
            {"ts": "2025-01-01T00:01:00", "tool": "tool_a", "error": "err",
             "fingerprint": fp, "healed": False},
        ]
        _write_events(log, events)
        result = chronic_infections(log, threshold=3)
        assert result == []

    def test_at_threshold(self, tmp_path):
        log = tmp_path / "inf.jsonl"
        fp = _fp("tool_a", "err")
        events = [
            {"ts": f"2025-01-01T00:0{i}:00", "tool": "tool_a", "error": "err",
             "fingerprint": fp, "healed": False}
            for i in range(3)
        ]
        _write_events(log, events)
        result = chronic_infections(log, threshold=3)
        assert len(result) == 1
        assert result[0]["tool"] == "tool_a"
        assert result[0]["count"] == 3
        assert result[0]["fingerprint"] == fp
        assert result[0]["healed_count"] == 0

    def test_all_healed_not_chronic(self, tmp_path):
        log = tmp_path / "inf.jsonl"
        fp = _fp("tool_a", "err")
        events = [
            {"ts": f"2025-01-01T00:0{i}:00", "tool": "tool_a", "error": "err",
             "fingerprint": fp, "healed": True}
            for i in range(5)
        ]
        _write_events(log, events)
        result = chronic_infections(log, threshold=3)
        assert result == []

    def test_mixed_healed_counts_unhealed(self, tmp_path):
        log = tmp_path / "inf.jsonl"
        fp = _fp("tool_a", "err")
        events = [
            {"ts": "2025-01-01T00:00:00", "tool": "tool_a", "error": "err",
             "fingerprint": fp, "healed": True},
            {"ts": "2025-01-01T00:01:00", "tool": "tool_a", "error": "err",
             "fingerprint": fp, "healed": True},
            {"ts": "2025-01-01T00:02:00", "tool": "tool_a", "error": "err",
             "fingerprint": fp, "healed": False},
            {"ts": "2025-01-01T00:03:00", "tool": "tool_a", "error": "err",
             "fingerprint": fp, "healed": False},
            {"ts": "2025-01-01T00:04:00", "tool": "tool_a", "error": "err",
             "fingerprint": fp, "healed": False},
        ]
        _write_events(log, events)
        result = chronic_infections(log, threshold=3)
        assert len(result) == 1
        assert result[0]["count"] == 5
        assert result[0]["healed_count"] == 2

    def test_last_error_from_latest_unhealed(self, tmp_path):
        log = tmp_path / "inf.jsonl"
        fp = _fp("tool_a", "err")
        events = [
            {"ts": "2025-01-01T00:00:00", "tool": "tool_a", "error": "early err",
             "fingerprint": fp, "healed": False},
            {"ts": "2025-01-01T00:01:00", "tool": "tool_a", "error": "mid err",
             "fingerprint": fp, "healed": True},
            {"ts": "2025-01-01T00:02:00", "tool": "tool_a", "error": "latest err",
             "fingerprint": fp, "healed": False},
        ]
        _write_events(log, events)
        result = chronic_infections(log, threshold=2)
        assert len(result) == 1
        assert result[0]["last_error"] == "latest err"
        assert result[0]["last_seen"] == "2025-01-01T00:02:00"

    def test_multiple_patterns_sorted_by_count(self, tmp_path):
        log = tmp_path / "inf.jsonl"
        fp_a = _fp("tool_a", "err_a")
        fp_b = _fp("tool_b", "err_b")
        events = (
            [{"ts": f"2025-01-01T00:0{i}:00", "tool": "tool_a", "error": "err_a",
              "fingerprint": fp_a, "healed": False} for i in range(3)]
            + [{"ts": f"2025-01-02T00:0{i}:00", "tool": "tool_b", "error": "err_b",
                "fingerprint": fp_b, "healed": False} for i in range(5)]
        )
        _write_events(log, events)
        result = chronic_infections(log, threshold=3)
        assert len(result) == 2
        assert result[0]["tool"] == "tool_b"  # 5 events > 3 events
        assert result[0]["count"] == 5
        assert result[1]["tool"] == "tool_a"
        assert result[1]["count"] == 3

    def test_different_tools_same_fingerprint(self, tmp_path):
        # Two tools sharing the same fingerprint string (unlikely but possible)
        fp = "aaaa1111bbbb"
        events = [
            {"ts": "2025-01-01T00:00:00", "tool": "tool_a", "error": "err",
             "fingerprint": fp, "healed": False},
            {"ts": "2025-01-01T00:01:00", "tool": "tool_a", "error": "err",
             "fingerprint": fp, "healed": False},
            {"ts": "2025-01-01T00:02:00", "tool": "tool_a", "error": "err",
             "fingerprint": fp, "healed": False},
        ]
        log = tmp_path / "inf.jsonl"
        _write_events(log, events)
        result = chronic_infections(log, threshold=3)
        assert len(result) == 1


# ---------------------------------------------------------------------------
# infection_summary
# ---------------------------------------------------------------------------

class TestInfectionSummary:
    def test_empty_log(self, tmp_path):
        log = tmp_path / "inf.jsonl"
        assert infection_summary(log) == ""

    def test_nonempty_no_chronics(self, tmp_path):
        log = tmp_path / "inf.jsonl"
        fp = _fp("t", "e")
        events = [
            {"ts": "2025-01-01T00:00:00", "tool": "t", "error": "e",
             "fingerprint": fp, "healed": True},
        ]
        _write_events(log, events)
        summary = infection_summary(log)
        assert "Infections: 1 events" in summary
        assert "1 unhealed" not in summary  # 0 unhealed
        assert "CHRONIC" not in summary

    def test_with_unhealed(self, tmp_path):
        log = tmp_path / "inf.jsonl"
        fp = _fp("t", "e")
        events = [
            {"ts": "2025-01-01T00:00:00", "tool": "t", "error": "e",
             "fingerprint": fp, "healed": False},
            {"ts": "2025-01-01T00:01:00", "tool": "t", "error": "e",
             "fingerprint": fp, "healed": True},
        ]
        _write_events(log, events)
        summary = infection_summary(log)
        assert "2 events" in summary
        assert "1 unhealed" in summary

    def test_with_chronic_pattern(self, tmp_path):
        log = tmp_path / "inf.jsonl"
        fp = _fp("chronic_tool", "persistent error")
        events = [
            {"ts": f"2025-01-01T00:0{i}:00", "tool": "chronic_tool",
             "error": "persistent error", "fingerprint": fp, "healed": False}
            for i in range(4)
        ]
        _write_events(log, events)
        summary = infection_summary(log)
        assert "CHRONIC" in summary
        assert "chronic_tool" in summary
        assert "x4" in summary

    def test_chronic_error_truncated_80(self, tmp_path):
        log = tmp_path / "inf.jsonl"
        long_err = "Z" * 200
        fp = _fp("t", long_err)
        events = [
            {"ts": f"2025-01-01T00:0{i}:00", "tool": "t", "error": long_err,
             "fingerprint": fp, "healed": False}
            for i in range(3)
        ]
        _write_events(log, events)
        summary = infection_summary(log)
        # The last_error in summary is truncated to 80 chars
        lines = summary.splitlines()
        chronic_lines = [l for l in lines if "CHRONIC:" in l]
        assert len(chronic_lines) == 1
        # The error part after " — " should be at most 80 chars
        after_dash = chronic_lines[0].split(" — ")[1]
        assert len(after_dash) <= 80


# ---------------------------------------------------------------------------
# Integration: round-trip record -> recall -> chronic
# ---------------------------------------------------------------------------

class TestRoundTrip:
    def test_record_recall_roundtrip(self, tmp_path):
        log = tmp_path / "inf.jsonl"
        ev1 = record_infection("tool_x", "badness", log_path=log)
        ev2 = record_infection("tool_y", "other badness", healed=True, log_path=log)
        recalled = recall_infections(log)
        assert len(recalled) == 2
        assert recalled[0]["tool"] == "tool_x"
        assert recalled[0]["fingerprint"] == ev1["fingerprint"]
        assert recalled[1]["tool"] == "tool_y"
        assert recalled[1]["healed"] is True

    def test_record_chronic_flow(self, tmp_path):
        log = tmp_path / "inf.jsonl"
        for _ in range(4):
            record_infection("flaky_tool", "timeout exceeded", log_path=log)
        chronics = chronic_infections(log, threshold=3)
        assert len(chronics) == 1
        assert chronics[0]["tool"] == "flaky_tool"
        assert chronics[0]["count"] == 4
        summary = infection_summary(log)
        assert "4 events" in summary
        assert "flaky_tool" in summary
