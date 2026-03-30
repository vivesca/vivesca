from __future__ import annotations

import base64
import copy
from datetime import datetime

from metabolon.organelles import moneo


def test_parse_due_time_only() -> None:
    at, date = moneo.parse_due_string("16:15")
    assert at == "16:15"
    assert date is None


def test_parse_due_date_only() -> None:
    at, date = moneo.parse_due_string("2026-03-16")
    assert at is None
    assert date == "2026-03-16"


def test_parse_due_today_with_time() -> None:
    now = datetime(2026, 3, 16, 9, 0, tzinfo=moneo.HKT)
    at, date = moneo.parse_due_string("today 10:00")
    assert at == "10:00"
    assert date == moneo.resolve_date_keyword("today")


def test_parse_due_tomorrow_with_time() -> None:
    at, date = moneo.parse_due_string("tomorrow 09:00")
    assert at == "09:00"
    assert date == moneo.resolve_date_keyword("tomorrow")


def test_parse_due_iso_date_with_time() -> None:
    at, date = moneo.parse_due_string("2026-12-25 14:30")
    assert at == "14:30"
    assert date == "2026-12-25"


def test_parse_due_today_keyword_alone() -> None:
    at, date = moneo.parse_due_string("today")
    assert at is None
    assert date == moneo.resolve_date_keyword("today")


def test_parse_due_tomorrow_keyword_alone() -> None:
    at, date = moneo.parse_due_string("tomorrow")
    assert at is None
    assert date == moneo.resolve_date_keyword("tomorrow")


def test_resolve_date_keyword_today_case_insensitive() -> None:
    now = datetime(2026, 3, 16, 9, 0, tzinfo=moneo.HKT)
    today = "2026-03-16"
    assert moneo.resolve_date_keyword("today", now=now) == today
    assert moneo.resolve_date_keyword("Today", now=now) == today
    assert moneo.resolve_date_keyword("TODAY", now=now) == today


def test_resolve_date_keyword_passthrough() -> None:
    assert moneo.resolve_date_keyword("2026-03-16") == "2026-03-16"


def test_parse_time_with_date_defaults_to_0900() -> None:
    now = datetime(2026, 3, 16, 8, 0, tzinfo=moneo.HKT)
    ts = moneo.parse_time(None, None, "2026-03-20", now=now)
    assert moneo.hkt_from_ts(ts) == datetime(2026, 3, 20, 9, 0, tzinfo=moneo.HKT)


def test_expand_schedule_skips_night_by_default() -> None:
    base = int(datetime(2026, 3, 16, 9, 0, tzinfo=moneo.HKT).timestamp())
    expanded = moneo.expand_schedule(base, moneo.parse_interval("6h"), "2026-03-17")
    formatted = [moneo.hkt_from_ts(ts).strftime("%Y-%m-%d %H:%M") for ts in expanded]
    assert formatted == [
        "2026-03-16 09:00",
        "2026-03-16 15:00",
        "2026-03-16 21:00",
        "2026-03-17 09:00",
        "2026-03-17 15:00",
        "2026-03-17 21:00",
    ]


def test_expand_schedule_can_include_night() -> None:
    base = int(datetime(2026, 3, 16, 9, 0, tzinfo=moneo.HKT).timestamp())
    expanded = moneo.expand_schedule(
        base,
        moneo.parse_interval("6h"),
        "2026-03-17",
        skip_night=False,
    )
    formatted = [moneo.hkt_from_ts(ts).strftime("%Y-%m-%d %H:%M") for ts in expanded]
    assert formatted == [
        "2026-03-16 09:00",
        "2026-03-16 15:00",
        "2026-03-16 21:00",
        "2026-03-17 03:00",
        "2026-03-17 09:00",
        "2026-03-17 15:00",
        "2026-03-17 21:00",
    ]


# --- recur_code ---


def test_recur_code_all_frequencies() -> None:
    assert moneo.recur_code("daily") == "d"
    assert moneo.recur_code("weekly") == "w"
    assert moneo.recur_code("monthly") == "m"
    assert moneo.recur_code("quarterly") == "q"
    assert moneo.recur_code("yearly") == "y"


def test_recur_code_unknown_returns_none() -> None:
    assert moneo.recur_code("hourly") is None
    assert moneo.recur_code("") is None


# --- generate_uuid ---


