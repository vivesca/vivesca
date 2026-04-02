"""Tests for metabolon.pathways.overnight."""
from __future__ import annotations

import json
import os
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


class TestSterileEnv:
    def test_removes_claudecode(self):
        env = {**os.environ, "CLAUDECODE": "1"}
        with patch.dict(os.environ, env, clear=True):
            result = _sterile_env()
        assert "CLAUDECODE" not in result

    def test_preserves_other_vars(self):
        env = {"HOME": "/home/test", "PATH": "/usr/bin", "CLAUDECODE": "yes"}
        with patch.dict(os.environ, env, clear=True):
            result = _sterile_env()
        assert result["HOME"] == "/home/test"
        assert result["PATH"] == "/usr/bin"

    def test_works_when_no_claudecode(self):
        env = {"HOME": "/home/test"}
        with patch.dict(os.environ, env, clear=True):
            result = _sterile_env()
        assert result == {"HOME": "/home/test"}


class TestMetabolise:
    @patch("metabolon.pathways.overnight.subprocess.run")
    @patch("metabolon.pathways.overnight._sterile_env", return_value={"HOME": "/tmp"})
    def test_reads_outfile_when_exists(self, mock_env, mock_run, tmp_path):
        outfile = tmp_path / "metabolised-test.md"
        outfile.write_text("crystallised insight")
        mock_run.return_value = MagicMock(stdout="", returncode=0)

        with patch.object(Path, "__truediv__", return_value=outfile):
            # Directly test the logic by calling metabolise and patching LOGDIR
            with patch("metabolon.pathways.overnight.LOGDIR", tmp_path):
                result = metabolise("seed text", "test")
        assert result == "crystallised insight"

    @patch("metabolon.pathways.overnight.subprocess.run")
    @patch("metabolon.pathways.overnight._sterile_env", return_value={})
    def test_returns_stdout_when_no_outfile(self, mock_env, mock_run, tmp_path):
        mock_run.return_value = MagicMock(stdout="fallback output", returncode=0)
        with patch("metabolon.pathways.overnight.LOGDIR", tmp_path):
            result = metabolise("seed", "noslug")
        assert result == "fallback output"

    @patch("metabolon.pathways.overnight.subprocess.run", side_effect=TimeoutError("boom"))
    @patch("metabolon.pathways.overnight._sterile_env", return_value={})
    def test_returns_none_on_exception(self, mock_env, mock_run, tmp_path):
        with patch("metabolon.pathways.overnight.LOGDIR", tmp_path):
            result = metabolise("seed", "fail")
        assert result is None


class TestComposePost:
    @patch("metabolon.pathways.overnight._acquire_catalyst")
    @patch("metabolon.pathways.overnight.PUBLISHED", Path("/tmp/fake-published"))
    def test_writes_file_and_returns_path(self, mock_get_symbiont, tmp_path):
        mock_symbiont = MagicMock()
        mock_symbiont.transduce.return_value = "---\ntitle: Test\n---\nBody."
        mock_get_symbiont.return_value = mock_symbiont

        published = tmp_path / "pub"
        published.mkdir()
        with patch("metabolon.pathways.overnight.PUBLISHED", published):
            result = compose_post("insight", "My Title", "my-slug")

        assert result is not None
        assert result.name == "my-slug.md"
        assert result.read_text() == "---\ntitle: Test\n---\nBody."

    @patch("metabolon.pathways.overnight._acquire_catalyst")
    def test_returns_none_on_transduce_error(self, mock_get_symbiont, tmp_path):
        mock_symbiont = MagicMock()
        mock_symbiont.transduce.side_effect = RuntimeError("model down")
        mock_get_symbiont.return_value = mock_symbiont

        with patch("metabolon.pathways.overnight.PUBLISHED", tmp_path):
            result = compose_post("insight", "Title", "slug")
        assert result is None

    @patch("metabolon.pathways.overnight._acquire_catalyst")
    @patch("metabolon.pathways.overnight.PUBLISHED", Path("/tmp/fake-published"))
    def test_prompt_includes_timestamp_and_title(self, mock_get_symbiont):
        mock_symbiont = MagicMock()
        mock_symbiont.transduce.return_value = "content"
        mock_get_symbiont.return_value = mock_symbiont

        published_dir = Path("/tmp/fake-published-compose")
        published_dir.mkdir(exist_ok=True)
        with patch("metabolon.pathways.overnight.PUBLISHED", published_dir):
            compose_post("my result", "My Title", "slug", model="glm")

        call_args = mock_symbiont.transduce.call_args
        prompt = call_args[0][1]  # second positional arg
        assert "My Title" in prompt
        assert "my result" in prompt
        # Check timestamp format (YYYY-MM-DDTHH:MM:SS.000Z)
        assert "T" in call_args[0][1]
        assert ".000Z" in call_args[0][1]
        # cleanup
        (published_dir / "slug.md").unlink(missing_ok=True)
        published_dir.rmdir()


