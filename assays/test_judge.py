"""Tests for metabolon/enzymes/judge.py."""

from unittest.mock import patch

import pytest

from metabolon.enzymes.judge import judge_evaluate, BINARY, _TIMEOUT


class TestJudgeEvaluate:
    """Tests for judge_evaluate function."""

    def test_valid_rubric_article(self):
        """Test evaluation with article rubric."""
        with patch("metabolon.enzymes.judge.run_cli") as mock_run:
            mock_run.return_value = '{"score": 8, "feedback": "Good article"}'
            result = judge_evaluate("article", "Sample article content")
            assert result == '{"score": 8, "feedback": "Good article"}'
            mock_run.assert_called_once_with(
                BINARY,
                ["article", "--json", "--model", "glm"],
                timeout=_TIMEOUT,
                stdin_text="Sample article content",
            )

    def test_valid_rubric_job_eval(self):
        """Test evaluation with job-eval rubric."""
        with patch("metabolon.enzymes.judge.run_cli") as mock_run:
            mock_run.return_value = '{"score": 7}'
            result = judge_evaluate("job-eval", "Job description")
            assert result == '{"score": 7}'
            mock_run.assert_called_once_with(
                BINARY,
                ["job-eval", "--json", "--model", "glm"],
                timeout=_TIMEOUT,
                stdin_text="Job description",
            )

    def test_valid_rubric_outreach(self):
        """Test evaluation with outreach rubric."""
        with patch("metabolon.enzymes.judge.run_cli") as mock_run:
            mock_run.return_value = '{"score": 9}'
            result = judge_evaluate("outreach", "Outreach email")
            assert result == '{"score": 9}'
            mock_run.assert_called_once_with(
                BINARY,
                ["outreach", "--json", "--model", "glm"],
                timeout=_TIMEOUT,
                stdin_text="Outreach email",
            )

    def test_with_context(self):
        """Test that context is passed correctly."""
        with patch("metabolon.enzymes.judge.run_cli") as mock_run:
            mock_run.return_value = "Done."
            result = judge_evaluate(
                "article", "Content", context="Additional context"
            )
            assert result == "Done."
            mock_run.assert_called_once_with(
                BINARY,
                ["article", "--json", "--model", "glm", "--context", "Additional context"],
                timeout=_TIMEOUT,
                stdin_text="Content",
            )

    def test_custom_model(self):
        """Test evaluation with custom model."""
        with patch("metabolon.enzymes.judge.run_cli") as mock_run:
            mock_run.return_value = '{"score": 6}'
            result = judge_evaluate("article", "Content", model="gpt-4")
            assert result == '{"score": 6}'
            mock_run.assert_called_once_with(
                BINARY,
                ["article", "--json", "--model", "gpt-4"],
                timeout=_TIMEOUT,
                stdin_text="Content",
            )

    def test_context_and_model_together(self):
        """Test evaluation with both context and custom model."""
        with patch("metabolon.enzymes.judge.run_cli") as mock_run:
            mock_run.return_value = '{"score": 8}'
            result = judge_evaluate(
                "job-eval", "Content", context="Senior role", model="claude"
            )
            assert result == '{"score": 8}'
            mock_run.assert_called_once_with(
                BINARY,
                ["job-eval", "--json", "--model", "claude", "--context", "Senior role"],
                timeout=_TIMEOUT,
                stdin_text="Content",
            )

    def test_invalid_rubric(self):
        """Test that invalid rubric raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            judge_evaluate("invalid", "Content")
        assert "Invalid rubric 'invalid'" in str(exc_info.value)
        assert "article" in str(exc_info.value)
        assert "job-eval" in str(exc_info.value)
        assert "outreach" in str(exc_info.value)

    def test_invalid_rubric_suggestion_format(self):
        """Test that error message lists all valid rubrics."""
        with pytest.raises(ValueError) as exc_info:
            judge_evaluate("unknown", "Content")
        # Check format: should list all valid rubrics sorted
        assert "article, job-eval, outreach" in str(exc_info.value)

    def test_run_cli_error_propagates(self):
        """Test that run_cli errors are propagated."""
        with patch("metabolon.enzymes.judge.run_cli") as mock_run:
            mock_run.side_effect = ValueError("Binary not found: /path/to/judge")
            with pytest.raises(ValueError) as exc_info:
                judge_evaluate("article", "Content")
            assert "Binary not found" in str(exc_info.value)

    def test_run_cli_timeout_propagates(self):
        """Test that timeout errors are propagated."""
        with patch("metabolon.enzymes.judge.run_cli") as mock_run:
            mock_run.side_effect = ValueError("judge timed out (60s)")
            with pytest.raises(ValueError) as exc_info:
                judge_evaluate("article", "Content")
            assert "timed out" in str(exc_info.value)

    def test_empty_content(self):
        """Test with empty content string."""
        with patch("metabolon.enzymes.judge.run_cli") as mock_run:
            mock_run.return_value = '{"score": 0}'
            result = judge_evaluate("article", "")
            assert result == '{"score": 0}'
            mock_run.assert_called_once_with(
                BINARY,
                ["article", "--json", "--model", "glm"],
                timeout=_TIMEOUT,
                stdin_text="",
            )

    def test_none_context_omitted(self):
        """Test that None context is not added to args."""
        with patch("metabolon.enzymes.judge.run_cli") as mock_run:
            mock_run.return_value = "Done."
            result = judge_evaluate("article", "Content", context=None)
            # Verify --context is NOT in args
            call_args = mock_run.call_args
            assert "--context" not in call_args[0][1]