def test_generate_uuid_format() -> None:
    uid = moneo.generate_uuid()
    assert isinstance(uid, str)
    assert len(uid) == 22  # base64url of 16 bytes, no padding
    assert "=" not in uid
    # Should decode back to 16 bytes
    raw = base64.urlsafe_b64decode(uid + "==")
    assert len(raw) == 16


def test_generate_uuid_uniqueness() -> None:
    uuids = {moneo.generate_uuid() for _ in range(100)}
    assert len(uuids) == 100


# --- make_reminder ---


def test_make_reminder_basic() -> None:
    ts = int(datetime(2026, 3, 20, 10, 0, tzinfo=moneo.HKT).timestamp())
    reminder = moneo.make_reminder("Test reminder", ts, None, None)
    assert reminder["n"] == "Test reminder"
    assert reminder["d"] == ts
    assert reminder["si"] == 300  # default 5 min autosnooze
    assert "u" in reminder
    assert len(reminder["u"]) == 22
    assert "b" in reminder  # created timestamp
    assert "m" in reminder  # modified timestamp
    assert "rf" not in reminder  # no recurrence


def test_make_reminder_with_autosnooze() -> None:
    ts = int(datetime(2026, 3, 20, 10, 0, tzinfo=moneo.HKT).timestamp())
    reminder = moneo.make_reminder("Test", ts, None, 15)
    assert reminder["si"] == 900  # 15 * 60


def test_make_reminder_daily_recurrence() -> None:
    ts = int(datetime(2026, 3, 20, 10, 0, tzinfo=moneo.HKT).timestamp())
    reminder = moneo.make_reminder("Daily", ts, "daily", None)
    assert reminder["rf"] == "d"
    assert reminder["rd"] == ts
    assert reminder["rn"] == 16  # daily unit


def test_make_reminder_weekly_recurrence() -> None:
    ts = int(datetime(2026, 3, 20, 10, 0, tzinfo=moneo.HKT).timestamp())
    reminder = moneo.make_reminder("Weekly", ts, "weekly", None)
    assert reminder["rf"] == "w"
    assert reminder["rd"] == ts
    assert reminder["rn"] == 256  # weekly unit
    assert "rb" in reminder  # weekday byday


def test_make_reminder_quarterly_recurrence() -> None:
    ts = int(datetime(2026, 3, 20, 10, 0, tzinfo=moneo.HKT).timestamp())
    reminder = moneo.make_reminder("Quarterly", ts, "quarterly", None)
    assert reminder["rf"] == "q"
    assert reminder["ru"] == {"i": 3}  # interval 3 months


# --- add_direct ---


def _empty_db() -> dict:
    return {"re": [], "mt": {"ts": 0}, "dl": {}}


def test_add_direct_appends_to_data() -> None:
    data = _empty_db()
    uid = moneo.add_direct("Test", 1000000, None, None, data)
    assert len(data["re"]) == 1
    assert data["re"][0]["u"] == uid
    assert data["re"][0]["n"] == "Test"


def test_add_direct_multiple() -> None:
    data = _empty_db()
    moneo.add_direct("First", 1000000, None, None, data)
    moneo.add_direct("Second", 2000000, None, None, data)
    assert len(data["re"]) == 2
    titles = {r["n"] for r in data["re"]}
    assert titles == {"First", "Second"}


def test_add_direct_preserves_existing() -> None:
    data = _empty_db()
    data["re"].append({"u": "existing123456789012", "n": "Existing", "d": 500000})
    moneo.add_direct("New", 1000000, None, None, data)
    assert len(data["re"]) == 2
    assert data["re"][0]["n"] == "Existing"
    assert data["re"][1]["n"] == "New"


# --- find_duplicate ---


def test_find_duplicate_detects_same_title_and_time() -> None:
    ts = int(datetime(2026, 3, 20, 10, 0, tzinfo=moneo.HKT).timestamp())
    data = _empty_db()
    data["re"].append({"u": "abc", "n": "Med reminder", "d": ts})
    result = moneo.find_duplicate("Med reminder", ts, data)
    assert result is not None


def test_find_duplicate_case_insensitive() -> None:
    ts = int(datetime(2026, 3, 20, 10, 0, tzinfo=moneo.HKT).timestamp())
    data = _empty_db()
    data["re"].append({"u": "abc", "n": "Med Reminder", "d": ts})
    result = moneo.find_duplicate("med reminder", ts, data)
    assert result is not None


