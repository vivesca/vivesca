from __future__ import annotations

from unittest.mock import MagicMock, patch

from metabolon.enzymes.circadian import circadian


def test_circadian_list():
    with patch("metabolon.organelles.circadian_clock.scheduled_events") as mock_scheduled:
        mock_scheduled.return_value = "Mocked events"
        result = circadian("list", date="today")
        assert result.output == "Mocked events"
        mock_scheduled.assert_called_once_with("today")


def test_circadian_set_success():
    with patch("metabolon.organelles.circadian_clock.schedule_event") as mock_schedule:
        mock_schedule.return_value = "Mock schedule result"
        result = circadian(
            "set",
            summary="Test Event",
            date="2026-04-01",
            from_time="10:00",
            to_time="11:00",
        )
        assert result.output == "Mock schedule result"
        mock_schedule.assert_called_once_with("Test Event", "2026-04-01", "10:00", duration=60)


def test_circadian_set_with_details():
    with patch("metabolon.organelles.circadian_clock.schedule_event") as mock_schedule:
        mock_schedule.return_value = "Mock schedule result"
        result = circadian(
            "set",
            summary="Test Event",
            date="2026-04-01",
            from_time="10:00",
            to_time="11:00",
            description="Test description",
            location="Test location",
        )
        assert "description ignored" in result.output
        assert "location ignored" in result.output


def test_circadian_set_missing_params():
    result = circadian("set")
    assert not result.success
    assert "requires" in result.message


def test_circadian_move():
    with patch("metabolon.organelles.circadian_clock.reschedule_event") as mock_reschedule:
        mock_reschedule.return_value = "Mock move result"
        result = circadian("move", event_id="123", date="2026-04-01", time="14:00")
        assert result.output == "Mock move result"
        mock_reschedule.assert_called_once_with("123", "2026-04-01", "14:00")


def test_circadian_delete():
    with patch("metabolon.organelles.circadian_clock.cancel_event") as mock_cancel:
        mock_cancel.return_value = "Mock delete result"
        result = circadian("delete", event_id="123")
        assert result.output == "Mock delete result"
        mock_cancel.assert_called_once_with("123")


def test_circadian_sleep():
    mock_sleep_obj = MagicMock()
    mock_sleep_obj.summary = "Mock sleep summary"
    with patch("metabolon.enzymes.interoception._sleep_result") as mock_sleep:
        mock_sleep.return_value = mock_sleep_obj
        result = circadian("sleep", period="yesterday")
        assert result.output == "Mock sleep summary"
        mock_sleep.assert_called_once_with("yesterday")


def test_circadian_heartrate():
    mock_hr_obj = MagicMock()
    mock_hr_obj.summary = "Mock heartrate summary"
    with patch("metabolon.enzymes.interoception._heartrate_result") as mock_heartrate:
        mock_heartrate.return_value = mock_hr_obj
        result = circadian(
            "heartrate", start_datetime="2026-04-01T00:00", end_datetime="2026-04-01T23:59"
        )
        assert result.output == "Mock heartrate summary"
        mock_heartrate.assert_called_once_with("2026-04-01T00:00", "2026-04-01T23:59")


def test_circadian_unknown_action():
    result = circadian("invalid")
    assert not result.success
    assert "Unknown action" in result.message
