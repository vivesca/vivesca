"""Tests for metabolon.organelles.baroreceptor — HK Observatory weather sensor."""

from __future__ import annotations

import io
import json
import urllib.error
from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest

from metabolon.organelles import baroreceptor


class TestFetchJson:
    """Tests for _fetch_json function."""

    def test_fetch_json_success(self):
        """Successfully fetch and parse JSON response."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"key": "value"}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            result = baroreceptor._fetch_json("https://example.com/api")
            assert result == {"key": "value"}

    def test_fetch_json_timeout(self):
        """Timeout raises URLError."""
        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("timeout"),
        ):
            with pytest.raises(urllib.error.URLError):
                baroreceptor._fetch_json("https://example.com/api")

    def test_fetch_json_invalid_json(self):
        """Invalid JSON raises ValueError."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"not valid json"
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            with pytest.raises(ValueError, match="Invalid JSON"):
                baroreceptor._fetch_json("https://example.com/api")


class TestToInt:
    """Tests for _to_int helper."""

    def test_to_int_from_int(self):
        assert baroreceptor._to_int(42) == 42

    def test_to_int_from_float(self):
        assert baroreceptor._to_int(3.7) == 3

    def test_to_int_from_numeric_string(self):
        assert baroreceptor._to_int("25") == 25

    def test_to_int_from_float_string(self):
        assert baroreceptor._to_int("25.5") == 25

    def test_to_int_from_invalid_string(self):
        assert baroreceptor._to_int("hello") is None

    def test_to_int_from_none(self):
        assert baroreceptor._to_int(None) is None

    def test_to_int_from_list(self):
        assert baroreceptor._to_int([1, 2]) is None


class TestGetPlaceValue:
    """Tests for _get_place_value helper."""

    def test_get_place_value_found(self):
        data = [
            {"place": "Central", "max": 10},
            {"place": "Kowloon", "max": 20},
        ]
        assert baroreceptor._get_place_value(data, "Kowloon", "max") == 20

    def test_get_place_value_not_found(self):
        data = [
            {"place": "Central", "max": 10},
        ]
        assert baroreceptor._get_place_value(data, "Sai Kung", "max") is None

    def test_get_place_value_missing_key(self):
        data = [
            {"place": "Central", "min": 5},
        ]
        assert baroreceptor._get_place_value(data, "Central", "max") is None

    def test_get_place_value_custom_cast(self):
        data = [
            {"place": "Eastern", "max": "12.5"},
        ]
        result = baroreceptor._get_place_value(data, "Eastern", "max", cast=float)
        assert result == 12.5


class TestFormatRain:
    """Tests for _format_rain helper."""

    def test_format_rain_integer(self):
        assert baroreceptor._format_rain(10.0) == "10"

    def test_format_rain_decimal(self):
        assert baroreceptor._format_rain(10.5) == "10.5"

    def test_format_rain_zero(self):
        assert baroreceptor._format_rain(0.0) == "0"


