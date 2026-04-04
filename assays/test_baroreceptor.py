from __future__ import annotations

"""Tests for baroreceptor — HK Observatory weather sensor."""

import pytest


class TestToInt:
    def test_int_value(self):
        from metabolon.organelles.baroreceptor import _to_int

        assert _to_int(42) == 42

    def test_float_value(self):
        from metabolon.organelles.baroreceptor import _to_int

        assert _to_int(25.7) == 25

    def test_string_number(self):
        from metabolon.organelles.baroreceptor import _to_int

        assert _to_int("30") == 30

    def test_string_float(self):
        from metabolon.organelles.baroreceptor import _to_int

        assert _to_int("25.5") == 25

    def test_invalid_string(self):
        from metabolon.organelles.baroreceptor import _to_int

        assert _to_int("abc") is None

    def test_none(self):
        from metabolon.organelles.baroreceptor import _to_int

        assert _to_int(None) is None


class TestGetPlaceValue:
    def test_finds_place(self):
        from metabolon.organelles.baroreceptor import _get_place_value

        data = [{"place": "Eastern District", "max": 5.0}]
        assert _get_place_value(data, "Eastern District", "max", cast=float) == 5.0

    def test_missing_place(self):
        from metabolon.organelles.baroreceptor import _get_place_value

        data = [{"place": "Sha Tin", "max": 3.0}]
        assert _get_place_value(data, "Eastern District", "max", cast=float) is None


class TestFormatRain:
    def test_integer_mm(self):
        from metabolon.organelles.baroreceptor import _format_rain

        assert _format_rain(5.0) == "5"

    def test_decimal_mm(self):
        from metabolon.organelles.baroreceptor import _format_rain

        assert _format_rain(2.5) == "2.5"


class TestBuildWeatherLine:
    def _make_now(self, humidity=75, uv=3, rain=0.0):
        return {
            "humidity": {"data": [{"value": humidity}]},
            "uvindex": {"data": [{"value": uv}]},
            "rainfall": {"data": [{"place": "Eastern District", "max": rain}]},
        }

    def _make_find(self, lo=22, hi=28, desc="Cloudy."):
        from datetime import datetime

        today = datetime.now().strftime("%Y%m%d")
        return {
            "weatherForecast": [
                {
                    "forecastDate": today,
                    "forecastMintemp": {"value": lo},
                    "forecastMaxtemp": {"value": hi},
                    "forecastWeather": desc,
                }
            ]
        }

    def test_basic_output(self):
        from metabolon.organelles.baroreceptor import build_weather_line

        line = build_weather_line(self._make_now(), self._make_find(), {})
        assert "22" in line
        assert "28" in line
        assert "cloudy" in line.lower()

    def test_rain_included(self):
        from metabolon.organelles.baroreceptor import build_weather_line

        line = build_weather_line(self._make_now(rain=3.5), self._make_find(), {})
        assert "3.5mm" in line

    def test_high_uv(self):
        from metabolon.organelles.baroreceptor import build_weather_line

        line = build_weather_line(self._make_now(uv=8), self._make_find(), {})
        assert "UV 8" in line

    def test_muggy(self):
        from metabolon.organelles.baroreceptor import build_weather_line

        line = build_weather_line(self._make_now(humidity=95), self._make_find(), {})
        assert "muggy" in line

    def test_warnings_shown(self):
        from metabolon.organelles.baroreceptor import build_weather_line

        warn = {"WRAIN": {"name": "Rainstorm Warning Signal"}}
        line = build_weather_line(self._make_now(), self._make_find(), warn)
        assert "Rainstorm" in line

    def test_typhoon_signal(self):
        from metabolon.organelles.baroreceptor import build_weather_line

        warn = {"WTCSGNL": {"name": "Tropical Cyclone", "code": "8NE"}}
        line = build_weather_line(self._make_now(), self._make_find(), warn)
        assert "T8NE" in line

    def test_missing_forecast_raises(self):
        from metabolon.organelles.baroreceptor import build_weather_line

        with pytest.raises(ValueError, match="missing"):
            build_weather_line(self._make_now(), {"weatherForecast": []}, {})

    def test_sunny_emoji(self):
        from metabolon.organelles.baroreceptor import build_weather_line

        line = build_weather_line(self._make_now(), self._make_find(desc="Fine."), {})
        assert "\u2600" in line  # sun emoji
