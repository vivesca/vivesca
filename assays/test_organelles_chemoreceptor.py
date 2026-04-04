from __future__ import annotations

"""Tests for chemoreceptor public API: _fetch, _fetch_datetime, today, readiness,
sleep_score, sleep_detail, heartrate, week, _fetch_daily, sense."""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers / constants
# ---------------------------------------------------------------------------

MOD = "metabolon.organelles.chemoreceptor"
TOKEN = "fake-oura-token"
TODAY = str(date.today())
YESTERDAY = str(date.today() - timedelta(days=1))


def _mock_response(data=None, status_code=200):
    """Build a fake httpx response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = {"data": data or []}
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        import httpx

        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "err", request=MagicMock(), response=resp
        )
    return resp


def _patch_token():
    return patch.dict("os.environ", {"OURA_TOKEN": TOKEN})


# ---------------------------------------------------------------------------
# _fetch
# ---------------------------------------------------------------------------


class TestFetch:
    @_patch_token()
    def test_fetch_basic(self):
        from metabolon.organelles.chemoreceptor import _fetch

        mock_resp = _mock_response([{"score": 85, "day": TODAY}])
        with patch(f"{MOD}.httpx.Client") as MockClient:
            client_inst = MagicMock()
            client_inst.get.return_value = mock_resp
            MockClient.return_value.__enter__ = lambda s: client_inst
            MockClient.return_value.__exit__ = MagicMock(return_value=False)
            result = _fetch("daily_sleep", TODAY, TODAY)

        assert result == [{"score": 85, "day": TODAY}]
        client_inst.get.assert_called_once()
        call_args = client_inst.get.call_args
        assert call_args[0][0] == "/daily_sleep"
        params = call_args[1]["params"]
        assert params["start_date"] == TODAY
        # end_date is bumped by 1 day
        expected_end = str(date.fromisoformat(TODAY) + timedelta(days=1))
        assert params["end_date"] == expected_end

    def test_fetch_with_explicit_token(self):
        from metabolon.organelles.chemoreceptor import _fetch

        mock_resp = _mock_response([{"score": 90}])
        with patch(f"{MOD}.httpx.Client") as MockClient:
            client_inst = MagicMock()
            client_inst.get.return_value = mock_resp
            MockClient.return_value.__enter__ = lambda s: client_inst
            MockClient.return_value.__exit__ = MagicMock(return_value=False)
            result = _fetch("daily_sleep", TODAY, TODAY, token="explicit")

        assert result == [{"score": 90}]
        # Check Authorization header uses the explicit token
        call_kwargs = MockClient.call_args
        headers = (
            call_kwargs[1]["headers"]
            if "headers" in call_kwargs[1]
            else call_kwargs[0][0]
            if call_kwargs[0]
            else {}
        )
        assert headers["Authorization"] == "Bearer explicit"

    def test_fetch_empty_data(self):
        from metabolon.organelles.chemoreceptor import _fetch

        mock_resp = _mock_response([])
        with patch(f"{MOD}.httpx.Client") as MockClient:
            client_inst = MagicMock()
            client_inst.get.return_value = mock_resp
            MockClient.return_value.__enter__ = lambda s: client_inst
            MockClient.return_value.__exit__ = MagicMock(return_value=False)
            result = _fetch("daily_sleep", TODAY, TODAY, token="t")

        assert result == []

    def test_fetch_no_token_raises(self):
        from metabolon.organelles.chemoreceptor import _fetch

        with (
            patch.dict("os.environ", {}, clear=True),
            patch(f"{MOD}._keychain_token", return_value=None),
        ):
            with pytest.raises(RuntimeError, match="OURA_TOKEN"):
                _fetch("daily_sleep", TODAY, TODAY)

    def test_fetch_http_error_propagates(self):
        import httpx

        from metabolon.organelles.chemoreceptor import _fetch

        mock_resp = _mock_response(status_code=500)
        with patch(f"{MOD}.httpx.Client") as MockClient:
            client_inst = MagicMock()
            client_inst.get.return_value = mock_resp
            MockClient.return_value.__enter__ = lambda s: client_inst
            MockClient.return_value.__exit__ = MagicMock(return_value=False)
            with pytest.raises(httpx.HTTPStatusError):
                _fetch("daily_sleep", TODAY, TODAY, token="t")


# ---------------------------------------------------------------------------
# _fetch_datetime
# ---------------------------------------------------------------------------


class TestFetchDatetime:
    def test_fetch_datetime_basic(self):
        from metabolon.organelles.chemoreceptor import _fetch_datetime

        data = [{"bpm": 62, "timestamp": "2026-03-27T23:05:00+08:00"}]
        mock_resp = _mock_response(data)
        with patch(f"{MOD}.httpx.Client") as MockClient:
            client_inst = MagicMock()
            client_inst.get.return_value = mock_resp
            MockClient.return_value.__enter__ = lambda s: client_inst
            MockClient.return_value.__exit__ = MagicMock(return_value=False)
            result = _fetch_datetime(
                "heartrate",
                "2026-03-27T22:00:00+08:00",
                "2026-03-28T06:00:00+08:00",
                token="t",
            )

        assert result == data
        call_args = client_inst.get.call_args
        params = call_args[1]["params"]
        assert params["start_datetime"] == "2026-03-27T22:00:00+08:00"
        assert params["end_datetime"] == "2026-03-28T06:00:00+08:00"

    def test_fetch_datetime_no_token_raises(self):
        from metabolon.organelles.chemoreceptor import _fetch_datetime

        with (
            patch.dict("os.environ", {}, clear=True),
            patch(f"{MOD}._keychain_token", return_value=None),
        ):
            with pytest.raises(RuntimeError):
                _fetch_datetime("heartrate", "s", "e")


# ---------------------------------------------------------------------------
# today()
# ---------------------------------------------------------------------------


class TestToday:
    @_patch_token()
    def test_today_with_data(self):
        from metabolon.organelles.chemoreceptor import today

        with patch(f"{MOD}._fetch") as mock_fetch:
            mock_fetch.side_effect = [
                [{"score": 85, "contributors": {"deep_sleep": 90}}],
                [
                    {
                        "score": 92,
                        "contributors": {"activity_balance": 88},
                        "temperature_deviation": 0.1,
                        "temperature_trend_deviation": -0.05,
                    }
                ],
            ]
            result = today("2026-03-25")

        assert result["date"] == "2026-03-25"
        assert result["sleep_score"] == 85
        assert result["readiness_score"] == 92
        assert result["sleep_contributors"] == {"deep_sleep": 90}
        assert result["contributors"] == {"activity_balance": 88}
        assert result["temperature_deviation"] == 0.1
        assert result["temperature_trend_deviation"] == -0.05

    @_patch_token()
    def test_today_no_data(self):
        from metabolon.organelles.chemoreceptor import today

        with patch(f"{MOD}._fetch") as mock_fetch:
            mock_fetch.side_effect = [[], []]
            result = today("2026-03-25")

        assert result == {"date": "2026-03-25"}

    @_patch_token()
    def test_today_sleep_only(self):
        from metabolon.organelles.chemoreceptor import today

        with patch(f"{MOD}._fetch") as mock_fetch:
            mock_fetch.side_effect = [
                [{"score": 80, "contributors": {}}],
                [],
            ]
            result = today("2026-03-25")

        assert result["sleep_score"] == 80
        assert "readiness_score" not in result

    @_patch_token()
    def test_today_defaults_to_today(self):
        from metabolon.organelles.chemoreceptor import today

        with (
            patch(f"{MOD}._fetch") as mock_fetch,
            patch(f"{MOD}._today_date", return_value="2026-04-01"),
        ):
            mock_fetch.side_effect = [[], []]
            today()

        mock_fetch.assert_any_call("daily_sleep", "2026-04-01", "2026-04-01", TOKEN)


# ---------------------------------------------------------------------------
# readiness()
# ---------------------------------------------------------------------------


class TestReadiness:
    def test_readiness_with_data(self):
        from metabolon.organelles.chemoreceptor import readiness

        with patch(f"{MOD}._fetch") as mock_fetch:
            mock_fetch.return_value = [
                {
                    "score": 88,
                    "contributors": {"temp": 0.5},
                    "temperature_deviation": 0.3,
                    "temperature_trend_deviation": 0.1,
                }
            ]
            result = readiness("2026-03-25")

        assert result["date"] == "2026-03-25"
        assert result["score"] == 88
        assert result["contributors"] == {"temp": 0.5}
        assert result["temperature_deviation"] == 0.3
        assert result["temperature_trend_deviation"] == 0.1

    def test_readiness_no_data(self):
        from metabolon.organelles.chemoreceptor import readiness

        with patch(f"{MOD}._fetch") as mock_fetch:
            mock_fetch.return_value = []
            result = readiness("2026-03-25")

        assert result == {
            "date": "2026-03-25",
            "score": None,
            "contributors": {},
            "temperature_deviation": None,
        }

    def test_readiness_defaults_to_today(self):
        from metabolon.organelles.chemoreceptor import readiness

        with (
            patch(f"{MOD}._fetch") as mock_fetch,
            patch(f"{MOD}._today_date", return_value="2026-04-01"),
        ):
            mock_fetch.return_value = []
            readiness()

        mock_fetch.assert_called_once_with("daily_readiness", "2026-04-01", "2026-04-01")


# ---------------------------------------------------------------------------
# sleep_score()
# ---------------------------------------------------------------------------


class TestSleepScore:
    def test_sleep_score_with_data(self):
        from metabolon.organelles.chemoreceptor import sleep_score

        with patch(f"{MOD}._fetch") as mock_fetch:
            mock_fetch.return_value = [{"score": 78, "contributors": {"efficiency": 95}}]
            result = sleep_score("2026-03-25")

        assert result["date"] == "2026-03-25"
        assert result["score"] == 78
        assert result["contributors"] == {"efficiency": 95}

    def test_sleep_score_no_data(self):
        from metabolon.organelles.chemoreceptor import sleep_score

        with patch(f"{MOD}._fetch") as mock_fetch:
            mock_fetch.return_value = []
            result = sleep_score("2026-03-25")

        assert result == {"date": "2026-03-25", "score": None, "contributors": {}}


# ---------------------------------------------------------------------------
# sleep_detail()
# ---------------------------------------------------------------------------


class TestSleepDetail:
    def test_sleep_detail_picks_longest(self):
        from metabolon.organelles.chemoreceptor import sleep_detail

        records = [
            {"id": "abc", "total_sleep_duration": 18000, "bedtime_start": "22:00"},
            {"id": "def", "total_sleep_duration": 28800, "bedtime_start": "23:00"},
        ]
        with patch(f"{MOD}._fetch") as mock_fetch:
            mock_fetch.return_value = records
            result = sleep_detail("2026-03-25")

        assert result["date"] == "2026-03-25"
        assert result["total_sleep_duration"] == 28800
        assert result["bedtime_start"] == "23:00"
        # id is removed
        assert "id" not in result
        # shorter session in extra_periods
        assert len(result["extra_periods"]) == 1
        assert result["extra_periods"][0]["total_sleep_duration"] == 18000

    def test_sleep_detail_no_data(self):
        from metabolon.organelles.chemoreceptor import sleep_detail

        with patch(f"{MOD}._fetch") as mock_fetch:
            mock_fetch.return_value = []
            result = sleep_detail("2026-03-25")

        assert result == {"date": "2026-03-25"}

    def test_sleep_detail_single_record(self):
        from metabolon.organelles.chemoreceptor import sleep_detail

        with patch(f"{MOD}._fetch") as mock_fetch:
            mock_fetch.return_value = [{"id": "x", "total_sleep_duration": 25000, "hrv": [45, 46]}]
            result = sleep_detail("2026-03-25")

        assert "extra_periods" not in result
        assert result["hrv"] == [45, 46]

    def test_sleep_detail_missing_duration_field(self):
        from metabolon.organelles.chemoreceptor import sleep_detail

        with patch(f"{MOD}._fetch") as mock_fetch:
            mock_fetch.return_value = [
                {"id": "a", "bedtime_start": "22:00"},
                {"id": "b", "total_sleep_duration": 10000},
            ]
            result = sleep_detail("2026-03-25")

        # Record with actual duration wins; missing duration defaults to 0
        assert result["total_sleep_duration"] == 10000

    def test_sleep_detail_extra_periods_have_no_id(self):
        from metabolon.organelles.chemoreceptor import sleep_detail

        with patch(f"{MOD}._fetch") as mock_fetch:
            mock_fetch.return_value = [
                {"id": "long", "total_sleep_duration": 30000},
                {"id": "short", "total_sleep_duration": 5000, "extra_key": True},
            ]
            result = sleep_detail("2026-03-25")

        for ep in result["extra_periods"]:
            assert "id" not in ep


# ---------------------------------------------------------------------------
# heartrate()
# ---------------------------------------------------------------------------


class TestHeartrate:
    def test_heartrate_with_explicit_range(self):
        from metabolon.organelles.chemoreceptor import heartrate

        with patch(f"{MOD}._fetch_datetime") as mock_fdt:
            mock_fdt.return_value = [{"bpm": 58, "timestamp": "t1"}]
            result = heartrate("2026-03-27T22:00:00+08:00", "2026-03-28T06:00:00+08:00")

        assert result == [{"bpm": 58, "timestamp": "t1"}]

    def test_heartrate_defaults_from_sleep_detail(self):
        from metabolon.organelles.chemoreceptor import heartrate

        with patch(f"{MOD}.sleep_detail") as mock_sd, patch(f"{MOD}._fetch_datetime") as mock_fdt:
            mock_sd.return_value = {
                "bedtime_start": "2026-03-27T22:30:00+08:00",
                "bedtime_end": "2026-03-28T06:15:00+08:00",
            }
            mock_fdt.return_value = [{"bpm": 60}]
            result = heartrate()

        mock_fdt.assert_called_once_with(
            "heartrate",
            "2026-03-27T22:30:00+08:00",
            "2026-03-28T06:15:00+08:00",
        )
        assert result == [{"bpm": 60}]

    def test_heartrate_no_sleep_detail_returns_empty(self):
        from metabolon.organelles.chemoreceptor import heartrate

        with patch(f"{MOD}.sleep_detail") as mock_sd:
            mock_sd.return_value = {"date": TODAY}
            result = heartrate()

        assert result == []

    def test_heartrate_partial_override_start(self):
        """If only start_dt is given, end_dt comes from sleep_detail."""
        from metabolon.organelles.chemoreceptor import heartrate

        with patch(f"{MOD}.sleep_detail") as mock_sd, patch(f"{MOD}._fetch_datetime") as mock_fdt:
            mock_sd.return_value = {
                "bedtime_start": "should-not-be-used",
                "bedtime_end": "2026-03-28T06:00:00+08:00",
            }
            mock_fdt.return_value = [{"bpm": 55}]
            heartrate("2026-03-27T22:00:00+08:00", None)

        mock_fdt.assert_called_once_with(
            "heartrate",
            "2026-03-27T22:00:00+08:00",
            "2026-03-28T06:00:00+08:00",
        )


# ---------------------------------------------------------------------------
# hrv alias
# ---------------------------------------------------------------------------


class TestHrvAlias:
    def test_hrv_is_sleep_detail(self):
        from metabolon.organelles.chemoreceptor import hrv, sleep_detail

        assert hrv is sleep_detail


# ---------------------------------------------------------------------------
# week()
# ---------------------------------------------------------------------------


class TestWeek:
    @_patch_token()
    def test_week_merges_by_date(self):
        from metabolon.organelles.chemoreceptor import week

        sleep_records = [
            {"day": "2026-03-20", "score": 80, "contributors": {"deep": 85}},
            {"day": "2026-03-21", "score": 75, "contributors": {"deep": 70}},
        ]
        readiness_records = [
            {
                "day": "2026-03-20",
                "score": 90,
                "temperature_deviation": 0.1,
                "contributors": {"temp": 0.5},
            },
            {"day": "2026-03-22", "score": 85, "temperature_deviation": -0.2, "contributors": {}},
        ]
        with patch(f"{MOD}._fetch") as mock_fetch:
            mock_fetch.side_effect = [sleep_records, readiness_records]
            result = week(7)

        assert len(result) == 3
        # sorted oldest first
        assert result[0]["date"] == "2026-03-20"
        assert result[0]["sleep_score"] == 80
        assert result[0]["readiness_score"] == 90
        assert result[1]["date"] == "2026-03-21"
        assert result[1]["sleep_score"] == 75
        assert result[1]["readiness_score"] is None
        assert result[2]["date"] == "2026-03-22"
        assert result[2]["sleep_score"] is None
        assert result[2]["readiness_score"] == 85

    @_patch_token()
    def test_week_no_data(self):
        from metabolon.organelles.chemoreceptor import week

        with patch(f"{MOD}._fetch") as mock_fetch:
            mock_fetch.side_effect = [[], []]
            result = week(3)

        assert result == []

    @_patch_token()
    def test_week_custom_days(self):
        from metabolon.organelles.chemoreceptor import week

        with (
            patch(f"{MOD}._fetch") as mock_fetch,
            patch(f"{MOD}._today_date", return_value="2026-04-01"),
            patch(f"{MOD}._week_start_date", return_value="2026-03-25") as mock_week,
        ):
            mock_fetch.side_effect = [[], []]
            week(7)

        mock_week.assert_called_once_with(7)


# ---------------------------------------------------------------------------
# _fetch_daily
# ---------------------------------------------------------------------------


class TestFetchDaily:
    def test_returns_first_record(self):
        from metabolon.organelles.chemoreceptor import _fetch_daily

        with patch(f"{MOD}._fetch") as mock_fetch:
            mock_fetch.return_value = [{"score": 88}, {"score": 77}]
            result = _fetch_daily("daily_activity", TODAY, TOKEN)

        assert result == {"score": 88}

    def test_returns_empty_on_no_records(self):
        from metabolon.organelles.chemoreceptor import _fetch_daily

        with patch(f"{MOD}._fetch") as mock_fetch:
            mock_fetch.return_value = []
            result = _fetch_daily("daily_activity", TODAY, TOKEN)

        assert result == {}

    def test_returns_empty_on_exception(self):
        from metabolon.organelles.chemoreceptor import _fetch_daily

        with patch(f"{MOD}._fetch") as mock_fetch:
            mock_fetch.side_effect = Exception("network error")
            result = _fetch_daily("daily_activity", TODAY, TOKEN)

        assert result == {}


# ---------------------------------------------------------------------------
# sense()
# ---------------------------------------------------------------------------


class TestSense:
    @_patch_token()
    def test_sense_full_snapshot(self):
        from metabolon.organelles.chemoreceptor import sense

        with (
            patch(f"{MOD}.today") as mock_today,
            patch(f"{MOD}.sleep_detail") as mock_sd,
            patch(f"{MOD}._fetch_daily") as mock_fd,
            patch(f"{MOD}._fetch") as mock_fetch,
        ):
            mock_today.return_value = {
                "date": TODAY,
                "sleep_score": 85,
                "readiness_score": 90,
            }
            mock_sd.return_value = {
                "date": TODAY,
                "bedtime_start": "22:30",
                "heart_rate": [58, 60],
            }

            def _fd_side_effect(endpoint, d, token):
                data = {
                    "daily_activity": {
                        "score": 75,
                        "steps": 8000,
                        "active_calories": 300,
                        "total_calories": 2200,
                        "high_activity_time": 1200,
                        "medium_activity_time": 900,
                        "low_activity_time": 3600,
                        "sedentary_time": 20000,
                        "resting_time": 15000,
                        "equivalent_walking_distance": 6000,
                        "contributors": {"meet_daily_targets": 1},
                    },
                    "daily_stress": {
                        "day_summary": "normal",
                        "stress_high": 0.5,
                        "recovery_high": 0.8,
                    },
                    "daily_spo2": {
                        "spo2_percentage": {"average": 97.5},
                        "breathing_disturbance_index": 1.2,
                    },
                    "daily_resilience": {"level": "good", "contributors": {"recovery": 0.9}},
                    "sleep_time": {
                        "recommendation": "improve",
                        "status": "insufficient",
                        "optimal_bedtime": "22:00",
                    },
                    "daily_cardiovascular_age": {"vascular_age": 35},
                    "vO2_max": {"vo2_max": 42},
                }
                return data.get(endpoint, {})

            mock_fd.side_effect = _fd_side_effect
            mock_fetch.return_value = [
                {
                    "activity": "running",
                    "calories": 250,
                    "distance": 5000,
                    "intensity": "moderate",
                    "source": "manual",
                    "start_datetime": "t1",
                    "end_datetime": "t2",
                    "label": "Morning run",
                }
            ]

            result = sense()

        assert result["sleep_score"] == 85
        assert result["readiness_score"] == 90
        assert result["bedtime_start"] == "22:30"
        assert result["heart_rate"] == [58, 60]
        assert result["activity"]["steps"] == 8000
        assert result["activity"]["score"] == 75
        assert result["stress"]["day_summary"] == "normal"
        assert result["spo2"]["average"] == 97.5
        assert result["resilience"]["level"] == "good"
        assert result["sleep_time"]["status"] == "insufficient"
        assert result["vascular_age"] == 35
        assert result["vo2_max"] == 42
        assert len(result["workouts"]) == 1
        assert result["workouts"][0]["activity"] == "running"

    def test_sense_error_returns_error_dict(self):
        from metabolon.organelles.chemoreceptor import sense

        with patch(f"{MOD}._get_token") as mock_token:
            mock_token.side_effect = RuntimeError("no token")
            result = sense()

        assert "error" in result
        assert "no token" in result["error"]

    @_patch_token()
    def test_sense_minimal_data(self):
        """sense() when today/sleep_detail return minimal data and all extra endpoints empty."""
        from metabolon.organelles.chemoreceptor import sense

        with (
            patch(f"{MOD}.today") as mock_today,
            patch(f"{MOD}.sleep_detail") as mock_sd,
            patch(f"{MOD}._fetch_daily") as mock_fd,
            patch(f"{MOD}._fetch") as mock_fetch,
        ):
            mock_today.return_value = {"date": TODAY}
            mock_sd.return_value = {"date": TODAY}
            mock_fd.return_value = {}
            mock_fetch.return_value = []

            result = sense()

        assert result["date"] == TODAY
        assert "activity" not in result
        assert "stress" not in result
        assert "spo2" not in result
        assert "resilience" not in result
        assert "sleep_time" not in result
        assert "workouts" not in result

    @_patch_token()
    def test_sense_sleep_detail_overwrite_does_not_clobber_today(self):
        """sleep_detail keys merged after today; unique keys from both preserved."""
        from metabolon.organelles.chemoreceptor import sense

        with (
            patch(f"{MOD}.today") as mock_today,
            patch(f"{MOD}.sleep_detail") as mock_sd,
            patch(f"{MOD}._fetch_daily") as mock_fd,
            patch(f"{MOD}._fetch") as mock_fetch,
        ):
            mock_today.return_value = {"date": TODAY, "sleep_score": 85}
            mock_sd.return_value = {"date": TODAY, "bedtime_start": "23:00"}
            mock_fd.return_value = {}
            mock_fetch.return_value = []

            result = sense()

        # today's keys preserved
        assert result["sleep_score"] == 85
        # sleep_detail unique keys merged
        assert result["bedtime_start"] == "23:00"
        # sleep_detail date excluded from merge
        assert result["date"] == TODAY

    @_patch_token()
    def test_sense_spo2_none_percentage(self):
        """spo2_percentage can be None; average should be None."""
        from metabolon.organelles.chemoreceptor import sense

        with (
            patch(f"{MOD}.today") as mock_today,
            patch(f"{MOD}.sleep_detail") as mock_sd,
            patch(f"{MOD}._fetch_daily") as mock_fd,
            patch(f"{MOD}._fetch") as mock_fetch,
        ):
            mock_today.return_value = {"date": TODAY}
            mock_sd.return_value = {"date": TODAY}

            def _fd(endpoint, d, token):
                if endpoint == "daily_spo2":
                    return {"spo2_percentage": None, "breathing_disturbance_index": 2.0}
                return {}

            mock_fd.side_effect = _fd
            mock_fetch.return_value = []

            result = sense()

        assert result["spo2"]["average"] is None
        assert result["spo2"]["breathing_disturbance_index"] == 2.0