def test_find_duplicate_different_time_no_match() -> None:
    ts1 = int(datetime(2026, 3, 20, 10, 0, tzinfo=moneo.HKT).timestamp())
    ts2 = int(datetime(2026, 3, 20, 14, 0, tzinfo=moneo.HKT).timestamp())
    data = _empty_db()
    data["re"].append({"u": "abc", "n": "Med reminder", "d": ts1})
    result = moneo.find_duplicate("Med reminder", ts2, data)
    assert result is None


def test_find_duplicate_different_title_no_match() -> None:
    ts = int(datetime(2026, 3, 20, 10, 0, tzinfo=moneo.HKT).timestamp())
    data = _empty_db()
    data["re"].append({"u": "abc", "n": "Med reminder", "d": ts})
    result = moneo.find_duplicate("Different", ts, data)
    assert result is None


# --- short_uuid ---


def test_short_uuid_returns_first_8_chars() -> None:
    assert moneo.short_uuid("abcdefghij1234567890XY") == "abcdefgh"


def test_short_uuid_none_returns_dashes() -> None:
    assert moneo.short_uuid(None) == "--------"


def test_short_uuid_short_input() -> None:
    assert moneo.short_uuid("abc") == "abc"


# --- is_uuid_prefix ---


def test_is_uuid_prefix_valid_8_chars() -> None:
    uid = moneo.generate_uuid()
    assert moneo.is_uuid_prefix(uid[:8])


def test_is_uuid_prefix_valid_full_uuid() -> None:
    uid = moneo.generate_uuid()
    assert moneo.is_uuid_prefix(uid)


def test_is_uuid_prefix_too_short() -> None:
    assert not moneo.is_uuid_prefix("abcde")  # 5 chars


def test_is_uuid_prefix_too_long() -> None:
    assert not moneo.is_uuid_prefix("a" * 23)


def test_is_uuid_prefix_with_spaces() -> None:
    assert not moneo.is_uuid_prefix("abc def gh")


def test_is_uuid_prefix_with_special_chars() -> None:
    assert not moneo.is_uuid_prefix("abc!@#gh")


def test_is_uuid_prefix_base64url_chars() -> None:
    # base64url includes A-Z, a-z, 0-9, -, _
    assert moneo.is_uuid_prefix("Ab0-_X")


# --- is_numeric ---


def test_is_numeric_positive_int() -> None:
    assert moneo.is_numeric("1")
    assert moneo.is_numeric("42")


def test_is_numeric_zero_is_false() -> None:
    assert not moneo.is_numeric("0")


def test_is_numeric_negative_is_false() -> None:
    assert not moneo.is_numeric("-1")


def test_is_numeric_non_number() -> None:
    assert not moneo.is_numeric("abc")
    assert not moneo.is_numeric("1a")


# --- find_by_uuid_prefix ---


def test_find_by_uuid_prefix_exact_match() -> None:
    data = _empty_db()
    data["re"].append({"u": "ABCDEF12345678901234", "n": "Test", "d": 1000})
    matches = moneo.find_by_uuid_prefix(data, "ABCDEF")
    assert len(matches) == 1
    assert matches[0]["n"] == "Test"


def test_find_by_uuid_prefix_no_match() -> None:
    data = _empty_db()
    data["re"].append({"u": "ABCDEF12345678901234", "n": "Test", "d": 1000})
    matches = moneo.find_by_uuid_prefix(data, "ZZZZZ1")
    assert len(matches) == 0


def test_find_by_uuid_prefix_multiple_matches() -> None:
    data = _empty_db()
    data["re"].append({"u": "ABCDEF1234_first____", "n": "First", "d": 1000})
    data["re"].append({"u": "ABCDEF5678_second___", "n": "Second", "d": 2000})
    data["re"].append({"u": "XYZ12345678_third___", "n": "Third", "d": 3000})
    matches = moneo.find_by_uuid_prefix(data, "ABCDEF")
    assert len(matches) == 2
    titles = {m["n"] for m in matches}
    assert titles == {"First", "Second"}


# --- resolve_target ---


