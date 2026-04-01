"""Tests for metabolon.metabolism.nociceptor — comprehensive coverage."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from metabolon.metabolism.nociceptor import (
    CHRONIC_THRESHOLD,
    HKT,
    HOOK_LOG,
    INFECTION_LOG,
    SIGNAL_LOG,
    PainEvent,
    _read_jsonl,
    classify_error,
    recommended_action,
    report,
    scan,
)

MOD = "metabolon.metabolism.nociceptor"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ts(hours_ago: float = 0) -> str:
    """ISO timestamp relative to now in HKT."""
    return (datetime.now(HKT) - timedelta(hours=hours_ago)).isoformat()


def _write_jsonl(path: Path, entries: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(e) for e in entries) + "\n")


def _patched_logs(tmp_path):
    """Context manager that patches all three log paths."""
    pi = patch(f"{MOD}.INFECTION_LOG", tmp_path / "inf.jsonl")
    ps = patch(f"{MOD}.SIGNAL_LOG", tmp_path / "sig.jsonl")
    ph = patch(f"{MOD}.HOOK_LOG", tmp_path / "hook.jsonl")
    return pi, ps, ph


# ---------------------------------------------------------------------------
# classify_error
# ---------------------------------------------------------------------------

class TestClassifyError:
    @pytest.mark.parametrize("msg", [
        "timeout after 30s",
        "Connection timed out",
        "connection refused by remote",
        "connection reset by peer",
        "DNS resolution failed",
    ])
    def test_network_variants(self, msg):
        assert classify_error(msg) == "network"

    @pytest.mark.parametrize("msg", [
        "HTTP 401 Unauthorized",
        "Got 403 Forbidden",
        "unauthorized access",
        "forbidden: insufficient perms",
        "auth failure",
        "token expired at noon",
    ])
    def test_auth_variants(self, msg):
        assert classify_error(msg) == "auth"

    @pytest.mark.parametrize("msg", [
        "429 Too Many Requests",
        "rate limit exceeded",
        "quota exceeded for project",
        "disk full",
        "No space left on device",
        "resource exhausted",
    ])
    def test_resource_variants(self, msg):
        assert classify_error(msg) == "resource"

    @pytest.mark.parametrize("msg", [
        "KeyError: 'foo'",
        "AttributeError: no 'bar'",
        "TypeError: wrong type",
        "ValueError: bad value",
        "assertion failed: x != y",
    ])
    def test_logic_variants(self, msg):
        assert classify_error(msg) == "logic"

    def test_unknown(self):
        assert classify_error("something completely novel") == "unknown"

    def test_case_insensitive(self):
        assert classify_error("TIMEOUT") == "network"
        assert classify_error("FORBIDDEN") == "auth"


# ---------------------------------------------------------------------------
# recommended_action
# ---------------------------------------------------------------------------

class TestRecommendedAction:
    def test_network(self):
        assert "retry" in recommended_action("network", 1)

    def test_auth(self):
        r = recommended_action("auth", 1)
        assert "alert" in r or "pause" in r

    def test_resource(self):
        r = recommended_action("resource", 1)
        assert "throttle" in r or "wait" in r

    def test_logic(self):
        assert "investigate" in recommended_action("logic", 1)

    def test_unknown(self):
        assert recommended_action("unknown", 1) == "investigate"

    def test_chronic_type(self):
        assert "escalate" in recommended_action("chronic", 1)

    def test_chronic_threshold_triggers_escalate(self):
        assert "escalate" in recommended_action("network", CHRONIC_THRESHOLD)
        assert "escalate" in recommended_action("logic", CHRONIC_THRESHOLD + 5)

    def test_below_threshold(self):
        assert "escalate" not in recommended_action("network", CHRONIC_THRESHOLD - 1)


# ---------------------------------------------------------------------------
# _read_jsonl
# ---------------------------------------------------------------------------

class TestReadJsonl:
    def test_missing_file(self, tmp_path):
        assert _read_jsonl(tmp_path / "nope.jsonl") == []

    def test_recent_entry(self, tmp_path):
        f = tmp_path / "log.jsonl"
        f.write_text(json.dumps({"ts": _ts(0), "val": 1}) + "\n")
        assert len(_read_jsonl(f, 1)) == 1

    def test_old_entry_filtered(self, tmp_path):
        f = tmp_path / "log.jsonl"
        f.write_text(json.dumps({"ts": _ts(48), "val": 1}) + "\n")
        assert _read_jsonl(f, max_age_hours=24) == []

    def test_timestamp_field_name(self, tmp_path):
        f = tmp_path / "log.jsonl"
        f.write_text(json.dumps({"timestamp": _ts(0), "val": 1}) + "\n")
        assert len(_read_jsonl(f, 1)) == 1

    def test_naive_timestamp_gets_hkt(self, tmp_path):
        f = tmp_path / "log.jsonl"
        naive = datetime.now(HKT).replace(tzinfo=None).isoformat()
        f.write_text(json.dumps({"ts": naive}) + "\n")
        assert len(_read_jsonl(f, 1)) == 1

    def test_empty_lines_skipped(self, tmp_path):
        f = tmp_path / "log.jsonl"
        f.write_text("\n\n" + json.dumps({"ts": _ts(0)}) + "\n\n")
        assert len(_read_jsonl(f, 1)) == 1

    def test_malformed_json_skipped(self, tmp_path):
        f = tmp_path / "log.jsonl"
        f.write_text("not json\n" + json.dumps({"ts": _ts(0)}) + "\n")
        assert len(_read_jsonl(f, 1)) == 1

    def test_bad_timestamp_still_included(self, tmp_path):
        f = tmp_path / "log.jsonl"
        f.write_text(json.dumps({"ts": "not-a-date", "val": 1}) + "\n")
        assert len(_read_jsonl(f, 1)) == 1

    def test_oserror_returns_empty(self, tmp_path):
        f = tmp_path / "log.jsonl"
        f.write_text(json.dumps({"ts": _ts(0)}) + "\n")
        with patch.object(Path, "read_text", side_effect=OSError("boom")):
            assert _read_jsonl(f, 1) == []


# ---------------------------------------------------------------------------
# scan
# ---------------------------------------------------------------------------

class TestScan:
    def test_empty_logs(self, tmp_path):
        pi, ps, ph = _patched_logs(tmp_path)
        with pi, ps, ph:
            assert scan(hours=24) == []

    def test_infection_entries(self, tmp_path):
        _write_jsonl(tmp_path / "inf.jsonl", [
            {"ts": _ts(0), "error": "timeout", "tool": "curl", "fingerprint": "fp1"},
        ])
        pi, ps, ph = _patched_logs(tmp_path)
        with pi, ps, ph:
            events = scan(1)
        assert len(events) == 1
        assert events[0].source == "infection"
        assert events[0].pain_type == "network"
        assert events[0].site == "curl"

    def test_signal_error_entries(self, tmp_path):
        _write_jsonl(tmp_path / "sig.jsonl", [
            {"ts": _ts(0), "outcome": "error", "error": "403 denied", "tool": "deploy"},
        ])
        pi, ps, ph = _patched_logs(tmp_path)
        with pi, ps, ph:
            events = scan(1)
        assert len(events) == 1
        assert events[0].source == "signal"
        assert events[0].pain_type == "auth"

    def test_signal_correction_entries(self, tmp_path):
        _write_jsonl(tmp_path / "sig.jsonl", [
            {"ts": _ts(0), "outcome": "correction", "message": "fixed", "substrate": "x"},
        ])
        pi, ps, ph = _patched_logs(tmp_path)
        with pi, ps, ph:
            events = scan(1)
        assert len(events) == 1
        assert events[0].source == "signal"

    def test_signal_non_error_filtered(self, tmp_path):
        _write_jsonl(tmp_path / "sig.jsonl", [
            {"ts": _ts(0), "outcome": "success", "message": "ok"},
        ])
        pi, ps, ph = _patched_logs(tmp_path)
        with pi, ps, ph:
            assert scan(1) == []

    def test_hook_denial_entries(self, tmp_path):
        _write_jsonl(tmp_path / "hook.jsonl", [
            {"ts": _ts(0), "rule": "deny-dangerous", "hook": "pre-commit"},
        ])
        pi, ps, ph = _patched_logs(tmp_path)
        with pi, ps, ph:
            events = scan(1)
        assert len(events) == 1
        assert events[0].source == "hook"
        assert events[0].pain_type == "logic"
        assert events[0].recommended_action == "review hook rule"

    def test_hook_empty_rule_skipped(self, tmp_path):
        _write_jsonl(tmp_path / "hook.jsonl", [
            {"ts": _ts(0), "rule": "", "hook": "pre-commit"},
        ])
        pi, ps, ph = _patched_logs(tmp_path)
        with pi, ps, ph:
            assert scan(1) == []

    def test_chronic_detection(self, tmp_path):
        """Same fingerprint >= CHRONIC_THRESHOLD triggers chronic type."""
        _write_jsonl(tmp_path / "inf.jsonl", [
            {"ts": _ts(0), "error": "timeout", "tool": "curl", "fingerprint": "fpX"}
            for _ in range(CHRONIC_THRESHOLD)
        ])
        pi, ps, ph = _patched_logs(tmp_path)
        with pi, ps, ph:
            events = scan(1)
        assert len(events) == CHRONIC_THRESHOLD
        assert events[-1].pain_type == "chronic"
        assert events[-1].count == CHRONIC_THRESHOLD

    def test_error_truncated_to_200(self, tmp_path):
        long_err = "x" * 300
        _write_jsonl(tmp_path / "inf.jsonl", [
            {"ts": _ts(0), "error": long_err, "tool": "t", "fingerprint": "fp1"},
        ])
        pi, ps, ph = _patched_logs(tmp_path)
        with pi, ps, ph:
            events = scan(1)
        assert len(events[0].error) <= 200

    def test_signal_uses_message_fallback(self, tmp_path):
        _write_jsonl(tmp_path / "sig.jsonl", [
            {"ts": _ts(0), "outcome": "error", "message": "quota hit", "substrate": "sub1"},
        ])
        pi, ps, ph = _patched_logs(tmp_path)
        with pi, ps, ph:
            events = scan(1)
        assert events[0].error == "quota hit"
        assert events[0].site == "sub1"


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------

class TestReport:
    def test_no_events(self, tmp_path):
        pi, ps, ph = _patched_logs(tmp_path)
        with pi, ps, ph:
            r = report(hours=1)
        assert "No pain events" in r

    def test_with_events(self, tmp_path):
        _write_jsonl(tmp_path / "inf.jsonl", [
            {"ts": _ts(0), "error": "timeout", "tool": "curl", "fingerprint": "fp1"},
        ])
        pi, ps, ph = _patched_logs(tmp_path)
        with pi, ps, ph:
            r = report(hours=1)
        assert "Pain report" in r
        assert "NETWORK" in r

    def test_chronic_section(self, tmp_path):
        _write_jsonl(tmp_path / "inf.jsonl", [
            {"ts": _ts(0), "error": "timeout", "tool": "curl", "fingerprint": "fpC"}
            for _ in range(CHRONIC_THRESHOLD)
        ])
        pi, ps, ph = _patched_logs(tmp_path)
        with pi, ps, ph:
            r = report(hours=1)
        assert "CHRONIC INFECTIONS" in r

    def test_deduplication_in_report(self, tmp_path):
        """Same site:error pair appears only once per type section."""
        _write_jsonl(tmp_path / "sig.jsonl", [
            {"ts": _ts(0), "outcome": "error", "error": "timeout", "tool": "a"},
            {"ts": _ts(0), "outcome": "error", "error": "timeout", "tool": "a"},
        ])
        pi, ps, ph = _patched_logs(tmp_path)
        with pi, ps, ph:
            r = report(hours=1)
        assert r.count("[signal] a: timeout") == 1


# ---------------------------------------------------------------------------
# PainEvent dataclass
# ---------------------------------------------------------------------------

class TestPainEvent:
    def test_defaults(self):
        e = PainEvent(timestamp="t", source="s", site="x", error="e", pain_type="network")
        assert e.count == 1
        assert e.recommended_action == "investigate"

    def test_custom_fields(self):
        e = PainEvent(
            timestamp="t", source="s", site="x", error="e",
            pain_type="chronic", count=5, recommended_action="escalate",
        )
        assert e.count == 5
        assert e.pain_type == "chronic"


# ---------------------------------------------------------------------------
# Module constants
# ---------------------------------------------------------------------------

class TestConstants:
    def test_chronic_threshold_positive(self):
        assert CHRONIC_THRESHOLD >= 1

    def test_log_paths_are_path_objects(self):
        assert isinstance(INFECTION_LOG, Path)
        assert isinstance(SIGNAL_LOG, Path)
        assert isinstance(HOOK_LOG, Path)

    def test_hkt_is_utc8(self):
        assert HKT.utcoffset(None) == timedelta(hours=8)
