"""Comprehensive tests for metabolon.metabolism.nociceptor."""
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

# ---------------------------------------------------------------------------
# classify_error
# ---------------------------------------------------------------------------

class TestClassifyError:
    """classify_error maps error strings to pain types."""

    # network
    @pytest.mark.parametrize("msg", [
        "timeout after 30s",
        "Connection Timed Out",
        "connection refused by peer",
        "connection reset by remote",
        "DNS resolution failed",
        "dial tcp: lookup api.example.com: no such host (dns)",
    ])
    def test_network_variants(self, msg):
        assert classify_error(msg) == "network"

    # auth
    @pytest.mark.parametrize("msg", [
        "HTTP 401 Unauthorized",
        "403 Forbidden",
        "unauthorized access",
        "forbidden: insufficient permissions",
        "auth token invalid",
        "token expired at midnight",
    ])
    def test_auth_variants(self, msg):
        assert classify_error(msg) == "auth"

    # resource
    @pytest.mark.parametrize("msg", [
        "429 Too Many Requests",
        "rate limit exceeded",
        "quota exceeded for project",
        "disk full on /dev/sda1",
        "No space left on device",
        "resource exhausted: cpu",
    ])
    def test_resource_variants(self, msg):
        assert classify_error(msg) == "resource"

    # logic
    @pytest.mark.parametrize("msg", [
        "KeyError: 'missing'",
        "AttributeError: 'NoneType' has no 'x'",
        "TypeError: expected str got int",
        "ValueError: invalid literal",
        "AssertionError: expected True",
    ])
    def test_logic_variants(self, msg):
        assert classify_error(msg) == "logic"

    def test_unknown_returns_unknown(self):
        assert classify_error("something completely unexpected") == "unknown"

    def test_empty_string_is_unknown(self):
        assert classify_error("") == "unknown"

    def test_case_insensitive(self):
        assert classify_error("TIMEOUT") == "network"
        assert classify_error("CONNECTION REFUSED") == "network"


# ---------------------------------------------------------------------------
# recommended_action
# ---------------------------------------------------------------------------

class TestRecommendedAction:
    """recommended_action returns sensible guidance per pain type."""

    def test_network_retry(self):
        assert "retry" in recommended_action("network", 1)

    def test_auth_alert(self):
        assert "alert" in recommended_action("auth", 1)

    def test_resource_throttle(self):
        assert "throttle" in recommended_action("resource", 1)

    def test_logic_investigate(self):
        assert "investigate" in recommended_action("logic", 1)

    def test_unknown_investigate(self):
        assert "investigate" in recommended_action("unknown", 1)

    def test_chronic_escalate(self):
        assert "escalate" in recommended_action("chronic", 1)

    def test_above_chronic_threshold_escalates(self):
        result = recommended_action("network", CHRONIC_THRESHOLD)
        assert "escalate" in result

    def test_below_chronic_threshold_no_escalate(self):
        result = recommended_action("network", CHRONIC_THRESHOLD - 1)
        assert "escalate" not in result
        assert "retry" in result


# ---------------------------------------------------------------------------
# _read_jsonl
# ---------------------------------------------------------------------------

