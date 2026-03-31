"""Tests for effectors/chemoreception.py — keyword-based retrieval hook."""

import json
import sys
import time
from io import StringIO
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


# Import the module directly (it has a .py extension and is on the path)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "effectors"))
import chemoreception


# ── tokenize ──────────────────────────────────────────────────────────────────


class TestTokenize:
    def test_extracts_meaningful_words(self):
        result = chemoreception.tokenize("How do I deploy a Flask app to AWS?")
        assert "deploy" in result
        assert "flask" in result
        assert "app" in result
        assert "aws" in result

    def test_filters_stop_words(self):
        result = chemoreception.tokenize("This is a test of the system")
        # "this", "is", "a", "of", "the" are all stop words
        assert "this" not in result
        assert "is" not in result
        assert "a" not in result
        assert "of" not in result
        assert "the" not in result
        assert "test" in result
        assert "system" in result

    def test_filters_short_words(self):
        result = chemoreception.tokenize("I am a go")
        # len <= 2 are filtered, plus stop words
        assert all(len(w) > 2 for w in result)

    def test_lowercase(self):
        result = chemoreception.tokenize("Docker Kubernetes Terraform")
        assert all(w.islower() for w in result)

    def test_empty_string(self):
        assert chemoreception.tokenize("") == []

    def test_hyphenated_words(self):
        result = chemoreception.tokenize("use auto-scaling policies")
        assert "auto-scaling" in result

    def test_underscores_preserved(self):
        result = chemoreception.tokenize("configure my_module")
        assert "my_module" in result


# ── should_debounce / update_debounce ─────────────────────────────────────────


class TestDebounce:
    def test_should_debounce_when_recent(self, tmp_path):
        debounce_file = tmp_path / "state.json"
        debounce_file.write_text(str(time.time()))
        with patch.object(chemoreception, "DEBOUNCE_FILE", debounce_file):
            assert chemoreception.should_debounce() is True

    def test_should_not_debounce_when_stale(self, tmp_path):
        debounce_file = tmp_path / "state.json"
        debounce_file.write_text(str(time.time() - 1000))
        with patch.object(chemoreception, "DEBOUNCE_FILE", debounce_file):
            assert chemoreception.should_debounce() is False

    def test_should_not_debounce_when_no_file(self, tmp_path):
        debounce_file = tmp_path / "nonexistent.json"
        with patch.object(chemoreception, "DEBOUNCE_FILE", debounce_file):
            assert chemoreception.should_debounce() is False

    def test_should_not_debounce_on_corrupt_file(self, tmp_path):
        debounce_file = tmp_path / "state.json"
        debounce_file.write_text("not-a-number")
        with patch.object(chemoreception, "DEBOUNCE_FILE", debounce_file):
            assert chemoreception.should_debounce() is False

    def test_update_debounce_writes_timestamp(self, tmp_path):
        debounce_file = tmp_path / "state.json"
        with patch.object(chemoreception, "DEBOUNCE_FILE", debounce_file):
            chemoreception.update_debounce()
        content = float(debounce_file.read_text())
        assert abs(content - time.time()) < 2

    def test_update_debounce_creates_parent_dirs(self, tmp_path):
        debounce_file = tmp_path / "deep" / "nested" / "state.json"
        with patch.object(chemoreception, "DEBOUNCE_FILE", debounce_file):
            chemoreception.update_debounce()
        assert debounce_file.exists()


# ── collect_documents ─────────────────────────────────────────────────────────


