"""Tests for judge.py."""
import pytest
from unittest.mock import patch, MagicMock

from metabolon.enzymes.judge import judge_evaluate


def test_judge_evaluate_invalid_rubric():
    """Test that ValueError is raised for invalid rubrics."""
    with pytest.raises(ValueError) as excinfo:
        judge_evaluate("invalid_rubric", "content")
    assert "Invalid rubric 'invalid_rubric'" in str(excinfo.value)
    assert "article, job-eval, outreach" in str(excinfo.value)


@pytest.mark.parametrize(
    "rubric",
    ["article", "job-eval", "outreach"],
)
def test_judge_evaluate_valid_rubrics_no_context(rubric):
    """Test that valid rubrics work without context."""
    mock_return = '{"score": 90, "feedback": "Great"}'
    with patch("metabolon.enzymes.judge.run_cli") as mock_run:
        mock_run.return_value = mock_return
        result = judge_evaluate(rubric, "test content")
        assert result == mock_return
        mock_run.assert_called_once()
        args = mock_run.call_args[0][1]
        assert args[0] == rubric
        assert "--json" in args
        assert "--model" in args
        assert "glm" in args
        assert len(args) == 4  # rubric --json --model glm


def test_judge_evaluate_with_context_custom_model():
    """Test that context and custom model are correctly added to args."""
    mock_return = '{"score": 85, "feedback": "Good"}'
    with patch("metabolon.enzymes.judge.run_cli") as mock_run:
        mock_run.return_value = mock_return
        result = judge_evaluate(
            rubric="article",
            content="test content",
            context="Additional context",
            model="gpt-4",
        )
        assert result == mock_return
        mock_run.assert_called_once()
        args = mock_run.call_args[0][1]
        assert args[0] == "article"
        assert "--json" in args
        assert "--model" in args
        assert "gpt-4" in args
        assert "--context" in args
        assert "Additional context" in args
