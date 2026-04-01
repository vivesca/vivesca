from __future__ import annotations

"""Tests for metabolon.pathways.overnight — mock all external calls."""

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

import metabolon.pathways.overnight as mod


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_subprocess_result(stdout="", stderr="", returncode=0):
    """Build a fake subprocess.CompletedProcess."""
    return MagicMock(
        stdout=stdout, stderr=stderr, returncode=returncode
    )


# ── _sterile_env ─────────────────────────────────────────────────────────────

class TestSterileEnv:
    def test_removes_claudecode(self):
        with patch.dict(os.environ, {"CLAUDECODE": "1", "PATH": "/usr/bin"}, clear=False):
            env = mod._sterile_env()
            assert "CLAUDECODE" not in env
            assert "PATH" in env

    def test_preserves_all_other_vars(self):
        with patch.dict(os.environ, {"FOO": "bar", "BAZ": "qux"}, clear=True):
            env = mod._sterile_env()
            assert env == {"FOO": "bar", "BAZ": "qux"}

    def test_empty_environ(self):
        with patch.dict(os.environ, {}, clear=True):
            env = mod._sterile_env()
            assert env == {}


# ── metabolise ───────────────────────────────────────────────────────────────

class TestMetabolise:
    @patch("metabolon.pathways.overnight.subprocess.run")
    @patch("metabolon.pathways.overnight.LOGDIR", new_callable=lambda: PropertyMock)
    def test_reads_outfile(self, mock_logdir_prop, mock_run):
        """When outfile exists, return its contents."""
        fake_outfile = MagicMock()
        fake_outfile.exists.return_value = True
        fake_outfile.read_text.return_value = "  crystallised insight  "

        # LOGDIR / f"metabolised-{slug}.md" → fake_outfile
        mock_logdir = MagicMock()
        mock_logdir.__truediv__ = MagicMock(return_value=fake_outfile)
        # We need to patch the module-level LOGDIR
        with patch.object(mod, "LOGDIR", mock_logdir):
            result = mod.metabolise("seed text", "my-slug")
        assert result == "crystallised insight"

    @patch("metabolon.pathways.overnight.subprocess.run")
    @patch("metabolon.pathways.overnight.LOGDIR", new_callable=lambda: PropertyMock)
    def test_falls_back_to_stdout(self, mock_logdir_prop, mock_run):
        """When outfile doesn't exist, return stdout."""
        mock_run.return_value = _make_subprocess_result(stdout="stdout result\n")
        fake_outfile = MagicMock()
        fake_outfile.exists.return_value = False
        mock_logdir = MagicMock()
        mock_logdir.__truediv__ = MagicMock(return_value=fake_outfile)
        with patch.object(mod, "LOGDIR", mock_logdir):
            result = mod.metabolise("seed", "slug")
        assert result == "stdout result"

    @patch("metabolon.pathways.overnight.subprocess.run")
    @patch("metabolon.pathways.overnight.LOGDIR", new_callable=lambda: PropertyMock)
    def test_returns_none_on_no_output(self, mock_logdir_prop, mock_run):
        """When outfile missing and stdout empty, return None."""
        mock_run.return_value = _make_subprocess_result(stdout="")
        fake_outfile = MagicMock()
        fake_outfile.exists.return_value = False
        mock_logdir = MagicMock()
        mock_logdir.__truediv__ = MagicMock(return_value=fake_outfile)
        with patch.object(mod, "LOGDIR", mock_logdir):
            result = mod.metabolise("seed", "slug")
        assert result is None

    @patch("metabolon.pathways.overnight.subprocess.run", side_effect=Exception("boom"))
    def test_returns_none_on_exception(self, mock_run):
        result = mod.metabolise("seed", "slug")
        assert result is None

    @patch("metabolon.pathways.overnight.subprocess.run")
    @patch("metabolon.pathways.overnight.LOGDIR", new_callable=lambda: PropertyMock)
    def test_passes_expander_and_pusher(self, mock_logdir_prop, mock_run):
        """Verify subprocess.run receives the correct CLI args."""
        mock_run.return_value = _make_subprocess_result(stdout="")
        fake_outfile = MagicMock()
        fake_outfile.exists.return_value = False
        mock_logdir = MagicMock()
        mock_logdir.__truediv__ = MagicMock(return_value=fake_outfile)
        with patch.object(mod, "LOGDIR", mock_logdir):
            mod.metabolise("seed", "slug", expander="deepseek", pusher="glm")
        args = mock_run.call_args[0][0]
        assert "--expander" in args
        idx_exp = args.index("--expander")
        assert args[idx_exp + 1] == "deepseek"
        idx_push = args.index("--pusher")
        assert args[idx_push + 1] == "glm"

    @patch("metabolon.pathways.overnight.subprocess.run")
    @patch("metabolon.pathways.overnight.LOGDIR", new_callable=lambda: PropertyMock)
    def test_uses_sterile_env(self, mock_logdir_prop, mock_run):
        """subprocess.run must receive env without CLAUDECODE."""
        mock_run.return_value = _make_subprocess_result(stdout="")
        fake_outfile = MagicMock()
        fake_outfile.exists.return_value = False
        mock_logdir = MagicMock()
        mock_logdir.__truediv__ = MagicMock(return_value=fake_outfile)
        with patch.dict(os.environ, {"CLAUDECODE": "yes"}, clear=False):
            with patch.object(mod, "LOGDIR", mock_logdir):
                mod.metabolise("seed", "slug")
        passed_env = mock_run.call_args[1]["env"]
        assert "CLAUDECODE" not in passed_env

    @patch("metabolon.pathways.overnight.subprocess.run")
    @patch("metabolon.pathways.overnight.LOGDIR", new_callable=lambda: PropertyMock)
    def test_uses_vivesca_cwd(self, mock_logdir_prop, mock_run):
        """subprocess.run cwd must point at the vivesca checkout."""
        mock_run.return_value = _make_subprocess_result(stdout="")
        fake_outfile = MagicMock()
        fake_outfile.exists.return_value = False
        mock_logdir = MagicMock()
        mock_logdir.__truediv__ = MagicMock(return_value=fake_outfile)
        with patch.object(mod, "LOGDIR", mock_logdir):
            mod.metabolise("seed", "slug")
        cwd = mock_run.call_args[1]["cwd"]
        assert "vivesca" in cwd