class TestReadJsonl:
    """_read_jsonl reads and filters JSONL files."""

    def test_missing_file_returns_empty(self, tmp_path):
        assert _read_jsonl(tmp_path / "nope.jsonl") == []

    def test_reads_valid_entries(self, tmp_path):
        f = tmp_path / "log.jsonl"
        now = datetime.now(HKT).isoformat()
        f.write_text(json.dumps({"ts": now, "msg": "a"}) + "\n")
        assert len(_read_jsonl(f, max_age_hours=1)) == 1

    def test_filters_old_entries(self, tmp_path):
        f = tmp_path / "log.jsonl"
        old = (datetime.now(HKT) - timedelta(hours=48)).isoformat()
        f.write_text(json.dumps({"ts": old, "msg": "old"}) + "\n")
        assert _read_jsonl(f, max_age_hours=24) == []

    def test_keeps_entry_without_timestamp(self, tmp_path):
        f = tmp_path / "log.jsonl"
        f.write_text(json.dumps({"msg": "no_ts"}) + "\n")
        assert len(_read_jsonl(f)) == 1

    def test_handles_malformed_json_lines(self, tmp_path):
        f = tmp_path / "log.jsonl"
        now = datetime.now(HKT).isoformat()
        f.write_text("bad line\n" + json.dumps({"ts": now}) + "\n")
        assert len(_read_jsonl(f)) == 1

    def test_handles_empty_lines(self, tmp_path):
        f = tmp_path / "log.jsonl"
        now = datetime.now(HKT).isoformat()
        f.write_text("\n\n" + json.dumps({"ts": now}) + "\n\n")
        assert len(_read_jsonl(f)) == 1

    def test_naive_datetime_treated_as_hkt(self, tmp_path):
        f = tmp_path / "log.jsonl"
        now_naive = datetime.now(HKT).replace(tzinfo=None).isoformat()
        f.write_text(json.dumps({"ts": now_naive}) + "\n")
        assert len(_read_jsonl(f, max_age_hours=1)) == 1

    def test_uses_timestamp_field_as_fallback(self, tmp_path):
        f = tmp_path / "log.jsonl"
        now = datetime.now(HKT).isoformat()
        f.write_text(json.dumps({"timestamp": now, "msg": "alt_ts"}) + "\n")
        assert len(_read_jsonl(f, max_age_hours=1)) == 1

    def test_oserror_returns_empty(self, tmp_path):
        f = tmp_path / "log.jsonl"
        f.write_text("ok")
        with patch.object(Path, "read_text", side_effect=OSError("permission denied")):
            assert _read_jsonl(f) == []


# ---------------------------------------------------------------------------
# scan
# ---------------------------------------------------------------------------

def _write_jsonl(path: Path, entries: list[dict]) -> None:
    """Write JSONL entries to a file."""
    path.write_text("\n".join(json.dumps(e) for e in entries) + "\n")


