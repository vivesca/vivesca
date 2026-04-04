from __future__ import annotations

"""Tests for metabolon.enzymes.censor — mock run_cli, verify arg construction."""

from unittest.mock import patch

import pytest

# The module imports run_cli from metabolon.organelles.effector
# We mock at the point of use: metabolon.enzymes.censor.run_cli
MODULE = "metabolon.enzymes.censor"


@pytest.fixture(autouse=True)
def _import_module():
    """Import the module once so tests can reference it."""
    import importlib

    import metabolon.enzymes.censor as mod
    importlib.reload(mod)
    return mod


# ---- rubric validation ----

def test_enzymes_censor_invalid_rubric_raises():
    """Passing an unknown rubric name raises ValueError."""
    import metabolon.enzymes.censor as mod

    with pytest.raises(ValueError, match="Invalid rubric 'bad'"):
        mod.censor_evaluate(rubric="bad", content="hello")


def test_valid_rubrics_accepted():
    """Each valid rubric name reaches run_cli without error."""
    import metabolon.enzymes.censor as mod

    for name in ("article", "job-eval", "outreach"):
        with patch(f"{MODULE}.run_cli", return_value="ok") as mock_cli:
            result = mod.censor_evaluate(rubric=name, content="text")
            assert result == "ok"
            mock_cli.assert_called_once()


# ---- argument construction ----

def test_basic_args():
    """Minimal call passes rubric, --json, --model glm."""
    import metabolon.enzymes.censor as mod

    with patch(f"{MODULE}.run_cli", return_value="scored") as mock_cli:
        mod.censor_evaluate(rubric="article", content="some article text")

        binary = mock_cli.call_args[0][0]
        args = mock_cli.call_args[0][1]

        assert "censor" in binary
        assert args == ["article", "--json", "--model", "glm"]


def test_custom_model():
    """Custom model name is forwarded in args."""
    import metabolon.enzymes.censor as mod

    with patch(f"{MODULE}.run_cli", return_value="ok") as mock_cli:
        mod.censor_evaluate(rubric="job-eval", content="cv text", model="deepseek")

        args = mock_cli.call_args[0][1]
        assert args == ["job-eval", "--json", "--model", "deepseek"]


def test_context_arg_appended():
    """When context is given, --context <value> is appended."""
    import metabolon.enzymes.censor as mod

    with patch(f"{MODULE}.run_cli", return_value="ok") as mock_cli:
        mod.censor_evaluate(
            rubric="outreach",
            content="email body",
            context="candidate profile",
        )

        args = mock_cli.call_args[0][1]
        assert args[-2:] == ["--context", "candidate profile"]


def test_no_context_arg():
    """Without context, no --context flag appears in args."""
    import metabolon.enzymes.censor as mod

    with patch(f"{MODULE}.run_cli", return_value="ok") as mock_cli:
        mod.censor_evaluate(rubric="article", content="text")

        args = mock_cli.call_args[0][1]
        assert "--context" not in args


def test_content_passed_as_stdin():
    """Content string is forwarded as stdin_text kwarg to run_cli."""
    import metabolon.enzymes.censor as mod

    with patch(f"{MODULE}.run_cli", return_value="ok") as mock_cli:
        mod.censor_evaluate(rubric="article", content="my article content")

        kwargs = mock_cli.call_args[1]
        assert kwargs.get("stdin_text") == "my article content"


def test_timeout_forwarded():
    """The module's _TIMEOUT (60) is forwarded to run_cli."""
    import metabolon.enzymes.censor as mod

    with patch(f"{MODULE}.run_cli", return_value="ok") as mock_cli:
        mod.censor_evaluate(rubric="article", content="text")

        kwargs = mock_cli.call_args[1]
        assert kwargs.get("timeout") == 60


def test_run_cli_exception_propagates():
    """If run_cli raises, it propagates to the caller."""
    import metabolon.enzymes.censor as mod

    with patch(f"{MODULE}.run_cli", side_effect=ValueError("Binary not found")):
        with pytest.raises(ValueError, match="Binary not found"):
            mod.censor_evaluate(rubric="article", content="text")


def test_return_value_passed_through():
    """The return value from run_cli is returned unchanged."""
    import metabolon.enzymes.censor as mod

    with patch(f"{MODULE}.run_cli", return_value='{"score": 42}'):
        result = mod.censor_evaluate(rubric="article", content="text")
        assert result == '{"score": 42}'
