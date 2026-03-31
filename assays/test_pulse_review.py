#!/usr/bin/env python3
from __future__ import annotations

"""Tests for effectors/pulse-review — cross-model review of copia manifests.

Pulse-review is a script (effectors/pulse-review), not an importable module.
It is loaded via exec() into isolated namespaces.
"""


import subprocess
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PULSE_REVIEW_PATH = Path(__file__).resolve().parents[1] / "effectors" / "pulse-review"


# ── Fixture ─────────────────────────────────────────────────────────────────


@pytest.fixture()
def pr(tmp_path):
    """Load pulse-review via exec into an isolated namespace dict."""
    ns: dict = {"__name__": "test_pulse_review", "__doc__": ""}
    source = PULSE_REVIEW_PATH.read_text(encoding="utf-8")
    exec(source, ns)
    return ns


# ── main: argument handling ────────────────────────────────────────────────


class TestMainArgs:
    def test_no_args_shows_help(self, pr, capsys):
        """Should print docstring and exit 0 when no args given."""
        with patch.object(sys, "argv", ["pulse-review"]):
            with pytest.raises(SystemExit) as exc_info:
                pr["main"]()
        assert exc_info.value.code == 0
        out = capsys.readouterr().out
        assert "copia-review" in out.lower() or "manifest" in out.lower()

    def test_help_flag_exits_zero(self, pr, capsys):
        """Should print help and exit 0 with -h flag."""
        with patch.object(sys, "argv", ["pulse-review", "-h"]):
            with pytest.raises(SystemExit) as exc_info:
                pr["main"]()
        assert exc_info.value.code == 0

    def test_missing_manifest_exits(self, pr, tmp_path, capsys):
        """Should exit 1 when manifest file doesn't exist."""
        nonexistent = tmp_path / "no-such-manifest.md"
        with patch.object(sys, "argv", ["pulse-review", str(nonexistent)]):
            with pytest.raises(SystemExit) as exc_info:
                pr["main"]()
        assert exc_info.value.code == 1

    def test_with_manifest_calls_parallel_query(self, pr, tmp_path, capsys):
        """Should call parallel_query when given a valid manifest."""
        manifest = tmp_path / "manifest.md"
        manifest.write_text("# Manifest\n- item 1\n- item 2\n", encoding="utf-8")

        mock_pq = MagicMock(return_value=[("gemini-3.1-pro", "Looks good."), ("codex", "Clean.")])
        pr["parallel_query"] = mock_pq

        with patch.object(sys, "argv", ["pulse-review", str(manifest)]), \
             patch.object(Path, "home", return_value=tmp_path):
            pr["main"]()

        mock_pq.assert_called_once()
        # Check prompt includes the manifest path
        call_args = mock_pq.call_args
        prompt = call_args[0][1]  # second positional arg is the prompt
        assert str(manifest) in prompt


# ── output formatting ──────────────────────────────────────────────────────