class TestScan:
    """scan reads all three log sources and returns PainEvents."""

    def _make_ts(self) -> str:
        return datetime.now(HKT).isoformat()

    def test_empty_logs(self, tmp_path):
        with patch("metabolon.metabolism.nociceptor.INFECTION_LOG", tmp_path / "i.jsonl"), \
             patch("metabolon.metabolism.nociceptor.SIGNAL_LOG", tmp_path / "s.jsonl"), \
             patch("metabolon.metabolism.nociceptor.HOOK_LOG", tmp_path / "h.jsonl"):
            assert scan(hours=1) == []

    def test_infection_log_basic(self, tmp_path):
        ts = self._make_ts()
        inf = tmp_path / "i.jsonl"
        _write_jsonl(inf, [{"ts": ts, "error": "timeout", "tool": "fetcher", "fingerprint": "fp1"}])

        with patch("metabolon.metabolism.nociceptor.INFECTION_LOG", inf), \
             patch("metabolon.metabolism.nociceptor.SIGNAL_LOG", tmp_path / "s.jsonl"), \
             patch("metabolon.metabolism.nociceptor.HOOK_LOG", tmp_path / "h.jsonl"):
            events = scan(hours=1)
        assert len(events) == 1
        assert events[0].source == "infection"
        assert events[0].site == "fetcher"
        assert events[0].pain_type == "network"
        assert events[0].count == 1

    def test_infection_log_chronic_detection(self, tmp_path):
        ts = self._make_ts()
        inf = tmp_path / "i.jsonl"
        entries = [
            {"ts": ts, "error": "timeout", "tool": "x", "fingerprint": "fpA"},
            {"ts": ts, "error": "timeout", "tool": "x", "fingerprint": "fpA"},
            {"ts": ts, "error": "timeout", "tool": "x", "fingerprint": "fpA"},
        ]
        _write_jsonl(inf, entries)

        with patch("metabolon.metabolism.nociceptor.INFECTION_LOG", inf), \
             patch("metabolon.metabolism.nociceptor.SIGNAL_LOG", tmp_path / "s.jsonl"), \
             patch("metabolon.metabolism.nociceptor.HOOK_LOG", tmp_path / "h.jsonl"):
            events = scan(hours=1)
        # Third occurrence should be classified as chronic
        assert events[-1].pain_type == "chronic"
        assert events[-1].count == CHRONIC_THRESHOLD

    def test_infection_log_default_site(self, tmp_path):
        ts = self._make_ts()
        inf = tmp_path / "i.jsonl"
        _write_jsonl(inf, [{"ts": ts, "error": "oops", "fingerprint": "fpX"}])

        with patch("metabolon.metabolism.nociceptor.INFECTION_LOG", inf), \
             patch("metabolon.metabolism.nociceptor.SIGNAL_LOG", tmp_path / "s.jsonl"), \
             patch("metabolon.metabolism.nociceptor.HOOK_LOG", tmp_path / "h.jsonl"):
            events = scan(hours=1)
        assert events[0].site == "unknown"

    def test_infection_log_error_truncation(self, tmp_path):
        ts = self._make_ts()
        inf = tmp_path / "i.jsonl"
        long_err = "x" * 500
        _write_jsonl(inf, [{"ts": ts, "error": long_err, "fingerprint": "fpL"}])

        with patch("metabolon.metabolism.nociceptor.INFECTION_LOG", inf), \
             patch("metabolon.metabolism.nociceptor.SIGNAL_LOG", tmp_path / "s.jsonl"), \
             patch("metabolon.metabolism.nociceptor.HOOK_LOG", tmp_path / "h.jsonl"):
            events = scan(hours=1)
        assert len(events[0].error) <= 200

    def test_signal_log_error_outcome(self, tmp_path):
        ts = self._make_ts()
        sig = tmp_path / "s.jsonl"
        _write_jsonl(sig, [{"ts": ts, "outcome": "error", "error": "403 forbidden", "tool": "api"}])

        with patch("metabolon.metabolism.nociceptor.INFECTION_LOG", tmp_path / "i.jsonl"), \
             patch("metabolon.metabolism.nociceptor.SIGNAL_LOG", sig), \
             patch("metabolon.metabolism.nociceptor.HOOK_LOG", tmp_path / "h.jsonl"):
            events = scan(hours=1)
        assert len(events) == 1
        assert events[0].source == "signal"
        assert events[0].site == "api"
        assert events[0].pain_type == "auth"

    def test_signal_log_correction_outcome(self, tmp_path):
        ts = self._make_ts()
        sig = tmp_path / "s.jsonl"
        _write_jsonl(sig, [{"ts": ts, "outcome": "correction", "message": "fixed", "substrate": "sub1"}])

        with patch("metabolon.metabolism.nociceptor.INFECTION_LOG", tmp_path / "i.jsonl"), \
             patch("metabolon.metabolism.nociceptor.SIGNAL_LOG", sig), \
             patch("metabolon.metabolism.nociceptor.HOOK_LOG", tmp_path / "h.jsonl"):
            events = scan(hours=1)
        assert len(events) == 1
        assert events[0].source == "signal"
        assert events[0].site == "sub1"

    def test_signal_log_skips_success_outcome(self, tmp_path):
        ts = self._make_ts()
        sig = tmp_path / "s.jsonl"
        _write_jsonl(sig, [{"ts": ts, "outcome": "success", "error": "n/a"}])

        with patch("metabolon.metabolism.nociceptor.INFECTION_LOG", tmp_path / "i.jsonl"), \
             patch("metabolon.metabolism.nociceptor.SIGNAL_LOG", sig), \
             patch("metabolon.metabolism.nociceptor.HOOK_LOG", tmp_path / "h.jsonl"):
            assert scan(hours=1) == []

    def test_signal_log_uses_timestamp_fallback(self, tmp_path):
        ts = self._make_ts()
        sig = tmp_path / "s.jsonl"
        _write_jsonl(sig, [{"timestamp": ts, "outcome": "error", "error": "fail", "tool": "t"}])

        with patch("metabolon.metabolism.nociceptor.INFECTION_LOG", tmp_path / "i.jsonl"), \
             patch("metabolon.metabolism.nociceptor.SIGNAL_LOG", sig), \
             patch("metabolon.metabolism.nociceptor.HOOK_LOG", tmp_path / "h.jsonl"):
            events = scan(hours=1)
        assert len(events) == 1
        assert events[0].timestamp == ts

    def test_signal_log_error_message_fallback(self, tmp_path):
        ts = self._make_ts()
        sig = tmp_path / "s.jsonl"
        _write_jsonl(sig, [{"ts": ts, "outcome": "error", "message": "something broke", "tool": "t"}])

        with patch("metabolon.metabolism.nociceptor.INFECTION_LOG", tmp_path / "i.jsonl"), \
             patch("metabolon.metabolism.nociceptor.SIGNAL_LOG", sig), \
             patch("metabolon.metabolism.nociceptor.HOOK_LOG", tmp_path / "h.jsonl"):
            events = scan(hours=1)
        assert events[0].error == "something broke"

    def test_hook_log_basic(self, tmp_path):
        ts = self._make_ts()
        hook = tmp_path / "h.jsonl"
        _write_jsonl(hook, [{"ts": ts, "rule": "deny-dangerous-write", "hook": "pre-commit"}])

        with patch("metabolon.metabolism.nociceptor.INFECTION_LOG", tmp_path / "i.jsonl"), \
             patch("metabolon.metabolism.nociceptor.SIGNAL_LOG", tmp_path / "s.jsonl"), \
             patch("metabolon.metabolism.nociceptor.HOOK_LOG", hook):
            events = scan(hours=1)
        assert len(events) == 1
        assert events[0].source == "hook"
        assert events[0].site == "pre-commit"
        assert events[0].pain_type == "logic"
        assert events[0].recommended_action == "review hook rule"

    def test_hook_log_skips_entries_without_rule(self, tmp_path):
        ts = self._make_ts()
        hook = tmp_path / "h.jsonl"
        _write_jsonl(hook, [{"ts": ts, "hook": "pre-commit"}])

        with patch("metabolon.metabolism.nociceptor.INFECTION_LOG", tmp_path / "i.jsonl"), \
             patch("metabolon.metabolism.nociceptor.SIGNAL_LOG", tmp_path / "s.jsonl"), \
             patch("metabolon.metabolism.nociceptor.HOOK_LOG", hook):
            assert scan(hours=1) == []

    def test_hook_log_default_site(self, tmp_path):
        ts = self._make_ts()
        hook = tmp_path / "h.jsonl"
        _write_jsonl(hook, [{"ts": ts, "rule": "some-rule"}])

        with patch("metabolon.metabolism.nociceptor.INFECTION_LOG", tmp_path / "i.jsonl"), \
             patch("metabolon.metabolism.nociceptor.SIGNAL_LOG", tmp_path / "s.jsonl"), \
             patch("metabolon.metabolism.nociceptor.HOOK_LOG", hook):
            events = scan(hours=1)
        assert events[0].site == "unknown"

    def test_all_sources_combined(self, tmp_path):
        ts = self._make_ts()
        inf = tmp_path / "i.jsonl"
        sig = tmp_path / "s.jsonl"
        hook = tmp_path / "h.jsonl"
        _write_jsonl(inf, [{"ts": ts, "error": "timeout", "fingerprint": "fp1"}])
        _write_jsonl(sig, [{"ts": ts, "outcome": "error", "error": "401", "tool": "api"}])
        _write_jsonl(hook, [{"ts": ts, "rule": "deny", "hook": "h"}])

        with patch("metabolon.metabolism.nociceptor.INFECTION_LOG", inf), \
             patch("metabolon.metabolism.nociceptor.SIGNAL_LOG", sig), \
             patch("metabolon.metabolism.nociceptor.HOOK_LOG", hook):
            events = scan(hours=1)
        assert len(events) == 3
        sources = {e.source for e in events}
        assert sources == {"infection", "signal", "hook"}


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------

