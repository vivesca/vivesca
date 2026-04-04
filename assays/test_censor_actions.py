from __future__ import annotations

"""Tests for censor enzyme."""


from unittest.mock import patch

import pytest


def test_censor_actions_invalid_rubric_raises():
    from metabolon.enzymes.censor import censor_evaluate

    with pytest.raises(ValueError, match="Invalid rubric"):
        censor_evaluate(rubric="nonexistent", content="test")


def test_valid_rubric_article():
    from metabolon.enzymes.censor import censor_evaluate

    with patch("metabolon.enzymes.censor.run_cli") as mock:
        mock.return_value = '{"score": 8}'
        result = censor_evaluate(rubric="article", content="some article text")
        assert result == '{"score": 8}'
        args = mock.call_args[0][1]
        assert "article" in args
        assert "--json" in args


def test_context_passed_when_provided():
    from metabolon.enzymes.censor import censor_evaluate

    with patch("metabolon.enzymes.censor.run_cli") as mock:
        mock.return_value = "ok"
        censor_evaluate(rubric="job-eval", content="text", context="extra info")
        args = mock.call_args[0][1]
        assert "--context" in args
        assert "extra info" in args


def test_context_omitted_when_none():
    from metabolon.enzymes.censor import censor_evaluate

    with patch("metabolon.enzymes.censor.run_cli") as mock:
        mock.return_value = "ok"
        censor_evaluate(rubric="outreach", content="text")
        args = mock.call_args[0][1]
        assert "--context" not in args


def test_model_default_is_glm():
    from metabolon.enzymes.censor import censor_evaluate

    with patch("metabolon.enzymes.censor.run_cli") as mock:
        mock.return_value = "ok"
        censor_evaluate(rubric="article", content="text")
        args = mock.call_args[0][1]
        assert "--model" in args
        idx = args.index("--model")
        assert args[idx + 1] == "glm"


def test_stdin_text_is_content():
    from metabolon.enzymes.censor import censor_evaluate

    with patch("metabolon.enzymes.censor.run_cli") as mock:
        mock.return_value = "ok"
        censor_evaluate(rubric="article", content="my content here")
        assert mock.call_args[1].get("stdin_text") == "my content here"


def test_custom_model_parameter():
    from metabolon.enzymes.censor import censor_evaluate

    with patch("metabolon.enzymes.censor.run_cli") as mock:
        mock.return_value = "ok"
        censor_evaluate(rubric="article", content="text", model="claude")
        args = mock.call_args[0][1]
        idx = args.index("--model")
        assert args[idx + 1] == "claude"


def test_timeout_passed_to_run_cli():
    from metabolon.enzymes.censor import censor_evaluate

    with patch("metabolon.enzymes.censor.run_cli") as mock:
        mock.return_value = "ok"
        censor_evaluate(rubric="article", content="text")
        assert mock.call_args[1].get("timeout") == 60


def test_all_valid_rubrics():
    from metabolon.enzymes.censor import censor_evaluate

    for rubric in ["article", "job-eval", "outreach"]:
        with patch("metabolon.enzymes.censor.run_cli") as mock:
            mock.return_value = "ok"
            result = censor_evaluate(rubric=rubric, content="text")
            assert result == "ok"
            args = mock.call_args[0][1]
            assert rubric in args


def test_run_cli_binary_path():
    from metabolon.enzymes.censor import BINARY, censor_evaluate

    with patch("metabolon.enzymes.censor.run_cli") as mock:
        mock.return_value = "ok"
        censor_evaluate(rubric="article", content="text")
        assert mock.call_args[0][0] == BINARY
