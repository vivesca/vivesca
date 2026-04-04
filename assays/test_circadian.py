"""Tests for metabolon.enzymes.circadian."""

from unittest.mock import MagicMock, patch

from metabolon.enzymes.circadian import CircadianResult, circadian
from metabolon.morphology import EffectorResult


class TestCircadianList:
    """Tests for circadian(action='list')."""

    @patch("metabolon.organelles.circadian_clock.scheduled_events")
    def test_list_returns_events(self, mock_scheduled: MagicMock) -> None:
        mock_scheduled.return_value = "10:00 Meeting\n12:00 Lunch"
        result = circadian(action="list", date="today")
        assert isinstance(result, CircadianResult)
        assert "Meeting" in result.output
        mock_scheduled.assert_called_once_with("today")

    @patch("metabolon.organelles.circadian_clock.scheduled_events")
    def test_list_with_custom_date(self, mock_scheduled: MagicMock) -> None:
        mock_scheduled.return_value = "No events"
        result = circadian(action="list", date="2024-01-15")
        assert isinstance(result, CircadianResult)
        mock_scheduled.assert_called_once_with("2024-01-15")


class TestCircadianSet:
    """Tests for circadian(action='set')."""

    @patch("metabolon.organelles.circadian_clock.schedule_event")
    def test_set_creates_event(self, mock_schedule: MagicMock) -> None:
        mock_schedule.return_value = "Created event #123"
        result = circadian(
            action="set",
            summary="Team sync",
            date="2024-01-15",
            from_time="10:00",
            to_time="11:00",
        )
        assert isinstance(result, CircadianResult)
        assert "Created event" in result.output
        mock_schedule.assert_called_once_with("Team sync", "2024-01-15", "10:00", duration=60)

    @patch("metabolon.organelles.circadian_clock.schedule_event")
    def test_set_calculates_duration(self, mock_schedule: MagicMock) -> None:
        mock_schedule.return_value = "Created"
        circadian(
            action="set",
            summary="Long meeting",
            date="2024-01-15",
            from_time="09:00",
            to_time="12:30",
        )
        # 9:00 to 12:30 = 3.5 hours = 210 minutes
        mock_schedule.assert_called_once_with("Long meeting", "2024-01-15", "09:00", duration=210)

    @patch("metabolon.organelles.circadian_clock.schedule_event")
    def test_set_ignores_description_and_location(self, mock_schedule: MagicMock) -> None:
        mock_schedule.return_value = "Created"
        result = circadian(
            action="set",
            summary="Event",
            date="2024-01-15",
            from_time="10:00",
            to_time="11:00",
            description="This is ignored",
            location="Conference room",
        )
        assert "description ignored" in result.output
        assert "location ignored" in result.output

    def test_set_missing_params_returns_error(self) -> None:
        result = circadian(action="set", summary="Test")
        assert isinstance(result, EffectorResult)
        assert result.success is False
        assert "set requires" in result.message


class TestCircadianMove:
    """Tests for circadian(action='move')."""

    @patch("metabolon.organelles.circadian_clock.reschedule_event")
    def test_move_reschedules_event(self, mock_reschedule: MagicMock) -> None:
        mock_reschedule.return_value = "Event moved"
        result = circadian(
            action="move",
            event_id="evt123",
            date="2024-01-20",
            time="14:00",
        )
        assert isinstance(result, CircadianResult)
        assert "moved" in result.output
        mock_reschedule.assert_called_once_with("evt123", "2024-01-20", "14:00")

    def test_move_missing_params_returns_error(self) -> None:
        result = circadian(action="move", event_id="evt123")
        assert isinstance(result, EffectorResult)
        assert result.success is False
        assert "move requires" in result.message


class TestCircadianDelete:
    """Tests for circadian(action='delete')."""

    @patch("metabolon.organelles.circadian_clock.cancel_event")
    def test_delete_cancels_event(self, mock_cancel: MagicMock) -> None:
        mock_cancel.return_value = "Event deleted"
        result = circadian(action="delete", event_id="evt456")
        assert isinstance(result, CircadianResult)
        assert "deleted" in result.output
        mock_cancel.assert_called_once_with("evt456")

    def test_delete_missing_event_id_returns_error(self) -> None:
        result = circadian(action="delete")
        assert isinstance(result, EffectorResult)
        assert result.success is False
        assert "delete requires" in result.message


class TestCircadianSleep:
    """Tests for circadian(action='sleep')."""

    @patch("metabolon.enzymes.interoception._sleep_result")
    def test_sleep_returns_sleep_data(self, mock_sleep: MagicMock) -> None:
        mock_result = MagicMock()
        mock_result.summary = "Sleep score: 85"
        mock_sleep.return_value = mock_result

        result = circadian(action="sleep", period="today")
        assert isinstance(result, CircadianResult)
        assert "Sleep score" in result.output
        mock_sleep.assert_called_once_with("today")

    @patch("metabolon.enzymes.interoception._sleep_result")
    def test_sleep_with_week_period(self, mock_sleep: MagicMock) -> None:
        mock_result = MagicMock()
        mock_result.summary = "Weekly sleep data"
        mock_sleep.return_value = mock_result

        circadian(action="sleep", period="week")
        mock_sleep.assert_called_once_with("week")


class TestCircadianHeartrate:
    """Tests for circadian(action='heartrate')."""

    @patch("metabolon.enzymes.interoception._heartrate_result")
    def test_heartrate_returns_data(self, mock_hr: MagicMock) -> None:
        mock_result = MagicMock()
        mock_result.summary = "Avg HR: 72 bpm"
        mock_hr.return_value = mock_result

        result = circadian(
            action="heartrate",
            start_datetime="2024-01-15T00:00:00",
            end_datetime="2024-01-15T23:59:59",
        )
        assert isinstance(result, CircadianResult)
        assert "HR" in result.output
        mock_hr.assert_called_once_with("2024-01-15T00:00:00", "2024-01-15T23:59:59")

    @patch("metabolon.enzymes.interoception._heartrate_result")
    def test_heartrate_with_defaults(self, mock_hr: MagicMock) -> None:
        mock_result = MagicMock()
        mock_result.summary = "HR data"
        mock_hr.return_value = mock_result

        circadian(action="heartrate")
        mock_hr.assert_called_once_with("", "")


class TestCircadianUnknownAction:
    """Tests for unknown actions."""

    def test_unknown_action_returns_error(self) -> None:
        result = circadian(action="invalid")
        assert isinstance(result, EffectorResult)
        assert result.success is False
        assert "Unknown action" in result.message

    def test_action_is_case_insensitive(self) -> None:
        with patch("metabolon.organelles.circadian_clock.scheduled_events") as mock:
            mock.return_value = "Events"
            circadian(action="LIST")
            mock.assert_called_once()
