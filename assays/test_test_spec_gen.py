"""Tests for effectors/test-spec-gen — generate sortase-ready test specs."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

EFFECTOR = Path(__file__).resolve().parent.parent / "effectors" / "test-spec-gen"


@pytest.fixture()
def spec_mod(tmp_path, monkeypatch):
    """Load test-spec-gen via exec into an isolated namespace."""
    # Point GERMLINE / PLANS_DIR at tmp so we never write into real loci/plans
    ns: dict = {}
    exec(EFFECTOR.read_text(), ns)
    # Override paths inside the loaded namespace
    monkeypatch.setattr(ns["Path"], "home", classmethod(lambda cls: tmp_path))
    # Re-evaluate GERMLINE and PLANS_DIR after patching home
    ns["GERMLINE"] = tmp_path / "germline"
    ns["PLANS_DIR"] = ns["GERMLINE"] / "loci" / "plans"
    ns["PLANS_DIR"].mkdir(parents=True, exist_ok=True)
    return ns


# ── _test_filename ──────────────────────────────────────────────────────────

class TestTestFilename:
    def test_simple_module(self, spec_mod):
        assert spec_mod["_test_filename"]("metabolon/foo.py") == "test_foo.py"

    def test_enzymes_subdir(self, spec_mod):
        assert spec_mod["_test_filename"]("metabolon/enzymes/bar.py") == "test_bar_actions.py"

    def test_sortase_subdir(self, spec_mod):
        assert spec_mod["_test_filename"]("metabolon/sortase/baz.py") == "test_sortase_baz.py"

    def test_organelles_subdir(self, spec_mod):
        assert spec_mod["_test_filename"]("metabolon/organelles/qux.py") == "test_qux.py"

    def test_metabolism_deep_subdir(self, spec_mod):
        assert spec_mod["_test_filename"]("metabolon/metabolism/spending/qux.py") == "test_qux_substrate.py"

    def test_shallow_metabolism(self, spec_mod):
        """metabolon/metabolism/qux.py (only 2 parts after split) → plain test_."""
        assert spec_mod["_test_filename"]("metabolon/metabolism/qux.py") == "test_qux.py"

    def test_strips_suffix(self, spec_mod):
        assert spec_mod["_test_filename"]("foo/bar/baz.py") == "test_baz.py"


# ── _read_imports ───────────────────────────────────────────────────────────

class TestReadImports:
    def test_extracts_metabolon_imports(self, spec_mod):
        src = "from metabolon.foo import bar\nimport metabolon.baz\nimport os\n"
        result = spec_mod["_read_imports"](src)
        assert len(result) == 2
        assert "from metabolon.foo import bar" in result
        assert "import metabolon.baz" in result

    def test_no_metabolon_imports(self, spec_mod):
        src = "import os\nimport sys\n"
        assert spec_mod["_read_imports"](src) == []

    def test_empty_source(self, spec_mod):
        assert spec_mod["_read_imports"]("") == []


# ── generate_spec ───────────────────────────────────────────────────────────

class TestGenerateSpec:
    def _write_module(self, spec_mod, rel_path: str, source: str) -> Path:
        full = spec_mod["GERMLINE"] / rel_path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(source)
        return full

    def test_generates_plan_file(self, spec_mod):
        self._write_module(spec_mod, "metabolon/example.py",
                           "def foo():\n    pass\n")
        plan = spec_mod["generate_spec"]("metabolon/example.py")
        assert plan.exists()
        content = plan.read_text()
        assert "test_example.py" in content

    def test_embeds_small_source(self, spec_mod):
        src = "def hello():\n    return 42\n"
        self._write_module(spec_mod, "metabolon/small.py", src)
        plan = spec_mod["generate_spec"]("metabolon/small.py")
        content = plan.read_text()
        assert "def hello():" in content
        assert "Source code" in content

    def test_summarises_large_source(self, spec_mod):
        src = "\n".join([f"# line {i}" for i in range(250)] + "def big():\n    pass\n")
        self._write_module(spec_mod, "metabolon/big.py", src)
        plan = spec_mod["generate_spec"]("metabolon/big.py")
        content = plan.read_text()
        assert "API signatures" in content
        assert "def big():" in content

    def test_wave_prefix(self, spec_mod):
        self._write_module(spec_mod, "metabolon/wmod.py", "pass\n")
        plan = spec_mod["generate_spec"]("metabolon/wmod.py", wave=6)
        assert plan.name == "wave-6-test-wmod.md"

    def test_public_api_extraction(self, spec_mod):
        src = "def public_fn():\n    pass\n\ndef _private():\n    pass\n\nclass Pub:\n    pass\n"
        self._write_module(spec_mod, "metabolon/api.py", src)
        plan = spec_mod["generate_spec"]("metabolon/api.py")
        content = plan.read_text()
        assert "public_fn" in content
        assert "Pub" in content
        assert "_private" not in content

    def test_missing_module_exits(self, spec_mod):
        with pytest.raises(SystemExit):
            spec_mod["generate_spec"]("metabolon/nonexistent.py")

    def test_shell_redirect_instruction(self, spec_mod):
        self._write_module(spec_mod, "metabolon/rr.py", "pass\n")
        plan = spec_mod["generate_spec"]("metabolon/rr.py")
        content = plan.read_text()
        assert "cat << 'PYEOF'" in content
        assert "write_file" not in content or "Do NOT use the write_file tool" in content


# ── main (CLI) ──────────────────────────────────────────────────────────────

class TestMain:
    def test_main_generates_plans(self, spec_mod, capsys, monkeypatch):
        self = sys.modules[__name__]
        full = spec_mod["GERMLINE"] / "metabolon" / "cli_test.py"
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text("pass\n")
        monkeypatch.setattr(sys, "argv", ["test-spec-gen", "metabolon/cli_test.py"])
        spec_mod["main"]()
        out = capsys.readouterr().out
        assert "Generated:" in out