class TestCollectDocuments:
    def test_collects_md_files(self, tmp_path):
        ref_dir = tmp_path / "euchromatin"
        ref_dir.mkdir()
        (ref_dir / "note1.md").write_text("A" * 60)
        (ref_dir / "note2.md").write_text("B" * 60)

        with patch.object(chemoreception, "REFERENCE_DIR", ref_dir):
            docs = chemoreception.collect_documents()
        assert len(docs) == 2
        assert "note1.md" in docs
        assert "note2.md" in docs

    def test_skips_small_files(self, tmp_path):
        ref_dir = tmp_path / "euchromatin"
        ref_dir.mkdir()
        (ref_dir / "tiny.md").write_text("hi")  # < 50 chars

        with patch.object(chemoreception, "REFERENCE_DIR", ref_dir):
            docs = chemoreception.collect_documents()
        assert len(docs) == 0

    def test_skips_excluded_patterns(self, tmp_path):
        ref_dir = tmp_path / "euchromatin"
        obsidian = ref_dir / ".obsidian"
        obsidian.mkdir(parents=True)
        (obsidian / "config.md").write_text("A" * 60)
        (ref_dir / "knowledge-structure.md").write_text("B" * 60)
        (ref_dir / "good.md").write_text("C" * 60)

        with patch.object(chemoreception, "REFERENCE_DIR", ref_dir):
            docs = chemoreception.collect_documents()
        assert "good.md" in docs
        assert len(docs) == 1

    def test_empty_dir(self, tmp_path):
        ref_dir = tmp_path / "euchromatin"
        ref_dir.mkdir()
        with patch.object(chemoreception, "REFERENCE_DIR", ref_dir):
            docs = chemoreception.collect_documents()
        assert docs == {}

    def test_nonexistent_dir(self, tmp_path):
        ref_dir = tmp_path / "nope"
        with patch.object(chemoreception, "REFERENCE_DIR", ref_dir):
            docs = chemoreception.collect_documents()
        assert docs == {}


# ── score_documents ───────────────────────────────────────────────────────────


class TestScoreDocuments:
    def test_ranks_relevant_docs_higher(self):
        docs = {
            "python.md": "Python programming language for data science",
            "cooking.md": "How to bake a chocolate cake with frosting",
            "python-web.md": "Python web frameworks Flask Django FastAPI",
        }
        tokens = chemoreception.tokenize("Python web framework")
        scored = chemoreception.score_documents(tokens, docs)
        # python-web.md should rank high (filename + content match)
        paths = [p for p, _ in scored]
        assert "python-web.md" in paths

    def test_empty_query(self):
        docs = {"a.md": "content"}
        assert chemoreception.score_documents([], docs) == []

    def test_empty_docs(self):
        tokens = chemoreception.tokenize("python")
        assert chemoreception.score_documents(tokens, {}) == []

    def test_no_matching_docs(self):
        docs = {"a.md": "cooking recipes for dinner"}
        tokens = chemoreception.tokenize("kubernetes docker deployment")
        scored = chemoreception.score_documents(tokens, docs)
        assert scored == []

    def test_respects_top_k(self):
        docs = {f"doc{i}.md": f"python keyword match item {i}" for i in range(10)}
        tokens = chemoreception.tokenize("python keyword")
        scored = chemoreception.score_documents(tokens, docs)
        assert len(scored) <= chemoreception.TOP_K


# ── format_suggestions ────────────────────────────────────────────────────────


class TestFormatSuggestions:
    def test_formats_single_match(self, tmp_path):
        ref_dir = tmp_path / "euchromatin"
        ref_dir.mkdir()
        doc = ref_dir / "my-note.md"
        doc.write_text("# My Note Title\nSome interesting content about Python.")

        with patch.object(chemoreception, "REFERENCE_DIR", ref_dir):
            result = chemoreception.format_suggestions([("my-note.md", 5.0)])
        assert "my-note" in result
        assert "My Note Title" in result

    def test_formats_multiple_matches(self, tmp_path):
        ref_dir = tmp_path / "euchromatin"
        ref_dir.mkdir()
        (ref_dir / "a.md").write_text("# Alpha\nAlpha content.")
        (ref_dir / "b.md").write_text("# Beta\nBeta content.")

        with patch.object(chemoreception, "REFERENCE_DIR", ref_dir):
            result = chemoreception.format_suggestions([
                ("a.md", 5.0),
                ("b.md", 3.0),
            ])
        assert "Alpha" in result
        assert "Beta" in result

    def test_handles_missing_file_gracefully(self, tmp_path):
        ref_dir = tmp_path / "euchromatin"
        ref_dir.mkdir()
        with patch.object(chemoreception, "REFERENCE_DIR", ref_dir):
            # File doesn't exist — should not crash
            result = chemoreception.format_suggestions([("missing.md", 1.0)])
        assert result == ""

    def test_strips_frontmatter(self, tmp_path):
        ref_dir = tmp_path / "euchromatin"
        ref_dir.mkdir()
        doc = ref_dir / "frontmatter.md"
        doc.write_text("---\ntitle: Test\ntags: [a]\n---\n# Real Title\nBody text here.")

        with patch.object(chemoreception, "REFERENCE_DIR", ref_dir):
            result = chemoreception.format_suggestions([("frontmatter.md", 2.0)])
        assert "Real Title" in result