# ── compose_post ─────────────────────────────────────────────────────────────

class TestComposePost:
    @patch("metabolon.pathways.overnight._acquire_catalyst")
    @patch("metabolon.pathways.overnight.PUBLISHED", new_callable=lambda: PropertyMock)
    def test_writes_post(self, mock_published_prop, mock_catalyst):
        fake_symbiont = MagicMock()
        fake_symbiont.transduce.return_value = "---\ntitle: Test\n---\nBody text."
        mock_catalyst.return_value = fake_symbiont
        fake_dir = MagicMock()
        fake_path = MagicMock()
        fake_dir.__truediv__ = MagicMock(return_value=fake_path)
        with patch.object(mod, "PUBLISHED", fake_dir):
            result = mod.compose_post("crystal text", "Test Title", "test-slug")
        assert result is fake_path
        fake_path.write_text.assert_called_once_with("---\ntitle: Test\n---\nBody text.")

    @patch("metabolon.pathways.overnight._acquire_catalyst")
    @patch("metabolon.pathways.overnight.PUBLISHED", new_callable=lambda: PropertyMock)
    def test_passes_model_to_transduce(self, mock_published_prop, mock_catalyst):
        fake_symbiont = MagicMock()
        fake_symbiont.transduce.return_value = "content"
        mock_catalyst.return_value = fake_symbiont
        fake_dir = MagicMock()
        fake_path = MagicMock()
        fake_dir.__truediv__ = MagicMock(return_value=fake_path)
        with patch.object(mod, "PUBLISHED", fake_dir):
            mod.compose_post("crystal", "Title", "slug", model="deepseek")
        call_args = fake_symbiont.transduce.call_args
        assert call_args[0][0] == "deepseek"

    @patch(
        "metabolon.pathways.overnight._acquire_catalyst",
        side_effect=Exception("no catalyst"),
    )
    def test_returns_none_on_exception(self, mock_catalyst):
        result = mod.compose_post("crystal", "Title", "slug")
        assert result is None

    @patch("metabolon.pathways.overnight._acquire_catalyst")
    @patch("metabolon.pathways.overnight.PUBLISHED", new_callable=lambda: PropertyMock)
    def test_prompt_includes_result_and_title(self, mock_published_prop, mock_catalyst):
        fake_symbiont = MagicMock()
        fake_symbiont.transduce.return_value = "content"
        mock_catalyst.return_value = fake_symbiont
        fake_dir = MagicMock()
        fake_path = MagicMock()
        fake_dir.__truediv__ = MagicMock(return_value=fake_path)
        with patch.object(mod, "PUBLISHED", fake_dir):
            mod.compose_post("MY_INSIGHT", "MY_TITLE", "slug")
        prompt = fake_symbiont.transduce.call_args[0][1]
        assert "MY_INSIGHT" in prompt
        assert "MY_TITLE" in prompt

    @patch("metabolon.pathways.overnight._acquire_catalyst")
    @patch("metabolon.pathways.overnight.PUBLISHED", new_callable=lambda: PropertyMock)
    def test_uses_slug_as_filename(self, mock_published_prop, mock_catalyst):
        fake_symbiont = MagicMock()
        fake_symbiont.transduce.return_value = "content"
        mock_catalyst.return_value = fake_symbiont
        fake_dir = MagicMock()
        fake_path = MagicMock()
        fake_dir.__truediv__ = MagicMock(return_value=fake_path)
        with patch.object(mod, "PUBLISHED", fake_dir):
            mod.compose_post("crystal", "Title", "my-special-slug")
        # __truediv__ should have been called with "my-special-slug.md"
        fake_dir.__truediv__.assert_called_with("my-special-slug.md")


