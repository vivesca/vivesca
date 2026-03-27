"""Tests for the immune infection log — honest error pattern detection."""

from __future__ import annotations

from metabolon.metabolism.infection import (
    CHRONIC_THRESHOLD,
    _fingerprint,
    chronic_infections,
    infection_summary,
    recall_infections,
    record_infection,
)

# ---------------------------------------------------------------------------
# _fingerprint
# ---------------------------------------------------------------------------


def test_fingerprint_is_deterministic():
    fp1 = _fingerprint("my_tool", "connection refused")
    fp2 = _fingerprint("my_tool", "connection refused")
    assert fp1 == fp2


def test_fingerprint_differs_by_tool():
    fp1 = _fingerprint("tool_a", "same error")
    fp2 = _fingerprint("tool_b", "same error")
    assert fp1 != fp2


def test_fingerprint_differs_by_error():
    fp1 = _fingerprint("tool", "error A")
    fp2 = _fingerprint("tool", "error B")
    assert fp1 != fp2


def test_fingerprint_length():
    fp = _fingerprint("x", "y")
    assert len(fp) == 12


# ---------------------------------------------------------------------------
# record_infection / recall_infections
# ---------------------------------------------------------------------------


def test_record_infection_creates_file(tmp_path):
    log = tmp_path / "infections.jsonl"
    event = record_infection("my_tool", "timeout", healed=False, log_path=log)
    assert log.exists()
    assert event["tool"] == "my_tool"
    assert event["healed"] is False


def test_record_infection_appends(tmp_path):
    log = tmp_path / "infections.jsonl"
    record_infection("tool_a", "err1", log_path=log)
    record_infection("tool_b", "err2", log_path=log)
    lines = log.read_text().splitlines()
    assert len(lines) == 2


def test_record_infection_healed_flag(tmp_path):
    log = tmp_path / "infections.jsonl"
    ev = record_infection("t", "e", healed=True, log_path=log)
    assert ev["healed"] is True
    events = recall_infections(log)
    assert events[0]["healed"] is True


def test_recall_infections_empty_when_no_log(tmp_path):
    log = tmp_path / "nonexistent.jsonl"
    assert recall_infections(log) == []


def test_recall_infections_returns_all_events(tmp_path):
    log = tmp_path / "infections.jsonl"
    for i in range(5):
        record_infection(f"tool_{i}", "some error", log_path=log)
    events = recall_infections(log)
    assert len(events) == 5


def test_recall_infections_skips_bad_lines(tmp_path):
    log = tmp_path / "infections.jsonl"
    record_infection("good_tool", "err", log_path=log)
    with log.open("a") as f:
        f.write("this is not json\n")
    events = recall_infections(log)
    assert len(events) == 1


def test_infection_event_has_fingerprint(tmp_path):
    log = tmp_path / "infections.jsonl"
    ev = record_infection("my_tool", "timeout error", log_path=log)
    assert ev["fingerprint"] == _fingerprint("my_tool", "timeout error")


# ---------------------------------------------------------------------------
# chronic_infections
# ---------------------------------------------------------------------------


def test_no_chronics_below_threshold(tmp_path):
    log = tmp_path / "infections.jsonl"
    for _ in range(CHRONIC_THRESHOLD - 1):
        record_infection("flaky_tool", "same error", log_path=log)
    assert chronic_infections(log) == []


def test_chronic_detected_at_threshold(tmp_path):
    log = tmp_path / "infections.jsonl"
    for _ in range(CHRONIC_THRESHOLD):
        record_infection("flaky_tool", "same error", log_path=log)
    patterns = chronic_infections(log)
    assert len(patterns) == 1
    assert patterns[0]["tool"] == "flaky_tool"
    assert patterns[0]["count"] == CHRONIC_THRESHOLD


def test_chronic_healed_count(tmp_path):
    log = tmp_path / "infections.jsonl"
    # 3 unhealed, 2 healed — unhealed meets threshold of 3
    record_infection("t", "err", healed=False, log_path=log)
    record_infection("t", "err", healed=False, log_path=log)
    record_infection("t", "err", healed=False, log_path=log)
    record_infection("t", "err", healed=True, log_path=log)
    record_infection("t", "err", healed=True, log_path=log)
    patterns = chronic_infections(log)
    assert len(patterns) == 1
    assert patterns[0]["healed_count"] == 2


def test_distinct_tools_tracked_separately(tmp_path):
    log = tmp_path / "infections.jsonl"
    # Tool A: 4 events (chronic)
    for _ in range(4):
        record_infection("tool_a", "conn refused", log_path=log)
    # Tool B: 1 event (not chronic)
    record_infection("tool_b", "timeout", log_path=log)
    patterns = chronic_infections(log)
    assert len(patterns) == 1
    assert patterns[0]["tool"] == "tool_a"


def test_chronics_sorted_by_count_descending(tmp_path):
    log = tmp_path / "infections.jsonl"
    for _ in range(5):
        record_infection("tool_x", "err x", log_path=log)
    for _ in range(3):
        record_infection("tool_y", "err y", log_path=log)
    patterns = chronic_infections(log)
    assert patterns[0]["count"] >= patterns[-1]["count"]


def test_chronic_empty_when_no_log(tmp_path):
    log = tmp_path / "nope.jsonl"
    assert chronic_infections(log) == []


# ---------------------------------------------------------------------------
# infection_summary
# ---------------------------------------------------------------------------


def test_infection_summary_empty_when_no_events(tmp_path):
    log = tmp_path / "infections.jsonl"
    assert infection_summary(log) == ""


def test_infection_summary_includes_totals(tmp_path):
    log = tmp_path / "infections.jsonl"
    record_infection("t", "e", healed=True, log_path=log)
    record_infection("t", "e", healed=False, log_path=log)
    summary = infection_summary(log)
    assert "2 events" in summary
    assert "1 unhealed" in summary


def test_infection_summary_flags_chronic(tmp_path):
    log = tmp_path / "infections.jsonl"
    for _ in range(CHRONIC_THRESHOLD):
        record_infection("sick_tool", "repeated error", log_path=log)
    summary = infection_summary(log)
    assert "CHRONIC" in summary
    assert "sick_tool" in summary


def test_infection_summary_no_chronic_label_below_threshold(tmp_path):
    log = tmp_path / "infections.jsonl"
    for _ in range(CHRONIC_THRESHOLD - 1):
        record_infection("t", "e", log_path=log)
    summary = infection_summary(log)
    assert "CHRONIC" not in summary
