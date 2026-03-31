"""Tests for synthase enzyme."""
from unittest.mock import patch
import pytest


def test_invalid_model_raises():
    from metabolon.enzymes.synthase import synthase

    with pytest.raises(ValueError, match="Unknown model"):
        synthase(prompt="hello", model="gpt4")


def test_valid_model_haiku():
    from metabolon.enzymes.synthase import synthase

    with patch("metabolon.enzymes.synthase.run_cli") as mock:
        mock.return_value = "result"
        result = synthase(prompt="test task", model="haiku")
        assert result == "result"
        mock.assert_called_once()
        args = mock.call_args
        assert "haiku" in args[0][1]
        assert "-p" in args[0][1]
        assert "test task" in args[0][1]


def test_valid_model_opus():
    from metabolon.enzymes.synthase import synthase

    with patch("metabolon.enzymes.synthase.run_cli") as mock:
        mock.return_value = "opus result"
        result = synthase(prompt="do thing", model="opus")
        assert result == "opus result"


def test_default_model_is_sonnet():
    from metabolon.enzymes.synthase import synthase

    with patch("metabolon.enzymes.synthase.run_cli") as mock:
        mock.return_value = "sonnet result"
        result = synthase(prompt="hello")
        assert result == "sonnet result"
        assert "sonnet" in mock.call_args[0][1]


def test_timeout_is_300():
    from metabolon.enzymes.synthase import synthase

    with patch("metabolon.enzymes.synthase.run_cli") as mock:
        mock.return_value = "ok"
        synthase(prompt="x")
        assert mock.call_args[1].get("timeout", mock.call_args[0][2] if len(mock.call_args[0]) > 2 else None) == 300