class TestBuildWeatherLine:
    """Tests for build_weather_line function."""

    @pytest.fixture
    def sample_now(self):
        return {
            "humidity": {"data": [{"value": 85}]},
            "uvindex": {"data": [{"value": 3}]},
            "rainfall": {"data": []},
        }

    @pytest.fixture
    def sample_fnd(self):
        today = datetime.now().strftime("%Y%m%d")
        return {
            "weatherForecast": [
                {
                    "forecastDate": today,
                    "forecastMintemp": {"value": 22},
                    "forecastMaxtemp": {"value": 28},
                    "forecastWeather": "Sunny periods.",
                }
            ]
        }

    @pytest.fixture
    def sample_warn(self):
        return {}

    def test_basic_weather_line(self, sample_now, sample_fnd, sample_warn):
        """Basic weather line without warnings or special conditions."""
        line = baroreceptor.build_weather_line(sample_now, sample_fnd, sample_warn)
        assert "22–28°C" in line
        assert "sunny periods" in line

    def test_weather_line_with_rain(self, sample_now, sample_fnd, sample_warn):
        """Weather line includes rainfall when present."""
        sample_now["rainfall"]["data"] = [
            {"place": "Eastern District", "max": 15.0}
        ]
        line = baroreceptor.build_weather_line(sample_now, sample_fnd, sample_warn)
        assert "15mm rain" in line

    def test_weather_line_chai_wan_fallback(self, sample_now, sample_fnd, sample_warn):
        """Rainfall falls back to Chai Wan if Eastern District unavailable."""
        sample_now["rainfall"]["data"] = [
            {"place": "Chai Wan", "max": 8.5}
        ]
        line = baroreceptor.build_weather_line(sample_now, sample_fnd, sample_warn)
        assert "8.5mm rain" in line

    def test_weather_line_with_high_uv(self, sample_now, sample_fnd, sample_warn):
        """Weather line includes UV index when >= 6."""
        sample_now["uvindex"]["data"] = [{"value": 8}]
        line = baroreceptor.build_weather_line(sample_now, sample_fnd, sample_warn)
        assert "UV 8" in line

    def test_weather_line_uv_below_threshold(self, sample_now, sample_fnd, sample_warn):
        """Weather line omits UV index when < 6."""
        sample_now["uvindex"]["data"] = [{"value": 3}]
        line = baroreceptor.build_weather_line(sample_now, sample_fnd, sample_warn)
        assert "UV" not in line

    def test_weather_line_muggy(self, sample_now, sample_fnd, sample_warn):
        """Weather line includes 'muggy' when humidity >= 90."""
        sample_now["humidity"]["data"] = [{"value": 92}]
        line = baroreceptor.build_weather_line(sample_now, sample_fnd, sample_warn)
        assert "muggy" in line

    def test_weather_line_typhoon_warning(self, sample_now, sample_fnd, sample_warn):
        """Typhoon warning is formatted correctly."""
        sample_warn["WTCSGNL"] = {"name": "Typhoon Signal", "code": "8"}
        line = baroreceptor.build_weather_line(sample_now, sample_fnd, sample_warn)
        assert "🌀 T8" in line

    def test_weather_line_rain_warning(self, sample_now, sample_fnd, sample_warn):
        """Rain warning is formatted correctly."""
        sample_warn["WRAIN"] = {"name": "Rainstorm Warning Signal"}
        line = baroreceptor.build_weather_line(sample_now, sample_fnd, sample_warn)
        assert "⛈️ Rainstorm" in line

    def test_weather_line_fire_warning_suppressed(self, sample_now, sample_fnd, sample_warn):
        """Fire danger warning is suppressed."""
        sample_warn["WFIRE"] = {"name": "Fire Danger Warning"}
        line = baroreceptor.build_weather_line(sample_now, sample_fnd, sample_warn)
        assert "Fire" not in line

    def test_weather_line_cold_warning(self, sample_now, sample_fnd, sample_warn):
        """Cold warning is formatted correctly."""
        sample_warn["WCOLD"] = {"name": "Cold Weather Warning"}
        line = baroreceptor.build_weather_line(sample_now, sample_fnd, sample_warn)
        assert "🥶 Cold Weather" in line

    def test_weather_line_thunderstorm_forecast(self, sample_now, sample_fnd, sample_warn):
        """Thunderstorm in forecast shows correct emoji."""
        sample_fnd["weatherForecast"][0]["forecastWeather"] = "Thunderstorms"
        line = baroreceptor.build_weather_line(sample_now, sample_fnd, sample_warn)
        assert "⛈️" in line

    def test_weather_line_cloudy_forecast(self, sample_now, sample_fnd, sample_warn):
        """Cloudy forecast shows correct emoji."""
        sample_fnd["weatherForecast"][0]["forecastWeather"] = "Cloudy"
        line = baroreceptor.build_weather_line(sample_now, sample_fnd, sample_warn)
        assert "☁️" in line

    def test_weather_line_rain_forecast(self, sample_now, sample_fnd, sample_warn):
        """Rain in forecast shows correct emoji."""
        sample_fnd["weatherForecast"][0]["forecastWeather"] = "Light rain"
        line = baroreceptor.build_weather_line(sample_now, sample_fnd, sample_warn)
        assert "🌦️" in line

    def test_weather_line_missing_forecast_raises(self, sample_now, sample_warn):
        """Missing weatherForecast raises ValueError."""
        fnd = {"weatherForecast": []}
        with pytest.raises(ValueError, match="missing weatherForecast"):
            baroreceptor.build_weather_line(sample_now, fnd, sample_warn)

    def test_weather_line_missing_temp_raises(self, sample_now, sample_warn):
        """Missing temperature values raise ValueError."""
        fnd = {
            "weatherForecast": [
                {"forecastDate": datetime.now().strftime("%Y%m%d"), "forecastWeather": "Sunny"}
            ]
        }
        with pytest.raises(ValueError, match="missing forecastMintemp/forecastMaxtemp"):
            baroreceptor.build_weather_line(sample_now, fnd, sample_warn)

    def test_weather_line_uses_first_forecast_if_no_date_match(
        self, sample_now, sample_warn
    ):
        """Uses first forecast entry when date doesn't match."""
        fnd = {
            "weatherForecast": [
                {
                    "forecastDate": "20000101",  # Old date
                    "forecastMintemp": {"value": 18},
                    "forecastMaxtemp": {"value": 24},
                    "forecastWeather": "Cloudy",
                }
            ]
        }
        line = baroreceptor.build_weather_line(sample_now, fnd, sample_warn)
        assert "18–24°C" in line

    def test_weather_line_no_humidity_data(self, sample_fnd, sample_warn):
        """Handles missing humidity data gracefully."""
        now = {"uvindex": {"data": [{"value": 3}]}, "rainfall": {"data": []}}
        line = baroreceptor.build_weather_line(now, sample_fnd, sample_warn)
        assert "muggy" not in line

    def test_weather_line_no_uv_data(self, sample_now, sample_fnd, sample_warn):
        """Handles missing UV data gracefully (defaults to 0)."""
        now = {"humidity": {"data": [{"value": 50}]}, "rainfall": {"data": []}}
        line = baroreceptor.build_weather_line(now, sample_fnd, sample_warn)
        assert "UV" not in line

    def test_weather_line_heavy_rain_emoji(self, sample_now, sample_fnd, sample_warn):
        """Heavy rain (>5mm) shows rain emoji."""
        sample_now["rainfall"]["data"] = [
            {"place": "Eastern District", "max": 10.0}
        ]
        line = baroreceptor.build_weather_line(sample_now, sample_fnd, sample_warn)
        assert "🌧️" in line

    def test_weather_line_falls_back_to_partial_sun_emoji(
        self, sample_now, sample_warn
    ):
        """Unknown forecast defaults to partial sun emoji."""
        fnd = {
            "weatherForecast": [
                {
                    "forecastDate": datetime.now().strftime("%Y%m%d"),
                    "forecastMintemp": {"value": 20},
                    "forecastMaxtemp": {"value": 25},
                    "forecastWeather": "Unknown condition",
                }
            ]
        }
        line = baroreceptor.build_weather_line(sample_now, fnd, sample_warn)
        assert "🌤️" in line