class TestPublish:
    @patch("metabolon.pathways.overnight.subprocess.run")
    def test_returns_true_on_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        assert publish("my-post") is True
        mock_run.assert_called_once_with(
            ["sarcio", "publish", "my-post", "--push"],
            capture_output=True,
            text=True,
            timeout=60,
        )

    @patch("metabolon.pathways.overnight.subprocess.run")
    def test_returns_false_on_nonzero_exit(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1)
        assert publish("bad-post") is False

    @patch("metabolon.pathways.overnight.subprocess.run", side_effect=FileNotFoundError)
    def test_returns_false_on_exception(self, mock_run):
        assert publish("missing") is False


class TestPipeline:
    @patch("metabolon.pathways.overnight.publish", return_value=True)
    @patch("metabolon.pathways.overnight.compose_post")
    @patch("metabolon.pathways.overnight.metabolise")
    @patch("metabolon.pathways.overnight.time")
    def test_full_success_path(self, mock_time, mock_meta, mock_compose, mock_pub, tmp_path):
        mock_meta.return_value = "crystal text"
        post = tmp_path / "s1.md"
        post.write_text("post body")
        mock_compose.return_value = post

        with patch("metabolon.pathways.overnight.LOGDIR", tmp_path):
            result = metabolize_pipeline(
                [{"seed": "s", "slug": "s1", "title": "T1"}]
            )

        assert result["published"] == ["s1"]
        assert result["failed"] == []
        assert result["no_convergence"] == []

    @patch("metabolon.pathways.overnight.compose_post")
    @patch("metabolon.pathways.overnight.metabolise", return_value=None)
    @patch("metabolon.pathways.overnight.time")
    def test_no_convergence(self, mock_time, mock_meta, mock_compose, tmp_path):
        with patch("metabolon.pathways.overnight.LOGDIR", tmp_path):
            result = metabolize_pipeline(
                [{"seed": "s", "slug": "nope", "title": "T"}]
            )
        assert result["no_convergence"] == ["nope"]
        mock_compose.assert_not_called()

    @patch("metabolon.pathways.overnight.publish", return_value=False)
    @patch("metabolon.pathways.overnight.compose_post")
    @patch("metabolon.pathways.overnight.metabolise")
    @patch("metabolon.pathways.overnight.time")
    def test_compose_fail_goes_to_failed(self, mock_time, mock_meta, mock_compose, mock_pub, tmp_path):
        mock_meta.return_value = "ok"
        mock_compose.return_value = None

        with patch("metabolon.pathways.overnight.LOGDIR", tmp_path):
            result = metabolize_pipeline(
                [{"seed": "s", "slug": "bad", "title": "T"}]
            )
        assert result["failed"] == ["bad"]

    @patch("metabolon.pathways.overnight.publish", return_value=True)
    @patch("metabolon.pathways.overnight.compose_post")
    @patch("metabolon.pathways.overnight.metabolise")
    @patch("metabolon.pathways.overnight.time")
    def test_summary_json_written(self, mock_time, mock_meta, mock_compose, mock_pub, tmp_path):
        mock_meta.return_value = "crystal"
        post = tmp_path / "slug1.md"
        post.write_text("body")
        mock_compose.return_value = post

        with patch("metabolon.pathways.overnight.LOGDIR", tmp_path):
            result = metabolize_pipeline(
                [{"seed": "s", "slug": "slug1", "title": "T"}]
            )

        summary_file = tmp_path / "overnight-metabolise-summary.json"
        assert summary_file.exists()
        data = json.loads(summary_file.read_text())
        assert data["published"] == ["slug1"]
