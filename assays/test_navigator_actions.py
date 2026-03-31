"""Tests for navigator enzyme."""

from __future__ import annotations

from unittest.mock import patch

import pytest


def test_unknown_action():
    """Unknown action returns error with 'Unknown action' in message."""
    from metabolon.enzymes.navigator import navigator

    result = navigator(action="nonexistent")
    assert result.success is False
    assert "Unknown action" in result.error


def test_extract_requires_url():
    """extract action without url returns error."""
    from metabolon.enzymes.navigator import navigator

    result = navigator(action="extract")
    assert result.success is False
    assert "url" in result.error.lower()


def test_extract_success():
    """extract action with mocked _run_ab returns page data."""
    from metabolon.enzymes.navigator import navigator

    with patch("metabolon.enzymes.navigator._run_ab") as mock_ab, patch("time.sleep"):
        mock_ab.side_effect = [
            (True, "navigated"),  # open
            (True, "Page Title"),  # get title
            (True, "Page content"),  # get text
            (True, "https://x.com"),  # get url
        ]
        result = navigator(action="extract", url="https://x.com", wait_ms=0)
        assert result.success is True
        assert result.data["title"] == "Page Title"
        assert result.data["text"] == "Page content"


def test_extract_navigation_failure():
    """extract action when open fails returns error."""
    from metabolon.enzymes.navigator import navigator

    with patch("metabolon.enzymes.navigator._run_ab") as mock_ab:
        mock_ab.return_value = (False, "Connection refused")
        result = navigator(action="extract", url="https://x.com")
        assert result.success is False
        assert "failed" in result.error.lower()


def test_screenshot_requires_url():
    """screenshot action without url returns error."""
    from metabolon.enzymes.navigator import navigator

    result = navigator(action="screenshot")
    assert result.success is False
    assert "url" in result.error.lower()


def test_screenshot_success():
    """screenshot action with mocked _run_ab returns output_path."""
    from metabolon.enzymes.navigator import navigator

    with patch("metabolon.enzymes.navigator._run_ab") as mock_ab, patch(
        "subprocess.run"
    ), patch("time.sleep"):
        mock_ab.side_effect = [
            (True, "navigated"),  # open
            (True, "captured"),  # screenshot
        ]
        result = navigator(
            action="screenshot",
            url="https://x.com",
            output_path="/tmp/test.png",
            wait_ms=0,
        )
        assert result.success is True
        assert result.data["output_path"] == "/tmp/test.png"


def test_check_auth_requires_domain():
    """check_auth action without domain returns error."""
    from metabolon.enzymes.navigator import navigator

    result = navigator(action="check_auth")
    assert result.success is False
    assert "domain" in result.error.lower()


def test_check_auth_authenticated():
    """check_auth when redirected to dashboard → authenticated."""
    from metabolon.enzymes.navigator import navigator

    with patch("metabolon.enzymes.navigator._run_ab") as mock_ab, patch("time.sleep"):
        mock_ab.side_effect = [
            (True, "navigated"),  # open
            (True, "https://app.example.com/dashboard"),  # get url
        ]
        result = navigator(action="check_auth", domain="example.com")
        assert result.success is True
        assert result.data["is_authenticated"] is True


def test_check_auth_not_authenticated():
    """check_auth when redirected to login → not authenticated, guidance mentions porta."""
    from metabolon.enzymes.navigator import navigator

    with patch("metabolon.enzymes.navigator._run_ab") as mock_ab, patch("time.sleep"):
        mock_ab.side_effect = [
            (True, "navigated"),
            (True, "https://example.com/login?redirect=dashboard"),
        ]
        result = navigator(action="check_auth", domain="example.com")
        assert result.success is True
        assert result.data["is_authenticated"] is False
        assert "porta" in result.data.get("guidance", "").lower()
