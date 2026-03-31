from __future__ import annotations
"""Tests for metabolon.pathways.overnight — overnight metabolism pipeline."""


import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from metabolon.pathways.overnight import (
    DRAFT_PROMPT,
    LOGDIR,
    PUBLISHED,
    VIVESCA,
    _sterile_env,
    compose_post,
    metabolise,
    metabolize_pipeline,
    publish,
)


# ---------------------------------------------------------------------------
# _sterile_env
# ---------------------------------------------------------------------------

class TestSterileEnv:
    def test_removes_claudecode(self):
        with patch.dict(os.environ, {"CLAUDECODE": "yes", "HOME": "/tmp"}, clear=False):
            env = _sterile_env()
            assert "CLAUDECODE" not in env
            assert "HOME" in env

    def test_preserves_other_vars(self):
        with patch.dict(os.environ, {"PATH": "/usr/bin", "TERM": "xterm"}, clear=False):
            env = _sterile_env()
            assert env["PATH"] == "/usr/bin"
            assert env["TERM"] == "xterm"

    def test_empty_env_safe(self):
        with patch.dict(os.environ, {}, clear=True):
            env = _sterile_env()
            assert env == {}


# ---------------------------------------------------------------------------
# metabolise
# ---------------------------------------------------------------------------

class TestMetabolise:
    @patch("metabolon.pathways.overnight.subprocess.run")
    @patch("metabolon.pathways.overnight.LOGDIR", Path("/fake/logdir"))
    def test_valid_input_file_created(self, mock_run, tmp_path):
        outfile = tmp_path / "metabolised-test-slug.md"
        outfile.write_text("crystallised insight here")
        mock_run.return_value = MagicMock(stdout="", returncode=0)

        with patch.object(Path, "exists", return_value=True):
            with patch.object(Path, "read_text", return_value="crystallised insight here"):
                result = metabolise("my seed text", "test-slug")
        assert result == "crystallised insight here"

    @patch("metabolon.pathways.overnight.subprocess.run")
    def test_no_outfile_returns_stdout(self, mock_run):
        mock_run.return_value = MagicMock(stdout="fallback output", returncode=0)
        with patch("metabolon.pathways.overnight.LOGDIR", Path("/nonexistent")):
            result = metabolise("seed", "slug")
        assert result == "fallback output"

    @patch("metabolon.pathways.overnight.subprocess.run")
    def test_no_outfile_no_stdout_returns_none(self, mock_run):
        mock_run.return_value = MagicMock(stdout="", returncode=0)
        with patch("metabolon.pathways.overnight.LOGDIR", Path("/nonexistent")):
            result = metabolise("seed", "slug")
        assert result is None

    @patch("metabolon.pathways.overnight.subprocess.run")
    def test_subprocess_exception_returns_none(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="uv", timeout=600)
        result = metabolise("seed", "slug")
        assert result is None

    @patch("metabolon.pathways.overnight.subprocess.run")
    def test_empty_seed_still_calls(self, mock_run):
        mock_run.return_value = MagicMock(stdout="", returncode=0)
        with patch("metabolon.pathways.overnight.LOGDIR", Path("/nonexistent")):
            metabolise("", "slug")
        mock_run.assert_called_once()

    @patch("metabolon.pathways.overnight.subprocess.run")
    def test_passes_expander_and_pusher(self, mock_run):
        mock_run.return_value = MagicMock(stdout="out", returncode=0)
        with patch("metabolon.pathways.overnight.LOGDIR", Path("/nonexistent")):
            metabolise("seed", "slug", expander="opus", pusher="gemini")
        cmd = mock_run.call_args[0][0]
        assert "--expander" in cmd
        idx_exp = cmd.index("--expander")
        assert cmd[idx_exp + 1] == "opus"
        idx_push = cmd.index("--pusher")
        assert cmd[idx_push + 1] == "gemini"

    @patch("metabolon.pathways.overnight.subprocess.run")
    def test_sterile_env_used(self, mock_run):
        mock_run.return_value = MagicMock(stdout="out", returncode=0)
        with patch.dict(os.environ, {"CLAUDECODE": "present"}, clear=False):
            with patch("metabolon.pathways.overnight.LOGDIR", Path("/nonexistent")):
                metabolise("seed", "slug")
        passed_env = mock_run.call_args[1]["env"]
        assert "CLAUDECODE" not in passed_env


# ---------------------------------------------------------------------------
# compose_post
# ---------------------------------------------------------------------------

