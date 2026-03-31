from __future__ import annotations

"""Tests for effectors/chemoreception.py — keyword-based retrieval hook."""

import json
import sys
import time
from io import StringIO
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# ── Load effector via exec (never import) ─────────────────────────────────────

_CHEMO_PATH = Path(__file__).resolve().parents[1] / "effectors" / "chemoreception.py"
_CHEMO_CODE = _CHEMO_PATH.read_text()
_mod: dict = {"__name__": "chemoreception", "__file__": str(_CHEMO_PATH)}
exec(_CHEMO_CODE, _mod)


class _M:
    """Proxy that reads/writes the exec'd module dict."""

    def __getattr__(self, name):
        return _mod[name]

    def __setattr__(self, name, value):
        _mod[name] = value


chemo = _M()


# ── Script structure tests ────────────────────────────────────────────────────


class TestScriptStructure:
    def test_script_exists(self):
        assert _CHEMO_PATH.exists()

    def test_has_python_shebang(self):
        first = _CHEMO_PATH.read_text().splitlines()[0]
        assert "python" in first.lower()

    def test_has_main_guard(self):
        assert 'if __name__ == "__main__"' in _CHEMO_CODE


# ── Constants ─────────────────────────────────────────────────────────────────


class TestConstants:
    def test_reference_dir_under_home(self):
        assert "euchromatin" in str(chemo.REFERENCE_DIR)

    def test_debounce_seconds_is_positive(self):
        assert chemo.DEBOUNCE_SECONDS > 0

    def test_top_k_is_positive(self):
        assert chemo.TOP_K > 0

    def test_min_score_is_positive(self):
        assert chemo.MIN_SCORE > 0

    def test_stop_words_is_set(self):
        assert isinstance(chemo.STOP_WORDS, set)
        assert "the" in chemo.STOP_WORDS
        assert "and" in chemo.STOP_WORDS

    def test_skip_patterns_is_set(self):
        assert isinstance(chemo.SKIP_PATTERNS, set)
        assert "knowledge-structure.md" in chemo.SKIP_PATTERNS


# ── tokenize ──────────────────────────────────────────────────────────────────


class TestTokenize:
    def test_extracts_meaningful_words(self):
        result = chemo.tokenize("How do I deploy a Flask app to AWS?")
        assert "deploy" in result
        assert "flask" in result
        assert "app" in result
        assert "aws" in result

    def test_filters_stop_words(self):
        result = chemo.tokenize("This is a test of the system")
        assert "this" not in result
        assert "is" not in result
        assert "a" not in result
        assert "of" not in result
        assert "the" not in result
        assert "test" in result
        assert "system" in result

    def test_filters_short_words(self):
        result = chemo.tokenize("I am a go")
        assert all(len(w) > 2 for w in result)

    def test_lowercase(self):
        result = chemo.tokenize("Docker Kubernetes Terraform")
        assert all(w.islower() for w in result)

    def test_empty_string(self):
        assert chemo.tokenize("") == []

    def test_hyphenated_words(self):
        result = chemo.tokenize("use auto-scaling policies")
        assert "auto-scaling" in result

    def test_underscores_preserved(self):
        result = chemo.tokenize("configure my_module")
        assert "my_module" in result

    def test_numbers_in_tokens(self):
        result = chemo.tokenize("configure k8s cluster")
        assert "k8s" in result


# ── should_debounce / update_debounce ─────────────────────────────────────────


class TestDebounce:
    def test_should_debounce_when_recent(self, tmp_path):
        debounce_file = tmp_path / "state.json"
        debounce_file.write_text(str(time.time()))
        with _patch_attr("DEBOUNCE_FILE", debounce_file):
            assert chemo.should_debounce() is True

    def test_should_not_debounce_when_stale(self, tmp_path):
        debounce_file = tmp_path / "state.json"
        debounce_file.write_text(str(time.time() - 1000))
        with _patch_attr("DEBOUNCE_FILE", debounce_file):
            assert chemo.should_debounce() is False

    def test_should_not_debounce_when_no_file(self, tmp_path):
        debounce_file = tmp_path / "nonexistent.json"
        with _patch_attr("DEBOUNCE_FILE", debounce_file):
            assert chemo.should_debounce() is False

    def test_should_not_debounce_on_corrupt_file(self, tmp_path):
        debounce_file = tmp_path / "state.json"
        debounce_file.write_text("not-a-number")
        with _patch_attr("DEBOUNCE_FILE", debounce_file):
            assert chemo.should_debounce() is False

    def test_update_debounce_writes_timestamp(self, tmp_path):
        debounce_file = tmp_path / "state.json"
        with _patch_attr("DEBOUNCE_FILE", debounce_file):
            chemo.update_debounce()
        content = float(debounce_file.read_text())
        assert abs(content - time.time()) < 2

    def test_update_debounce_creates_parent_dirs(self, tmp_path):
        debounce_file = tmp_path / "deep" / "nested" / "state.json"
        with _patch_attr("DEBOUNCE_FILE", debounce_file):
            chemo.update_debounce()
        assert debounce_file.exists()


