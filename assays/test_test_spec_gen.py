#!/usr/bin/env python3
"""Tests for effectors/test-spec-gen — sortase-ready test spec generator."""
from __future__ import annotations

import re
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

EFFECTOR_PATH = Path(__file__).resolve().parents[1] / "effectors" / "test-spec-gen"


def _load_module():
    """Load test-spec-gen via exec (effector pattern, not importable)."""
    source = EFFECTOR_PATH.read_text(encoding="utf-8")
    ns: dict = {"__name__": "test_spec_gen", "__file__": str(EFFECTOR_PATH)}
    exec(source, ns)
    return ns


_mod = _load_module()
_test_filename = _mod["_test_filename"]
_read_imports = _mod["_read_imports"]
generate_spec = _mod["generate_spec"]
GERMLINE = _mod["GERMLINE"]
PLANS_DIR = _mod["PLANS_DIR"]


# ── File-level tests ────────────────────────────────────────────────────────


class TestFileBasics:
    def test_file_exists(self):
        assert EFFECTOR_PATH.exists()
        assert EFFECTOR_PATH.is_file()

    def test_is_python_script(self):
        first_line = EFFECTOR_PATH.read_text().split("\n")[0]
        assert first_line.startswith("#!/usr/bin/env python")

    def test_has_docstring(self):
        source = EFFECTOR_PATH.read_text()
        assert "Generate sortase-ready test specs" in source


# ── _test_filename tests ───────────────────────────────────────────────────


class TestTestFilename:
    def test_simple_module(self):
        assert _test_filename("metabolon/organelles/chromatin.py") == "test_chromatin.py"

    def test_enzymes_subdir(self):
        assert _test_filename("metabolon/enzymes/sortase.py") == "test_sortase_actions.py"

    def test_sortase_subdir(self):
        assert _test_filename("metabolon/sortase/linter.py") == "test_sortase_linter.py"

    def test_organelles_subdir(self):
        assert _test_filename("metabolon/organelles/pulse.py") == "test_pulse.py"

    def test_metabolism_substrate(self):
        """Metabolism subdir with extra nesting → substrate suffix."""
        assert _test_filename("metabolon/metabolism/spending/parser.py") == "test_parser_substrate.py"

    def test_flat_module(self):
        """Module without matching subdir falls through to default."""
        assert _test_filename("metabolon/other/thing.py") == "test_thing.py"

    def test_single_component(self):
        """Bare filename produces test_<name>.py."""
        assert _test_filename("foo.py") == "test_foo.py"


# ── _read_imports tests ────────────────────────────────────────────────────


class TestReadImports:
    def test_extracts_metabolon_imports(self):
        src = textwrap.dedent("""\
            from metabolon.organelles.pulse import Pulse
            import metabolon
            from metabolon.enzymes.sortase import run
        """)
        result = _read_imports(src)
        assert len(result) == 3
        assert "from metabolon.organelles.pulse import Pulse" in result

    def test_ignores_other_imports(self):
        src = textwrap.dedent("""\
            import os
            from pathlib import Path
            from unittest.mock import patch
        """)
        assert _read_imports(src) == []

    def test_empty_source(self):
        assert _read_imports("") == []

    def test_mixed_imports(self):
        src = textwrap.dedent("""\
            import os
            from metabolon.core import Engine
            import sys
        """)
        result = _read_imports(src)
        assert len(result) == 1
        assert "from metabolon.core import Engine" in result


# ── generate_spec tests ────────────────────────────────────────────────────


