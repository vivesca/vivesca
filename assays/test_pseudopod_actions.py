"""Tests for pseudopod enzyme."""

from __future__ import annotations

from unittest.mock import patch
import pytest


def test_porta_inject_success():
    from metabolon.enzymes.pseudopod import porta_inject

    with patch("metabolon.organelles.porta.inject") as mock:
        mock.return_value = {"success": True, "message": "Injected 5 cookies", "count": 5}
        result = porta_inject(domain="github.com")
        assert result.success is True
        assert result.data["count"] == 5
        assert result.data["domain"] == "github.com"


def test_porta_inject_failure():
    from metabolon.enzymes.pseudopod import porta_inject

    with patch("metabolon.organelles.porta.inject") as mock:
        mock.return_value = {"success": False, "message": "No cookies found", "count": 0}
        result = porta_inject(domain="example.com")
        assert result.success is False


def test_translocon_dispatch_success():
    from metabolon.enzymes.pseudopod import translocon_dispatch

    with patch("metabolon.organelles.translocon.dispatch") as mock:
        mock.return_value = {"success": True, "output": "Task completed successfully"}
        result = translocon_dispatch(prompt="write a test")
        assert result.success is True


def test_translocon_dispatch_default_mode():
    from metabolon.enzymes.pseudopod import translocon_dispatch

    with patch("metabolon.organelles.translocon.dispatch") as mock:
        mock.return_value = {"success": True, "output": "ok"}
        translocon_dispatch(prompt="test")
        call_kwargs = mock.call_args[1]
        assert call_kwargs["mode"] == "explore"


def test_translocon_dispatch_empty_strings_become_none():
    from metabolon.enzymes.pseudopod import translocon_dispatch

    with patch("metabolon.organelles.translocon.dispatch") as mock:
        mock.return_value = {"success": True, "output": "ok"}
        translocon_dispatch(prompt="test", skill="", model="", backend="")
        call_kwargs = mock.call_args[1]
        assert call_kwargs["skill"] is None
        assert call_kwargs["model"] is None
        assert call_kwargs["backend"] is None


def test_translocon_dispatch_truncates_message():
    from metabolon.enzymes.pseudopod import translocon_dispatch

    with patch("metabolon.organelles.translocon.dispatch") as mock:
        long_output = "x" * 500
        mock.return_value = {"success": True, "output": long_output}
        result = translocon_dispatch(prompt="test")
        assert len(result.message) <= 200
