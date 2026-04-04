"""Tests for phenotype_rename — tmux window labeling from prompts."""

import pathlib
import runpy
import sys
from unittest.mock import patch

SCRIPT = str(
    pathlib.Path(__file__).resolve().parent.parent
    / "membrane"
    / "cytoskeleton"
    / "phenotype_rename.py"
)


def _label(prompt: str) -> str:
    """Run phenotype_rename.py and capture the tmux rename-window label."""
    with patch("subprocess.run") as mock_run:
        with patch.object(sys, "argv", ["phenotype_rename.py", prompt, "@99"]):
            try:
                runpy.run_path(SCRIPT, run_name="__main__")
            except SystemExit:
                pass

        if mock_run.called:
            args = mock_run.call_args[0][0]
            # args = ["tmux", "rename-window", "-t", "@99", label]
            return args[-1]
        return ""


# --- Current behavior (regression) ---


class TestSlashCommands:
    def test_slash_command_uses_name(self):
        assert _label("/circadian") == "circadian"

    def test_slash_with_args(self):
        assert _label("/fasti list tomorrow") == "fasti"

    def test_long_slash_truncated(self):
        label = _label("/superlongcommandname-that-exceeds")
        assert len(label) <= 20


class TestContentWords:
    def test_basic_prompt(self):
        label = _label("fix the rheotaxis backend")
        assert len(label) > 0
        assert len(label) <= 20

    def test_empty_prompt_no_rename(self):
        assert _label("") == ""

    def test_all_stopwords_no_rename(self):
        assert _label("can you help me with this") == ""


# --- Improvements ---


class TestFilePaths:
    """Paths should yield basename as high-signal token."""

    def test_absolute_path(self):
        label = _label("fix bug in /home/terry/germline/metabolon/enzymes/golem_queue.py")
        assert "golem" in label or "queue" in label

    def test_relative_path(self):
        label = _label("read membrane/cytoskeleton/synapse.py")
        assert "synapse" in label

    def test_tilde_path(self):
        label = _label("edit ~/germline/effectors/golem")
        assert "golem" in label


class TestActionVerbs:
    """Action verbs (fix, debug, refactor, deploy) are high-signal for tab names."""

    def test_fix_verb_kept(self):
        label = _label("fix rheotaxis backend failures")
        assert "fix" in label.lower() or "rheotaxis" in label.lower()

    def test_debug_verb_kept(self):
        label = _label("debug temporal dispatch poller")
        assert "debug" in label.lower() or "temporal" in label.lower()


class TestSnakeCamelCase:
    """snake_case and CamelCase should split into meaningful parts."""

    def test_snake_case_splits(self):
        label = _label("update phenotype_rename logic")
        # Should see "phenotype" or "rename" as separate tokens
        assert "phenotype" in label or "rename" in label

    def test_camel_case_splits(self):
        label = _label("refactor BatchHttpRequest handler")
        assert "batch" in label.lower() or "http" in label.lower() or "request" in label.lower()


class TestQuotedStrings:
    """Quoted strings are almost always the intent — prioritize them."""

    def test_single_quoted(self):
        label = _label("search for 'tmux rename'")
        assert "tmux" in label.lower() or "rename" in label.lower()

    def test_double_quoted(self):
        label = _label('grep for "golem dispatch"')
        assert "golem" in label.lower() or "dispatch" in label.lower()


class TestTruncation:
    def test_max_20_chars(self):
        label = _label(
            "refactor the extremely complicated authentication middleware system"
        )
        assert len(label) <= 20