class TestOutputFormatting:
    def test_creates_output_file(self, pr, tmp_path, capsys):
        """Should create a review markdown file in ~/tmp/."""
        manifest = tmp_path / "manifest.md"
        manifest.write_text("# Test\n", encoding="utf-8")

        pr["parallel_query"] = MagicMock(
            return_value=[("gemini-3.1-pro", "Gemini review text."), ("codex", "Codex review text.")]
        )
        with patch.object(sys, "argv", ["pulse-review", str(manifest)]), \
             patch.object(Path, "home", return_value=tmp_path):
            pr["main"]()

        out_dir = tmp_path / "tmp"
        assert out_dir.exists()
        review_files = list(out_dir.glob("copia-review-*.md"))
        assert len(review_files) == 1
        content = review_files[0].read_text(encoding="utf-8")
        assert "Gemini review text." in content
        assert "Codex review text." in content

    def test_output_has_correct_headers(self, pr, tmp_path, capsys):
        """Should have proper markdown structure with model labels."""
        manifest = tmp_path / "manifest.md"
        manifest.write_text("# Test\n", encoding="utf-8")

        pr["parallel_query"] = MagicMock(
            return_value=[("gemini-3.1-pro", "Review A."), ("codex", "Review B.")]
        )
        with patch.object(sys, "argv", ["pulse-review", str(manifest)]), \
             patch.object(Path, "home", return_value=tmp_path):
            pr["main"]()

        out_dir = tmp_path / "tmp"
        review_file = list(out_dir.glob("copia-review-*.md"))[0]
        content = review_file.read_text(encoding="utf-8")
        assert "# Copia Review" in content
        assert "## Gemini 3.1 Pro" in content
        assert "## Codex (GPT-5.4)" in content

    def test_output_includes_manifest_path(self, pr, tmp_path, capsys):
        """Should include the manifest path in the output."""
        manifest = tmp_path / "manifest.md"
        manifest.write_text("# Test\n", encoding="utf-8")

        pr["parallel_query"] = MagicMock(
            return_value=[("gemini-3.1-pro", "ok"), ("codex", "ok")]
        )
        with patch.object(sys, "argv", ["pulse-review", str(manifest)]), \
             patch.object(Path, "home", return_value=tmp_path):
            pr["main"]()

        out_dir = tmp_path / "tmp"
        review_file = list(out_dir.glob("copia-review-*.md"))[0]
        content = review_file.read_text(encoding="utf-8")
        assert str(manifest) in content

    def test_missing_model_response_shows_fallback(self, pr, tmp_path, capsys):
        """Should show '(no response)' when a model is missing from results."""
        manifest = tmp_path / "manifest.md"
        manifest.write_text("# Test\n", encoding="utf-8")

        # Only one model responds
        pr["parallel_query"] = MagicMock(
            return_value=[("gemini-3.1-pro", "Only Gemini responded.")]
        )
        with patch.object(sys, "argv", ["pulse-review", str(manifest)]), \
             patch.object(Path, "home", return_value=tmp_path):
            pr["main"]()

        out_dir = tmp_path / "tmp"
        review_file = list(out_dir.glob("copia-review-*.md"))[0]
        content = review_file.read_text(encoding="utf-8")
        assert "(no response)" in content

    def test_prints_console_summary(self, pr, tmp_path, capsys):
        """Should print review summary to stdout."""
        manifest = tmp_path / "manifest.md"
        manifest.write_text("# Test\n", encoding="utf-8")

        pr["parallel_query"] = MagicMock(
            return_value=[("gemini-3.1-pro", "Review text."), ("codex", "Codex text.")]
        )
        with patch.object(sys, "argv", ["pulse-review", str(manifest)]), \
             patch.object(Path, "home", return_value=tmp_path):
            pr["main"]()

        out = capsys.readouterr().out
        assert "Reviewing:" in out
        assert "Models:" in out
        assert "Running reviews" in out
        assert "Review text." in out

    def test_prints_models_correctly(self, pr, tmp_path, capsys):
        """Should print human-readable model names."""
        manifest = tmp_path / "manifest.md"
        manifest.write_text("# Test\n", encoding="utf-8")

        pr["parallel_query"] = MagicMock(
            return_value=[("gemini-3.1-pro", "ok"), ("codex", "ok")]
        )
        with patch.object(sys, "argv", ["pulse-review", str(manifest)]), \
             patch.object(Path, "home", return_value=tmp_path):
            pr["main"]()

        out = capsys.readouterr().out
        assert "Gemini 3.1 Pro" in out
        assert "Codex (GPT-5.4)" in out


# ── constants ───────────────────────────────────────────────────────────────


class TestConstants:
    def test_models_list(self, pr):
        """Should have exactly two models configured."""
        assert len(pr["MODELS"]) == 2
        assert "gemini-3.1-pro" in pr["MODELS"]
        assert "codex" in pr["MODELS"]

    def test_timeout_value(self, pr):
        """Timeout should be 120 seconds."""
        assert pr["TIMEOUT"] == 120

    def test_model_labels(self, pr):
        """MODEL_LABELS should map internal names to display names."""
        assert pr["MODEL_LABELS"]["gemini-3.1-pro"] == "Gemini 3.1 Pro"
        assert pr["MODEL_LABELS"]["codex"] == "Codex (GPT-5.4)"

    def test_prompt_template_contains_placeholders(self, pr):
        """PROMPT_TEMPLATE should contain manifest_path placeholder."""
        assert "{manifest_path}" in pr["PROMPT_TEMPLATE"]
        assert "ROUTING" in pr["PROMPT_TEMPLATE"]
        assert "QUALITY" in pr["PROMPT_TEMPLATE"]


# ── CLI subprocess ──────────────────────────────────────────────────────────


class TestCLISubprocess:
    def test_no_args_shows_help(self):
        """Running pulse-review with no args should show help and exit 0."""
        r = subprocess.run(
            [sys.executable, str(PULSE_REVIEW_PATH)],
            capture_output=True, text=True, timeout=60,
        )
        assert r.returncode == 0
        assert "copia-review" in r.stdout.lower() or "manifest" in r.stdout.lower()

    def test_nonexistent_manifest_exits_nonzero(self):
        """Running with a nonexistent manifest path should exit nonzero."""
        r = subprocess.run(
            [sys.executable, str(PULSE_REVIEW_PATH), "/tmp/no-such-file-xyz.md"],
            capture_output=True, text=True, timeout=60,
        )
        assert r.returncode != 0
        assert "not found" in r.stderr.lower()
