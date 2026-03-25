"""Tests for promotion gates."""

from metabolon.metabolism.gates import reflex_check


def test_valid_description_passes():
    result = reflex_check("List calendar events for a given date in HKT timezone.")
    assert result.passed is True


def test_too_short_fails():
    result = reflex_check("List.")
    assert result.passed is False
    assert "too short" in result.reason.lower()


def test_too_long_fails():
    result = reflex_check("word " * 250)
    assert result.passed is False
    assert "too long" in result.reason.lower()


def test_empty_fails():
    result = reflex_check("")
    assert result.passed is False


def test_whitespace_only_fails():
    result = reflex_check("   \n\t  ")
    assert result.passed is False