# ── collect_documents ─────────────────────────────────────────────────────────


class TestCollectDocuments:
    def test_collects_md_files(self, tmp_path):
        ref_dir = tmp_path / "euchromatin"
        ref_dir.mkdir()
        (ref_dir / "note1.md").write_text("A" * 60)
        (ref_dir / "note2.md").write_text("B" * 60)

        with _patch_attr("REFERENCE_DIR", ref_dir):
            docs = chemo.collect_documents()
        assert len(docs) == 2
        assert "note1.md" in docs
        assert "note2.md" in docs

    def test_skips_small_files(self, tmp_path):
        ref_dir = tmp_path / "euchromatin"
        ref_dir.mkdir()
        (ref_dir / "tiny.md").write_text("hi")

        with _patch_attr("REFERENCE_DIR", ref_dir):
            docs = chemo.collect_documents()
        assert len(docs) == 0

    def test_skips_excluded_patterns(self, tmp_path):
        ref_dir = tmp_path / "euchromatin"
        obsidian = ref_dir / ".obsidian"
        obsidian.mkdir(parents=True)
        (obsidian / "config.md").write_text("A" * 60)
        (ref_dir / "knowledge-structure.md").write_text("B" * 60)
        (ref_dir / "good.md").write_text("C" * 60)

        with _patch_attr("REFERENCE_DIR", ref_dir):
            docs = chemo.collect_documents()
        assert "good.md" in docs
        assert len(docs) == 1

    def test_collects_nested_files(self, tmp_path):
        ref_dir = tmp_path / "euchromatin"
        sub = ref_dir / "sub" / "dir"
        sub.mkdir(parents=True)
        (sub / "deep.md").write_text("D" * 60)

        with _patch_attr("REFERENCE_DIR", ref_dir):
            docs = chemo.collect_documents()
        assert len(docs) == 1
        key = list(docs.keys())[0]
        assert "deep.md" in key
        assert "sub" in key

    def test_empty_dir(self, tmp_path):
        ref_dir = tmp_path / "euchromatin"
        ref_dir.mkdir()
        with _patch_attr("REFERENCE_DIR", ref_dir):
            docs = chemo.collect_documents()
        assert docs == {}

    def test_nonexistent_dir(self, tmp_path):
        ref_dir = tmp_path / "nope"
        with _patch_attr("REFERENCE_DIR", ref_dir):
            docs = chemo.collect_documents()
        assert docs == {}


# ── score_documents ───────────────────────────────────────────────────────────


class TestScoreDocuments:
    def test_ranks_relevant_docs_higher(self):
        docs = {
            "python.md": "Python programming language for data science",
            "cooking.md": "How to bake a chocolate cake with frosting",
            "python-web.md": "Python web frameworks Flask Django FastAPI",
        }
        tokens = chemo.tokenize("Python web framework")
        scored = chemo.score_documents(tokens, docs)
        paths = [p for p, _ in scored]
        assert "python-web.md" in paths

    def test_empty_query(self):
        docs = {"a.md": "content"}
        assert chemo.score_documents([], docs) == []

    def test_empty_docs(self):
        tokens = chemo.tokenize("python")
        assert chemo.score_documents(tokens, {}) == []

    def test_no_matching_docs(self):
        docs = {"a.md": "cooking recipes for dinner"}
        tokens = chemo.tokenize("kubernetes docker deployment")
        scored = chemo.score_documents(tokens, docs)
        assert scored == []

    def test_respects_top_k(self):
        docs = {f"doc{i}.md": f"python keyword match item {i}" for i in range(10)}
        tokens = chemo.tokenize("python keyword")
        scored = chemo.score_documents(tokens, docs)
        assert len(scored) <= chemo.TOP_K

    def test_scores_are_sorted_descending(self):
        docs = {
            "low.md": "vaguely related topic",
            "high.md": "python python python python programming",
            "mid.md": "python code example",
        }
        tokens = chemo.tokenize("python")
        scored = chemo.score_documents(tokens, docs)
        scores = [s for _, s in scored]
        assert scores == sorted(scores, reverse=True)

    def test_filename_boost(self):
        """Docs whose filename matches the query should score higher."""
        docs = {
            "kubernetes-best-practices.md": "general devops guide",
            "random.md": "kubernetes kubernetes kubernetes kubernetes kubernetes",
        }
        tokens = chemo.tokenize("kubernetes best practices")
        scored = chemo.score_documents(tokens, docs)
        assert scored[0][0] == "kubernetes-best-practices.md"