class TestSense:
    """Tests for sense() function."""

    def test_sense_success(self):
        """sense() returns weather line on successful fetch."""
        mock_now = {
            "humidity": {"data": [{"value": 75}]},
            "uvindex": {"data": [{"value": 4}]},
            "rainfall": {"data": []},
        }
        today = datetime.now().strftime("%Y%m%d")
        mock_fnd = {
            "weatherForecast": [
                {
                    "forecastDate": today,
                    "forecastMintemp": {"value": 20},
                    "forecastMaxtemp": {"value": 26},
                    "forecastWeather": "Partly cloudy",
                }
            ]
        }
        mock_warn = {}

        def mock_urlopen(url, timeout=10):
            resp = MagicMock()
            if "rhrread" in url:
                resp.read.return_value = json.dumps(mock_now).encode()
            elif "fnd" in url:
                resp.read.return_value = json.dumps(mock_fnd).encode()
            elif "warnsum" in url:
                resp.read.return_value = json.dumps(mock_warn).encode()
            resp.__enter__ = MagicMock(return_value=resp)
            resp.__exit__ = MagicMock(return_value=False)
            return resp

        with patch("urllib.request.urlopen", mock_urlopen):
            result = baroreceptor.sense()
            assert "20–26°C" in result
            assert "partly cloudy" in result


