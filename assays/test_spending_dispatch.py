"""Tests for parser dispatch."""

from metabolon.spending.parsers import get_parser


def test_get_mox_parser():
    parser = get_parser("mox")
    assert parser is not None
    assert callable(parser)


def test_get_hsbc_parser():
    parser = get_parser("hsbc")
    assert parser is not None


def test_get_ccba_parser():
    parser = get_parser("ccba")
    assert parser is not None


def test_get_scb_parser():
    parser = get_parser("scb")
    assert parser is not None


def test_get_unknown_parser():
    assert get_parser("unknown") is None
