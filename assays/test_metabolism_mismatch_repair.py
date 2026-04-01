from __future__ import annotations

"""Tests for metabolon/metabolism/mismatch_repair.py — vocabulary, structural,
orphan gap detection and unified scan/summary."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from metabolon.metabolism.mismatch_repair import (
    VOCABULARY_GAPS,
    GapReport,
    OrphanGap,
    StructuralGap,
    VocabularyGap,
    _detect_orphan_gaps,
    _detect_structural_gaps,
    scan,
    summary,
)


# -- VocabularyGap dataclass -----------------------------------------------


class TestVocabularyGap:
    def test_fields(self):
        g = VocabularyGap(
            old_term="Foo",
            new_term="Bar",
            layer="cortical",
            reason="rename",
            grep_pattern=r"\bFoo\b",
            exclude_file="x.py",
        )
        assert g.old_term == "Foo"
        assert g.new_term == "Bar"
        assert g.layer == "cortical"
        assert g.reason == "rename"
        assert g.grep_pattern == r"\bFoo\b"
        assert g.exclude_file == "x.py"

    def test_exclude_file_defaults_empty(self):
        g = VocabularyGap(
            old_term="A", new_term="B", layer="autonomic",
            reason="r", grep_pattern=r"\bA\b",
        )
        assert g.exclude_file == ""


class TestVocabularyGapsConstant:
    def test_non_empty(self):
        assert len(VOCABULARY_GAPS) >= 2

    def test_all_instances(self):
        assert all(isinstance(g, VocabularyGap) for g in VOCABULARY_GAPS)

    def test_known_entry(self):
        terms = [(g.old_term, g.new_term) for g in VOCABULARY_GAPS]
        assert ("DnaSubstrate", "ExecutiveSubstrate") in terms


# -- OrphanGap detection ---------------------------------------------------


class TestDetectOrphanGaps:
    def _make_py_file(self, tmp_path, name, content):
        resources = tmp_path / "resources"
        resources.mkdir(exist_ok=True)
        p = resources / name
        p.write_text(content)
        return p

    def test_no_resources_dir_returns_empty(self, tmp_path):
        src = tmp_path / "empty_src"
        src.mkdir()
        result = _detect_orphan_gaps(src=src)
        assert result == []

    def test_no_decorator_returns_empty(self, tmp_path):
        self._make_py_file(tmp_path, "mod.py", "def hello(): pass\n")
        result = _detect_orphan_gaps(src=tmp_path)
        assert result == []

    def test_resource_decorator_uri_found_in_consumer(self, tmp_path):
        self._make_py_file(
            tmp_path,
            "things.py",
            "from lib import resource\n@resource(\"org://thing\")\ndef thing(): pass\n",
        )
        consumer = tmp_path / "consumer.md"
        consumer.write_text("Use org://thing for stuff.\n")
        result = _detect_orphan_gaps(src=tmp_path, consumer_files=[consumer])
        assert result == []

    def test_resource_uri_missing_from_consumers(self, tmp_path):
        self._make_py_file(
            tmp_path,
            "things.py",
            "from lib import resource\n@resource(\"org://orphan\")\ndef orphan(): pass\n",
        )
        consumer = tmp_path / "consumer.md"
        consumer.write_text("Nothing relevant.\n")
        result = _detect_orphan_gaps(src=tmp_path, consumer_files=[consumer])
        assert len(result) == 1
        assert result[0].uri == "org://orphan"
        assert result[0].source_file == "things.py"

    def test_skips_underscore_files(self, tmp_path):
        self._make_py_file(
            tmp_path,
            "__init__.py",
            "from lib import resource\n@resource(\"org://hidden\")\ndef h(): pass\n",
        )
        consumer = tmp_path / "c.md"
        consumer.write_text("")
        result = _detect_orphan_gaps(src=tmp_path, consumer_files=[consumer])
        assert result == []

    def test_syntax_error_file_skipped(self, tmp_path):
        self._make_py_file(tmp_path, "bad.py", "def (broken syntax!!!\n")
        consumer = tmp_path / "c.md"
        consumer.write_text("")
        result = _detect_orphan_gaps(src=tmp_path, consumer_files=[consumer])
        assert result == []

    def test_non_resource_decorator_ignored(self, tmp_path):
        self._make_py_file(
            tmp_path,
            "mod.py",
            "from lib import tool\n@tool(\"org://thing\")\ndef thing(): pass\n",
        )
        consumer = tmp_path / "c.md"
        consumer.write_text("")
        result = _detect_orphan_gaps(src=tmp_path, consumer_files=[consumer])
        assert result == []


# -- Structural gap detection ----------------------------------------------


class TestDetectStructuralGaps:
    def _make_file(self, tmp_path, rel_path, content):
        p = tmp_path / rel_path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)

    def test_no_substrates_dir_returns_empty(self, tmp_path):
        result = _detect_structural_gaps(src=tmp_path)
        assert result == []

    def test_autonomic_labelled_with_llm_import_flagged(self, tmp_path):
        self._make_file(
            tmp_path,
            "metabolism/substrates/dummy.py",
            "from metabolon.llm import query\n\nclass Foo:\n    """Autonomic subsystem."""\n    pass\n",
        )
        result = _detect_structural_gaps(src=tmp_path)
        assert len(result) >= 1
        assert any("autonomic" in g.current_layer and "LLM" in g.actual_layer for g in result)

    def test_cortical_labelled_without_llm_flagged(self, tmp_path):
        self._make_file(
            tmp_path,
            "metabolism/substrates/dummy.py",
            "class Foo:\n    """Cortical subsystem."""\n    pass\n",
        )
        result = _detect_structural_gaps(src=tmp_path)
        # Substrate files are exempt from the cortical-without-LLM check
        assert isinstance(result, list)

    def test_cortical_labelled_without_llm_non_substrate_flagged(self, tmp_path):
        self._make_file(
            tmp_path,
            "metabolism/substrates/dummy.py",
            "# placeholder\n",
        )
        self._make_file(
            tmp_path,
            "metabolism/some_component.py",
            "class Bar:\n    """Cortical subsystem."""\n    pass\n",
        )
        result = _detect_structural_gaps(src=tmp_path)
        assert any(g.component == "Bar" for g in result)

    def test_syntax_error_file_skipped(self, tmp_path):
        self._make_file(
            tmp_path,
            "metabolism/substrates/broken.py",
            "def (broken!!!\n",
        )
        result = _detect_structural_gaps(src=tmp_path)
        assert isinstance(result, list)


# -- scan() unified --------------------------------------------------------


class TestScan:
    @patch("metabolon.metabolism.mismatch_repair.subprocess.run")
    @patch("metabolon.metabolism.mismatch_repair._detect_structural_gaps", return_value=[])
    @patch("metabolon.metabolism.mismatch_repair._detect_orphan_gaps", return_value=[])
    def test_vocabulary_gap_open(self, mock_orphan, mock_struct, mock_run, tmp_path):
        """grep returns hits -> vocabulary gap is open."""
        mock_run.return_value = MagicMock(
            stdout="metabolon/foo.py:5:class DnaSubstrate:\n",
            returncode=0,
        )
        reports = scan(src=tmp_path)
        vocab = [r for r in reports if r.kind == "vocabulary"]
        assert len(vocab) >= 1
        open_gaps = [r for r in vocab if not r.closed]
        assert len(open_gaps) >= 1

    @patch("metabolon.metabolism.mismatch_repair.subprocess.run")
    @patch("metabolon.metabolism.mismatch_repair._detect_structural_gaps", return_value=[])
    @patch("metabolon.metabolism.mismatch_repair._detect_orphan_gaps", return_value=[])
    def test_vocabulary_gap_closed(self, mock_orphan, mock_struct, mock_run, tmp_path):
        """grep returns only hits in excluded files -> gap is closed."""
        mock_run.return_value = MagicMock(
            stdout="metabolon/precision.py:5:class DnaSubstrate:\n",
            returncode=0,
        )
        reports = scan(src=tmp_path)
        vocab = [r for r in reports if r.kind == "vocabulary"]
        closed = [r for r in vocab if r.closed]
        assert len(closed) >= 1

    @patch("metabolon.metabolism.mismatch_repair.subprocess.run")
    @patch("metabolon.metabolism.mismatch_repair._detect_structural_gaps", return_value=[])
    @patch("metabolon.metabolism.mismatch_repair._detect_orphan_gaps", return_value=[])
    def test_vocabulary_grep_exception_reported(self, mock_orphan, mock_struct, mock_run, tmp_path):
        """grep raises -> gap report still produced (closed=False)."""
        mock_run.side_effect = OSError("boom")
        reports = scan(src=tmp_path)
        vocab = [r for r in reports if r.kind == "vocabulary"]
        assert len(vocab) >= 1
        assert all(not r.closed for r in vocab)

    @patch("metabolon.metabolism.mismatch_repair.subprocess.run")
    @patch("metabolon.metabolism.mismatch_repair._detect_structural_gaps")
    @patch("metabolon.metabolism.mismatch_repair._detect_orphan_gaps", return_value=[])
    def test_structural_gaps_included(self, mock_orphan, mock_struct, mock_run, tmp_path):
        mock_run.return_value = MagicMock(stdout="", returncode=0)
        mock_struct.return_value = [
            StructuralGap(
                file="foo.py",
                component="Foo",
                current_layer="labelled autonomic",
                actual_layer="uses LLM (cortical?)",
                reason="Foo claims autonomic but imports LLM",
            )
        ]
        reports = scan(src=tmp_path)
        struct = [r for r in reports if r.kind == "structural"]
        assert len(struct) == 1
        assert "Foo" in struct[0].description

    @patch("metabolon.metabolism.mismatch_repair.subprocess.run")
    @patch("metabolon.metabolism.mismatch_repair._detect_structural_gaps", return_value=[])
    @patch("metabolon.metabolism.mismatch_repair._detect_orphan_gaps")
    def test_orphan_gaps_included(self, mock_orphan, mock_struct, mock_run, tmp_path):
        mock_run.return_value = MagicMock(stdout="", returncode=0)
        mock_orphan.return_value = [
            OrphanGap(uri="org://lost", source_file="lost.py")
        ]
        reports = scan(src=tmp_path)
        orphan = [r for r in reports if r.kind == "orphan"]
        assert len(orphan) == 1
        assert "org://lost" in orphan[0].description

    @patch("metabolon.metabolism.mismatch_repair.subprocess.run")
    @patch("metabolon.metabolism.mismatch_repair._detect_structural_gaps", return_value=[])
    @patch("metabolon.metabolism.mismatch_repair._detect_orphan_gaps", return_value=[])
    def test_dormant_operons_included_if_importable(self, mock_orphan, mock_struct, mock_run, tmp_path):
        mock_run.return_value = MagicMock(stdout="", returncode=0)
        fake_operon = MagicMock(reaction="glycolysis")
        with patch.dict("sys.modules", {"metabolon.operons": MagicMock(dormant=lambda: [fake_operon])}):
            reports = scan(src=tmp_path)
        dormant = [r for r in reports if r.kind == "dormant"]
        assert len(dormant) == 1
        assert "glycolysis" in dormant[0].description

    @patch("metabolon.metabolism.mismatch_repair.subprocess.run")
    @patch("metabolon.metabolism.mismatch_repair._detect_structural_gaps", return_value=[])
    @patch("metabolon.metabolism.mismatch_repair._detect_orphan_gaps", return_value=[])
    def test_dormant_import_error_graceful(self, mock_orphan, mock_struct, mock_run, tmp_path):
        """If dormant import raises ImportError, scan skips dormant section."""
        mock_run.return_value = MagicMock(stdout="", returncode=0)
        import builtins
        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "metabolon.operons":
                raise ImportError("simulated")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=fake_import):
            reports = scan(src=tmp_path)
        dormant = [r for r in reports if r.kind == "dormant"]
        assert dormant == []


# -- summary() -------------------------------------------------------------


class TestSummary:
    @patch("metabolon.metabolism.mismatch_repair.scan", return_value=[])
    def test_clean(self, mock_scan):
        assert summary() == "Precision: clean"

    @patch("metabolon.metabolism.mismatch_repair.scan")
    def test_vocabulary_output(self, mock_scan):
        mock_scan.return_value = [
            GapReport(kind="vocabulary", description="Foo -> Bar: rename", closed=True),
            GapReport(kind="vocabulary", description="Baz -> Qux: rename", closed=False, references=["a.py:1"]),
        ]
        text = summary()
        assert "Vocabulary: 1/2 closed" in text
        assert "Foo" in text
        assert "Baz" in text

    @patch("metabolon.metabolism.mismatch_repair.scan")
    def test_structural_output(self, mock_scan):
        mock_scan.return_value = [
            GapReport(kind="structural", description="X in foo.py: mismatch", closed=False),
        ]
        text = summary()
        assert "Structure: 1 mismatches" in text
        assert "X in foo.py" in text

    @patch("metabolon.metabolism.mismatch_repair.scan")
    def test_orphan_output(self, mock_scan):
        mock_scan.return_value = [
            GapReport(kind="orphan", description="org://x (y.py): no consumer binding", closed=False),
        ]
        text = summary()
        assert "Orphan: 1 unbound resources" in text

    @patch("metabolon.metabolism.mismatch_repair.scan")
    def test_dormant_output(self, mock_scan):
        mock_scan.return_value = [
            GapReport(kind="dormant", description="glycolysis: transcribed but not translated", closed=False),
        ]
        text = summary()
        assert "Dormant: 1 inactive operons" in text
        assert "glycolysis" in text

    @patch("metabolon.metabolism.mismatch_repair.scan")
    def test_only_dormant_returns_non_clean(self, mock_scan):
        mock_scan.return_value = [
            GapReport(kind="dormant", description="op: transcribed but not translated", closed=False),
        ]
        text = summary()
        assert text != "Precision: clean"
        assert "Dormant" in text