class TestComposePost:
    @patch("metabolon.pathways.overnight.PUBLISHED", Path("/fake/published"))
    @patch("metabolon.pathways.overnight._acquire_catalyst")
    def test_valid_input_returns_path(self, mock_acquire):
        mock_symbiont = MagicMock()
        mock_symbiont.transduce.return_value = "---\ntitle: test\n---\nContent"
        mock_acquire.return_value = mock_symbiont

        with patch.object(Path, "write_text"):
            result = compose_post("insight text", "Test Title", "test-slug")
        assert result == Path("/fake/published/test-slug.md")

    @patch("metabolon.pathways.overnight.PUBLISHED", Path("/fake/published"))
    @patch("metabolon.pathways.overnight._acquire_catalyst")
    def test_transduce_error_returns_none(self, mock_acquire):
        mock_symbiont = MagicMock()
        mock_symbiont.transduce.side_effect = RuntimeError("LLM down")
        mock_acquire.return_value = mock_symbiont

        result = compose_post("insight", "Title", "slug")
        assert result is None

    @patch("metabolon.pathways.overnight.PUBLISHED", Path("/fake/published"))
    @patch("metabolon.pathways.overnight._acquire_catalyst")
    def test_empty_result_handled(self, mock_acquire):
        mock_symbiont = MagicMock()
        mock_symbiont.transduce.return_value = ""
        mock_acquire.return_value = mock_symbiont

        with patch.object(Path, "write_text"):
            result = compose_post("", "Title", "slug")
        assert result == Path("/fake/published/slug.md")

    @patch("metabolon.pathways.overnight.PUBLISHED", Path("/fake/published"))
    @patch("metabolon.pathways.overnight._acquire_catalyst")
    def test_prompt_includes_seed_content(self, mock_acquire):
        mock_symbiont = MagicMock()
        mock_symbiont.transduce.return_value = "output"
        mock_acquire.return_value = mock_symbiont

        with patch.object(Path, "write_text"):
            compose_post("my special insight", "My Title", "slug")

        call_prompt = mock_symbiont.transduce.call_args[0][1]
        assert "my special insight" in call_prompt
        assert "My Title" in call_prompt

    @patch("metabolon.pathways.overnight.PUBLISHED", Path("/fake/published"))
    @patch("metabolon.pathways.overnight._acquire_catalyst")
    def test_default_model_is_glm(self, mock_acquire):
        mock_symbiont = MagicMock()
        mock_symbiont.transduce.return_value = "output"
        mock_acquire.return_value = mock_symbiont

        with patch.object(Path, "write_text"):
            compose_post("insight", "Title", "slug")

        model_arg = mock_symbiont.transduce.call_args[0][0]
        assert model_arg == "glm"

    @patch("metabolon.pathways.overnight.PUBLISHED", Path("/fake/published"))
    @patch("metabolon.pathways.overnight._acquire_catalyst")
    def test_custom_model_passed(self, mock_acquire):
        mock_symbiont = MagicMock()
        mock_symbiont.transduce.return_value = "output"
        mock_acquire.return_value = mock_symbiont

        with patch.object(Path, "write_text"):
            compose_post("insight", "Title", "slug", model="opus")

        model_arg = mock_symbiont.transduce.call_args[0][0]
        assert model_arg == "opus"


# ---------------------------------------------------------------------------
# publish
# ---------------------------------------------------------------------------