# ── publish ──────────────────────────────────────────────────────────────────

class TestPublish:
    @patch("metabolon.pathways.overnight.subprocess.run")
    def test_returns_true_on_success(self, mock_run):
        mock_run.return_value = _make_subprocess_result(returncode=0)
        assert mod.publish("my-slug") is True

    @patch("metabolon.pathways.overnight.subprocess.run")
    def test_returns_false_on_failure(self, mock_run):
        mock_run.return_value = _make_subprocess_result(returncode=1)
        assert mod.publish("my-slug") is False

    @patch("metabolon.pathways.overnight.subprocess.run", side_effect=Exception("err"))
    def test_returns_false_on_exception(self, mock_run):
        assert mod.publish("my-slug") is False

    @patch("metabolon.pathways.overnight.subprocess.run")
    def test_passes_slug_and_push(self, mock_run):
        mock_run.return_value = _make_subprocess_result(returncode=0)
        mod.publish("test-slug")
        args = mock_run.call_args[0][0]
        assert args == ["sarcio", "publish", "test-slug", "--push"]

    @patch("metabolon.pathways.overnight.subprocess.run")
    def test_timeout(self, mock_run):
        mock_run.return_value = _make_subprocess_result(returncode=0)
        mod.publish("slug")
        assert mock_run.call_args[1]["timeout"] == 60


# ── metabolize_pipeline ─────────────────────────────────────────────────────