class TestCLI:
    """Tests for _cli function."""

    def test_cli_success(self, capsys):
        """_cli prints weather line on success."""
        mock_now = {
            "humidity": {"data": [{"value": 70}]},
            "uvindex": {"data": [{"value": 2}]},
            "rainfall": {"data": []},
        }
        today = datetime.now().strftime("%Y%m%d")
        mock_fnd = {
            "weatherForecast": [
                {
                    "forecastDate": today,
                    "forecastMintemp": {"value": 21},
                    "forecastMaxtemp": {"value": 27},
                    "forecastWeather": "Fine",
                }
            ]
        }
        mock_warn = {}

        def mock_urlopen(url, timeout=10):
            resp = MagicMock()
            if "rhrread" in url:
                resp.read.return_value = json.dumps(mock_now).encode()
            elif "fnd" in url:
                resp.read.return_value = json.dumps(mock_fnd).encode()
            elif "warnsum" in url:
                resp.read.return_value = json.dumps(mock_warn).encode()
            resp.__enter__ = MagicMock(return_value=resp)
            resp.__exit__ = MagicMock(return_value=False)
            return resp

        with patch("urllib.request.urlopen", mock_urlopen):
            with patch("sys.exit"):
                baroreceptor._cli()
            captured = capsys.readouterr()
            assert "21–27°C" in captured.out

    def test_cli_failure_exits_nonzero(self, capsys):
        """_cli exits with error message on failure."""
        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("network error"),
        ):
            with patch("sys.exit") as mock_exit:
                baroreceptor._cli()
            mock_exit.assert_called_once_with(1)
            captured = capsys.readouterr()
            assert "network error" in captured.err


class TestWarnIcons:
    """Tests for warning icon mappings."""

    def test_warn_icons_exist(self):
        """All expected warning types have icons."""
        expected = {
            "WTCSGNL",  # Typhoon
            "WRAIN",    # Rain
            "WHOT",     # Hot
            "WCOLD",    # Cold
            "WFROST",   # Frost
            "WMSGNL",   # Monsoon
            "WTS",      # Thunderstorm
            "WFIRE",    # Fire
            "WL",       # Landslip
            "WTMW",     # Tsunami
        }
        assert set(baroreceptor.WARN_ICONS.keys()) == expected

    def test_warn_icons_are_emoji(self):
        """Warning icons are emoji characters."""
        for key, icon in baroreceptor.WARN_ICONS.items():
            # Emoji are typically outside ASCII range
            assert any(ord(c) > 127 for c in icon), f"{key} icon should be emoji"


class TestEdgeCases:
    """Edge case tests."""

    def test_build_weather_line_warning_with_non_dict_value(
        self, sample_now, sample_fnd
    ):
        """Handles warning with non-dict value gracefully."""
        warn = {"WRAIN": "not a dict"}
        line = baroreceptor.build_weather_line(sample_now, sample_fnd, warn)
        assert "⚠️" not in line  # No warning added

    def test_build_weather_line_warning_missing_name(self, sample_now, sample_fnd):
        """Handles warning missing 'name' field gracefully."""
        warn = {"WRAIN": {"code": "AMBER"}}
        line = baroreceptor.build_weather_line(sample_now, sample_fnd, warn)
        assert "⚠️" not in line

    @pytest.fixture
    def sample_now(self):
        return {
            "humidity": {"data": [{"value": 75}]},
            "uvindex": {"data": [{"value": 4}]},
            "rainfall": {"data": []},
        }

    @pytest.fixture
    def sample_fnd(self):
        today = datetime.now().strftime("%Y%m%d")
        return {
            "weatherForecast": [
                {
                    "forecastDate": today,
                    "forecastMintemp": {"value": 22},
                    "forecastMaxtemp": {"value": 28},
                    "forecastWeather": "Sunny",
                }
            ]
        }
