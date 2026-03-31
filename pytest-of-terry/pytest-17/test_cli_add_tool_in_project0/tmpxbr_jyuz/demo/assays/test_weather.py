"""Tests for tool: weather_fetch."""


def test_weather_fetch_exists():
    """Verify weather_fetch can be imported."""
    from demo.enzymes.weather import weather_fetch
    assert callable(weather_fetch)