class TestPublish:
    @patch("metabolon.pathways.overnight.subprocess.run")
    def test_success_returns_true(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        assert publish("my-post") is True

    @patch("metabolon.pathways.overnight.subprocess.run")
    def test_failure_returns_false(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1)
        assert publish("my-post") is False

    @patch("metabolon.pathways.overnight.subprocess.run")
    def test_exception_returns_false(self, mock_run):
        mock_run.side_effect = Exception("boom")
        assert publish("my-post") is False

    @patch("metabolon.pathways.overnight.subprocess.run")
    def test_calls_sarcio_publish_push(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        publish("my-post")
        cmd = mock_run.call_args[0][0]
        assert cmd == ["sarcio", "publish", "my-post", "--push"]


# ---------------------------------------------------------------------------
# metabolize_pipeline
# ---------------------------------------------------------------------------

class TestMetabolizePipeline:
    @patch("metabolon.pathways.overnight.publish", return_value=True)
    @patch("metabolon.pathways.overnight.compose_post")
    @patch("metabolon.pathways.overnight.metabolise")
    @patch("metabolon.pathways.overnight.LOGDIR")
    def test_full_success(self, mock_logdir, mock_meta, mock_compose, mock_pub):
        mock_meta.return_value = "crystal"
        mock_compose.return_value = Path("/fake/post.md")
        mock_logdir.__truediv__ = MagicMock(return_value=MagicMock())

        seeds = [
            {"seed": "idea1", "slug": "post-1", "title": "First Post"},
            {"seed": "idea2", "slug": "post-2", "title": "Second Post"},
        ]
        results = metabolize_pipeline(seeds)

        assert results["published"] == ["post-1", "post-2"]
        assert results["failed"] == []
        assert results["no_convergence"] == []

    @patch("metabolon.pathways.overnight.publish", return_value=False)
    @patch("metabolon.pathways.overnight.compose_post", return_value=Path("/fake/post.md"))
    @patch("metabolon.pathways.overnight.metabolise", return_value="crystal")
    @patch("metabolon.pathways.overnight.LOGDIR")
    def test_publish_failure(self, mock_logdir, mock_meta, mock_compose, mock_pub):
        mock_logdir.__truediv__ = MagicMock(return_value=MagicMock())

        seeds = [{"seed": "idea", "slug": "fail-post", "title": "Fail"}]
        results = metabolize_pipeline(seeds)

        assert results["published"] == []
        assert results["failed"] == ["fail-post"]

    @patch("metabolon.pathways.overnight.publish")
    @patch("metabolon.pathways.overnight.compose_post")
    @patch("metabolon.pathways.overnight.metabolise", return_value=None)
    @patch("metabolon.pathways.overnight.LOGDIR")
    def test_no_convergence(self, mock_logdir, mock_meta, mock_compose, mock_pub):
        mock_logdir.__truediv__ = MagicMock(return_value=MagicMock())

        seeds = [{"seed": "idea", "slug": "no-conv", "title": "Nope"}]
        results = metabolize_pipeline(seeds)

        assert results["no_convergence"] == ["no-conv"]
        mock_compose.assert_not_called()
        mock_pub.assert_not_called()

    @patch("metabolon.pathways.overnight.publish")
    @patch("metabolon.pathways.overnight.compose_post", return_value=None)
    @patch("metabolon.pathways.overnight.metabolise", return_value="crystal")
    @patch("metabolon.pathways.overnight.LOGDIR")
    def test_compose_failure(self, mock_logdir, mock_meta, mock_compose, mock_pub):
        mock_logdir.__truediv__ = MagicMock(return_value=MagicMock())

        seeds = [{"seed": "idea", "slug": "bad-compose", "title": "Bad"}]
        results = metabolize_pipeline(seeds)

        assert results["failed"] == ["bad-compose"]
        mock_pub.assert_not_called()

    @patch("metabolon.pathways.overnight.publish", return_value=True)
    @patch("metabolon.pathways.overnight.compose_post")
    @patch("metabolon.pathways.overnight.metabolise")
    @patch("metabolon.pathways.overnight.LOGDIR")
    def test_mixed_results(self, mock_logdir, mock_meta, mock_compose, mock_pub):
        mock_logdir.__truediv__ = MagicMock(return_value=MagicMock())

        # Three seeds: converge+publish, no convergence, converge+publish
        mock_meta.side_effect = ["crystal1", None, "crystal3"]
        mock_compose.side_effect = [Path("/a.md"), Path("/c.md")]

        seeds = [
            {"seed": "s1", "slug": "a", "title": "A"},
            {"seed": "s2", "slug": "b", "title": "B"},
            {"seed": "s3", "slug": "c", "title": "C"},
        ]
        results = metabolize_pipeline(seeds)

        assert results["published"] == ["a", "c"]
        assert results["no_convergence"] == ["b"]

    @patch("metabolon.pathways.overnight.publish")
    @patch("metabolon.pathways.overnight.compose_post")
    @patch("metabolon.pathways.overnight.metabolise")
    @patch("metabolon.pathways.overnight.LOGDIR")
    def test_empty_seeds_list(self, mock_logdir, mock_meta, mock_compose, mock_pub):
        mock_logdir.__truediv__ = MagicMock(return_value=MagicMock())

        results = metabolize_pipeline([])

        assert results["published"] == []
        assert results["failed"] == []
        assert results["no_convergence"] == []
        mock_meta.assert_not_called()

    @patch("metabolon.pathways.overnight.publish", return_value=True)
    @patch("metabolon.pathways.overnight.compose_post", return_value=Path("/x.md"))
    @patch("metabolon.pathways.overnight.metabolise", return_value="crystal")
    @patch("metabolon.pathways.overnight.LOGDIR")
    def test_summary_json_written(self, mock_logdir, mock_meta, mock_compose, mock_pub):
        mock_summary = MagicMock()
        mock_logdir.__truediv__ = MagicMock(return_value=mock_summary)

        seeds = [{"seed": "s", "slug": "x", "title": "X"}]
        metabolize_pipeline(seeds)

        mock_summary.write_text.assert_called_once()
        written = mock_summary.write_text.call_args[0][0]
        parsed = json.loads(written)
        assert parsed["published"] == ["x"]