# ── format_suggestions ────────────────────────────────────────────────────────


class TestFormatSuggestions:
    def test_formats_single_match(self, tmp_path):
        ref_dir = tmp_path / "euchromatin"
        ref_dir.mkdir()
        doc = ref_dir / "my-note.md"
        doc.write_text("# My Note Title\nSome interesting content about Python.")

        with _patch_attr("REFERENCE_DIR", ref_dir):
            result = chemo.format_suggestions([("my-note.md", 5.0)])
        assert "my-note" in result
        assert "My Note Title" in result

    def test_formats_multiple_matches(self, tmp_path):
        ref_dir = tmp_path / "euchromatin"
        ref_dir.mkdir()
        (ref_dir / "a.md").write_text("# Alpha\nAlpha content.")
        (ref_dir / "b.md").write_text("# Beta\nBeta content.")

        with _patch_attr("REFERENCE_DIR", ref_dir):
            result = chemo.format_suggestions([
                ("a.md", 5.0),
                ("b.md", 3.0),
            ])
        assert "Alpha" in result
        assert "Beta" in result

    def test_handles_missing_file_gracefully(self, tmp_path):
        ref_dir = tmp_path / "euchromatin"
        ref_dir.mkdir()
        with _patch_attr("REFERENCE_DIR", ref_dir):
            result = chemo.format_suggestions([("missing.md", 1.0)])
        assert result == ""

    def test_strips_frontmatter(self, tmp_path):
        ref_dir = tmp_path / "euchromatin"
        ref_dir.mkdir()
        doc = ref_dir / "frontmatter.md"
        doc.write_text("---\ntitle: Test\ntags: [a]\n---\n# Real Title\nBody text here.")

        with _patch_attr("REFERENCE_DIR", ref_dir):
            result = chemo.format_suggestions([("frontmatter.md", 2.0)])
        assert "Real Title" in result

    def test_uses_filename_when_no_heading(self, tmp_path):
        ref_dir = tmp_path / "euchromatin"
        ref_dir.mkdir()
        doc = ref_dir / "plain-doc.md"
        doc.write_text("No heading here, just plain text content about things.")

        with _patch_attr("REFERENCE_DIR", ref_dir):
            result = chemo.format_suggestions([("plain-doc.md", 1.0)])
        assert "plain-doc" in result


# ── main ──────────────────────────────────────────────────────────────────────


