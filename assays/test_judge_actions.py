from __future__ import annotations
"""Tests for judge enzyme."""


from unittest.mock import patch
import pytest


def test_invalid_rubric_raises():
    from metabolon.enzymes.judge import judge_evaluate

    with pytest.raises(ValueError, match="Invalid rubric"):
        judge_evaluate(rubric="nonexistent", content="test")


def test_valid_rubric_article():
    from metabolon.enzymes.judge import judge_evaluate

    with patch("metabolon.enzymes.judge.run_cli") as mock:
        mock.return_value = '{"score": 8}'
        result = judge_evaluate(rubric="article", content="some article text")
        assert result == '{"score": 8}'
        args = mock.call_args[0][1]
        assert "article" in args
        assert "--json" in args


def test_context_passed_when_provided():
    from metabolon.enzymes.judge import judge_evaluate

    with patch("metabolon.enzymes.judge.run_cli") as mock:
        mock.return_value = "ok"
        judge_evaluate(rubric="job-eval", content="text", context="extra info")
        args = mock.call_args[0][1]
        assert "--context" in args
        assert "extra info" in args


def test_context_omitted_when_none():
    from metabolon.enzymes.judge import judge_evaluate

    with patch("metabolon.enzymes.judge.run_cli") as mock:
        mock.return_value = "ok"
        judge_evaluate(rubric="outreach", content="text")
        args = mock.call_args[0][1]
        assert "--context" not in args


def test_model_default_is_glm():
    from metabolon.enzymes.judge import judge_evaluate

    with patch("metabolon.enzymes.judge.run_cli") as mock:
        mock.return_value = "ok"
        judge_evaluate(rubric="article", content="text")
        args = mock.call_args[0][1]
        assert "--model" in args
        idx = args.index("--model")
        assert args[idx + 1] == "glm"


def test_stdin_text_is_content():
    from metabolon.enzymes.judge import judge_evaluate

    with patch("metabolon.enzymes.judge.run_cli") as mock:
        mock.return_value = "ok"
        judge_evaluate(rubric="article", content="my content here")
        assert mock.call_args[1].get("stdin_text") == "my content here"


def test_custom_model_parameter():
    from metabolon.enzymes.judge import judge_evaluate

    with patch("metabolon.enzymes.judge.run_cli") as mock:
        mock.return_value = "ok"
        judge_evaluate(rubric="article", content="text", model="claude")
        args = mock.call_args[0][1]
        idx = args.index("--model")
        assert args[idx + 1] == "claude"


def test_timeout_passed_to_run_cli():
    from metabolon.enzymes.judge import judge_evaluate

    with patch("metabolon.enzymes.judge.run_cli") as mock:
        mock.return_value = "ok"
        judge_evaluate(rubric="article", content="text")
        assert mock.call_args[1].get("timeout") == 60


def test_all_valid_rubrics():
    from metabolon.enzymes.judge import judge_evaluate

    for rubric in ["article", "job-eval", "outreach"]:
        with patch("metabolon.enzymes.judge.run_cli") as mock:
            mock.return_value = "ok"
            result = judge_evaluate(rubric=rubric, content="text")
            assert result == "ok"
            args = mock.call_args[0][1]
            assert rubric in args


def test_run_cli_binary_path():
    from metabolon.enzymes.judge import judge_evaluate, BINARY

    with patch("metabolon.enzymes.judge.run_cli") as mock:
        mock.return_value = "ok"
        judge_evaluate(rubric="article", content="text")
        assert mock.call_args[0][0] == BINARY