class TestMetabolizePipeline:
    @patch("metabolon.pathways.overnight.time.sleep")
    @patch("metabolon.pathways.overnight.publish", return_value=True)
    @patch("metabolon.pathways.overnight.compose_post", return_value=Path("/fake/post.md"))
    @patch("metabolon.pathways.overnight.metabolise", return_value="crystal text")
    @patch("metabolon.pathways.overnight.LOGDIR", new_callable=lambda: PropertyMock)
    def test_happy_path(self, mock_logdir_prop, mock_metabolise, mock_compose, mock_publish, mock_sleep):
        fake_logdir = MagicMock()
        fake_summary = MagicMock()
        fake_logdir.__truediv__ = MagicMock(return_value=fake_summary)
        with patch.object(mod, "LOGDIR", fake_logdir):
            results = mod.metabolize_pipeline(
                [{"seed": "s1", "slug": "slug-1", "title": "Title 1"}]
            )
        assert results["published"] == ["slug-1"]
        assert results["failed"] == []
        assert results["no_convergence"] == []
        mock_sleep.assert_called_once_with(5)

    @patch("metabolon.pathways.overnight.time.sleep")
    @patch("metabolon.pathways.overnight.publish")
    @patch("metabolon.pathways.overnight.compose_post", return_value=Path("/fake/post.md"))
    @patch("metabolon.pathways.overnight.metabolise", return_value="crystal")
    @patch("metabolon.pathways.overnight.LOGDIR", new_callable=lambda: PropertyMock)
    def test_compose_failure(self, mock_logdir_prop, mock_metabolise, mock_compose, mock_publish, mock_sleep):
        mock_publish.return_value = True
        mock_compose.return_value = None
        fake_logdir = MagicMock()
        fake_summary = MagicMock()
        fake_logdir.__truediv__ = MagicMock(return_value=fake_summary)
        with patch.object(mod, "LOGDIR", fake_logdir):
            results = mod.metabolize_pipeline(
                [{"seed": "s1", "slug": "slug-1", "title": "Title 1"}]
            )
        assert results["published"] == []
        assert results["failed"] == ["slug-1"]

    @patch("metabolon.pathways.overnight.time.sleep")
    @patch("metabolon.pathways.overnight.publish", return_value=False)
    @patch("metabolon.pathways.overnight.compose_post", return_value=Path("/fake/post.md"))
    @patch("metabolon.pathways.overnight.metabolise", return_value="crystal")
    @patch("metabolon.pathways.overnight.LOGDIR", new_callable=lambda: PropertyMock)
    def test_publish_failure(self, mock_logdir_prop, mock_metabolise, mock_compose, mock_publish, mock_sleep):
        fake_logdir = MagicMock()
        fake_summary = MagicMock()
        fake_logdir.__truediv__ = MagicMock(return_value=fake_summary)
        with patch.object(mod, "LOGDIR", fake_logdir):
            results = mod.metabolize_pipeline(
                [{"seed": "s1", "slug": "slug-1", "title": "Title 1"}]
            )
        assert results["published"] == []
        assert results["failed"] == ["slug-1"]

    @patch("metabolon.pathways.overnight.time.sleep")
    @patch("metabolon.pathways.overnight.publish")
    @patch("metabolon.pathways.overnight.compose_post")
    @patch("metabolon.pathways.overnight.metabolise", return_value=None)
    @patch("metabolon.pathways.overnight.LOGDIR", new_callable=lambda: PropertyMock)
    def test_no_convergence(self, mock_logdir_prop, mock_metabolise, mock_compose, mock_publish, mock_sleep):
        fake_logdir = MagicMock()
        fake_summary = MagicMock()
        fake_logdir.__truediv__ = MagicMock(return_value=fake_summary)
        with patch.object(mod, "LOGDIR", fake_logdir):
            results = mod.metabolize_pipeline(
                [{"seed": "s1", "slug": "slug-1", "title": "Title 1"}]
            )
        assert results["no_convergence"] == ["slug-1"]
        mock_compose.assert_not_called()
        mock_publish.assert_not_called()

    @patch("metabolon.pathways.overnight.time.sleep")
    @patch("metabolon.pathways.overnight.publish", return_value=True)
    @patch("metabolon.pathways.overnight.compose_post", return_value=Path("/fake/post.md"))
    @patch("metabolon.pathways.overnight.metabolise", return_value="crystal")
    @patch("metabolon.pathways.overnight.LOGDIR", new_callable=lambda: PropertyMock)
    def test_writes_summary_json(self, mock_logdir_prop, mock_metabolise, mock_compose, mock_publish, mock_sleep):
        fake_logdir = MagicMock()
        fake_summary = MagicMock()
        fake_logdir.__truediv__ = MagicMock(return_value=fake_summary)
        with patch.object(mod, "LOGDIR", fake_logdir):
            results = mod.metabolize_pipeline(
                [{"seed": "s1", "slug": "slug-1", "title": "Title 1"}]
            )
        fake_summary.write_text.assert_called_once()
        written = fake_summary.write_text.call_args[0][0]
        parsed = json.loads(written)
        assert parsed["published"] == ["slug-1"]

    @patch("metabolon.pathways.overnight.time.sleep")
    @patch("metabolon.pathways.overnight.publish", return_value=True)
    @patch("metabolon.pathways.overnight.compose_post", return_value=Path("/fake/post.md"))
    @patch("metabolon.pathways.overnight.metabolise", return_value="crystal")
    @patch("metabolon.pathways.overnight.LOGDIR", new_callable=lambda: PropertyMock)
    def test_multiple_seeds(self, mock_logdir_prop, mock_metabolise, mock_compose, mock_publish, mock_sleep):
        seeds = [
            {"seed": "s1", "slug": "slug-1", "title": "T1"},
            {"seed": "s2", "slug": "slug-2", "title": "T2"},
            {"seed": "s3", "slug": "slug-3", "title": "T3"},
        ]
        # Make the second seed fail metabolise
        mock_metabolise.side_effect = ["crystal", None, "crystal"]
        fake_logdir = MagicMock()
        fake_summary = MagicMock()
        fake_logdir.__truediv__ = MagicMock(return_value=fake_summary)
        with patch.object(mod, "LOGDIR", fake_logdir):
            results = mod.metabolize_pipeline(seeds)
        assert results["published"] == ["slug-1", "slug-3"]
        assert results["no_convergence"] == ["slug-2"]
        assert mock_sleep.call_count == 2  # only for published seeds


# ── _acquire_catalyst ────────────────────────────────────────────────────────

class TestAcquireCatalyst:
    def test_returns_symbiont_module(self):
        from metabolon import symbiont as real_symbiont

        result = mod._acquire_catalyst()
        assert result is real_symbiont
