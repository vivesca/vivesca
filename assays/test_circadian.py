"""Tests for the circadian module."""
import pytest
from unittest.mock import patch, MagicMock

from metabolon.enzymes.circadian import circadian, CircadianResult
from metabolon.morphology import EffectorResult


class TestCircadianActions:
    """Test all action types for the circadian function."""

    def test_unknown_action_returns_error(self):
        """Test that unknown action returns error result."""
        result = circadian(action="invalid_action")
        assert isinstance(result, EffectorResult)
        assert not result.success
        assert "Unknown action" in result.message
        assert "list, set, move, delete, sleep, heartrate" in result.message

    def test_list_action_calls_scheduled_events(self):
        """Test that list action correctly calls scheduled_events."""
        mock_output = "Event 1\nEvent 2"
        
        with patch("metabolon.organelles.circadian_clock.scheduled_events", return_value=mock_output) as mock_scheduled:
            result = circadian(action="list", date="2026-04-01")
            
            assert isinstance(result, CircadianResult)
            assert result.output == mock_output
            mock_scheduled.assert_called_once_with("2026-04-01")

    def test_list_action_default_date_is_today(self):
        """Test that list action uses 'today' as default date."""
        mock_output = "Events for today"
        
        with patch("metabolon.organelles.circadian_clock.scheduled_events", return_value=mock_output) as mock_scheduled:
            result = circadian(action="list")
            
            assert isinstance(result, CircadianResult)
            mock_scheduled.assert_called_once_with("today")

    # Tests for set action
    def test_set_action_missing_parameters_returns_error(self):
        """Test that set action with missing parameters returns error."""
        # Missing all required parameters
        result = circadian(action="set")
        assert isinstance(result, EffectorResult)
        assert not result.success
        assert "set requires: summary, date, from_time, to_time" in result.message
        
        # Missing some parameters
        result = circadian(action="set", summary="Meeting", date="today")
        assert isinstance(result, EffectorResult)
        assert not result.success

    def test_set_action_calculates_duration_correctly(self):
        """Test that duration is calculated correctly from from_time and to_time."""
        mock_result = "Event scheduled successfully"
        
        with patch("metabolon.organelles.circadian_clock.schedule_event", return_value=mock_result) as mock_schedule:
            result = circadian(
                action="set",
                summary="Team Meeting",
                date="2026-04-01",
                from_time="10:00",
                to_time="11:30"
            )
            
            assert isinstance(result, CircadianResult)
            mock_schedule.assert_called_once_with("Team Meeting", "2026-04-01", "10:00", duration=90)
            assert result.output == mock_result

    def test_set_action_handles_invalid_time_format(self):
        """Test that invalid time format defaults to 60 minutes duration."""
        mock_result = "Event scheduled"
        
        with patch("metabolon.organelles.circadian_clock.schedule_event", return_value=mock_result) as mock_schedule:
            result = circadian(
                action="set",
                summary="Meeting",
                date="today",
                from_time="invalid",
                to_time="11:00"
            )
            
            assert isinstance(result, CircadianResult)
            mock_schedule.assert_called_once_with("Meeting", "today", "invalid", duration=60)

    def test_set_action_handles_negative_duration(self):
        """Test that negative duration defaults to 60 minutes."""
        mock_result = "Event scheduled"
        
        with patch("metabolon.organelles.circadian_clock.schedule_event", return_value=mock_result) as mock_schedule:
            result = circadian(
                action="set",
                summary="Meeting",
                date="today",
                from_time="14:00",
                to_time="13:00"
            )
            
            assert isinstance(result, CircadianResult)
            mock_schedule.assert_called_once_with("Meeting", "today", "14:00", duration=60)

    def test_set_action_includes_description_and_location_note(self):
        """Test that notes about ignored description and location are included."""
        mock_result = "Scheduled"
        
        with patch("metabolon.organelles.circadian_clock.schedule_event", return_value=mock_result) as mock_schedule:
            result = circadian(
                action="set",
                summary="Meeting",
                date="today",
                from_time="10:00",
                to_time="11:00",
                description="Quarterly review",
                location="Conference Room A"
            )
            
            assert isinstance(result, CircadianResult)
            assert "description ignored by circadian_clock: Quarterly review" in result.output
            assert "location ignored by circadian_clock: Conference Room A" in result.output
            assert "Scheduled" in result.output

    def test_set_action_successful_without_optional_fields(self):
        """Test successful set action without optional description and location."""
        mock_result = "Event created: 12345"
        
        with patch("metabolon.organelles.circadian_clock.schedule_event", return_value=mock_result) as mock_schedule:
            result = circadian(
                action="set",
                summary="Simple Event",
                date="2026-04-01",
                from_time="09:00",
                to_time="10:00"
            )
            
            assert isinstance(result, CircadianResult)
            assert result.output == mock_result
            mock_schedule.assert_called_once_with("Simple Event", "2026-04-01", "09:00", duration=60)

    # Tests for move action
    def test_move_action_missing_parameters_returns_error(self):
        """Test that move with missing parameters returns error."""
        result = circadian(action="move")
        assert isinstance(result, EffectorResult)
        assert not result.success
        assert "move requires: event_id, date, time" in result.message

    def test_move_action_calls_reschedule_event(self):
        """Test that move action correctly calls reschedule_event."""
        mock_output = "Event moved successfully"
        
        with patch("metabolon.organelles.circadian_clock.reschedule_event", return_value=mock_output) as mock_reschedule:
            result = circadian(
                action="move",
                event_id="event_123",
                date="2026-04-02",
                time="14:30"
            )
            
            assert isinstance(result, CircadianResult)
            assert result.output == mock_output
            mock_reschedule.assert_called_once_with("event_123", "2026-04-02", "14:30")

    # Tests for delete action
    def test_delete_action_missing_event_id_returns_error(self):
        """Test that delete without event_id returns error."""
        result = circadian(action="delete")
        assert isinstance(result, EffectorResult)
        assert not result.success
        assert "delete requires: event_id" in result.message

    def test_delete_action_calls_cancel_event(self):
        """Test that delete action correctly calls cancel_event."""
        mock_output = "Event canceled"
        
        with patch("metabolon.organelles.circadian_clock.cancel_event", return_value=mock_output) as mock_cancel:
            result = circadian(action="delete", event_id="event_123")
            
            assert isinstance(result, CircadianResult)
            assert result.output == mock_output
            mock_cancel.assert_called_once_with("event_123")

    # Tests for sleep action
    def test_sleep_action_calls__sleep_result(self):
        """Test that sleep action correctly calls _sleep_result."""
        mock_summary = MagicMock()
        mock_summary.summary = "Sleep data for the period"
        
        with patch("metabolon.enzymes.interoception._sleep_result", return_value=mock_summary) as mock_sleep:
            result = circadian(action="sleep", period="week")
            
            assert isinstance(result, CircadianResult)
            assert result.output == "Sleep data for the period"
            mock_sleep.assert_called_once_with("week")

    def test_sleep_action_default_period_is_today(self):
        """Test that sleep action uses 'today' as default period."""
        mock_summary = MagicMock()
        mock_summary.summary = "Today's sleep data"
        
        with patch("metabolon.enzymes.interoception._sleep_result", return_value=mock_summary) as mock_sleep:
            result = circadian(action="sleep")
            
            assert isinstance(result, CircadianResult)
            mock_sleep.assert_called_once_with("today")

    # Tests for heartrate action
    def test_heartrate_action_calls__heartrate_result(self):
        """Test that heartrate action correctly calls _heartrate_result."""
        mock_summary = MagicMock()
        mock_summary.summary = "Heart rate: average 65 bpm"
        
        with patch("metabolon.enzymes.interoception._heartrate_result", return_value=mock_summary) as mock_hr:
            result = circadian(
                action="heartrate",
                start_datetime="2026-03-31T00:00:00",
                end_datetime="2026-03-31T23:59:59"
            )
            
            assert isinstance(result, CircadianResult)
            assert result.output == "Heart rate: average 65 bpm"
            mock_hr.assert_called_once_with("2026-03-31T00:00:00", "2026-03-31T23:59:59")

    def test_heartrate_action_accepts_empty_datetimes(self):
        """Test that heartrate action accepts empty start/end datetimes."""
        mock_summary = MagicMock()
        mock_summary.summary = "All-time heart rate data"
        
        with patch("metabolon.enzymes.interoception._heartrate_result", return_value=mock_summary) as mock_hr:
            result = circadian(action="heartrate")
            
            assert isinstance(result, CircadianResult)
            mock_hr.assert_called_once_with("", "")

    def test_action_case_insensitive(self):
        """Test that action is case-insensitive and stripped."""
        mock_output = "Events listed"
        
        with patch("metabolon.organelles.circadian_clock.scheduled_events", return_value=mock_output) as mock_scheduled:
            result = circadian(action="LIST")
            assert isinstance(result, CircadianResult)
            mock_scheduled.assert_called_once()
            
        with patch("metabolon.organelles.circadian_clock.scheduled_events", return_value=mock_output) as mock_scheduled:
            result = circadian(action="List")
            assert isinstance(result, CircadianResult)
            mock_scheduled.assert_called_once()
            
        with patch("metabolon.organelles.circadian_clock.scheduled_events", return_value=mock_output) as mock_scheduled:
            result = circadian(action="  list  ")
            assert isinstance(result, CircadianResult)
            mock_scheduled.assert_called_once()