class TestGenerateSpec:
    def test_generates_plan_for_existing_module(self, tmp_path, monkeypatch):
        """generate_spec creates a plan file when module exists."""
        mod_dir = tmp_path / "metabolon" / "organelles"
        mod_dir.mkdir(parents=True)
        mod_file = mod_dir / "chromatin.py"
        mod_file.write_text(textwrap.dedent("""\
            '''Chromatin module.'''
            from metabolon.core import Base

            def process(data):
                return data

            class Handler:
                pass
        """))

        plans = tmp_path / "loci" / "plans"
        plans.mkdir(parents=True, exist_ok=True)

        monkeypatch.setitem(_mod, "GERMLINE", tmp_path)
        monkeypatch.setitem(_mod, "PLANS_DIR", plans)

        result = generate_spec("metabolon/organelles/chromatin.py")

        assert result.exists()
        content = result.read_text()
        assert "test_chromatin.py" in content
        assert "process" in content
        assert "Handler" in content

    def test_embeds_full_source_for_small_module(self, tmp_path, monkeypatch):
        """Small modules (≤200 lines) get full source embedded."""
        mod_dir = tmp_path / "metabolon" / "organelles"
        mod_dir.mkdir(parents=True)
        mod_file = mod_dir / "small.py"
        mod_file.write_text("def hello():\n    return 'world'\n")

        plans = tmp_path / "loci" / "plans"
        plans.mkdir(parents=True, exist_ok=True)

        monkeypatch.setitem(_mod, "GERMLINE", tmp_path)
        monkeypatch.setitem(_mod, "PLANS_DIR", plans)

        result = generate_spec("metabolon/organelles/small.py")

        content = result.read_text()
        assert "Source code (DO NOT MODIFY" in content

    def test_api_signatures_for_large_module(self, tmp_path, monkeypatch):
        """Large modules (>200 lines) get API signatures only."""
        mod_dir = tmp_path / "metabolon" / "organelles"
        mod_dir.mkdir(parents=True)
        mod_file = mod_dir / "big.py"
        lines = ["# line"] * 250
        lines.insert(5, "def important():")
        lines.insert(6, '    """Do something."""')
        mod_file.write_text("\n".join(lines))

        plans = tmp_path / "loci" / "plans"
        plans.mkdir(parents=True, exist_ok=True)

        monkeypatch.setitem(_mod, "GERMLINE", tmp_path)
        monkeypatch.setitem(_mod, "PLANS_DIR", plans)

        result = generate_spec("metabolon/organelles/big.py")

        content = result.read_text()
        assert "API signatures" in content
        assert "250 lines" in content

    def test_wave_number_in_plan_name(self, tmp_path, monkeypatch):
        """--wave flag causes wave number prefix in plan name."""
        mod_dir = tmp_path / "metabolon" / "organelles"
        mod_dir.mkdir(parents=True)
        (mod_dir / "pulse.py").write_text("def run(): pass\n")

        plans = tmp_path / "loci" / "plans"
        plans.mkdir(parents=True, exist_ok=True)

        monkeypatch.setitem(_mod, "GERMLINE", tmp_path)
        monkeypatch.setitem(_mod, "PLANS_DIR", plans)

        result = generate_spec("metabolon/organelles/pulse.py", wave=6)
        assert result.name == "wave-6-test-pulse.md"

    def test_nonexistent_module_exits(self, tmp_path, monkeypatch):
        """generate_spec exits with error for nonexistent module."""
        monkeypatch.setitem(_mod, "GERMLINE", tmp_path)
        monkeypatch.setitem(_mod, "PLANS_DIR", tmp_path / "plans")

        with pytest.raises(SystemExit):
            generate_spec("nonexistent/module.py")

    def test_spec_lists_public_api(self, tmp_path, monkeypatch):
        """Generated spec lists public functions/classes."""
        mod_dir = tmp_path / "metabolon" / "organelles"
        mod_dir.mkdir(parents=True)
        (mod_dir / "api.py").write_text(textwrap.dedent("""\
            def public_func():
                pass
            def _private_func():
                pass
            class PublicClass:
                pass
        """))

        plans = tmp_path / "loci" / "plans"
        plans.mkdir(parents=True, exist_ok=True)

        monkeypatch.setitem(_mod, "GERMLINE", tmp_path)
        monkeypatch.setitem(_mod, "PLANS_DIR", plans)

        result = generate_spec("metabolon/organelles/api.py")

        content = result.read_text()
        assert "public_func" in content
        assert "PublicClass" in content
        api_lines = [l for l in content.splitlines() if "Public API:" in l]
        if api_lines:
            assert "_private_func" not in api_lines[0]

    def test_spec_includes_shell_redirect_instruction(self, tmp_path, monkeypatch):
        """Generated spec includes shell redirect instruction."""
        mod_dir = tmp_path / "metabolon" / "organelles"
        mod_dir.mkdir(parents=True)
        (mod_dir / "x.py").write_text("def run(): pass\n")

        plans = tmp_path / "loci" / "plans"
        plans.mkdir(parents=True, exist_ok=True)

        monkeypatch.setitem(_mod, "GERMLINE", tmp_path)
        monkeypatch.setitem(_mod, "PLANS_DIR", plans)

        result = generate_spec("metabolon/organelles/x.py")

        content = result.read_text()
        assert "cat << 'PYEOF'" in content
        assert "CRITICAL" in content


# ── main (CLI) tests ───────────────────────────────────────────────────────


class TestMain:
    def test_main_generates_plans(self, tmp_path, monkeypatch):
        """main() generates a plan per module."""
        mod_dir = tmp_path / "metabolon" / "organelles"
        mod_dir.mkdir(parents=True)
        (mod_dir / "target.py").write_text("def run(): pass\n")

        plans = tmp_path / "loci" / "plans"
        plans.mkdir(parents=True, exist_ok=True)

        monkeypatch.setitem(_mod, "GERMLINE", tmp_path)
        monkeypatch.setitem(_mod, "PLANS_DIR", plans)

        with patch("sys.argv", ["test-spec-gen", "metabolon/organelles/target.py"]):
            _mod["main"]()

        generated = list(plans.glob("test-target.md"))
        assert len(generated) == 1

    def test_main_with_wave(self, tmp_path, monkeypatch):
        """main() passes wave number to generate_spec."""
        mod_dir = tmp_path / "metabolon" / "organelles"
        mod_dir.mkdir(parents=True)
        (mod_dir / "wave.py").write_text("def run(): pass\n")

        plans = tmp_path / "loci" / "plans"
        plans.mkdir(parents=True, exist_ok=True)

        monkeypatch.setitem(_mod, "GERMLINE", tmp_path)
        monkeypatch.setitem(_mod, "PLANS_DIR", plans)

        with patch("sys.argv", ["test-spec-gen", "--wave", "3", "metabolon/organelles/wave.py"]):
            _mod["main"]()

        generated = list(plans.glob("wave-3-test-wave.md"))
        assert len(generated) == 1