class TestReport:
    """report produces human-readable pain summaries."""

    def test_no_events(self, tmp_path):
        with patch("metabolon.metabolism.nociceptor.INFECTION_LOG", tmp_path / "i.jsonl"), \
             patch("metabolon.metabolism.nociceptor.SIGNAL_LOG", tmp_path / "s.jsonl"), \
             patch("metabolon.metabolism.nociceptor.HOOK_LOG", tmp_path / "h.jsonl"):
            text = report(hours=1)
        assert "No pain events" in text

    def test_report_with_events(self, tmp_path):
        ts = datetime.now(HKT).isoformat()
        sig = tmp_path / "s.jsonl"
        _write_jsonl(sig, [{"ts": ts, "outcome": "error", "error": "403 forbidden", "tool": "gateway"}])

        with patch("metabolon.metabolism.nociceptor.INFECTION_LOG", tmp_path / "i.jsonl"), \
             patch("metabolon.metabolism.nociceptor.SIGNAL_LOG", sig), \
             patch("metabolon.metabolism.nociceptor.HOOK_LOG", tmp_path / "h.jsonl"):
            text = report(hours=1)
        assert "Pain report" in text
        assert "AUTH" in text
        assert "gateway" in text

    def test_report_with_chronic_section(self, tmp_path):
        ts = datetime.now(HKT).isoformat()
        inf = tmp_path / "i.jsonl"
        entries = [
            {"ts": ts, "error": "timeout", "tool": "x", "fingerprint": "fpC"},
            {"ts": ts, "error": "timeout", "tool": "x", "fingerprint": "fpC"},
            {"ts": ts, "error": "timeout", "tool": "x", "fingerprint": "fpC"},
        ]
        _write_jsonl(inf, entries)

        with patch("metabolon.metabolism.nociceptor.INFECTION_LOG", inf), \
             patch("metabolon.metabolism.nociceptor.SIGNAL_LOG", tmp_path / "s.jsonl"), \
             patch("metabolon.metabolism.nociceptor.HOOK_LOG", tmp_path / "h.jsonl"):
            text = report(hours=1)
        assert "CHRONIC INFECTIONS" in text

    def test_report_deduplicates_similar_events(self, tmp_path):
        ts = datetime.now(HKT).isoformat()
        sig = tmp_path / "s.jsonl"
        _write_jsonl(sig, [
            {"ts": ts, "outcome": "error", "error": "same error", "tool": "t"},
            {"ts": ts, "outcome": "error", "error": "same error", "tool": "t"},
        ])

        with patch("metabolon.metabolism.nociceptor.INFECTION_LOG", tmp_path / "i.jsonl"), \
             patch("metabolon.metabolism.nociceptor.SIGNAL_LOG", sig), \
             patch("metabolon.metabolism.nociceptor.HOOK_LOG", tmp_path / "h.jsonl"):
            text = report(hours=1)
        # Should mention 2 events but only show unique entries
        assert "2 events" in text


# ---------------------------------------------------------------------------
# PainEvent dataclass
# ---------------------------------------------------------------------------

class TestPainEvent:
    """PainEvent dataclass defaults and fields."""

    def test_defaults(self):
        e = PainEvent(timestamp="t", source="s", site="x", error="e", pain_type="network")
        assert e.count == 1
        assert e.recommended_action == "investigate"

    def test_custom_values(self):
        e = PainEvent(
            timestamp="t", source="s", site="x", error="e",
            pain_type="chronic", count=5, recommended_action="escalate",
        )
        assert e.count == 5
        assert e.recommended_action == "escalate"
