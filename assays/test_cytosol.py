from __future__ import annotations
"""Tests for cytosol shared helpers."""


import subprocess
from unittest.mock import patch, MagicMock
from metabolon.cytosol import invoke_organelle, synthesize, VIVESCA_ROOT


def test_vivesca_root_exists():
    assert VIVESCA_ROOT.exists()


def test_invoke_organelle_success():
    with patch("metabolon.cytosol.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="hello\n", returncode=0)
        result = invoke_organelle("echo", ["hello"])
        assert result == "hello"


def test_invoke_organelle_not_found():
    import pytest
    with pytest.raises(ValueError, match="Binary not found"):
        invoke_organelle("/nonexistent/binary", [])


def test_invoke_organelle_timeout():
    import pytest
    with patch("metabolon.cytosol.subprocess.run", side_effect=subprocess.TimeoutExpired("x", 1)):
        with pytest.raises(ValueError, match="timed out"):
            invoke_organelle("echo", ["hi"], timeout=1)


def test_invoke_organelle_error():
    import pytest
    err = subprocess.CalledProcessError(1, "cmd", stderr="bad input")
    with patch("metabolon.cytosol.subprocess.run", side_effect=err):
        with pytest.raises(ValueError, match="bad input"):
            invoke_organelle("echo", ["hi"])


def test_invoke_organelle_empty_output():
    with patch("metabolon.cytosol.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="", returncode=0)
        result = invoke_organelle("echo", [])
        assert result == "Done."


def test_synthesize_success():
    with patch("metabolon.cytosol.shutil.which", return_value="/usr/bin/synthase"), \
         patch("metabolon.cytosol.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="result text\n", returncode=0)
        result = synthesize("classify this")
        assert result == "result text"


def test_synthesize_not_found():
    import pytest
    with patch("metabolon.cytosol.shutil.which", return_value=None):
        with pytest.raises(ValueError, match="synthase not found"):
            synthesize("test")


def test_synthesize_error():
    import pytest
    with patch("metabolon.cytosol.shutil.which", return_value="/usr/bin/synthase"), \
         patch("metabolon.cytosol.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="", stderr="API error", returncode=1)
        with pytest.raises(ValueError, match="synthase error"):
            synthesize("test")