# ── main ──────────────────────────────────────────────────────────────────────


class TestMain:
    def test_main_with_valid_prompt(self, tmp_path):
        ref_dir = tmp_path / "euchromatin"
        ref_dir.mkdir()
        (ref_dir / "docker.md").write_text("# Docker Guide\nHow to use Docker containers for deployment.")
        debounce_file = tmp_path / "state.json"
        debounce_file.write_text(str(0))  # long ago — no debounce

        hook_input = json.dumps({"prompt": "How do I deploy Docker containers to production?"})

        with patch.object(chemoreception, "REFERENCE_DIR", ref_dir), \
             patch.object(chemoreception, "DEBOUNCE_FILE", debounce_file), \
             patch("sys.stdin", StringIO(hook_input)), \
             patch("builtins.print") as mock_print:
            chemoreception.main()
            mock_print.assert_called_once()
            output = json.loads(mock_print.call_args[0][0])
            assert output["result"] == "continue"
            assert "system-prompt-suffix" in output["metadata"]

    def test_main_short_prompt_skipped(self, tmp_path):
        hook_input = json.dumps({"prompt": "hi"})
        with patch("sys.stdin", StringIO(hook_input)), \
             patch("builtins.print") as mock_print:
            chemoreception.main()
            mock_print.assert_not_called()

    def test_main_no_prompt_skipped(self, tmp_path):
        hook_input = json.dumps({})
        with patch("sys.stdin", StringIO(hook_input)), \
             patch("builtins.print") as mock_print:
            chemoreception.main()
            mock_print.assert_not_called()

    def test_main_debounced_skipped(self, tmp_path):
        debounce_file = tmp_path / "state.json"
        debounce_file.write_text(str(time.time()))  # just now — debounce
        hook_input = json.dumps({"prompt": "How do I deploy Docker containers to production?"})

        with patch.object(chemoreception, "DEBOUNCE_FILE", debounce_file), \
             patch("sys.stdin", StringIO(hook_input)), \
             patch("builtins.print") as mock_print:
            chemoreception.main()
            mock_print.assert_not_called()

    def test_main_invalid_json_skipped(self, tmp_path):
        with patch("sys.stdin", StringIO("not json")), \
             patch("builtins.print") as mock_print:
            chemoreception.main()
            mock_print.assert_not_called()

    def test_main_few_tokens_skipped(self, tmp_path):
        debounce_file = tmp_path / "state.json"
        debounce_file.write_text(str(0))
        hook_input = json.dumps({"prompt": "the is a"})  # all stop words → < 2 tokens

        with patch.object(chemoreception, "DEBOUNCE_FILE", debounce_file), \
             patch("sys.stdin", StringIO(hook_input)), \
             patch("builtins.print") as mock_print:
            chemoreception.main()
            mock_print.assert_not_called()

    def test_main_no_docs_skipped(self, tmp_path):
        ref_dir = tmp_path / "euchromatin"
        ref_dir.mkdir()  # empty
        debounce_file = tmp_path / "state.json"
        debounce_file.write_text(str(0))
        hook_input = json.dumps({"prompt": "How do I deploy Docker containers to production?"})

        with patch.object(chemoreception, "REFERENCE_DIR", ref_dir), \
             patch.object(chemoreception, "DEBOUNCE_FILE", debounce_file), \
             patch("sys.stdin", StringIO(hook_input)), \
             patch("builtins.print") as mock_print:
            chemoreception.main()
            mock_print.assert_not_called()
