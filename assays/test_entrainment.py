from __future__ import annotations
"""Tests for entrainment — circadian zeitgeber sensing."""

import datetime
from unittest.mock import patch

import pytest

HKT = datetime.timezone(datetime.timedelta(hours=8))


class TestZeitgebers:
    def test_returns_dict(self):
        from metabolon.organelles.entrainment import zeitgebers
        with patch("metabolon.organelles.entrainment.datetime") as mock_dt:
            now = datetime.datetime(2026, 3, 30, 14, 0, tzinfo=HKT)
            mock_dt.datetime.now.return_value = now
            mock_dt.timezone = datetime.timezone
            mock_dt.timedelta = datetime.timedelta
            result = zeitgebers()
        assert isinstance(result, dict)
        assert "hkt_hour" in result
        assert "is_weekend" in result

    def test_night_detection(self):
        from metabolon.organelles.entrainment import zeitgebers
        with patch("metabolon.organelles.entrainment.datetime") as mock_dt:
            now = datetime.datetime(2026, 3, 30, 23, 30, tzinfo=HKT)
            mock_dt.datetime.now.return_value = now
            mock_dt.timezone = datetime.timezone
            mock_dt.timedelta = datetime.timedelta
            result = zeitgebers()
        assert result["is_night"] is True
        assert result["asleep"] is True

    def test_daytime(self):
        from metabolon.organelles.entrainment import zeitgebers
        with patch("metabolon.organelles.entrainment.datetime") as mock_dt:
            now = datetime.datetime(2026, 3, 30, 10, 0, tzinfo=HKT)
            mock_dt.datetime.now.return_value = now
            mock_dt.timezone = datetime.timezone
            mock_dt.timedelta = datetime.timedelta
            result = zeitgebers()
        assert result["is_night"] is False
