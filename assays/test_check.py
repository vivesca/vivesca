"""Tests for metabolon.gastrulation.check."""

from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING

import pytest

from metabolon.gastrulation.check import (
    _check_prompt_file,
    _check_resource_file,
    _check_tool_file,
    _detect_module,
    probe_gastrulation,
)

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# _detect_module
# ---------------------------------------------------------------------------


class TestDetectModule:
    def test_single_module(self, tmp_path: Path) -> None:
        (tmp_path / "src" / "my_pkg").mkdir(parents=True)
        assert _detect_module(tmp_path) == "my_pkg"

    def test_multiple_modules(self, tmp_path: Path) -> None:
        (tmp_path / "src" / "pkg_a").mkdir(parents=True)
        (tmp_path / "src" / "pkg_b").mkdir(parents=True)
        assert _detect_module(tmp_path) == ""

    def test_no_src_dir_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            _detect_module(tmp_path)

    def test_hidden_dirs_ignored(self, tmp_path: Path) -> None:
        (tmp_path / "src" / ".hidden").mkdir(parents=True)
        (tmp_path / "src" / "real_pkg").mkdir(parents=True)
        assert _detect_module(tmp_path) == "real_pkg"


# ---------------------------------------------------------------------------
# _check_tool_file
# ---------------------------------------------------------------------------


class TestCheckToolFile:
    def test_tool_with_all_required(self, tmp_path: Path) -> None:
        code = textwrap.dedent("""\
            from typing import Annotated
            @tool(description="d", annotations=ToolAnnotations())
            def my_tool(x: int) -> str:
                return str(x)
        """)
        p = tmp_path / "good_tool.py"
        p.write_text(code)
        issues = _check_tool_file(p)
        assert issues == []

    def test_tool_missing_return_type(self, tmp_path: Path) -> None:
        code = textwrap.dedent("""\
            @tool(description="d", annotations=ToolAnnotations())
            def my_tool(x: int):
                return str(x)
        """)
        p = tmp_path / "no_return.py"
        p.write_text(code)
        issues = _check_tool_file(p)
        assert any("missing return type annotation" in i for i in issues)

    def test_tool_missing_annotations_kwarg(self, tmp_path: Path) -> None:
        code = textwrap.dedent("""\
            @tool(description="d")
            def my_tool(x: int) -> str:
                return str(x)
        """)
        p = tmp_path / "no_ann.py"
        p.write_text(code)
        issues = _check_tool_file(p)
        assert any("annotations=ToolAnnotations" in i for i in issues)

    def test_tool_missing_description_kwarg(self, tmp_path: Path) -> None:
        code = textwrap.dedent("""\
            @tool(annotations=ToolAnnotations())
            def my_tool(x: int) -> str:
                return str(x)
        """)
        p = tmp_path / "no_desc.py"
        p.write_text(code)
        issues = _check_tool_file(p)
        assert any("missing description" in i for i in issues)

    def test_syntax_error(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.py"
        p.write_text("def (broken:")
        issues = _check_tool_file(p)
        assert any("syntax error" in i for i in issues)

    def test_non_tool_function_ignored(self, tmp_path: Path) -> None:
        code = textwrap.dedent("""\
            def helper(x):
                return x
        """)
        p = tmp_path / "helper.py"
        p.write_text(code)
        assert _check_tool_file(p) == []


# ---------------------------------------------------------------------------
# _check_prompt_file
# ---------------------------------------------------------------------------


class TestCheckPromptFile:
    def test_prompt_with_description(self, tmp_path: Path) -> None:
        code = textwrap.dedent("""\
            @prompt(description="A helpful prompt")
            def my_prompt(name: str) -> str:
                return f"Hello {name}"
        """)
        p = tmp_path / "good_prompt.py"
        p.write_text(code)
        assert _check_prompt_file(p) == []

    def test_prompt_missing_description(self, tmp_path: Path) -> None:
        code = textwrap.dedent("""\
            @prompt()
            def my_prompt(name: str) -> str:
                return f"Hello {name}"
        """)
        p = tmp_path / "no_desc_prompt.py"
        p.write_text(code)
        issues = _check_prompt_file(p)
        assert any("missing description" in i for i in issues)

    def test_prompt_syntax_error(self, tmp_path: Path) -> None:
        p = tmp_path / "bad_prompt.py"
        p.write_text("@prompt(")
        issues = _check_prompt_file(p)
        assert any("syntax error" in i for i in issues)


# ---------------------------------------------------------------------------
# _check_resource_file
# ---------------------------------------------------------------------------


class TestCheckResourceFile:
    def test_resource_with_uri(self, tmp_path: Path) -> None:
        code = textwrap.dedent("""\
            @resource("my://resource")
            def my_resource() -> str:
                return "data"
        """)
        p = tmp_path / "good_res.py"
        p.write_text(code)
        assert _check_resource_file(p) == []

    def test_resource_missing_uri(self, tmp_path: Path) -> None:
        code = textwrap.dedent("""\
            @resource()
            def my_resource() -> str:
                return "data"
        """)
        p = tmp_path / "no_uri.py"
        p.write_text(code)
        issues = _check_resource_file(p)
        assert any("missing URI" in i for i in issues)

    def test_resource_syntax_error(self, tmp_path: Path) -> None:
        p = tmp_path / "bad_res.py"
        p.write_text("def (")
        issues = _check_resource_file(p)
        assert any("syntax error" in i for i in issues)


# ---------------------------------------------------------------------------
# probe_gastrulation (integration)
# ---------------------------------------------------------------------------


class TestProbeGastrulation:
    def test_empty_project(self, tmp_path: Path) -> None:
        (tmp_path / "src" / "pkg").mkdir(parents=True)
        assert probe_gastrulation(tmp_path) == []

    def test_full_project_with_issues(self, tmp_path: Path) -> None:
        pkg = tmp_path / "src" / "myapp"
        (pkg / "enzymes").mkdir(parents=True)
        (pkg / "codons").mkdir(parents=True)
        (pkg / "resources").mkdir(parents=True)

        # Bad tool — missing return type and annotations
        (pkg / "enzymes" / "bad_tool.py").write_text(
            textwrap.dedent("""\
            @tool(description="d")
            def bad(x: int):
                return x
        """)
        )
        # Bad prompt — missing description
        (pkg / "codons" / "bad_prompt.py").write_text(
            textwrap.dedent("""\
            @prompt()
            def bad_prompt() -> str:
                return "hi"
        """)
        )
        # Bad resource — missing URI
        (pkg / "resources" / "bad_res.py").write_text(
            textwrap.dedent("""\
            @resource()
            def bad_res() -> str:
                return "data"
        """)
        )

        issues = probe_gastrulation(tmp_path)
        assert len(issues) >= 3
        assert any("missing return type" in i for i in issues)
        assert any("missing description" in i and "prompt" in i for i in issues)
        assert any("missing URI" in i for i in issues)

    def test_full_project_all_good(self, tmp_path: Path) -> None:
        pkg = tmp_path / "src" / "myapp"
        (pkg / "enzymes").mkdir(parents=True)

        (pkg / "enzymes" / "good_tool.py").write_text(
            textwrap.dedent("""\
            @tool(description="d", annotations=ToolAnnotations())
            def good(x: int) -> str:
                return str(x)
        """)
        )

        assert probe_gastrulation(tmp_path) == []