class TestMain:
    def test_main_with_valid_prompt(self, tmp_path):
        ref_dir = tmp_path / "euchromatin"
        ref_dir.mkdir()
        (ref_dir / "docker.md").write_text(
            "# Docker Guide\nHow to use Docker containers for deployment."
        )
        debounce_file = tmp_path / "state.json"
        debounce_file.write_text(str(0))

        hook_input = json.dumps(
            {"prompt": "How do I deploy Docker containers to production?"}
        )

        with _patch_attr("REFERENCE_DIR", ref_dir), \
             _patch_attr("DEBOUNCE_FILE", debounce_file), \
             patch.object(_mod["sys"], "argv", [str(_CHEMO_PATH)]), \
             patch.object(_mod["sys"], "stdin", StringIO(hook_input)), \
             patch("builtins.print") as mock_print:
            chemo.main()
            mock_print.assert_called_once()
            output = json.loads(mock_print.call_args[0][0])
            assert output["result"] == "continue"
            assert "system-prompt-suffix" in output["metadata"]

    def test_main_short_prompt_skipped(self):
        hook_input = json.dumps({"prompt": "hi"})
        with patch.object(_mod["sys"], "argv", [str(_CHEMO_PATH)]), \
             patch.object(_mod["sys"], "stdin", StringIO(hook_input)), \
             patch("builtins.print") as mock_print:
            chemo.main()
            mock_print.assert_not_called()

    def test_main_no_prompt_skipped(self):
        hook_input = json.dumps({})
        with patch.object(_mod["sys"], "argv", [str(_CHEMO_PATH)]), \
             patch.object(_mod["sys"], "stdin", StringIO(hook_input)), \
             patch("builtins.print") as mock_print:
            chemo.main()
            mock_print.assert_not_called()

    def test_main_debounced_skipped(self, tmp_path):
        debounce_file = tmp_path / "state.json"
        debounce_file.write_text(str(time.time()))
        hook_input = json.dumps(
            {"prompt": "How do I deploy Docker containers to production?"}
        )

        with _patch_attr("DEBOUNCE_FILE", debounce_file), \
             patch.object(_mod["sys"], "argv", [str(_CHEMO_PATH)]), \
             patch.object(_mod["sys"], "stdin", StringIO(hook_input)), \
             patch("builtins.print") as mock_print:
            chemo.main()
            mock_print.assert_not_called()

    def test_main_invalid_json_skipped(self):
        with patch.object(_mod["sys"], "argv", [str(_CHEMO_PATH)]), \
             patch.object(_mod["sys"], "stdin", StringIO("not json")), \
             patch("builtins.print") as mock_print:
            chemo.main()
            mock_print.assert_not_called()

    def test_main_few_tokens_skipped(self, tmp_path):
        debounce_file = tmp_path / "state.json"
        debounce_file.write_text(str(0))
        hook_input = json.dumps({"prompt": "the is a"})

        with _patch_attr("DEBOUNCE_FILE", debounce_file), \
             patch.object(_mod["sys"], "argv", [str(_CHEMO_PATH)]), \
             patch.object(_mod["sys"], "stdin", StringIO(hook_input)), \
             patch("builtins.print") as mock_print:
            chemo.main()
            mock_print.assert_not_called()

    def test_main_no_docs_skipped(self, tmp_path):
        ref_dir = tmp_path / "euchromatin"
        ref_dir.mkdir()
        debounce_file = tmp_path / "state.json"
        debounce_file.write_text(str(0))
        hook_input = json.dumps(
            {"prompt": "How do I deploy Docker containers to production?"}
        )

        with _patch_attr("REFERENCE_DIR", ref_dir), \
             _patch_attr("DEBOUNCE_FILE", debounce_file), \
             patch.object(_mod["sys"], "argv", [str(_CHEMO_PATH)]), \
             patch.object(_mod["sys"], "stdin", StringIO(hook_input)), \
             patch("builtins.print") as mock_print:
            chemo.main()
            mock_print.assert_not_called()

    def test_main_output_contains_reference_suggestions(self, tmp_path):
        ref_dir = tmp_path / "euchromatin"
        ref_dir.mkdir()
        (ref_dir / "k8s.md").write_text(
            "# Kubernetes\nKubernetes orchestration for container deployment."
        )
        debounce_file = tmp_path / "state.json"
        debounce_file.write_text(str(0))

        hook_input = json.dumps(
            {"prompt": "How do I deploy Kubernetes clusters?"}
        )

        with _patch_attr("REFERENCE_DIR", ref_dir), \
             _patch_attr("DEBOUNCE_FILE", debounce_file), \
             patch.object(_mod["sys"], "argv", [str(_CHEMO_PATH)]), \
             patch.object(_mod["sys"], "stdin", StringIO(hook_input)), \
             patch("builtins.print") as mock_print:
            chemo.main()
            output = json.loads(mock_print.call_args[0][0])
            suffix = output["metadata"]["system-prompt-suffix"]
            assert "reference-suggestions" in suffix
            assert "Kubernetes" in suffix


# ── Integration: end-to-end via subprocess ────────────────────────────────────


class TestSubprocessExecution:
    def test_script_runs_with_empty_stdin(self):
        result = _run_script(stdin_data="")
        assert result.returncode == 0

    def test_script_runs_with_valid_json(self):
        result = _run_script(
            stdin_data=json.dumps({"prompt": "test query about things"})
        )
        assert result.returncode == 0


# ── Helpers ───────────────────────────────────────────────────────────────────


import contextlib
import subprocess


@contextlib.contextmanager
def _patch_attr(name, value):
    """Patch a module-level variable in the exec'd namespace."""
    old = _mod.get(name)
    _mod[name] = value
    try:
        yield
    finally:
        if old is None:
            _mod.pop(name, None)
        else:
            _mod[name] = old


def _run_script(stdin_data: str) -> subprocess.CompletedProcess:
    """Run the effector as a subprocess."""
    return subprocess.run(
        [sys.executable, str(_CHEMO_PATH)],
        input=stdin_data,
        capture_output=True,
        text=True,
        timeout=10,
    )
