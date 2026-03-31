"""Tests for proprioception enzyme: dispatch mechanism, gradient detection, structural validation."""

from __future__ import annotations

import json
import os
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest


# ---------------------------------------------------------------------------
# Structural / import tests
# ---------------------------------------------------------------------------


class TestDispatchStructure:
    """Verify dispatch dict aligns with the Target Literal."""

    def test_dispatch_keys_match_target_literal(self) -> None:
        """Every key in _DISPATCH must appear in the Target Literal values."""
        from metabolon.enzymes.proprioception import Target, _DISPATCH

        # typing.get_args gives the literal values for a Literal type
        from typing import get_args

        target_values = set(get_args(Target))
        dispatch_keys = set(_DISPATCH.keys())

        # Dispatch should be a subset of Target (Target includes "drill" which is
        # handled inline, not via dispatch)
        assert dispatch_keys <= target_values, (
            f"Dispatch keys not in Target: {dispatch_keys - target_values}"
        )

    def test_unknown_target_raises_key_error(self) -> None:
        """Calling proprioception with an invalid target should raise KeyError."""
        from metabolon.enzymes.proprioception import proprioception

        # The function dispatches via _DISPATCH[target] which raises KeyError
        # for unknown keys. We patch _log_and_gradient to avoid file I/O.
        with patch("metabolon.enzymes.proprioception._log_and_gradient", return_value=None):
            with pytest.raises(KeyError):
                proprioception("nonexistent_target_xyz")


# ---------------------------------------------------------------------------
# Gradient detection (_log_and_gradient)
# ---------------------------------------------------------------------------


class TestLogAndGradient:
    """Test the gradient logging and change-detection helper."""

    @patch("metabolon.enzymes.proprioception.os.makedirs")
    @patch("metabolon.enzymes.proprioception.open", side_effect=FileNotFoundError)
    def test_log_and_gradient_first_call_no_history(self, mock_file, mock_makedirs) -> None:
        """First call logs the entry but returns None (no gradient to detect).

        If open() raises FileNotFoundError even for the append call,
        the function should not crash — but in practice the first open("a")
        creates the file. We test the path where the read-after-write fails,
        returning None.
        """
        from metabolon.enzymes.proprioception import _log_and_gradient

        # open is called twice: append (succeeds), read (fails)
        write_handle = MagicMock()
        write_handle.__enter__ = MagicMock(return_value=write_handle)
        write_handle.__exit__ = MagicMock(return_value=False)

        mock_file.side_effect = [
            write_handle,  # open(..., "a") succeeds
            FileNotFoundError(),  # open() for read fails
        ]

        result = _log_and_gradient("genome", "some reading text")
        assert result is None
        mock_makedirs.assert_called_once()

    @patch("metabolon.enzymes.proprioception.os.makedirs")
    @patch("metabolon.enzymes.proprioception.open")
    def test_log_and_gradient_detects_growth(self, mock_file, mock_makedirs) -> None:
        """When prior readings exist and size changed significantly, returns gradient string."""
        from metabolon.enzymes.proprioception import _log_and_gradient

        # Build history: 4 small readings for "genome" target
        old_entries = [
            json.dumps({"ts": f"2026-03-31T0{i}:00:00+08:00", "target": "genome", "size": 100})
            for i in range(4)
        ]
        history_lines = "\n".join(old_entries) + "\n"

        # open called twice: append, then read
        write_handle = MagicMock()
        write_handle.__enter__ = MagicMock(return_value=write_handle)
        write_handle.__exit__ = MagicMock(return_value=False)

        read_handle = MagicMock()
        read_handle.__enter__ = MagicMock(return_value=StringIO(history_lines))
        read_handle.__exit__ = MagicMock(return_value=False)

        mock_file.side_effect = [write_handle, read_handle]

        # New reading is much larger than the 100-char baseline
        large_reading = "x" * 500
        result = _log_and_gradient("genome", large_reading)
        assert result is not None
        assert "growing" in result
        assert "genome" in result


# ---------------------------------------------------------------------------
# Drill target dispatch
# ---------------------------------------------------------------------------


class TestDrillTarget:
    """Test the drill target is dispatched correctly."""

    @patch("metabolon.enzymes.proprioception._log_and_gradient", return_value=None)
    def test_drill_target_calls_drill_function(self, mock_gradient) -> None:
        """Calling proprioception with target='drill' delegates to _drill()."""
        from metabolon.enzymes.proprioception import proprioception

        with patch("metabolon.enzymes.proprioception._drill") as mock_drill:
            mock_drill.return_value = "Recorded flashcard drill: test = 2/3 (goal: g1)"
            result = proprioception(
                target="drill",
                goal="g1",
                category="test",
                score=2,
                drill_type="flashcard",
                material="card",
                notes="ok",
            )
            mock_drill.assert_called_once_with("g1", "test", 2, "flashcard", "card", "ok")
            assert "Recorded" in result

    @patch("metabolon.enzymes.proprioception._log_and_gradient", return_value=None)
    def test_drill_rejects_invalid_score(self, mock_gradient) -> None:
        """Drill with score outside 1-3 should return a failure message."""
        from metabolon.enzymes.proprioception import proprioception

        # _drill returns "Failed: score must be 1-3" — no exception
        result = proprioception(target="drill", goal="g1", category="cat", score=5)
        assert "Failed" in result