def _db_with_reminders() -> dict:
    """Create a test DB with 3 reminders, sorted by due timestamp."""
    data = _empty_db()
    data["re"] = [
        {"u": "AAAAAAaaaaaabbbbbb", "n": "Buy milk", "d": 1000},
        {"u": "BBBBBBccccccdddddd", "n": "Call dentist", "d": 2000},
        {"u": "CCCCCCeeeeeeffffff", "n": "Read book", "d": 3000},
    ]
    return data


def test_resolve_target_by_numeric_index() -> None:
    data = _db_with_reminders()
    matches, needs_confirm = moneo.resolve_target(data, "1")
    assert needs_confirm is True
    assert len(matches) == 1
    assert matches[0][1]["n"] == "Buy milk"


def test_resolve_target_by_uuid_prefix() -> None:
    data = _db_with_reminders()
    matches, needs_confirm = moneo.resolve_target(data, "BBBBBBcc")
    assert needs_confirm is False
    assert len(matches) == 1
    assert matches[0][1]["n"] == "Call dentist"


def test_resolve_target_by_pattern() -> None:
    data = _db_with_reminders()
    matches, needs_confirm = moneo.resolve_target(data, "milk", allow_pattern=True)
    assert needs_confirm is False
    assert len(matches) == 1
    assert matches[0][1]["n"] == "Buy milk"


def test_resolve_target_pattern_case_insensitive() -> None:
    data = _db_with_reminders()
    matches, needs_confirm = moneo.resolve_target(data, "MILK", allow_pattern=True)
    assert needs_confirm is False
    assert len(matches) == 1
    assert matches[0][1]["n"] == "Buy milk"


def test_resolve_target_pattern_not_found() -> None:
    data = _db_with_reminders()
    try:
        moneo.resolve_target(data, "nonexistent", allow_pattern=True)
        assert False, "Should have raised"
    except moneo.MoneoError as exc:
        assert "No reminders matching" in str(exc)


def test_resolve_target_uuid_prefix_not_found() -> None:
    data = _db_with_reminders()
    try:
        moneo.resolve_target(data, "ZZZZZZ")
        assert False, "Should have raised"
    except moneo.MoneoError as exc:
        assert "No reminders" in str(exc)


def test_resolve_target_numeric_out_of_range() -> None:
    data = _db_with_reminders()
    try:
        moneo.resolve_target(data, "99")
        assert False, "Should have raised"
    except moneo.MoneoError as exc:
        assert "no reminder at index" in str(exc)


def test_resolve_target_prefers_numeric_over_uuid() -> None:
    """A string like '123456' should be treated as numeric index, not UUID prefix."""
    data = _empty_db()
    # Add enough reminders so index 123456 would be out of range
    data["re"].append({"u": "123456abcdef012345", "n": "Test", "d": 1000})
    # Numeric should be tried first and fail with out-of-range
    try:
        moneo.resolve_target(data, "123456")
        assert False, "Should have raised"
    except moneo.MoneoError as exc:
        assert "no reminder at index" in str(exc)


# --- confirm_action (unit-testable parts) ---


def test_confirm_action_eof_returns_false() -> None:
    """When input() raises EOFError (piped stdin), confirm returns False."""
    import io
    import sys

    data = _db_with_reminders()
    reminder = data["re"][0]
    old_stdin = sys.stdin
    sys.stdin = io.StringIO("")  # empty = EOF on first read
    try:
        result = moneo.confirm_action(reminder, "Delete")
        assert result is False
    finally:
        sys.stdin = old_stdin


def test_confirm_action_yes() -> None:
    import io
    import sys

    data = _db_with_reminders()
    reminder = data["re"][0]
    old_stdin = sys.stdin
    sys.stdin = io.StringIO("y\n")
    try:
        result = moneo.confirm_action(reminder, "Delete")
        assert result is True
    finally:
        sys.stdin = old_stdin


def test_confirm_action_no() -> None:
    import io
    import sys

    data = _db_with_reminders()
    reminder = data["re"][0]
    old_stdin = sys.stdin
    sys.stdin = io.StringIO("n\n")
    try:
        result = moneo.confirm_action(reminder, "Delete")
        assert result is False
    finally:
        sys.stdin = old_stdin


def test_confirm_action_empty_is_no() -> None:
    import io
    import sys

    data = _db_with_reminders()
    reminder = data["re"][0]
    old_stdin = sys.stdin
    sys.stdin = io.StringIO("\n")
    try:
        result = moneo.confirm_action(reminder, "Delete")
        assert result is False
    finally:
        sys.stdin = old_stdin



