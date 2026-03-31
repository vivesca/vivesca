"""Tests for nociceptor — unified error detection."""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch
import pytest

HKT = timezone(timedelta(hours=8))

def test_classify_error_network():
    from metabolon.metabolism.nociceptor import classify_error
    assert classify_error("Connection timed out after 30s") == "network"
    assert classify_error("connection refused") == "network"

def test_classify_error_auth():
    from metabolon.metabolism.nociceptor import classify_error
    assert classify_error("HTTP 401 Unauthorized") == "auth"
    assert classify_error("token expired") == "auth"

def test_classify_error_resource():
    from metabolon.metabolism.nociceptor import classify_error
    assert classify_error("429 rate limit exceeded") == "resource"
    assert classify_error("No space left on device") == "resource"

def test_classify_error_logic():
    from metabolon.metabolism.nociceptor import classify_error
    assert classify_error("KeyError: 'missing_field'") == "logic"

def test_classify_error_unknown():
    from metabolon.metabolism.nociceptor import classify_error
    assert classify_error("something weird happened") == "unknown"

def test_recommended_action_chronic():
    from metabolon.metabolism.nociceptor import recommended_action
    result = recommended_action("network", count=5)
    assert "escalate" in result

def test_recommended_action_network():
    from metabolon.metabolism.nociceptor import recommended_action
    result = recommended_action("network", count=1)
    assert "retry" in result

def test_read_jsonl_missing_file():
    from metabolon.metabolism.nociceptor import _read_jsonl
    result = _read_jsonl(Path("/nonexistent/file.jsonl"))
    assert result == []

def test_read_jsonl_with_data(tmp_path):
    from metabolon.metabolism.nociceptor import _read_jsonl
    log_file = tmp_path / "test.jsonl"
    now = datetime.now(HKT).isoformat()
    log_file.write_text(json.dumps({"ts": now, "error": "test"}) + "\n")
    result = _read_jsonl(log_file, max_age_hours=1)
    assert len(result) == 1

def test_scan_empty_logs(tmp_path):
    from metabolon.metabolism.nociceptor import scan
    with patch("metabolon.metabolism.nociceptor.INFECTION_LOG", tmp_path / "no.jsonl"), \
         patch("metabolon.metabolism.nociceptor.SIGNAL_LOG", tmp_path / "no2.jsonl"), \
         patch("metabolon.metabolism.nociceptor.HOOK_LOG", tmp_path / "no3.jsonl"):
        events = scan(hours=1)
        assert events == []

def test_report_no_events(tmp_path):
    from metabolon.metabolism.nociceptor import report
    with patch("metabolon.metabolism.nociceptor.INFECTION_LOG", tmp_path / "no.jsonl"), \
         patch("metabolon.metabolism.nociceptor.SIGNAL_LOG", tmp_path / "no2.jsonl"), \
         patch("metabolon.metabolism.nociceptor.HOOK_LOG", tmp_path / "no3.jsonl"):
        result = report(hours=1)
        assert "No pain events" in result

def test_pain_event_dataclass():
    from metabolon.metabolism.nociceptor import PainEvent
    e = PainEvent(timestamp="now", source="test", site="tool", error="err", pain_type="network")
    assert e.count == 1
    assert e.recommended_action == "investigate"
